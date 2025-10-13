#!/usr/bin/env python3
"""
Comprehensive System Health and Configuration Validation Test Script.

This script provides comprehensive testing for all system integrations:
- Digital Ocean Spaces configuration and connectivity
- GitHub integration setup and health
- Job queue system monitoring
- Database connectivity
- Overall system health validation

Requirements covered: 4.3, 4.4

Usage:
    python test_system_health.py [options]

Options:
    --config-only       Only test configuration validation
    --spaces-only       Only test Digital Ocean Spaces
    --github-only       Only test GitHub integration
    --queue-only        Only test job queue system
    --performance       Include performance tests
    --verbose           Enable verbose output
    --json              Output results in JSON format
"""

import asyncio
import argparse
import json
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.services.config_validation_service import config_validation_service
from app.services.file_storage_service import FileStorageService
from app.services.github_api_client import GitHubAPIClient
from app.services.queue_monitoring_service import queue_monitoring_service
from app.db.session import SessionLocal


class SystemHealthTester:
    """
    Comprehensive system health testing class.
    
    This class provides methods to test all system components and integrations
    with detailed reporting and error handling.
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = self._setup_logging()
        self.test_results = {
            "test_suite": "system_health_validation",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": settings.ENVIRONMENT,
            "tests": {},
            "summary": {},
            "overall_status": "unknown"
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("system_health_tester")
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def log(self, message: str, level: str = "info"):
        """Log a message with the specified level"""
        if level == "debug" and self.verbose:
            self.logger.debug(message)
        elif level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
    
    async def test_configuration_validation(self) -> Dict[str, Any]:
        """Test comprehensive configuration validation"""
        self.log("Testing configuration validation...")
        
        try:
            # Run comprehensive configuration validation
            validation_report = await config_validation_service.validate_all_configurations()
            
            test_result = {
                "status": validation_report.overall_status.value,
                "timestamp": validation_report.timestamp.isoformat(),
                "summary": validation_report.summary,
                "details": {
                    "spaces_validation": {
                        key: {
                            "status": result.status.value,
                            "message": result.message,
                            "suggestions": result.suggestions
                        }
                        for key, result in validation_report.spaces_validation.items()
                    },
                    "github_validation": {
                        key: {
                            "status": result.status.value,
                            "message": result.message,
                            "suggestions": result.suggestions
                        }
                        for key, result in validation_report.github_validation.items()
                    },
                    "general_validation": {
                        key: {
                            "status": result.status.value,
                            "message": result.message,
                            "suggestions": result.suggestions
                        }
                        for key, result in validation_report.general_validation.items()
                    }
                }
            }
            
            self.log(f"Configuration validation completed: {validation_report.overall_status.value}")
            return test_result
            
        except Exception as e:
            self.log(f"Configuration validation failed: {e}", "error")
            return {
                "status": "error",
                "message": f"Configuration validation failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def test_spaces_connectivity(self) -> Dict[str, Any]:
        """Test Digital Ocean Spaces connectivity and operations"""
        self.log("Testing Digital Ocean Spaces connectivity...")
        
        try:
            test_result = {
                "status": "unknown",
                "tests": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Test configuration presence
            self.log("Checking Spaces configuration...", "debug")
            spaces_config = config_validation_service._validate_spaces_config_presence()
            test_result["tests"]["configuration"] = {
                "status": spaces_config.status.value,
                "message": spaces_config.message
            }
            
            if spaces_config.status.value != "valid":
                test_result["status"] = "configuration_error"
                self.log(f"Spaces configuration invalid: {spaces_config.message}", "warning")
                return test_result
            
            # Test endpoint format
            self.log("Validating endpoint format...", "debug")
            endpoint_validation = config_validation_service._validate_spaces_endpoint_format()
            test_result["tests"]["endpoint_format"] = {
                "status": endpoint_validation.status.value,
                "message": endpoint_validation.message
            }
            
            # Test connectivity
            self.log("Testing Spaces connectivity...", "debug")
            connectivity_test = await config_validation_service._test_spaces_connectivity()
            test_result["tests"]["connectivity"] = {
                "status": connectivity_test.status.value,
                "message": connectivity_test.message
            }
            
            # Test credentials
            self.log("Validating Spaces credentials...", "debug")
            credentials_test = await config_validation_service._test_spaces_credentials()
            test_result["tests"]["credentials"] = {
                "status": credentials_test.status.value,
                "message": credentials_test.message
            }
            
            # Test bucket access
            self.log("Testing bucket access...", "debug")
            bucket_test = await config_validation_service._test_spaces_bucket_access()
            test_result["tests"]["bucket_access"] = {
                "status": bucket_test.status.value,
                "message": bucket_test.message
            }
            
            # Test file operations
            self.log("Testing file upload/download operations...", "debug")
            upload_test = await config_validation_service.test_spaces_upload()
            test_result["tests"]["file_operations"] = {
                "status": upload_test.status.value,
                "message": upload_test.message
            }
            
            # Test file storage service
            self.log("Testing file storage service initialization...", "debug")
            try:
                file_service = FileStorageService()
                file_service._validate_configuration()
                test_result["tests"]["service_initialization"] = {
                    "status": "valid",
                    "message": "File storage service initialized successfully"
                }
            except Exception as e:
                test_result["tests"]["service_initialization"] = {
                    "status": "error",
                    "message": f"Service initialization failed: {str(e)}"
                }
            
            # Determine overall status
            test_statuses = [test["status"] for test in test_result["tests"].values()]
            if "error" in test_statuses or "invalid" in test_statuses:
                test_result["status"] = "failed"
            elif "warning" in test_statuses:
                test_result["status"] = "degraded"
            else:
                test_result["status"] = "passed"
            
            self.log(f"Spaces connectivity test completed: {test_result['status']}")
            return test_result
            
        except Exception as e:
            self.log(f"Spaces connectivity test failed: {e}", "error")
            return {
                "status": "error",
                "message": f"Spaces test failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def test_github_integration(self) -> Dict[str, Any]:
        """Test GitHub integration health and connectivity"""
        self.log("Testing GitHub integration...")
        
        try:
            test_result = {
                "status": "unknown",
                "tests": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Test GitHub configuration
            self.log("Checking GitHub configuration...", "debug")
            github_config = await config_validation_service.validate_github_only()
            test_result["tests"]["configuration"] = {
                key: {
                    "status": result.status.value,
                    "message": result.message
                }
                for key, result in github_config.items()
            }
            
            # Test GitHub API connectivity
            self.log("Testing GitHub API connectivity...", "debug")
            try:
                github_client = GitHubAPIClient()
                rate_limit_info = await github_client.get_rate_limit_status()
                
                test_result["tests"]["api_connectivity"] = {
                    "status": "valid",
                    "message": "GitHub API is accessible",
                    "rate_limit": rate_limit_info
                }
            except Exception as e:
                test_result["tests"]["api_connectivity"] = {
                    "status": "error",
                    "message": f"GitHub API connectivity failed: {str(e)}"
                }
            
            # Test OAuth configuration
            self.log("Validating OAuth configuration...", "debug")
            if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
                test_result["tests"]["oauth_config"] = {
                    "status": "valid",
                    "message": "OAuth credentials are configured",
                    "client_id_preview": settings.GITHUB_CLIENT_ID[:8] + "..."
                }
            else:
                test_result["tests"]["oauth_config"] = {
                    "status": "not_configured",
                    "message": "OAuth credentials not configured"
                }
            
            # Test webhook configuration
            self.log("Validating webhook configuration...", "debug")
            if settings.GITHUB_WEBHOOK_SECRET:
                secret_strength = "strong" if len(settings.GITHUB_WEBHOOK_SECRET) >= 32 else "weak"
                test_result["tests"]["webhook_config"] = {
                    "status": "valid" if secret_strength == "strong" else "warning",
                    "message": f"Webhook secret configured ({secret_strength})",
                    "secret_length": len(settings.GITHUB_WEBHOOK_SECRET)
                }
            else:
                test_result["tests"]["webhook_config"] = {
                    "status": "not_configured",
                    "message": "Webhook secret not configured"
                }
            
            # Determine overall status
            config_statuses = []
            for test_group in test_result["tests"].values():
                if isinstance(test_group, dict) and "status" in test_group:
                    config_statuses.append(test_group["status"])
                elif isinstance(test_group, dict):
                    config_statuses.extend([t["status"] for t in test_group.values()])
            
            if "error" in config_statuses:
                test_result["status"] = "failed"
            elif "invalid" in config_statuses:
                test_result["status"] = "degraded"
            elif "not_configured" in config_statuses:
                test_result["status"] = "not_configured"
            else:
                test_result["status"] = "passed"
            
            self.log(f"GitHub integration test completed: {test_result['status']}")
            return test_result
            
        except Exception as e:
            self.log(f"GitHub integration test failed: {e}", "error")
            return {
                "status": "error",
                "message": f"GitHub test failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def test_queue_system(self) -> Dict[str, Any]:
        """Test job queue system health and performance"""
        self.log("Testing job queue system...")
        
        try:
            test_result = {
                "status": "unknown",
                "tests": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Test queue health
            self.log("Checking queue health...", "debug")
            try:
                queue_health = await queue_monitoring_service.check_queue_health()
                test_result["tests"]["queue_health"] = {
                    "status": "valid" if queue_health.get("overall_status") == "healthy" else "degraded",
                    "message": f"Queue system status: {queue_health.get('overall_status', 'unknown')}",
                    "details": queue_health
                }
            except Exception as e:
                test_result["tests"]["queue_health"] = {
                    "status": "error",
                    "message": f"Queue health check failed: {str(e)}"
                }
            
            # Test worker statistics
            self.log("Checking worker statistics...", "debug")
            try:
                worker_stats = await queue_monitoring_service.get_worker_statistics()
                active_workers = worker_stats.get("active_workers", 0)
                
                test_result["tests"]["worker_status"] = {
                    "status": "valid" if active_workers > 0 else "warning",
                    "message": f"Active workers: {active_workers}",
                    "details": worker_stats
                }
            except Exception as e:
                test_result["tests"]["worker_status"] = {
                    "status": "error",
                    "message": f"Worker status check failed: {str(e)}"
                }
            
            # Test queue statistics
            self.log("Retrieving queue statistics...", "debug")
            try:
                queue_stats = await queue_monitoring_service.get_queue_statistics()
                test_result["tests"]["queue_statistics"] = {
                    "status": "valid",
                    "message": "Queue statistics retrieved successfully",
                    "details": queue_stats
                }
            except Exception as e:
                test_result["tests"]["queue_statistics"] = {
                    "status": "error",
                    "message": f"Queue statistics failed: {str(e)}"
                }
            
            # Test performance metrics
            self.log("Gathering performance metrics...", "debug")
            try:
                performance_metrics = await queue_monitoring_service.get_performance_metrics(hours=1)
                test_result["tests"]["performance_metrics"] = {
                    "status": "valid",
                    "message": "Performance metrics retrieved successfully",
                    "details": performance_metrics
                }
            except Exception as e:
                test_result["tests"]["performance_metrics"] = {
                    "status": "warning",
                    "message": f"Performance metrics unavailable: {str(e)}"
                }
            
            # Determine overall status
            test_statuses = [test["status"] for test in test_result["tests"].values()]
            if "error" in test_statuses:
                test_result["status"] = "failed"
            elif "warning" in test_statuses or "degraded" in test_statuses:
                test_result["status"] = "degraded"
            else:
                test_result["status"] = "passed"
            
            self.log(f"Queue system test completed: {test_result['status']}")
            return test_result
            
        except Exception as e:
            self.log(f"Queue system test failed: {e}", "error")
            return {
                "status": "error",
                "message": f"Queue test failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def test_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity and basic operations"""
        self.log("Testing database connectivity...")
        
        try:
            test_result = {
                "status": "unknown",
                "tests": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Test basic connectivity
            self.log("Testing database connection...", "debug")
            try:
                db = SessionLocal()
                db.execute("SELECT 1")
                db.close()
                
                test_result["tests"]["connectivity"] = {
                    "status": "valid",
                    "message": "Database connection successful"
                }
            except Exception as e:
                test_result["tests"]["connectivity"] = {
                    "status": "error",
                    "message": f"Database connection failed: {str(e)}"
                }
            
            # Test configuration
            self.log("Validating database configuration...", "debug")
            db_config = config_validation_service._validate_database_config()
            test_result["tests"]["configuration"] = {
                "status": db_config.status.value,
                "message": db_config.message
            }
            
            # Determine overall status
            test_statuses = [test["status"] for test in test_result["tests"].values()]
            if "error" in test_statuses or "invalid" in test_statuses:
                test_result["status"] = "failed"
            elif "warning" in test_statuses:
                test_result["status"] = "degraded"
            else:
                test_result["status"] = "passed"
            
            self.log(f"Database connectivity test completed: {test_result['status']}")
            return test_result
            
        except Exception as e:
            self.log(f"Database connectivity test failed: {e}", "error")
            return {
                "status": "error",
                "message": f"Database test failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def run_comprehensive_tests(
        self,
        config_only: bool = False,
        spaces_only: bool = False,
        github_only: bool = False,
        queue_only: bool = False,
        include_performance: bool = False
    ) -> Dict[str, Any]:
        """Run comprehensive system health tests"""
        self.log("Starting comprehensive system health tests...")
        
        # Determine which tests to run
        if config_only:
            tests_to_run = ["configuration"]
        elif spaces_only:
            tests_to_run = ["spaces"]
        elif github_only:
            tests_to_run = ["github"]
        elif queue_only:
            tests_to_run = ["queue"]
        else:
            tests_to_run = ["configuration", "database", "spaces", "github", "queue"]
        
        # Run selected tests
        if "configuration" in tests_to_run:
            self.test_results["tests"]["configuration_validation"] = await self.test_configuration_validation()
        
        if "database" in tests_to_run:
            self.test_results["tests"]["database_connectivity"] = await self.test_database_connectivity()
        
        if "spaces" in tests_to_run:
            self.test_results["tests"]["spaces_connectivity"] = await self.test_spaces_connectivity()
        
        if "github" in tests_to_run:
            self.test_results["tests"]["github_integration"] = await self.test_github_integration()
        
        if "queue" in tests_to_run:
            self.test_results["tests"]["queue_system"] = await self.test_queue_system()
        
        # Generate summary
        test_statuses = []
        for test_name, test_result in self.test_results["tests"].items():
            status = test_result.get("status", "unknown")
            test_statuses.append(status)
        
        self.test_results["summary"] = {
            "total_tests": len(test_statuses),
            "passed_tests": sum(1 for s in test_statuses if s == "passed"),
            "degraded_tests": sum(1 for s in test_statuses if s in ["degraded", "warning"]),
            "failed_tests": sum(1 for s in test_statuses if s in ["failed", "error"]),
            "not_configured_tests": sum(1 for s in test_statuses if s == "not_configured"),
            "tests_run": tests_to_run
        }
        
        # Determine overall status
        if "failed" in test_statuses or "error" in test_statuses:
            self.test_results["overall_status"] = "failed"
        elif "degraded" in test_statuses or "warning" in test_statuses:
            self.test_results["overall_status"] = "degraded"
        elif "not_configured" in test_statuses:
            self.test_results["overall_status"] = "partially_configured"
        else:
            self.test_results["overall_status"] = "passed"
        
        self.log(f"Comprehensive tests completed: {self.test_results['overall_status']}")
        return self.test_results


def main():
    """Main function to run the system health tests"""
    parser = argparse.ArgumentParser(
        description="Comprehensive System Health and Configuration Validation Test Script"
    )
    parser.add_argument(
        "--config-only",
        action="store_true",
        help="Only test configuration validation"
    )
    parser.add_argument(
        "--spaces-only",
        action="store_true",
        help="Only test Digital Ocean Spaces"
    )
    parser.add_argument(
        "--github-only",
        action="store_true",
        help="Only test GitHub integration"
    )
    parser.add_argument(
        "--queue-only",
        action="store_true",
        help="Only test job queue system"
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Include performance tests"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = SystemHealthTester(verbose=args.verbose)
    
    # Run tests
    try:
        results = asyncio.run(tester.run_comprehensive_tests(
            config_only=args.config_only,
            spaces_only=args.spaces_only,
            github_only=args.github_only,
            queue_only=args.queue_only,
            include_performance=args.performance
        ))
        
        # Output results
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            # Human-readable output
            print(f"\n{'='*60}")
            print(f"SYSTEM HEALTH TEST RESULTS")
            print(f"{'='*60}")
            print(f"Overall Status: {results['overall_status'].upper()}")
            print(f"Timestamp: {results['timestamp']}")
            print(f"Environment: {results['environment']}")
            print(f"\nSummary:")
            print(f"  Total Tests: {results['summary']['total_tests']}")
            print(f"  Passed: {results['summary']['passed_tests']}")
            print(f"  Degraded: {results['summary']['degraded_tests']}")
            print(f"  Failed: {results['summary']['failed_tests']}")
            print(f"  Not Configured: {results['summary']['not_configured_tests']}")
            
            print(f"\nDetailed Results:")
            for test_name, test_result in results['tests'].items():
                status = test_result.get('status', 'unknown').upper()
                print(f"  {test_name}: {status}")
                if 'message' in test_result:
                    print(f"    Message: {test_result['message']}")
        
        # Exit with appropriate code
        if results['overall_status'] in ['failed', 'error']:
            sys.exit(1)
        elif results['overall_status'] in ['degraded', 'warning']:
            sys.exit(2)
        else:
            sys.exit(0)
            
    except Exception as e:
        tester.log(f"Test execution failed: {e}", "error")
        if args.json:
            print(json.dumps({
                "status": "error",
                "message": f"Test execution failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }))
        else:
            print(f"ERROR: Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()