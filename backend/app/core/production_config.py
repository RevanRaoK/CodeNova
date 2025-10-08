"""
Production readiness configuration and utilities.

This module provides production-specific configurations, health checks,
and deployment utilities for optimal performance and reliability.

Requirements covered: Performance and scalability for all features
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import psutil
import asyncio
from dataclasses import dataclass

from app.core.config import settings
from app.core.monitoring import system_monitor, health_checker
from app.core.cache import cache
from app.db.performance_indexes import create_performance_indexes, create_database_views


@dataclass
class ProductionRequirement:
    """Production readiness requirement."""
    name: str
    description: str
    check_function: callable
    critical: bool = True
    category: str = "general"


class ProductionReadinessChecker:
    """Production readiness validation and configuration."""
    
    def __init__(self):
        self.requirements = self._define_requirements()
        self.logger = logging.getLogger("production_readiness")
    
    def _define_requirements(self) -> List[ProductionRequirement]:
        """Define all production readiness requirements."""
        return [
            # Database requirements
            ProductionRequirement(
                "database_connection",
                "Database connection is healthy and responsive",
                self._check_database_connection,
                critical=True,
                category="database"
            ),
            ProductionRequirement(
                "database_indexes",
                "Performance indexes are created",
                self._check_database_indexes,
                critical=False,
                category="database"
            ),
            ProductionRequirement(
                "database_views",
                "Analytics views are created",
                self._check_database_views,
                critical=False,
                category="database"
            ),
            
            # Cache requirements
            ProductionRequirement(
                "redis_connection",
                "Redis cache is connected and responsive",
                self._check_redis_connection,
                critical=True,
                category="cache"
            ),
            ProductionRequirement(
                "cache_performance",
                "Cache performance meets requirements",
                self._check_cache_performance,
                critical=False,
                category="cache"
            ),
            
            # Security requirements
            ProductionRequirement(
                "secret_key_configured",
                "Secret key is properly configured",
                self._check_secret_key,
                critical=True,
                category="security"
            ),
            ProductionRequirement(
                "https_enabled",
                "HTTPS is enabled in production",
                self._check_https_config,
                critical=True,
                category="security"
            ),
            ProductionRequirement(
                "cors_configured",
                "CORS is properly configured",
                self._check_cors_config,
                critical=True,
                category="security"
            ),
            
            # Performance requirements
            ProductionRequirement(
                "system_resources",
                "System has adequate resources",
                self._check_system_resources,
                critical=True,
                category="performance"
            ),
            ProductionRequirement(
                "monitoring_enabled",
                "Monitoring systems are active",
                self._check_monitoring_systems,
                critical=False,
                category="monitoring"
            ),
            
            # Environment requirements
            ProductionRequirement(
                "environment_variables",
                "Required environment variables are set",
                self._check_environment_variables,
                critical=True,
                category="environment"
            ),
            ProductionRequirement(
                "log_level_configured",
                "Logging is properly configured",
                self._check_logging_config,
                critical=False,
                category="environment"
            ),
            
            # External services
            ProductionRequirement(
                "github_integration",
                "GitHub integration is configured",
                self._check_github_config,
                critical=False,
                category="external"
            ),
            ProductionRequirement(
                "file_storage",
                "File storage is configured",
                self._check_file_storage_config,
                critical=False,
                category="external"
            ),
        ]
    
    async def _check_database_connection(self) -> Dict[str, Any]:
        """Check database connection health."""
        try:
            db_health = await health_checker.check_database_health()
            return {
                "passed": db_health["status"] == "healthy",
                "details": db_health,
                "recommendations": [] if db_health["status"] == "healthy" else [
                    "Check database connection string",
                    "Verify database server is running",
                    "Check network connectivity"
                ]
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e),
                "recommendations": ["Fix database connection issues"]
            }
    
    async def _check_database_indexes(self) -> Dict[str, Any]:
        """Check if performance indexes are created."""
        try:
            # This would check if indexes exist in the database
            # For now, we'll assume they need to be created
            create_performance_indexes()
            return {
                "passed": True,
                "details": "Performance indexes created/verified",
                "recommendations": []
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e),
                "recommendations": ["Run database migration to create indexes"]
            }
    
    async def _check_database_views(self) -> Dict[str, Any]:
        """Check if analytics views are created."""
        try:
            create_database_views()
            return {
                "passed": True,
                "details": "Analytics views created/verified",
                "recommendations": []
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e),
                "recommendations": ["Run database migration to create views"]
            }
    
    async def _check_redis_connection(self) -> Dict[str, Any]:
        """Check Redis connection health."""
        try:
            cache_health = await health_checker.check_cache_health()
            return {
                "passed": cache_health["status"] == "healthy",
                "details": cache_health,
                "recommendations": [] if cache_health["status"] == "healthy" else [
                    "Check Redis connection string",
                    "Verify Redis server is running",
                    "Check Redis authentication"
                ]
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e),
                "recommendations": ["Fix Redis connection issues"]
            }
    
    async def _check_cache_performance(self) -> Dict[str, Any]:
        """Check cache performance metrics."""
        try:
            cache_health = await health_checker.check_cache_health()
            hit_rate = cache_health.get("hit_rate", 0)
            response_time = cache_health.get("response_time_ms", 0)
            
            passed = hit_rate > 0.7 and response_time < 10
            
            recommendations = []
            if hit_rate <= 0.7:
                recommendations.append("Improve cache hit rate by optimizing cache keys and TTL")
            if response_time >= 10:
                recommendations.append("Optimize Redis configuration for better performance")
            
            return {
                "passed": passed,
                "details": {
                    "hit_rate": hit_rate,
                    "response_time_ms": response_time
                },
                "recommendations": recommendations
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e),
                "recommendations": ["Check cache performance configuration"]
            }
    
    async def _check_secret_key(self) -> Dict[str, Any]:
        """Check if secret key is properly configured."""
        secret_key = settings.SECRET_KEY
        
        passed = (
            secret_key and 
            len(secret_key) >= 32 and 
            secret_key != "your-secret-key-here"
        )
        
        recommendations = []
        if not passed:
            recommendations.extend([
                "Set a strong SECRET_KEY environment variable",
                "Use a cryptographically secure random string",
                "Ensure SECRET_KEY is at least 32 characters long"
            ])
        
        return {
            "passed": passed,
            "details": {
                "key_length": len(secret_key) if secret_key else 0,
                "is_default": secret_key == "your-secret-key-here" if secret_key else True
            },
            "recommendations": recommendations
        }
    
    async def _check_https_config(self) -> Dict[str, Any]:
        """Check HTTPS configuration."""
        # In production, this should check if HTTPS is properly configured
        is_production = settings.ENVIRONMENT == "production"
        https_configured = not is_production or os.getenv("HTTPS_ENABLED", "false").lower() == "true"
        
        recommendations = []
        if is_production and not https_configured:
            recommendations.extend([
                "Enable HTTPS in production environment",
                "Configure SSL certificates",
                "Set HTTPS_ENABLED=true environment variable"
            ])
        
        return {
            "passed": https_configured,
            "details": {
                "environment": settings.ENVIRONMENT,
                "https_enabled": https_configured
            },
            "recommendations": recommendations
        }
    
    async def _check_cors_config(self) -> Dict[str, Any]:
        """Check CORS configuration."""
        # Check if CORS is properly configured for production
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
        is_production = settings.ENVIRONMENT == "production"
        
        passed = not is_production or (allowed_origins != "*" and allowed_origins)
        
        recommendations = []
        if is_production and allowed_origins == "*":
            recommendations.extend([
                "Configure specific allowed origins for production",
                "Set ALLOWED_ORIGINS environment variable",
                "Avoid using wildcard (*) in production"
            ])
        
        return {
            "passed": passed,
            "details": {
                "allowed_origins": allowed_origins,
                "environment": settings.ENVIRONMENT
            },
            "recommendations": recommendations
        }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource availability."""
        try:
            # Get current system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Define minimum requirements
            min_memory_gb = 2
            min_disk_gb = 10
            max_cpu_percent = 80
            
            memory_gb = memory.total / (1024**3)
            disk_gb = disk.total / (1024**3)
            
            passed = (
                memory_gb >= min_memory_gb and
                disk_gb >= min_disk_gb and
                cpu_percent < max_cpu_percent
            )
            
            recommendations = []
            if memory_gb < min_memory_gb:
                recommendations.append(f"Increase memory to at least {min_memory_gb}GB")
            if disk_gb < min_disk_gb:
                recommendations.append(f"Ensure at least {min_disk_gb}GB disk space")
            if cpu_percent >= max_cpu_percent:
                recommendations.append("High CPU usage detected, consider scaling")
            
            return {
                "passed": passed,
                "details": {
                    "memory_gb": round(memory_gb, 2),
                    "disk_gb": round(disk_gb, 2),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent
                },
                "recommendations": recommendations
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e),
                "recommendations": ["Check system resource monitoring"]
            }
    
    async def _check_monitoring_systems(self) -> Dict[str, Any]:
        """Check if monitoring systems are active."""
        try:
            # Check if system monitor is running
            monitoring_active = system_monitor.running
            
            return {
                "passed": monitoring_active,
                "details": {
                    "system_monitor_active": monitoring_active
                },
                "recommendations": [] if monitoring_active else [
                    "Start system monitoring",
                    "Configure monitoring alerts"
                ]
            }
        except Exception as e:
            return {
                "passed": False,
                "error": str(e),
                "recommendations": ["Fix monitoring system configuration"]
            }
    
    async def _check_environment_variables(self) -> Dict[str, Any]:
        """Check required environment variables."""
        required_vars = [
            "DATABASE_URL",
            "SECRET_KEY",
            "REDIS_HOST",
        ]
        
        optional_vars = [
            "GITHUB_CLIENT_ID",
            "GITHUB_CLIENT_SECRET",
            "DIGITAL_OCEAN_SPACES_KEY",
            "DIGITAL_OCEAN_SPACES_SECRET"
        ]
        
        missing_required = [var for var in required_vars if not os.getenv(var)]
        missing_optional = [var for var in optional_vars if not os.getenv(var)]
        
        passed = len(missing_required) == 0
        
        recommendations = []
        if missing_required:
            recommendations.append(f"Set required environment variables: {', '.join(missing_required)}")
        if missing_optional:
            recommendations.append(f"Consider setting optional variables: {', '.join(missing_optional)}")
        
        return {
            "passed": passed,
            "details": {
                "required_vars_set": len(required_vars) - len(missing_required),
                "optional_vars_set": len(optional_vars) - len(missing_optional),
                "missing_required": missing_required,
                "missing_optional": missing_optional
            },
            "recommendations": recommendations
        }
    
    async def _check_logging_config(self) -> Dict[str, Any]:
        """Check logging configuration."""
        log_level = settings.LOG_LEVEL
        is_production = settings.ENVIRONMENT == "production"
        
        # In production, log level should be INFO or higher
        production_levels = ["INFO", "WARNING", "ERROR", "CRITICAL"]
        passed = not is_production or log_level in production_levels
        
        recommendations = []
        if is_production and log_level not in production_levels:
            recommendations.append("Set log level to INFO or higher in production")
        
        return {
            "passed": passed,
            "details": {
                "log_level": log_level,
                "environment": settings.ENVIRONMENT
            },
            "recommendations": recommendations
        }
    
    async def _check_github_config(self) -> Dict[str, Any]:
        """Check GitHub integration configuration."""
        client_id = os.getenv("GITHUB_CLIENT_ID")
        client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        
        configured = bool(client_id and client_secret)
        
        return {
            "passed": True,  # Optional feature
            "details": {
                "github_configured": configured,
                "has_client_id": bool(client_id),
                "has_client_secret": bool(client_secret)
            },
            "recommendations": [] if configured else [
                "Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET for GitHub integration"
            ]
        }
    
    async def _check_file_storage_config(self) -> Dict[str, Any]:
        """Check file storage configuration."""
        spaces_key = os.getenv("DIGITAL_OCEAN_SPACES_KEY")
        spaces_secret = os.getenv("DIGITAL_OCEAN_SPACES_SECRET")
        
        configured = bool(spaces_key and spaces_secret)
        
        return {
            "passed": True,  # Optional feature
            "details": {
                "file_storage_configured": configured,
                "has_spaces_key": bool(spaces_key),
                "has_spaces_secret": bool(spaces_secret)
            },
            "recommendations": [] if configured else [
                "Set Digital Ocean Spaces credentials for file storage"
            ]
        }
    
    async def run_production_readiness_check(self) -> Dict[str, Any]:
        """Run comprehensive production readiness check."""
        self.logger.info("Starting production readiness check...")
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.ENVIRONMENT,
            "overall_status": "unknown",
            "categories": {},
            "critical_failures": [],
            "recommendations": [],
            "summary": {}
        }
        
        # Group requirements by category
        categories = {}
        for req in self.requirements:
            if req.category not in categories:
                categories[req.category] = []
            categories[req.category].append(req)
        
        # Run checks for each category
        total_checks = 0
        passed_checks = 0
        critical_failures = []
        all_recommendations = []
        
        for category, reqs in categories.items():
            category_results = {}
            category_passed = 0
            category_total = len(reqs)
            
            for req in reqs:
                try:
                    check_result = await req.check_function()
                    category_results[req.name] = {
                        "description": req.description,
                        "critical": req.critical,
                        "passed": check_result["passed"],
                        "details": check_result.get("details", {}),
                        "recommendations": check_result.get("recommendations", []),
                        "error": check_result.get("error")
                    }
                    
                    if check_result["passed"]:
                        category_passed += 1
                        passed_checks += 1
                    elif req.critical:
                        critical_failures.append(req.name)
                    
                    all_recommendations.extend(check_result.get("recommendations", []))
                    
                except Exception as e:
                    self.logger.error(f"Error running check {req.name}: {e}")
                    category_results[req.name] = {
                        "description": req.description,
                        "critical": req.critical,
                        "passed": False,
                        "error": str(e),
                        "recommendations": ["Fix check execution error"]
                    }
                    
                    if req.critical:
                        critical_failures.append(req.name)
                
                total_checks += 1
            
            results["categories"][category] = {
                "checks": category_results,
                "passed": category_passed,
                "total": category_total,
                "success_rate": category_passed / category_total if category_total > 0 else 0
            }
        
        # Determine overall status
        if critical_failures:
            overall_status = "not_ready"
        elif passed_checks / total_checks >= 0.9:
            overall_status = "ready"
        else:
            overall_status = "needs_attention"
        
        results.update({
            "overall_status": overall_status,
            "critical_failures": critical_failures,
            "recommendations": list(set(all_recommendations)),  # Remove duplicates
            "summary": {
                "total_checks": total_checks,
                "passed_checks": passed_checks,
                "success_rate": passed_checks / total_checks if total_checks > 0 else 0,
                "critical_failures_count": len(critical_failures)
            }
        })
        
        self.logger.info(f"Production readiness check completed. Status: {overall_status}")
        return results
    
    def generate_readiness_report(self, results: Dict[str, Any]) -> str:
        """Generate a formatted production readiness report."""
        report = []
        report.append("=" * 80)
        report.append("PRODUCTION READINESS REPORT")
        report.append("=" * 80)
        
        # Summary
        summary = results["summary"]
        report.append(f"Overall Status: {results['overall_status'].upper()}")
        report.append(f"Environment: {results['environment']}")
        report.append(f"Check Time: {results['timestamp']}")
        report.append(f"Success Rate: {summary['success_rate']:.1%} ({summary['passed_checks']}/{summary['total_checks']})")
        
        if results["critical_failures"]:
            report.append(f"Critical Failures: {len(results['critical_failures'])}")
        
        report.append("")
        
        # Category results
        for category, category_data in results["categories"].items():
            report.append(f"{category.upper()} CHECKS")
            report.append("-" * 40)
            report.append(f"Success Rate: {category_data['success_rate']:.1%} ({category_data['passed']}/{category_data['total']})")
            report.append("")
            
            for check_name, check_data in category_data["checks"].items():
                status = "✓ PASS" if check_data["passed"] else "✗ FAIL"
                critical = " (CRITICAL)" if check_data["critical"] else ""
                report.append(f"  {status}{critical} {check_name}")
                report.append(f"    {check_data['description']}")
                
                if not check_data["passed"] and check_data.get("recommendations"):
                    report.append("    Recommendations:")
                    for rec in check_data["recommendations"]:
                        report.append(f"      - {rec}")
                
                if check_data.get("error"):
                    report.append(f"    Error: {check_data['error']}")
                
                report.append("")
        
        # Overall recommendations
        if results["recommendations"]:
            report.append("OVERALL RECOMMENDATIONS")
            report.append("-" * 40)
            for rec in results["recommendations"]:
                report.append(f"  - {rec}")
            report.append("")
        
        return "\n".join(report)


