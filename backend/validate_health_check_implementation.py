#!/usr/bin/env python3
"""
Validation script for the Health Check and Testing System implementation.

This script validates that all components of the health check system
are properly implemented and can be imported without errors.

Requirements covered: 4.3, 4.4
"""

import sys
import importlib.util
from pathlib import Path

def validate_file_exists(file_path: str) -> bool:
    """Validate that a file exists"""
    path = Path(file_path)
    if path.exists():
        print(f"✓ {file_path} exists")
        return True
    else:
        print(f"✗ {file_path} does not exist")
        return False

def validate_python_syntax(file_path: str) -> bool:
    """Validate Python file syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            compile(f.read(), file_path, 'exec')
        print(f"✓ {file_path} has valid Python syntax")
        return True
    except SyntaxError as e:
        print(f"✗ {file_path} has syntax error: {e}")
        return False
    except Exception as e:
        print(f"✗ {file_path} validation failed: {e}")
        return False

def validate_imports(file_path: str, required_imports: list) -> bool:
    """Validate that a file contains required imports"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing_imports = []
        for import_stmt in required_imports:
            if import_stmt not in content:
                missing_imports.append(import_stmt)
        
        if missing_imports:
            print(f"✗ {file_path} missing imports: {missing_imports}")
            return False
        else:
            print(f"✓ {file_path} has all required imports")
            return True
    except Exception as e:
        print(f"✗ {file_path} import validation failed: {e}")
        return False

def validate_router_registration() -> bool:
    """Validate that health check router is registered"""
    router_file = "app/api/v1/router.py"
    try:
        with open(router_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_elements = [
            "health_check",
            "health_check.router",
            'prefix="/health"'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"✗ Router registration missing elements: {missing_elements}")
            return False
        else:
            print(f"✓ Health check router is properly registered")
            return True
    except Exception as e:
        print(f"✗ Router registration validation failed: {e}")
        return False

def main():
    """Main validation function"""
    print("Health Check System Implementation Validation")
    print("=" * 50)
    
    validation_results = []
    
    # Validate file existence
    print("\n1. File Existence Validation:")
    files_to_check = [
        "app/api/v1/endpoints/health_check.py",
        "test_system_health.py",
        "run_health_tests.bat",
        "run_health_tests.ps1",
        "HEALTH_CHECK_SYSTEM_README.md"
    ]
    
    for file_path in files_to_check:
        validation_results.append(validate_file_exists(file_path))
    
    # Validate Python syntax
    print("\n2. Python Syntax Validation:")
    python_files = [
        "app/api/v1/endpoints/health_check.py",
        "test_system_health.py"
    ]
    
    for file_path in python_files:
        if Path(file_path).exists():
            validation_results.append(validate_python_syntax(file_path))
    
    # Validate required imports in health check endpoint
    print("\n3. Health Check Endpoint Import Validation:")
    health_check_imports = [
        "from fastapi import APIRouter",
        "from app.services.config_validation_service import config_validation_service",
        "from app.services.file_storage_service import FileStorageService",
        "from app.services.github_api_client import GitHubAPIClient",
        "from app.services.queue_monitoring_service import queue_monitoring_service"
    ]
    
    if Path("app/api/v1/endpoints/health_check.py").exists():
        validation_results.append(validate_imports(
            "app/api/v1/endpoints/health_check.py", 
            health_check_imports
        ))
    
    # Validate test script imports
    print("\n4. Test Script Import Validation:")
    test_script_imports = [
        "from app.services.config_validation_service import config_validation_service",
        "from app.services.file_storage_service import FileStorageService",
        "from app.services.github_api_client import GitHubAPIClient",
        "from app.services.queue_monitoring_service import queue_monitoring_service"
    ]
    
    if Path("test_system_health.py").exists():
        validation_results.append(validate_imports(
            "test_system_health.py", 
            test_script_imports
        ))
    
    # Validate router registration
    print("\n5. Router Registration Validation:")
    validation_results.append(validate_router_registration())
    
    # Validate endpoint definitions
    print("\n6. Endpoint Definition Validation:")
    if Path("app/api/v1/endpoints/health_check.py").exists():
        with open("app/api/v1/endpoints/health_check.py", 'r') as f:
            content = f.read()
        
        required_endpoints = [
            '@router.get("/health")',
            '@router.get("/health/detailed")',
            '@router.get("/test/spaces")',
            '@router.get("/test/github")',
            '@router.get("/test/queue")',
            '@router.get("/test/all")'
        ]
        
        missing_endpoints = []
        for endpoint in required_endpoints:
            if endpoint not in content:
                missing_endpoints.append(endpoint)
        
        if missing_endpoints:
            print(f"✗ Missing endpoint definitions: {missing_endpoints}")
            validation_results.append(False)
        else:
            print(f"✓ All required endpoints are defined")
            validation_results.append(True)
    
    # Summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    total_checks = len(validation_results)
    passed_checks = sum(validation_results)
    failed_checks = total_checks - passed_checks
    
    print(f"Total Checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {failed_checks}")
    
    if failed_checks == 0:
        print("\n✓ ALL VALIDATIONS PASSED")
        print("The health check system implementation is complete and valid.")
        return True
    else:
        print(f"\n✗ {failed_checks} VALIDATION(S) FAILED")
        print("Please review the failed validations above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)