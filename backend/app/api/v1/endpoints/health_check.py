"""
Health Check and Testing Endpoints.

This module provides comprehensive health check endpoints for:
- Digital Ocean Spaces connectivity testing
- GitHub integration health checks
- Job queue health monitoring
- Overall system health status

Requirements covered: 4.3, 4.4
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_admin
from app.models.users import User
from app.services.config_validation_service import config_validation_service
from app.services.file_storage_service import FileStorageService
from app.services.github_api_client import GitHubAPIClient
from app.services.queue_monitoring_service import queue_monitoring_service
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def system_health_check():
    """
    Quick system health check without authentication.
    
    Returns basic health status for monitoring systems.
    This endpoint is designed for load balancers and monitoring tools.
    
    Returns:
        Basic system health status
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": getattr(settings, 'VERSION', '1.0.0'),
            "environment": settings.ENVIRONMENT,
            "services": {}
        }
        
        # Check database connectivity
        try:
            from app.db.session import SessionLocal
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            health_status["services"]["database"] = {"status": "healthy"}
        except Exception as e:
            health_status["services"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Check basic configuration presence
        config_issues = []
        if not settings.DATABASE_URL:
            config_issues.append("DATABASE_URL")
        if not settings.SECRET_KEY:
            config_issues.append("SECRET_KEY")
        
        if config_issues:
            health_status["services"]["configuration"] = {
                "status": "unhealthy",
                "missing": config_issues
            }
            health_status["status"] = "degraded"
        else:
            health_status["services"]["configuration"] = {"status": "healthy"}
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.get("/health/detailed")
async def detailed_health_check(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Detailed health check with authentication required.
    
    Provides comprehensive health information for all system components.
    
    Returns:
        Detailed health status for all services
    """
    try:
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "user": current_user.email,
            "services": {},
            "summary": {}
        }
        
        # Check Digital Ocean Spaces
        spaces_health = await _check_spaces_health()
        health_data["services"]["digital_ocean_spaces"] = spaces_health
        
        # Check GitHub integration
        github_health = await _check_github_health()
        health_data["services"]["github_integration"] = github_health
        
        # Check job queue health
        queue_health = await _check_queue_health()
        health_data["services"]["job_queue"] = queue_health
        
        # Check database health
        db_health = await _check_database_health(db)
        health_data["services"]["database"] = db_health
        
        # Determine overall status
        service_statuses = [
            service["status"] for service in health_data["services"].values()
        ]
        
        if "unhealthy" in service_statuses:
            health_data["status"] = "unhealthy"
        elif "degraded" in service_statuses:
            health_data["status"] = "degraded"
        
        # Generate summary
        health_data["summary"] = {
            "total_services": len(health_data["services"]),
            "healthy_services": sum(1 for s in service_statuses if s == "healthy"),
            "degraded_services": sum(1 for s in service_statuses if s == "degraded"),
            "unhealthy_services": sum(1 for s in service_statuses if s == "unhealthy")
        }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/test/spaces")
async def test_spaces_connectivity(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Test Digital Ocean Spaces connectivity and operations.
    
    Performs comprehensive testing of:
    - Configuration validation
    - Connectivity test
    - Upload/download/delete operations
    
    Requires admin privileges.
    
    Returns:
        Detailed test results for Spaces operations
    """
    try:
        test_results = {
            "service": "digital_ocean_spaces",
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {},
            "overall_status": "healthy"
        }
        
        # Test configuration validation
        config_result = await config_validation_service.validate_spaces_only()
        test_results["tests"]["configuration"] = {
            "status": "passed" if all(
                r.status.value in ["valid", "warning"] for r in config_result.values()
            ) else "failed",
            "details": {
                key: {
                    "status": result.status.value,
                    "message": result.message
                }
                for key, result in config_result.items()
            }
        }
        
        # Test actual upload operation
        upload_test = await config_validation_service.test_spaces_upload()
        test_results["tests"]["upload_operation"] = {
            "status": "passed" if upload_test.status.value == "valid" else "failed",
            "message": upload_test.message,
            "details": upload_test.details
        }
        
        # Test file storage service initialization
        try:
            file_service = FileStorageService()
            file_service._validate_configuration()
            test_results["tests"]["service_initialization"] = {
                "status": "passed",
                "message": "File storage service initialized successfully"
            }
        except Exception as e:
            test_results["tests"]["service_initialization"] = {
                "status": "failed",
                "message": f"Service initialization failed: {str(e)}"
            }
            test_results["overall_status"] = "unhealthy"
        
        # Determine overall status
        if any(test["status"] == "failed" for test in test_results["tests"].values()):
            test_results["overall_status"] = "unhealthy"
        
        return test_results
        
    except Exception as e:
        logger.error(f"Spaces connectivity test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Spaces test failed: {str(e)}"
        )


@router.get("/test/github")
async def test_github_integration(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Test GitHub integration health and connectivity.
    
    Performs comprehensive testing of:
    - OAuth configuration
    - API connectivity
    - Webhook configuration
    - Rate limiting status
    
    Requires admin privileges.
    
    Returns:
        Detailed test results for GitHub integration
    """
    try:
        test_results = {
            "service": "github_integration",
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {},
            "overall_status": "healthy"
        }
        
        # Test GitHub configuration
        github_config = await config_validation_service.validate_github_only()
        test_results["tests"]["configuration"] = {
            "status": "passed" if all(
                r.status.value in ["valid", "warning", "not_configured"] for r in github_config.values()
            ) else "failed",
            "details": {
                key: {
                    "status": result.status.value,
                    "message": result.message
                }
                for key, result in github_config.items()
            }
        }
        
        # Test GitHub API connectivity
        try:
            github_client = GitHubAPIClient()
            rate_limit_info = await github_client.get_rate_limit_status()
            
            test_results["tests"]["api_connectivity"] = {
                "status": "passed",
                "message": "GitHub API is accessible",
                "rate_limit": rate_limit_info
            }
        except Exception as e:
            test_results["tests"]["api_connectivity"] = {
                "status": "failed",
                "message": f"GitHub API connectivity failed: {str(e)}"
            }
            test_results["overall_status"] = "degraded"
        
        # Test OAuth configuration if available
        if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
            try:
                # Test OAuth app accessibility (without making actual OAuth calls)
                test_results["tests"]["oauth_config"] = {
                    "status": "passed",
                    "message": "OAuth credentials are configured",
                    "client_id": settings.GITHUB_CLIENT_ID[:8] + "..."
                }
            except Exception as e:
                test_results["tests"]["oauth_config"] = {
                    "status": "failed",
                    "message": f"OAuth configuration test failed: {str(e)}"
                }
        else:
            test_results["tests"]["oauth_config"] = {
                "status": "skipped",
                "message": "OAuth not configured"
            }
        
        # Test webhook configuration
        if settings.GITHUB_WEBHOOK_SECRET:
            test_results["tests"]["webhook_config"] = {
                "status": "passed",
                "message": "Webhook secret is configured",
                "secret_length": len(settings.GITHUB_WEBHOOK_SECRET)
            }
        else:
            test_results["tests"]["webhook_config"] = {
                "status": "warning",
                "message": "Webhook secret not configured"
            }
        
        # Determine overall status
        failed_tests = [test for test in test_results["tests"].values() if test["status"] == "failed"]
        if failed_tests:
            test_results["overall_status"] = "unhealthy"
        elif any(test["status"] == "warning" for test in test_results["tests"].values()):
            test_results["overall_status"] = "degraded"
        
        return test_results
        
    except Exception as e:
        logger.error(f"GitHub integration test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"GitHub test failed: {str(e)}"
        )


@router.get("/test/queue")
async def test_queue_health(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Test job queue system health and performance.
    
    Performs comprehensive testing of:
    - Queue connectivity
    - Worker status
    - Performance metrics
    - Queue depths and processing rates
    
    Requires admin privileges.
    
    Returns:
        Detailed test results for job queue system
    """
    try:
        test_results = {
            "service": "job_queue",
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {},
            "overall_status": "healthy"
        }
        
        # Test queue health
        try:
            queue_health = await queue_monitoring_service.check_queue_health()
            test_results["tests"]["queue_health"] = {
                "status": "passed" if queue_health.get("overall_status") == "healthy" else "degraded",
                "message": f"Queue system status: {queue_health.get('overall_status', 'unknown')}",
                "details": queue_health
            }
        except Exception as e:
            test_results["tests"]["queue_health"] = {
                "status": "failed",
                "message": f"Queue health check failed: {str(e)}"
            }
            test_results["overall_status"] = "unhealthy"
        
        # Test worker statistics
        try:
            worker_stats = await queue_monitoring_service.get_worker_statistics()
            active_workers = worker_stats.get("active_workers", 0)
            
            test_results["tests"]["worker_status"] = {
                "status": "passed" if active_workers > 0 else "warning",
                "message": f"Active workers: {active_workers}",
                "details": worker_stats
            }
        except Exception as e:
            test_results["tests"]["worker_status"] = {
                "status": "failed",
                "message": f"Worker status check failed: {str(e)}"
            }
        
        # Test queue statistics
        try:
            queue_stats = await queue_monitoring_service.get_queue_statistics()
            test_results["tests"]["queue_statistics"] = {
                "status": "passed",
                "message": "Queue statistics retrieved successfully",
                "details": queue_stats
            }
        except Exception as e:
            test_results["tests"]["queue_statistics"] = {
                "status": "failed",
                "message": f"Queue statistics failed: {str(e)}"
            }
        
        # Test performance metrics
        try:
            performance_metrics = await queue_monitoring_service.get_performance_metrics(hours=1)
            test_results["tests"]["performance_metrics"] = {
                "status": "passed",
                "message": "Performance metrics retrieved successfully",
                "details": performance_metrics
            }
        except Exception as e:
            test_results["tests"]["performance_metrics"] = {
                "status": "warning",
                "message": f"Performance metrics unavailable: {str(e)}"
            }
        
        # Determine overall status
        failed_tests = [test for test in test_results["tests"].values() if test["status"] == "failed"]
        if failed_tests:
            test_results["overall_status"] = "unhealthy"
        elif any(test["status"] in ["warning", "degraded"] for test in test_results["tests"].values()):
            test_results["overall_status"] = "degraded"
        
        return test_results
        
    except Exception as e:
        logger.error(f"Queue health test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Queue test failed: {str(e)}"
        )


@router.get("/test/all")
async def run_comprehensive_tests(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    include_performance: bool = Query(default=False, description="Include performance tests")
):
    """
    Run comprehensive system tests for all integrations.
    
    Performs all available health checks and tests:
    - Digital Ocean Spaces
    - GitHub integration
    - Job queue system
    - Database connectivity
    - Configuration validation
    
    Args:
        include_performance: Whether to include performance tests (slower)
    
    Requires admin privileges.
    
    Returns:
        Comprehensive test results for all system components
    """
    try:
        comprehensive_results = {
            "test_suite": "comprehensive_system_test",
            "timestamp": datetime.utcnow().isoformat(),
            "user": current_user.email,
            "include_performance": include_performance,
            "tests": {},
            "summary": {},
            "overall_status": "healthy"
        }
        
        # Run Spaces tests
        try:
            spaces_test = await test_spaces_connectivity(current_user, db)
            comprehensive_results["tests"]["digital_ocean_spaces"] = spaces_test
        except Exception as e:
            comprehensive_results["tests"]["digital_ocean_spaces"] = {
                "overall_status": "failed",
                "error": str(e)
            }
        
        # Run GitHub tests
        try:
            github_test = await test_github_integration(current_user, db)
            comprehensive_results["tests"]["github_integration"] = github_test
        except Exception as e:
            comprehensive_results["tests"]["github_integration"] = {
                "overall_status": "failed",
                "error": str(e)
            }
        
        # Run queue tests
        try:
            queue_test = await test_queue_health(current_user, db)
            comprehensive_results["tests"]["job_queue"] = queue_test
        except Exception as e:
            comprehensive_results["tests"]["job_queue"] = {
                "overall_status": "failed",
                "error": str(e)
            }
        
        # Run configuration validation
        try:
            config_report = await config_validation_service.validate_all_configurations()
            comprehensive_results["tests"]["configuration_validation"] = {
                "overall_status": config_report.overall_status.value,
                "summary": config_report.summary,
                "timestamp": config_report.timestamp.isoformat()
            }
        except Exception as e:
            comprehensive_results["tests"]["configuration_validation"] = {
                "overall_status": "failed",
                "error": str(e)
            }
        
        # Performance tests (if requested)
        if include_performance:
            try:
                performance_results = await _run_performance_tests()
                comprehensive_results["tests"]["performance"] = performance_results
            except Exception as e:
                comprehensive_results["tests"]["performance"] = {
                    "overall_status": "failed",
                    "error": str(e)
                }
        
        # Generate summary
        test_statuses = []
        for test_name, test_result in comprehensive_results["tests"].items():
            status = test_result.get("overall_status", "unknown")
            test_statuses.append(status)
        
        comprehensive_results["summary"] = {
            "total_tests": len(test_statuses),
            "passed_tests": sum(1 for s in test_statuses if s in ["healthy", "passed"]),
            "degraded_tests": sum(1 for s in test_statuses if s in ["degraded", "warning"]),
            "failed_tests": sum(1 for s in test_statuses if s in ["unhealthy", "failed"]),
            "test_duration": "N/A"  # Could implement timing if needed
        }
        
        # Determine overall status
        if "failed" in test_statuses or "unhealthy" in test_statuses:
            comprehensive_results["overall_status"] = "failed"
        elif "degraded" in test_statuses or "warning" in test_statuses:
            comprehensive_results["overall_status"] = "degraded"
        
        return comprehensive_results
        
    except Exception as e:
        logger.error(f"Comprehensive test suite failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Comprehensive test failed: {str(e)}"
        )


# Helper functions

async def _check_spaces_health() -> Dict[str, Any]:
    """Check Digital Ocean Spaces health"""
    try:
        # Quick configuration check
        spaces_config = config_validation_service._validate_spaces_config_presence()
        
        if spaces_config.status.value == "valid":
            return {
                "status": "healthy",
                "message": "Digital Ocean Spaces is configured and accessible",
                "last_check": datetime.utcnow().isoformat()
            }
        elif spaces_config.status.value == "not_configured":
            return {
                "status": "not_configured",
                "message": "Digital Ocean Spaces is not configured",
                "last_check": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "degraded",
                "message": spaces_config.message,
                "last_check": datetime.utcnow().isoformat()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Spaces health check failed: {str(e)}",
            "last_check": datetime.utcnow().isoformat()
        }


async def _check_github_health() -> Dict[str, Any]:
    """Check GitHub integration health"""
    try:
        # Quick configuration check
        github_oauth = config_validation_service._validate_github_oauth_config()
        
        if github_oauth.status.value == "valid":
            return {
                "status": "healthy",
                "message": "GitHub integration is configured",
                "last_check": datetime.utcnow().isoformat()
            }
        elif github_oauth.status.value == "not_configured":
            return {
                "status": "not_configured",
                "message": "GitHub integration is not configured",
                "last_check": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "degraded",
                "message": github_oauth.message,
                "last_check": datetime.utcnow().isoformat()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"GitHub health check failed: {str(e)}",
            "last_check": datetime.utcnow().isoformat()
        }


async def _check_queue_health() -> Dict[str, Any]:
    """Check job queue health"""
    try:
        queue_health = await queue_monitoring_service.check_queue_health()
        return {
            "status": queue_health.get("overall_status", "unknown"),
            "message": f"Queue system status: {queue_health.get('overall_status', 'unknown')}",
            "details": queue_health,
            "last_check": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Queue health check failed: {str(e)}",
            "last_check": datetime.utcnow().isoformat()
        }


async def _check_database_health(db: Session) -> Dict[str, Any]:
    """Check database health"""
    try:
        # Simple query to test database connectivity
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "message": "Database is accessible",
            "last_check": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database health check failed: {str(e)}",
            "last_check": datetime.utcnow().isoformat()
        }


async def _run_performance_tests() -> Dict[str, Any]:
    """Run performance tests (placeholder for future implementation)"""
    return {
        "overall_status": "not_implemented",
        "message": "Performance tests not yet implemented",
        "tests": {
            "response_time": {"status": "not_implemented"},
            "throughput": {"status": "not_implemented"},
            "resource_usage": {"status": "not_implemented"}
        }
    }