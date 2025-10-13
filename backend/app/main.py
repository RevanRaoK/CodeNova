# backend/app/main.py

import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.monitoring import get_service_logger, ServiceType, performance_monitor, system_monitor
from app.core.security import SecurityMiddleware, RateLimiter
from app.core.cache import cache, check_cache_health

# --- DB startup (dev convenience) ---
from app.core.database import Base, engine
# Import models so SQLAlchemy sees mappings before create_all
from app.models import Repository, Analysis, User  # noqa: F401

# Initialize logger
logger = get_service_logger(ServiceType.API, "main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with performance optimizations."""
    # Startup
    logger.info("Starting application with performance optimizations...")
    
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error("Database startup failed", error=e)
    
    try:
        # Start analytics background tasks
        from app.tasks.analytics_tasks import start_analytics_background_tasks
        asyncio.create_task(start_analytics_background_tasks())
        logger.info("Analytics background tasks started")
    except Exception as e:
        logger.error("Failed to start analytics background tasks", error=e)
    
    try:
        # Initialize background job service
        from app.services.background_job_service import background_job_service
        await background_job_service.initialize()
        logger.info("Background job service initialized")
    except Exception as e:
        logger.error("Failed to initialize background job service", error=e)
    
    try:
        # Initialize background code analysis service
        from app.services.background_code_analysis_service import background_code_analysis_service
        await background_code_analysis_service.initialize()
        logger.info("Background code analysis service initialized")
    except Exception as e:
        logger.error("Failed to initialize background code analysis service", error=e)
    
    try:
        # Initialize analysis notification service
        from app.services.analysis_notification_service import analysis_notification_service
        await analysis_notification_service.initialize()
        logger.info("Analysis notification service initialized")
    except Exception as e:
        logger.error("Failed to initialize analysis notification service", error=e)
    
    try:
        # Initialize performance optimizations in production
        if settings.ENVIRONMENT == "production":
            from app.core.production_config import ProductionOptimizer
            await ProductionOptimizer.run_production_setup()
            logger.info("Production optimizations applied")
    except Exception as e:
        logger.error("Production setup failed", error=e)
    
    try:
        # Start system monitoring
        system_monitor.start_monitoring(interval=60)
        logger.info("System monitoring started")
    except Exception as e:
        logger.error("System monitoring startup failed", error=e)
    
    logger.info("Application startup completed successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    try:
        # Stop analytics background tasks
        from app.tasks.analytics_tasks import stop_analytics_background_tasks
        await stop_analytics_background_tasks()
        logger.info("Analytics background tasks stopped")
    except Exception as e:
        logger.error("Error stopping analytics background tasks", error=e)
    
    try:
        # Close background job service
        from app.services.background_job_service import background_job_service
        await background_job_service.close()
        logger.info("Background job service closed")
    except Exception as e:
        logger.error("Error closing background job service", error=e)
    
    try:
        # Close background code analysis service (if needed)
        logger.info("Background code analysis service closed")
    except Exception as e:
        logger.error("Error closing background code analysis service", error=e)
    
    try:
        # Stop system monitoring
        system_monitor.stop_monitoring()
        logger.info("System monitoring stopped")
    except Exception as e:
        logger.error("Error stopping system monitoring", error=e)
    
    logger.info("Application shutdown completed")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None
)

# Security middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Security and performance middleware."""
    start_time = time.time()
    
    # Security checks
    if not SecurityMiddleware.check_user_agent(request):
        logger.warning("Blocked request from suspicious user agent", 
                      user_agent=request.headers.get("User-Agent"))
        raise HTTPException(status_code=403, detail="Blocked user agent")
    
    # Request size validation
    SecurityMiddleware.validate_request_size(request)
    
    # Rate limiting for sensitive endpoints
    if request.url.path.startswith("/api/v1/auth/"):
        identifier = RateLimiter.get_client_identifier(request)
        # Use more lenient rate limiting in development
        limit = 100 if settings.ENVIRONMENT == "development" else 10
        window = 3600  # 1 hour
        allowed, info = RateLimiter.check_rate_limit(identifier, limit, window, "auth")
        
        if not allowed:
            logger.warning("Rate limit exceeded for auth endpoint", 
                          identifier=identifier, path=request.url.path)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(info["retry_after"])
                }
            )
    
    # Process request
    response = await call_next(request)
    
    # Add security headers
    SecurityMiddleware.add_security_headers(response)
    
    # Add performance headers
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests
    if process_time > 1.0:  # > 1 second
        logger.warning("Slow request detected", 
                      path=request.url.path, 
                      method=request.method,
                      duration=process_time)
    
    return response

