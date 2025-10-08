#!/usr/bin/env python3
"""
Test script for Configuration Validation Service.

This script tests the configuration validation service functionality
without requiring the full FastAPI application to be running.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.config_validation_service import config_validation_service, ValidationStatus


async def test_configuration_validation():
    """Test the configuration validation service"""
    print("Testing Configuration Validation Service")
    print("=" * 50)
    
    try:
        # Test complete validation
        print("\n1. Testing complete configuration validation...")
        report = await config_validation_service.validate_all_configurations()
        
        print(f"Overall Status: {report.overall_status.value}")
        print(f"Validation Timestamp: {report.timestamp}")
        print(f"Summary: {report.summary}")
        
        # Display Digital Ocean Spaces validation results
        print("\n2. Digital Ocean Spaces Validation:")
        print("-" * 30)
        for key, result in report.spaces_validation.items():
            status_icon = "✅" if result.status == ValidationStatus.VALID else "❌" if result.status == ValidationStatus.INVALID else "⚠️"
            print(f"{status_icon} {key}: {result.message}")
            if result.suggestions:
                for suggestion in result.suggestions:
                    print(f"   💡 {suggestion}")
        
        # Display GitHub validation results
        print("\n3. GitHub Integration Validation:")
        print("-" * 30)
        for key, result in report.github_validation.items():
            status_icon = "✅" if result.status == ValidationStatus.VALID else "❌" if result.status == ValidationStatus.INVALID else "⚠️"
            print(f"{status_icon} {key}: {result.message}")
            if result.suggestions:
                for suggestion in result.suggestions:
                    print(f"   💡 {suggestion}")
        
        # Display general validation results
        print("\n4. General Configuration Validation:")
        print("-" * 30)
        for key, result in report.general_validation.items():
            status_icon = "✅" if result.status == ValidationStatus.VALID else "❌" if result.status == ValidationStatus.INVALID else "⚠️"
            print(f"{status_icon} {key}: {result.message}")
            if result.suggestions:
                for suggestion in result.suggestions:
                    print(f"   💡 {suggestion}")
        
        # Test individual service validations
        print("\n5. Testing individual service validations...")
        
        # Test Spaces only
        spaces_results = await config_validation_service.validate_spaces_only()
        spaces_status = config_validation_service._determine_overall_status(list(spaces_results.values()))
        print(f"Spaces Only Validation: {spaces_status.value}")
        
        # Test GitHub only
        github_results = await config_validation_service.validate_github_only()
        github_status = config_validation_service._determine_overall_status(list(github_results.values()))
        print(f"GitHub Only Validation: {github_status.value}")
        
        # Test Spaces upload if configuration is valid
        if spaces_status in [ValidationStatus.VALID, ValidationStatus.WARNING]:
            print("\n6. Testing Spaces upload functionality...")
            try:
                upload_result = await config_validation_service.test_spaces_upload()
                upload_icon = "✅" if upload_result.status == ValidationStatus.VALID else "❌"
                print(f"{upload_icon} Upload Test: {upload_result.message}")
            except Exception as e:
                print(f"❌ Upload Test Failed: {str(e)}")
        else:
            print("\n6. Skipping Spaces upload test (configuration invalid)")
        
        print("\n" + "=" * 50)
        print("Configuration validation test completed!")
        
        # Return success if no critical errors
        return report.overall_status != ValidationStatus.ERROR
        
    except Exception as e:
        print(f"❌ Configuration validation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def print_environment_info():
    """Print current environment configuration for debugging"""
    print("Current Environment Configuration:")
    print("-" * 40)
    
    # Digital Ocean Spaces
    print("Digital Ocean Spaces:")
    print(f"  DO_SPACES_KEY: {'✅ Set' if os.getenv('DO_SPACES_KEY') else '❌ Not set'}")
    print(f"  DO_SPACES_SECRET: {'✅ Set' if os.getenv('DO_SPACES_SECRET') else '❌ Not set'}")
    print(f"  DO_SPACES_BUCKET: {os.getenv('DO_SPACES_BUCKET', '❌ Not set')}")
    print(f"  DO_SPACES_REGION: {os.getenv('DO_SPACES_REGION', '❌ Not set')}")
    print(f"  DO_SPACES_ENDPOINT: {os.getenv('DO_SPACES_ENDPOINT', '❌ Not set')}")
    
    # GitHub Integration
    print("\nGitHub Integration:")
    print(f"  GITHUB_CLIENT_ID: {'✅ Set' if os.getenv('GITHUB_CLIENT_ID') else '❌ Not set'}")
    print(f"  GITHUB_CLIENT_SECRET: {'✅ Set' if os.getenv('GITHUB_CLIENT_SECRET') else '❌ Not set'}")
    print(f"  GITHUB_WEBHOOK_SECRET: {'✅ Set' if os.getenv('GITHUB_WEBHOOK_SECRET') else '❌ Not set'}")
    
    # General Configuration
    print("\nGeneral Configuration:")
    print(f"  DATABASE_URL: {'✅ Set' if os.getenv('DATABASE_URL') else '❌ Not set'}")
    print(f"  REDIS_URL: {'✅ Set' if os.getenv('REDIS_URL') else '❌ Not set'}")
    print(f"  SECRET_KEY: {'✅ Set' if os.getenv('SECRET_KEY') else '❌ Not set'}")
    
    print()


async def main():
    """Main test function"""
    print("Configuration Validation Service Test")
    print("=" * 50)
    
    # Print environment info
    print_environment_info()
    
    # Run validation tests
    success = await test_configuration_validation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())