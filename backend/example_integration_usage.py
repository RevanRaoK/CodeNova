"""
Example Integration Usage

This file demonstrates how to integrate the enhanced logging system
into existing application code for various integration scenarios.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import enhanced logging components
from app.core.enhanced_logging import (
    IntegrationComponent,
    ErrorSeverity,
    log_integration_operation,
    log_integration_context,
    create_error_context,
    error_handler,
    performance_monitor,
    health_check_logger
)


class FileStorageService:
    """Example file storage service with enhanced logging."""
    
    def __init__(self):
        self.logger = error_handler.get_logger(IntegrationComponent.FILE_STORAGE)
    
    @log_integration_operation(IntegrationComponent.FILE_STORAGE, "upload_file")
    async def upload_file(self, user_id: int, filename: str, content: bytes) -> Dict[str, Any]:
        """Upload a file with comprehensive logging."""
        file_size = len(content)
        
        # Log additional context
        self.logger.log_operation(
            "file_validation",
            level="info",
            user_id=user_id,
            filename=filename,
            file_size_bytes=file_size
        )
        
        # Simulate file processing
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            raise ValueError(f"File {filename} exceeds size limit")
        
        # Simulate upload
        await asyncio.sleep(0.1)
        
        file_id = f"file_{user_id}_{int(datetime.utcnow().timestamp())}"
        
        return {
            "file_id": file_id,
            "filename": filename,
            "size_bytes": file_size,
            "upload_time": datetime.utcnow().isoformat()
        }
    
    @log_integration_operation(IntegrationComponent.FILE_STORAGE, "delete_file")
    async def delete_file(self, user_id: int, file_id: str) -> bool:
        """Delete a file with logging."""
        # Simulate deletion
        await asyncio.sleep(0.05)
        
        # Log successful deletion
        self.logger.log_operation(
            "file_deleted",
            level="info",
            user_id=user_id,
            file_id=file_id
        )
        
        return True
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file information with manual logging."""
        start_time = datetime.utcnow()
        
        try:
            # Simulate database lookup
            if not file_id.startswith("file_"):
                raise ValueError("Invalid file ID format")
            
            file_info = {
                "file_id": file_id,
                "filename": "example.txt",
                "size_bytes": 1024,
                "created_at": "2024-01-01T00:00:00Z"
            }
            
            # Manual success logging
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.log_operation(
                "get_file_info",
                level="info",
                file_id=file_id,
                duration_seconds=duration,
                status="success"
            )
            
            return file_info
            
        except Exception as e:
            # Manual error logging
            duration = (datetime.utcnow() - start_time).total_seconds()
            error_context = create_error_context(
                IntegrationComponent.FILE_STORAGE,
                "get_file_info",
                e,
                ErrorSeverity.MEDIUM,
                metadata={
                    "file_id": file_id,
                    "duration_seconds": duration
                }
            )
            self.logger.log_error(error_context)
            raise