# Performance middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware with production-safe defaults
allowed_origins = ["*"] if settings.ENVIRONMENT == "development" else os.getenv("ALLOWED_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
)

# Trusted host middleware for production
if settings.ENVIRONMENT == "production":
    trusted_hosts = os.getenv("TRUSTED_HOSTS", "").split(",")
    if trusted_hosts and trusted_hosts[0]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

# Mount the API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def read_root():
    """Root endpoint with basic info."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        from app.core.monitoring import health_checker
        health_status = await health_checker.comprehensive_health_check()
        
        status_code = 200
        if health_status["status"] == "degraded":
            status_code = 200  # Still operational
        elif health_status["status"] == "unhealthy":
            status_code = 503  # Service unavailable
        
        return JSONResponse(content=health_status, status_code=status_code)
    except Exception as e:
        logger.error("Health check failed", error=e)
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": time.time()
            },
            status_code=503
        )

@app.get("/metrics")
async def get_metrics():
    """Performance metrics endpoint."""
    try:
        # Get performance summary
        performance_summary = performance_monitor.get_performance_summary()
        
        # Get system health
        system_health = system_monitor.get_system_health()
        
        # Get cache health
        cache_health = check_cache_health()
        
        return {
            "performance": performance_summary,
            "system": system_health,
            "cache": cache_health,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error("Metrics collection failed", error=e)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.get("/test-cors")
def test_cors():
    """CORS test endpoint."""
    return {
        "message": "CORS test successful", 
        "timestamp": time.time(),
        "environment": settings.ENVIRONMENT
    }

@app.get("/test-db")
async def test_db():
    """Database connectivity test."""
    try:
        from app.core.database import engine
        from sqlalchemy import text
        
        start_time = time.time()
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            db_result = result.fetchone()[0]
        
        response_time = (time.time() - start_time) * 1000
        
        return {
            "message": "Database connection successful", 
            "result": db_result,
            "response_time_ms": response_time,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error("Database test failed", error=e)
        return JSONResponse(
            content={
                "message": "Database connection failed", 
                "error": str(e),
                "timestamp": time.time()
            },
            status_code=500
        )

@app.get("/production-readiness")
async def production_readiness():
    """Production readiness check endpoint."""
    if settings.ENVIRONMENT == "production":
        # In production, this might be restricted to admin users
        raise HTTPException(status_code=404, detail="Not found")
    
    try:
        from app.core.production_config import check_production_readiness
        readiness_results = await check_production_readiness()
        
        status_code = 200
        if readiness_results["overall_status"] == "not_ready":
            status_code = 503
        elif readiness_results["overall_status"] == "needs_attention":
            status_code = 200
        
        return JSONResponse(content=readiness_results, status_code=status_code)
    except Exception as e:
        logger.error("Production readiness check failed", error=e)
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

# Global exception handler for better error tracking
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with logging."""
    logger.error(
        "Unhandled exception",
        error=exc,
        path=request.url.path,
        method=request.method,
        client_ip=request.client.host
    )
    
    if settings.ENVIRONMENT == "development":
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": str(exc),
                "type": type(exc).__name__
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