# Global production readiness checker
production_checker = ProductionReadinessChecker()


async def check_production_readiness() -> Dict[str, Any]:
    """Run production readiness check and return results."""
    return await production_checker.run_production_readiness_check()


def generate_production_report(results: Dict[str, Any]) -> str:
    """Generate production readiness report."""
    return production_checker.generate_readiness_report(results)


# Production optimization utilities
class ProductionOptimizer:
    """Production optimization utilities."""
    
    @staticmethod
    def optimize_database_settings():
        """Apply production database optimizations."""
        from app.db.performance_indexes import optimize_database_settings
        optimize_database_settings()
    
    @staticmethod
    def warm_caches():
        """Warm up caches with frequently accessed data."""
        from app.core.cache import CacheWarmer
        # This would warm up caches in production
        pass
    
    @staticmethod
    def setup_monitoring():
        """Set up production monitoring."""
        system_monitor.start_monitoring(interval=30)  # More frequent monitoring in production
    
    @staticmethod
    async def run_production_setup():
        """Run complete production setup."""
        print("Setting up production environment...")
        
        # Create database indexes and views
        try:
            create_performance_indexes()
            create_database_views()
            print("✓ Database optimizations applied")
        except Exception as e:
            print(f"✗ Database optimization failed: {e}")
        
        # Start monitoring
        try:
            ProductionOptimizer.setup_monitoring()
            print("✓ Monitoring systems started")
        except Exception as e:
            print(f"✗ Monitoring setup failed: {e}")
        
        # Run readiness check
        try:
            results = await check_production_readiness()
            report = generate_production_report(results)
            
            print("\n" + report)
            
            # Save report
            with open("production_readiness_report.txt", "w") as f:
                f.write(report)
            
            print("\nProduction readiness report saved to production_readiness_report.txt")
            
            return results["overall_status"] == "ready"
        except Exception as e:
            print(f"✗ Production readiness check failed: {e}")
            return False


if __name__ == "__main__":
    async def main():
        await ProductionOptimizer.run_production_setup()
    
    asyncio.run(main())