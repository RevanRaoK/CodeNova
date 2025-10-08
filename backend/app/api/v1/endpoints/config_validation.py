"""
Configuration Validation API endpoints.

This module provides REST API endpoints for validating system configurations
including Digital Ocean Spaces and GitHub integration settings.

Requirements covered: 4.1, 4.2, 4.3
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_admin
from app.models.users import User, UserRole
from app.services.config_validation_service import (
    config_validation_service,
    ConfigurationValidationReport,
    ValidationResult,
    ValidationStatus
)



router = APIRouter()


def require_admin_user(current_user: User = Depends(require_admin)) -> User:
    """Dependency to require admin user for configuration validation endpoints"""
    return current_user


@router.get("/validate/all", response_model=Dict[str, Any])
async def validate_all_configurations(
    current_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    Validate all system configurations.
    
    This endpoint performs comprehensive validation of:
    - Digital Ocean Spaces configuration and connectivity
    - GitHub integration configuration and credentials
    - General application configuration
    
    Returns:
        Complete validation report with status and details
    """
    try:
        report = await config_validation_service.validate_all_configurations()
        
        # Convert to dictionary for JSON response
        return {
            "overall_status": report.overall_status.value,
            "timestamp": report.timestamp.isoformat(),
            "summary": report.summary,
            "validations": {
                "digital_ocean_spaces": {
                    key: {
                        "status": result.status.value,
                        "message": result.message,
                        "details": result.details,
                        "error_code": result.error_code,
                        "suggestions": result.suggestions
                    }
                    for key, result in report.spaces_validation.items()
                },
                "github_integration": {
                    key: {
                        "status": result.status.value,
                        "message": result.message,
                        "details": result.details,
                        "error_code": result.error_code,
                        "suggestions": result.suggestions
                    }
                    for key, result in report.github_validation.items()
                },
                "general_configuration": {
                    key: {
                        "status": result.status.value,
                        "message": result.message,
                        "details": result.details,
                        "error_code": result.error_code,
                        "suggestions": result.suggestions
                    }
                    for key, result in report.general_validation.items()
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Configuration validation failed: {str(e)}"
        )


@router.get("/validate/spaces", response_model=Dict[str, Any])
async def validate_spaces_configuration(
    current_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    Validate Digital Ocean Spaces configuration only.
    
    This endpoint validates:
    - Configuration presence and format
    - Endpoint URL format
    - Connectivity to Digital Ocean Spaces
    - Credential validation
    - Bucket access permissions
    
    Returns:
        Spaces-specific validation results
    """
    try:
        results = await config_validation_service.validate_spaces_only()
        
        return {
            "service": "digital_ocean_spaces",
            "overall_status": config_validation_service._determine_overall_status(list(results.values())).value,
            "validations": {
                key: {
                    "status": result.status.value,
                    "message": result.message,
                    "details": result.details,
                    "error_code": result.error_code,
                    "suggestions": result.suggestions
                }
                for key, result in results.items()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Spaces configuration validation failed: {str(e)}"
        )


@router.get("/validate/github", response_model=Dict[str, Any])
async def validate_github_configuration(
    current_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    Validate GitHub integration configuration only.
    
    This endpoint validates:
    - OAuth configuration
    - GitHub App configuration (if configured)
    - Webhook configuration
    - API connectivity
    - Credential validation
    
    Returns:
        GitHub-specific validation results
    """
    try:
        results = await config_validation_service.validate_github_only()
        
        return {
            "service": "github_integration",
            "overall_status": config_validation_service._determine_overall_status(list(results.values())).value,
            "validations": {
                key: {
                    "status": result.status.value,
                    "message": result.message,
                    "details": result.details,
                    "error_code": result.error_code,
                    "suggestions": result.suggestions
                }
                for key, result in results.items()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"GitHub configuration validation failed: {str(e)}"
        )


@router.post("/test/spaces-upload", response_model=Dict[str, Any])
async def test_spaces_upload(
    current_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    Test actual file upload to Digital Ocean Spaces.
    
    This endpoint performs a real upload/download/delete test to verify
    that file operations work correctly with the current configuration.
    
    Returns:
        Test results with success/failure status
    """
    try:
        result = await config_validation_service.test_spaces_upload()
        
        return {
            "test": "spaces_upload",
            "status": result.status.value,
            "message": result.message,
            "details": result.details,
            "error_code": result.error_code,
            "suggestions": result.suggestions
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Spaces upload test failed: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, Any])
async def configuration_health_check(
    current_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db)
):
    """
    Quick health check for critical configurations.
    
    This endpoint provides a fast overview of configuration status
    without performing extensive connectivity tests.
    
    Returns:
        Quick health status for all integrations
    """
    try:
        # Perform basic configuration presence checks only
        spaces_config = config_validation_service._validate_spaces_config_presence()
        github_oauth = config_validation_service._validate_github_oauth_config()
        database_config = config_validation_service._validate_database_config()
        
        overall_healthy = all(
            result.status in [ValidationStatus.VALID, ValidationStatus.WARNING, ValidationStatus.NOT_CONFIGURED]
            for result in [spaces_config, github_oauth, database_config]
        )
        
        return {
            "healthy": overall_healthy,
            "services": {
                "digital_ocean_spaces": {
                    "status": spaces_config.status.value,
                    "message": spaces_config.message
                },
                "github_oauth": {
                    "status": github_oauth.status.value,
                    "message": github_oauth.message
                },
                "database": {
                    "status": database_config.status.value,
                    "message": database_config.message
                }
            }
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        }


@router.get("/status", response_model=Dict[str, Any])
async def get_configuration_status():
    """
    Get basic configuration status without authentication.
    
    This endpoint provides minimal configuration status information
    that can be used for system monitoring without requiring authentication.
    
    Returns:
        Basic configuration status
    """
    try:
        # Only check if basic configuration is present (no connectivity tests)
        from app.core.config import settings
        
        spaces_present = bool(
            settings.DO_SPACES_KEY and
            settings.DO_SPACES_SECRET and
            settings.DO_SPACES_BUCKET
        )
        
        github_present = bool(
            settings.GITHUB_CLIENT_ID and
            settings.GITHUB_CLIENT_SECRET
        )
        
        database_present = bool(settings.DATABASE_URL)
        
        return {
            "configured_services": {
                "digital_ocean_spaces": spaces_present,
                "github_integration": github_present,
                "database": database_present
            },
            "environment": settings.ENVIRONMENT
        }
        
    except Exception as e:
        return {
            "configured_services": {
                "digital_ocean_spaces": False,
                "github_integration": False,
                "database": False
            },
            "error": str(e)
        }