"""
Configuration Validation Service for Digital Ocean Spaces and GitHub Integration.

This service provides comprehensive validation for all integration configurations,
including connectivity tests and credential validation.

Requirements covered: 4.1, 4.2, 4.3
"""

import os
import re
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
import httpx
from github import Github
from github.GithubException import GithubException

from app.core.config import settings


class ValidationStatus(Enum):
    """Validation status enumeration"""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    ERROR = "error"
    NOT_CONFIGURED = "not_configured"


@dataclass
class ValidationResult:
    """Result of a configuration validation"""
    status: ValidationStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    suggestions: Optional[List[str]] = None


@dataclass
class ConfigurationValidationReport:
    """Complete configuration validation report"""
    overall_status: ValidationStatus
    spaces_validation: Dict[str, ValidationResult]
    github_validation: Dict[str, ValidationResult]
    general_validation: Dict[str, ValidationResult]
    timestamp: datetime
    summary: Dict[str, int]


class ConfigurationValidationService:
    """
    Service for validating Digital Ocean Spaces and GitHub integration configurations.
    
    This service provides comprehensive validation including:
    - Configuration presence and format validation
    - Connectivity testing
    - Credential validation
    - Service-specific health checks
    """
    
    def __init__(self):
        """Initialize the configuration validation service"""
        self.timeout = 30  # Default timeout for network operations
        
    async def validate_all_configurations(self) -> ConfigurationValidationReport:
        """
        Validate all integration configurations.
        
        Returns:
            ConfigurationValidationReport with complete validation results
        """
        # Run all validations concurrently
        spaces_validation_task = self._validate_spaces_configuration()
        github_validation_task = self._validate_github_configuration()
        general_validation_task = self._validate_general_configuration()
        
        spaces_validation, github_validation, general_validation = await asyncio.gather(
            spaces_validation_task,
            github_validation_task,
            general_validation_task,
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(spaces_validation, Exception):
            spaces_validation = {
                "error": ValidationResult(
                    status=ValidationStatus.ERROR,
                    message=f"Spaces validation failed: {str(spaces_validation)}",
                    error_code="VALIDATION_ERROR"
                )
            }
        
        if isinstance(github_validation, Exception):
            github_validation = {
                "error": ValidationResult(
                    status=ValidationStatus.ERROR,
                    message=f"GitHub validation failed: {str(github_validation)}",
                    error_code="VALIDATION_ERROR"
                )
            }
        
        if isinstance(general_validation, Exception):
            general_validation = {
                "error": ValidationResult(
                    status=ValidationStatus.ERROR,
                    message=f"General validation failed: {str(general_validation)}",
                    error_code="VALIDATION_ERROR"
                )
            }
        
        # Determine overall status
        all_results = []
        all_results.extend(spaces_validation.values())
        all_results.extend(github_validation.values())
        all_results.extend(general_validation.values())
        
        overall_status = self._determine_overall_status(all_results)
        
        # Generate summary
        summary = {
            "valid": sum(1 for r in all_results if r.status == ValidationStatus.VALID),
            "invalid": sum(1 for r in all_results if r.status == ValidationStatus.INVALID),
            "warning": sum(1 for r in all_results if r.status == ValidationStatus.WARNING),
            "error": sum(1 for r in all_results if r.status == ValidationStatus.ERROR),
            "not_configured": sum(1 for r in all_results if r.status == ValidationStatus.NOT_CONFIGURED)
        }
        
        return ConfigurationValidationReport(
            overall_status=overall_status,
            spaces_validation=spaces_validation,
            github_validation=github_validation,
            general_validation=general_validation,
            timestamp=datetime.utcnow(),
            summary=summary
        )
    
    async def _validate_spaces_configuration(self) -> Dict[str, ValidationResult]:
        """Validate Digital Ocean Spaces configuration"""
        results = {}
        
        # Validate required configuration presence
        results["config_presence"] = self._validate_spaces_config_presence()
        
        # If basic config is missing, skip connectivity tests
        if results["config_presence"].status in [ValidationStatus.INVALID, ValidationStatus.ERROR]:
            results["connectivity"] = ValidationResult(
                status=ValidationStatus.NOT_CONFIGURED,
                message="Skipping connectivity test due to missing configuration"
            )
            results["credentials"] = ValidationResult(
                status=ValidationStatus.NOT_CONFIGURED,
                message="Skipping credential test due to missing configuration"
            )
            results["bucket_access"] = ValidationResult(
                status=ValidationStatus.NOT_CONFIGURED,
                message="Skipping bucket access test due to missing configuration"
            )
            return results
        
        # Validate endpoint format
        results["endpoint_format"] = self._validate_spaces_endpoint_format()
        
        # Test connectivity and credentials
        results["connectivity"] = await self._test_spaces_connectivity()
        results["credentials"] = await self._test_spaces_credentials()
        results["bucket_access"] = await self._test_spaces_bucket_access()
        
        return results
    
    async def _validate_github_configuration(self) -> Dict[str, ValidationResult]:
        """Validate GitHub integration configuration"""
        results = {}
        
        # Validate OAuth configuration
        results["oauth_config"] = self._validate_github_oauth_config()
        
        # Validate App configuration (optional)
        results["app_config"] = self._validate_github_app_config()
        
        # Validate webhook configuration
        results["webhook_config"] = self._validate_github_webhook_config()
        
        # Test GitHub API connectivity
        results["api_connectivity"] = await self._test_github_api_connectivity()
        
        # Test OAuth credentials if configured
        if results["oauth_config"].status == ValidationStatus.VALID:
            results["oauth_credentials"] = await self._test_github_oauth_credentials()
        else:
            results["oauth_credentials"] = ValidationResult(
                status=ValidationStatus.NOT_CONFIGURED,
                message="Skipping OAuth credential test due to missing configuration"
            )
        
        return results
    
    async def _validate_general_configuration(self) -> Dict[str, ValidationResult]:
        """Validate general application configuration"""
        results = {}
        
        # Validate database configuration
        results["database_config"] = self._validate_database_config()
        
        # Validate Redis configuration
        results["redis_config"] = self._validate_redis_config()
        
        # Validate security configuration
        results["security_config"] = self._validate_security_config()
        
        # Validate file storage settings
        results["file_storage_settings"] = self._validate_file_storage_settings()
        
        return results
    
    def _validate_spaces_config_presence(self) -> ValidationResult:
        """Validate presence of required Digital Ocean Spaces configuration"""
        required_configs = {
            'DO_SPACES_KEY': settings.DO_SPACES_KEY,
            'DO_SPACES_SECRET': settings.DO_SPACES_SECRET,
            'DO_SPACES_BUCKET': settings.DO_SPACES_BUCKET,
            'DO_SPACES_ENDPOINT': settings.DO_SPACES_ENDPOINT,
            'DO_SPACES_REGION': settings.DO_SPACES_REGION
        }
        
        missing_configs = [key for key, value in required_configs.items() if not value]
        
        if missing_configs:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                message=f"Missing required Digital Ocean Spaces configuration",
                details={"missing_configs": missing_configs},
                error_code="MISSING_CONFIG",
                suggestions=[
                    f"Set {config} in your environment variables or .env file"
                    for config in missing_configs
                ]
            )
        
        return ValidationResult(
            status=ValidationStatus.VALID,
            message="All required Digital Ocean Spaces configuration is present"
        )
    
    def _validate_spaces_endpoint_format(self) -> ValidationResult:
        """Validate Digital Ocean Spaces endpoint format"""
        endpoint = settings.DO_SPACES_ENDPOINT
        region = settings.DO_SPACES_REGION
        
        if not endpoint:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                message="Digital Ocean Spaces endpoint is not configured",
                error_code="MISSING_ENDPOINT"
            )
        
        # Check if endpoint follows correct format
        expected_format = f"https://{region}.digitaloceanspaces.com"
        
        if endpoint != expected_format:
            # Check if it's the old incorrect format with bucket name
            bucket_format_pattern = rf"https://.*\.{re.escape(region)}\.digitaloceanspaces\.com"
            if re.match(bucket_format_pattern, endpoint):
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    message="Digital Ocean Spaces endpoint includes bucket name (incorrect format)",
                    details={
                        "current_endpoint": endpoint,
                        "expected_endpoint": expected_format
                    },
                    error_code="INCORRECT_ENDPOINT_FORMAT",
                    suggestions=[
                        f"Change DO_SPACES_ENDPOINT to: {expected_format}",
                        "Remove bucket name from endpoint URL"
                    ]
                )
            else:
                return ValidationResult(
                    status=ValidationStatus.WARNING,
                    message="Digital Ocean Spaces endpoint format may be incorrect",
                    details={
                        "current_endpoint": endpoint,
                        "expected_format": expected_format
                    },
                    suggestions=[
                        f"Verify endpoint format. Expected: {expected_format}"
                    ]
                )
        
        return ValidationResult(
            status=ValidationStatus.VALID,
            message="Digital Ocean Spaces endpoint format is correct"
        )
    
    async def _test_spaces_connectivity(self) -> ValidationResult:
        """Test connectivity to Digital Ocean Spaces"""
        try:
            config = Config(
                region_name=settings.DO_SPACES_REGION,
                retries={'max_attempts': 2, 'mode': 'adaptive'},
                connect_timeout=self.timeout,
                read_timeout=self.timeout
            )
            
            client = boto3.client(
                's3',
                endpoint_url=settings.DO_SPACES_ENDPOINT,
                aws_access_key_id=settings.DO_SPACES_KEY,
                aws_secret_access_key=settings.DO_SPACES_SECRET,
                config=config
            )
            
            # Test basic connectivity by listing buckets
            await asyncio.get_event_loop().run_in_executor(
                None, client.list_buckets
            )
            
            return ValidationResult(
                status=ValidationStatus.VALID,
                message="Successfully connected to Digital Ocean Spaces"
            )
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            return ValidationResult(
                status=ValidationStatus.INVALID,
                message=f"Failed to connect to Digital Ocean Spaces: {error_code}",
                details={"aws_error": str(e)},
                error_code="CONNECTIVITY_ERROR",
                suggestions=[
                    "Verify your DO_SPACES_KEY and DO_SPACES_SECRET",
                    "Check your internet connection",
                    "Verify the DO_SPACES_ENDPOINT is correct"
                ]
            )
        except Exception as e:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"Unexpected error testing Spaces connectivity: {str(e)}",
                error_code="CONNECTIVITY_ERROR"
            )
    
    async def _test_spaces_credentials(self) -> ValidationResult:
        """Test Digital Ocean Spaces credentials"""
        try:
            config = Config(
                region_name=settings.DO_SPACES_REGION,
                retries={'max_attempts': 2, 'mode': 'adaptive'},
                connect_timeout=self.timeout,
                read_timeout=self.timeout
            )
            
            client = boto3.client(
                's3',
                endpoint_url=settings.DO_SPACES_ENDPOINT,
                aws_access_key_id=settings.DO_SPACES_KEY,
                aws_secret_access_key=settings.DO_SPACES_SECRET,
                config=config
            )
            
            # Test credentials by getting account information
            response = await asyncio.get_event_loop().run_in_executor(
                None, client.list_buckets
            )
            
            return ValidationResult(
                status=ValidationStatus.VALID,
                message="Digital Ocean Spaces credentials are valid",
                details={"bucket_count": len(response.get('Buckets', []))}
            )
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code in ['InvalidAccessKeyId', 'SignatureDoesNotMatch']:
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    message="Invalid Digital Ocean Spaces credentials",
                    details={"aws_error_code": error_code},
                    error_code="INVALID_CREDENTIALS",
                    suggestions=[
                        "Verify your DO_SPACES_KEY is correct",
                        "Verify your DO_SPACES_SECRET is correct",
                        "Check if credentials have expired"
                    ]
                )
            else:
                return ValidationResult(
                    status=ValidationStatus.ERROR,
                    message=f"Error validating Spaces credentials: {error_code}",
                    details={"aws_error": str(e)},
                    error_code="CREDENTIAL_ERROR"
                )
        except Exception as e:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"Unexpected error validating Spaces credentials: {str(e)}",
                error_code="CREDENTIAL_ERROR"
            )
    
    async def _test_spaces_bucket_access(self) -> ValidationResult:
        """Test access to the configured Digital Ocean Spaces bucket"""
        try:
            config = Config(
                region_name=settings.DO_SPACES_REGION,
                retries={'max_attempts': 2, 'mode': 'adaptive'},
                connect_timeout=self.timeout,
                read_timeout=self.timeout
            )
            
            client = boto3.client(
                's3',
                endpoint_url=settings.DO_SPACES_ENDPOINT,
                aws_access_key_id=settings.DO_SPACES_KEY,
                aws_secret_access_key=settings.DO_SPACES_SECRET,
                config=config
            )
            
            # Test bucket access by getting bucket location
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: client.head_bucket(Bucket=settings.DO_SPACES_BUCKET)
            )
            
            # Test list objects permission
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: client.list_objects_v2(Bucket=settings.DO_SPACES_BUCKET, MaxKeys=1)
            )
            
            return ValidationResult(
                status=ValidationStatus.VALID,
                message=f"Successfully accessed bucket '{settings.DO_SPACES_BUCKET}'"
            )
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'NoSuchBucket':
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    message=f"Bucket '{settings.DO_SPACES_BUCKET}' does not exist",
                    details={"bucket_name": settings.DO_SPACES_BUCKET},
                    error_code="BUCKET_NOT_FOUND",
                    suggestions=[
                        f"Create bucket '{settings.DO_SPACES_BUCKET}' in Digital Ocean Spaces",
                        "Verify the bucket name is correct in DO_SPACES_BUCKET"
                    ]
                )
            elif error_code == 'AccessDenied':
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    message=f"Access denied to bucket '{settings.DO_SPACES_BUCKET}'",
                    details={"bucket_name": settings.DO_SPACES_BUCKET},
                    error_code="BUCKET_ACCESS_DENIED",
                    suggestions=[
                        "Verify your credentials have access to this bucket",
                        "Check bucket permissions in Digital Ocean Spaces console"
                    ]
                )
            else:
                return ValidationResult(
                    status=ValidationStatus.ERROR,
                    message=f"Error accessing bucket: {error_code}",
                    details={"aws_error": str(e)},
                    error_code="BUCKET_ERROR"
                )
        except Exception as e:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"Unexpected error testing bucket access: {str(e)}",
                error_code="BUCKET_ERROR"
            )
    
    def _validate_github_oauth_config(self) -> ValidationResult:
        """Validate GitHub OAuth configuration"""
        required_configs = {
            'GITHUB_CLIENT_ID': settings.GITHUB_CLIENT_ID,
            'GITHUB_CLIENT_SECRET': settings.GITHUB_CLIENT_SECRET,
            'GITHUB_OAUTH_REDIRECT_URI': settings.GITHUB_OAUTH_REDIRECT_URI
        }
        
        missing_configs = [key for key, value in required_configs.items() if not value]
        
        if missing_configs:
            return ValidationResult(
                status=ValidationStatus.NOT_CONFIGURED,
                message="GitHub OAuth is not configured",
                details={"missing_configs": missing_configs},
                suggestions=[
                    f"Set {config} in your environment variables"
                    for config in missing_configs
                ]
            )
        
        # Validate redirect URI format
        redirect_uri = settings.GITHUB_OAUTH_REDIRECT_URI
        if not redirect_uri.startswith(('http://', 'https://')):
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message="GitHub OAuth redirect URI should use http:// or https://",
                details={"redirect_uri": redirect_uri},
                suggestions=["Use a proper URL format for GITHUB_OAUTH_REDIRECT_URI"]
            )
        
        return ValidationResult(
            status=ValidationStatus.VALID,
            message="GitHub OAuth configuration is present and valid"
        )
    
    def _validate_github_app_config(self) -> ValidationResult:
        """Validate GitHub App configuration (optional)"""
        app_id = settings.GITHUB_APP_ID
        private_key = settings.GITHUB_PRIVATE_KEY
        private_key_path = settings.GITHUB_PRIVATE_KEY_PATH
        
        if not app_id and not private_key and not private_key_path:
            return ValidationResult(
                status=ValidationStatus.NOT_CONFIGURED,
                message="GitHub App is not configured (optional)"
            )
        
        missing_configs = []
        if not app_id:
            missing_configs.append('GITHUB_APP_ID')
        
        if not private_key and not private_key_path:
            missing_configs.append('GITHUB_PRIVATE_KEY or GITHUB_PRIVATE_KEY_PATH')
        
        if missing_configs:
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message="Incomplete GitHub App configuration",
                details={"missing_configs": missing_configs},
                suggestions=[
                    "Complete GitHub App configuration or remove partial configuration"
                ]
            )
        
        # Validate private key if provided directly
        if private_key and not private_key.startswith('-----BEGIN'):
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message="GitHub private key format may be incorrect",
                suggestions=["Ensure private key is in PEM format"]
            )
        
        # Validate private key file if path is provided
        if private_key_path and not os.path.exists(private_key_path):
            return ValidationResult(
                status=ValidationStatus.INVALID,
                message=f"GitHub private key file not found: {private_key_path}",
                error_code="KEY_FILE_NOT_FOUND",
                suggestions=[
                    f"Create the private key file at {private_key_path}",
                    "Verify the GITHUB_PRIVATE_KEY_PATH is correct"
                ]
            )
        
        return ValidationResult(
            status=ValidationStatus.VALID,
            message="GitHub App configuration is valid"
        )
    
    def _validate_github_webhook_config(self) -> ValidationResult:
        """Validate GitHub webhook configuration"""
        webhook_secret = settings.GITHUB_WEBHOOK_SECRET
        webhook_base_url = settings.GITHUB_WEBHOOK_BASE_URL
        
        if not webhook_secret:
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message="GitHub webhook secret is not configured",
                suggestions=[
                    "Set GITHUB_WEBHOOK_SECRET for secure webhook processing"
                ]
            )
        
        if len(webhook_secret) < 16:
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message="GitHub webhook secret is too short",
                suggestions=[
                    "Use a webhook secret with at least 16 characters"
                ]
            )
        
        if not webhook_base_url.startswith(('http://', 'https://')):
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message="GitHub webhook base URL should use http:// or https://",
                details={"webhook_base_url": webhook_base_url}
            )
        
        return ValidationResult(
            status=ValidationStatus.VALID,
            message="GitHub webhook configuration is valid"
        )
    
    async def _test_github_api_connectivity(self) -> ValidationResult:
        """Test connectivity to GitHub API"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{settings.GITHUB_API_BASE_URL}/rate_limit")
                
                if response.status_code == 200:
                    data = response.json()
                    return ValidationResult(
                        status=ValidationStatus.VALID,
                        message="Successfully connected to GitHub API",
                        details={
                            "rate_limit": data.get('rate', {}).get('limit'),
                            "remaining": data.get('rate', {}).get('remaining')
                        }
                    )
                else:
                    return ValidationResult(
                        status=ValidationStatus.WARNING,
                        message=f"GitHub API returned status {response.status_code}",
                        details={"status_code": response.status_code}
                    )
                    
        except httpx.TimeoutException:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message="Timeout connecting to GitHub API",
                error_code="TIMEOUT_ERROR",
                suggestions=["Check your internet connection"]
            )
        except Exception as e:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"Error connecting to GitHub API: {str(e)}",
                error_code="CONNECTIVITY_ERROR"
            )
    
    async def _test_github_oauth_credentials(self) -> ValidationResult:
        """Test GitHub OAuth credentials"""
        try:
            # Test by making a request to GitHub's OAuth application endpoint
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # This endpoint requires authentication but we can test if credentials are recognized
                auth = (settings.GITHUB_CLIENT_ID, settings.GITHUB_CLIENT_SECRET)
                response = await client.get(
                    f"{settings.GITHUB_API_BASE_URL}/applications/{settings.GITHUB_CLIENT_ID}/tokens",
                    auth=auth
                )
                
                if response.status_code in [200, 422]:  # 422 is expected for empty token list
                    return ValidationResult(
                        status=ValidationStatus.VALID,
                        message="GitHub OAuth credentials are valid"
                    )
                elif response.status_code == 401:
                    return ValidationResult(
                        status=ValidationStatus.INVALID,
                        message="Invalid GitHub OAuth credentials",
                        error_code="INVALID_OAUTH_CREDENTIALS",
                        suggestions=[
                            "Verify GITHUB_CLIENT_ID is correct",
                            "Verify GITHUB_CLIENT_SECRET is correct",
                            "Check if OAuth app exists in GitHub"
                        ]
                    )
                else:
                    return ValidationResult(
                        status=ValidationStatus.WARNING,
                        message=f"Unexpected response testing OAuth credentials: {response.status_code}",
                        details={"status_code": response.status_code}
                    )
                    
        except Exception as e:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"Error testing GitHub OAuth credentials: {str(e)}",
                error_code="OAUTH_TEST_ERROR"
            )
    
    def _validate_database_config(self) -> ValidationResult:
        """Validate database configuration"""
        database_url = settings.DATABASE_URL
        
        if not database_url:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                message="Database URL is not configured",
                error_code="MISSING_DATABASE_URL",
                suggestions=["Set DATABASE_URL in your environment variables"]
            )
        
        # Basic URL format validation
        if not database_url.startswith('postgresql://'):
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message="Database URL should start with 'postgresql://'",
                details={"database_url": database_url[:50] + "..."}
            )
        
        return ValidationResult(
            status=ValidationStatus.VALID,
            message="Database configuration is present"
        )
    
    def _validate_redis_config(self) -> ValidationResult:
        """Validate Redis configuration"""
        redis_url = settings.REDIS_URL
        
        if not redis_url:
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message="Redis URL is not configured",
                suggestions=["Set REDIS_URL for caching and queue functionality"]
            )
        
        if not redis_url.startswith('redis://'):
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message="Redis URL should start with 'redis://'",
                details={"redis_url": redis_url}
            )
        
        return ValidationResult(
            status=ValidationStatus.VALID,
            message="Redis configuration is present"
        )
    
    def _validate_security_config(self) -> ValidationResult:
        """Validate security configuration"""
        secret_key = settings.SECRET_KEY
        
        if not secret_key:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                message="Secret key is not configured",
                error_code="MISSING_SECRET_KEY",
                suggestions=["Set SECRET_KEY in your environment variables"]
            )
        
        if len(secret_key) < 32:
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message="Secret key is too short (should be at least 32 characters)",
                suggestions=["Use a longer secret key for better security"]
            )
        
        if secret_key == "your-super-secret-key-change-this-in-production-min-32-chars":
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message="Using default secret key (change in production)",
                suggestions=["Generate a unique secret key for production use"]
            )
        
        return ValidationResult(
            status=ValidationStatus.VALID,
            message="Security configuration is valid"
        )
    
    def _validate_file_storage_settings(self) -> ValidationResult:
        """Validate file storage settings"""
        issues = []
        
        # Validate max file size
        max_size = settings.MAX_FILE_SIZE_MB
        if max_size <= 0:
            issues.append("MAX_FILE_SIZE_MB should be greater than 0")
        elif max_size > 1000:
            issues.append("MAX_FILE_SIZE_MB is very large (>1GB), consider reducing")
        
        # Validate file extensions
        extensions = settings.ALLOWED_FILE_EXTENSIONS
        if not extensions:
            issues.append("ALLOWED_FILE_EXTENSIONS is empty")
        
        # Validate expiration hours
        expiration = settings.SIGNED_URL_EXPIRATION_HOURS
        if expiration <= 0:
            issues.append("SIGNED_URL_EXPIRATION_HOURS should be greater than 0")
        elif expiration > 168:  # 1 week
            issues.append("SIGNED_URL_EXPIRATION_HOURS is very long (>1 week)")
        
        if issues:
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message="File storage settings have issues",
                details={"issues": issues},
                suggestions=issues
            )
        
        return ValidationResult(
            status=ValidationStatus.VALID,
            message="File storage settings are valid"
        )
    
    def _determine_overall_status(self, results: List[ValidationResult]) -> ValidationStatus:
        """Determine overall validation status from individual results"""
        if not results:
            return ValidationStatus.ERROR
        
        statuses = [result.status for result in results]
        
        # If any critical errors, overall is error
        if ValidationStatus.ERROR in statuses:
            return ValidationStatus.ERROR
        
        # If any invalid configurations, overall is invalid
        if ValidationStatus.INVALID in statuses:
            return ValidationStatus.INVALID
        
        # If any warnings, overall is warning
        if ValidationStatus.WARNING in statuses:
            return ValidationStatus.WARNING
        
        # If everything is valid or not configured, overall is valid
        return ValidationStatus.VALID
    
    async def validate_spaces_only(self) -> Dict[str, ValidationResult]:
        """Validate only Digital Ocean Spaces configuration"""
        return await self._validate_spaces_configuration()
    
    async def validate_github_only(self) -> Dict[str, ValidationResult]:
        """Validate only GitHub integration configuration"""
        return await self._validate_github_configuration()
    
    async def test_spaces_upload(self, test_content: bytes = b"test") -> ValidationResult:
        """Test actual file upload to Digital Ocean Spaces"""
        try:
            config = Config(
                region_name=settings.DO_SPACES_REGION,
                retries={'max_attempts': 2, 'mode': 'adaptive'},
                connect_timeout=self.timeout,
                read_timeout=self.timeout
            )
            
            client = boto3.client(
                's3',
                endpoint_url=settings.DO_SPACES_ENDPOINT,
                aws_access_key_id=settings.DO_SPACES_KEY,
                aws_secret_access_key=settings.DO_SPACES_SECRET,
                config=config
            )
            
            # Test upload
            test_key = f"config-validation-test-{datetime.utcnow().isoformat()}.txt"
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.put_object(
                    Bucket=settings.DO_SPACES_BUCKET,
                    Key=test_key,
                    Body=test_content,
                    ContentType='text/plain'
                )
            )
            
            # Test download
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.get_object(Bucket=settings.DO_SPACES_BUCKET, Key=test_key)
            )
            
            # Clean up test file
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.delete_object(Bucket=settings.DO_SPACES_BUCKET, Key=test_key)
            )
            
            return ValidationResult(
                status=ValidationStatus.VALID,
                message="Successfully tested file upload/download operations"
            )
            
        except Exception as e:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                message=f"File upload test failed: {str(e)}",
                error_code="UPLOAD_TEST_FAILED"
            )


# Global instance
config_validation_service = ConfigurationValidationService()