class GitHubIntegrationService:
    """Example GitHub integration service with enhanced logging."""
    
    def __init__(self):
        self.logger = error_handler.get_logger(IntegrationComponent.GITHUB_API)
    
    @log_integration_operation(IntegrationComponent.GITHUB_API, "fetch_user_repos")
    async def fetch_user_repositories(self, user_id: int, github_token: str) -> List[Dict[str, Any]]:
        """Fetch user repositories from GitHub."""
        # Use context manager for complex operations
        with log_integration_context(
            IntegrationComponent.GITHUB_API,
            "github_api_request",
            user_id=user_id,
            endpoint="/user/repos"
        ) as logger:
            
            # Log API request details (without sensitive data)
            logger.log_operation(
                "api_request_started",
                level="debug",
                method="GET",
                endpoint="/user/repos",
                has_token=bool(github_token)
            )
            
            # Simulate API call
            await asyncio.sleep(0.3)
            
            # Simulate rate limiting check
            if not self._check_rate_limit():
                raise Exception("GitHub API rate limit exceeded")
            
            # Mock response
            repositories = [
                {"name": "repo1", "private": False, "language": "Python"},
                {"name": "repo2", "private": True, "language": "JavaScript"}
            ]
            
            logger.log_operation(
                "repositories_fetched",
                level="info",
                repository_count=len(repositories),
                private_repos=sum(1 for r in repositories if r["private"])
            )
            
            return repositories
    
    def _check_rate_limit(self) -> bool:
        """Check GitHub API rate limit."""
        # Simulate rate limit check
        import random
        return random.random() > 0.1  # 90% success rate
    
    @log_integration_operation(IntegrationComponent.GITHUB_WEBHOOK, "process_webhook")
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process GitHub webhook with logging."""
        event_type = webhook_data.get("action", "unknown")
        repository = webhook_data.get("repository", {}).get("name", "unknown")
        
        # Log webhook processing
        self.logger.log_operation(
            "webhook_received",
            level="info",
            event_type=event_type,
            repository=repository,
            payload_size=len(str(webhook_data))
        )
        
        # Process different event types
        if event_type == "push":
            return await self._process_push_event(webhook_data)
        elif event_type == "pull_request":
            return await self._process_pr_event(webhook_data)
        else:
            self.logger.log_operation(
                "webhook_ignored",
                level="warning",
                event_type=event_type,
                reason="unsupported_event_type"
            )
            return {"status": "ignored", "reason": "unsupported event type"}
    
    async def _process_push_event(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process push event."""
        commits = webhook_data.get("commits", [])
        
        self.logger.log_operation(
            "push_event_processed",
            level="info",
            commit_count=len(commits),
            branch=webhook_data.get("ref", "unknown")
        )
        
        return {"status": "processed", "commits": len(commits)}
    
    async def _process_pr_event(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process pull request event."""
        pr_action = webhook_data.get("action", "unknown")
        pr_number = webhook_data.get("number", 0)
        
        self.logger.log_operation(
            "pr_event_processed",
            level="info",
            pr_action=pr_action,
            pr_number=pr_number
        )
        
        return {"status": "processed", "pr_number": pr_number}


class BackgroundJobService:
    """Example background job service with enhanced logging."""
    
    def __init__(self):
        self.logger = error_handler.get_logger(IntegrationComponent.JOB_QUEUE)
    
    @log_integration_operation(IntegrationComponent.JOB_QUEUE, "enqueue_job")
    def enqueue_analysis_job(self, user_id: int, repository_id: str, job_type: str) -> str:
        """Enqueue a background analysis job."""
        job_id = f"job_{user_id}_{repository_id}_{int(datetime.utcnow().timestamp())}"
        
        # Log job details
        self.logger.log_operation(
            "job_enqueued",
            level="info",
            job_id=job_id,
            job_type=job_type,
            user_id=user_id,
            repository_id=repository_id
        )
        
        return job_id
    
    @log_integration_operation(IntegrationComponent.BACKGROUND_ANALYSIS, "process_analysis_job")
    async def process_analysis_job(self, job_id: str, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a background analysis job."""
        job_type = job_data.get("type", "unknown")
        
        # Use performance monitoring
        start_time = datetime.utcnow()
        
        try:
            # Simulate different types of analysis
            if job_type == "code_quality":
                result = await self._analyze_code_quality(job_data)
            elif job_type == "security_scan":
                result = await self._analyze_security(job_data)
            else:
                raise ValueError(f"Unknown job type: {job_type}")
            
            # Record successful operation
            duration = (datetime.utcnow() - start_time).total_seconds()
            performance_monitor.record_operation(
                IntegrationComponent.BACKGROUND_ANALYSIS,
                f"analysis_{job_type}",
                duration,
                success=True,
                job_id=job_id
            )
            
            return result
            
        except Exception as e:
            # Record failed operation
            duration = (datetime.utcnow() - start_time).total_seconds()
            performance_monitor.record_operation(
                IntegrationComponent.BACKGROUND_ANALYSIS,
                f"analysis_{job_type}",
                duration,
                success=False,
                job_id=job_id,
                error=str(e)
            )
            raise
    
    async def _analyze_code_quality(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate code quality analysis."""
        await asyncio.sleep(2.0)  # Simulate processing time
        
        return {
            "quality_score": 85,
            "issues_found": 3,
            "suggestions": ["Add more comments", "Reduce function complexity"]
        }
    
    async def _analyze_security(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate security analysis."""
        await asyncio.sleep(1.5)  # Simulate processing time
        
        return {
            "security_score": 92,
            "vulnerabilities": 1,
            "recommendations": ["Update dependency versions"]
        }


class HealthCheckService:
    """Example health check service with enhanced logging."""
    
    def __init__(self):
        self.services = {
            "database": "postgresql://localhost:5432/app",
            "redis": "redis://localhost:6379",
            "github_api": "https://api.github.com",
            "file_storage": "s3://bucket-name"
        }
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Check health of all services."""
        results = {}
        
        for service_name, endpoint in self.services.items():
            try:
                start_time = datetime.utcnow()
                
                # Simulate health check
                is_healthy = await self._check_service_health(service_name, endpoint)
                
                response_time = (datetime.utcnow() - start_time).total_seconds()
                status = "healthy" if is_healthy else "unhealthy"
                
                # Log health check result
                health_check_logger.log_health_check(
                    service_name,
                    status,
                    response_time,
                    {"endpoint": endpoint}
                )
                
                results[service_name] = {
                    "status": status,
                    "response_time": response_time,
                    "endpoint": endpoint
                }
                
            except Exception as e:
                # Log health check failure
                health_check_logger.log_health_check(
                    service_name,
                    "error",
                    0.0,
                    {"endpoint": endpoint, "error": str(e)}
                )
                
                results[service_name] = {
                    "status": "error",
                    "error": str(e),
                    "endpoint": endpoint
                }
        
        return results
    
    async def _check_service_health(self, service_name: str, endpoint: str) -> bool:
        """Simulate individual service health check."""
        await asyncio.sleep(0.1)  # Simulate network call
        
        # Simulate occasional failures
        import random
        return random.random() > 0.05  # 95% success rate


# Example usage function
async def demonstrate_enhanced_logging():
    """Demonstrate the enhanced logging system in action."""
    print("Demonstrating Enhanced Logging Integration")
    print("=" * 50)
    
    # Initialize services
    file_service = FileStorageService()
    github_service = GitHubIntegrationService()
    job_service = BackgroundJobService()
    health_service = HealthCheckService()
    
    # Example 1: File operations
    print("\n1. File Storage Operations:")
    try:
        result = await file_service.upload_file(123, "test.txt", b"Hello World")
        print(f"   Uploaded: {result['file_id']}")
        
        info = file_service.get_file_info(result['file_id'])
        print(f"   File info retrieved: {info['filename']}")
        
        await file_service.delete_file(123, result['file_id'])
        print("   File deleted successfully")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 2: GitHub integration
    print("\n2. GitHub Integration:")
    try:
        repos = await github_service.fetch_user_repositories(456, "fake_token")
        print(f"   Fetched {len(repos)} repositories")
        
        webhook_data = {
            "action": "push",
            "repository": {"name": "test-repo"},
            "commits": [{"id": "abc123"}]
        }
        webhook_result = await github_service.process_webhook(webhook_data)
        print(f"   Webhook processed: {webhook_result['status']}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 3: Background jobs
    print("\n3. Background Job Processing:")
    try:
        job_id = job_service.enqueue_analysis_job(789, "repo_123", "code_quality")
        print(f"   Job enqueued: {job_id}")
        
        job_data = {"type": "code_quality", "repository_id": "repo_123"}
        result = await job_service.process_analysis_job(job_id, job_data)
        print(f"   Analysis completed: Quality score {result['quality_score']}")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Example 4: Health checks
    print("\n4. Health Check Monitoring:")
    health_results = await health_service.check_all_services()
    for service, result in health_results.items():
        status = result.get('status', 'unknown')
        print(f"   {service}: {status}")
    
    print("\n" + "=" * 50)
    print("Enhanced logging demonstration completed!")
    
    # Show performance summary
    report = performance_monitor.get_performance_report()
    if report.get('operations'):
        print(f"\nPerformance Summary:")
        total_ops = sum(
            sum(ops.values() for ops in component_ops.values())
            for component_ops in report['operations'].values()
        )
        print(f"Total operations monitored: {total_ops}")


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(demonstrate_enhanced_logging())