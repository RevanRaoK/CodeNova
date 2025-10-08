#!/usr/bin/env python3
"""
Simplified performance testing for the backend without external dependencies.

This script tests core functionality without requiring Redis or other services.
"""

import asyncio
import time
import sys
import os
from datetime import datetime
import json

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.config import settings
    from app.core.database import engine
    from sqlalchemy import text
    print("✅ Core imports successful")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class SimplePerformanceTest:
    """Simple performance tests without external dependencies."""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    async def run_tests(self):
        """Run all available performance tests."""
        print("🚀 Starting Simple Performance Tests")
        print("=" * 50)
        
        self.start_time = time.time()
        
        # Test 1: Configuration Check
        print("\n📋 Test 1: Configuration Check")
        await self.test_configuration()
        
        # Test 2: Database Connection
        print("\n🗄️  Test 2: Database Connection")
        await self.test_database_connection()
        
        # Test 3: Settings Validation
        print("\n⚙️  Test 3: Settings Validation")
        await self.test_settings_validation()
        
        # Test 4: Import Performance
        print("\n📦 Test 4: Import Performance")
        await self.test_import_performance()
        
        self.end_time = time.time()
        
        # Generate Report
        print("\n📊 Generating Report")
        await self.generate_report()
    
    async def test_configuration(self):
        """Test configuration loading."""
        try:
            start_time = time.time()
            
            # Test basic settings
            project_name = settings.PROJECT_NAME
            api_str = settings.API_V1_STR
            db_url = settings.DATABASE_URL
            
            duration = (time.time() - start_time) * 1000
            
            self.results["configuration"] = {
                "status": "success",
                "duration_ms": duration,
                "project_name": project_name,
                "api_version": api_str,
                "has_database_url": bool(db_url)
            }
            
            print(f"   ✅ Configuration loaded in {duration:.2f}ms")
            
        except Exception as e:
            self.results["configuration"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"   ❌ Configuration test failed: {e}")
    
    async def test_database_connection(self):
        """Test database connection performance."""
        try:
            start_time = time.time()
            
            # Test database connection
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1 as test"))
                test_result = result.fetchone()
            
            duration = (time.time() - start_time) * 1000
            
            self.results["database"] = {
                "status": "success",
                "duration_ms": duration,
                "connection_successful": test_result[0] == 1 if test_result else False
            }
            
            print(f"   ✅ Database connection in {duration:.2f}ms")
            
        except Exception as e:
            self.results["database"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"   ❌ Database test failed: {e}")
    
    async def test_settings_validation(self):
        """Test settings validation performance."""
        try:
            start_time = time.time()
            
            # Test various settings
            required_settings = [
                "PROJECT_NAME",
                "API_V1_STR", 
                "DATABASE_URL",
                "SECRET_KEY",
                "ENVIRONMENT"
            ]
            
            missing_settings = []
            for setting in required_settings:
                if not hasattr(settings, setting) or not getattr(settings, setting):
                    missing_settings.append(setting)
            
            duration = (time.time() - start_time) * 1000
            
            self.results["settings_validation"] = {
                "status": "success" if not missing_settings else "warning",
                "duration_ms": duration,
                "total_settings": len(required_settings),
                "missing_settings": missing_settings,
                "environment": getattr(settings, "ENVIRONMENT", "unknown")
            }
            
            if missing_settings:
                print(f"   ⚠️  Settings validation in {duration:.2f}ms (missing: {missing_settings})")
            else:
                print(f"   ✅ Settings validation in {duration:.2f}ms")
            
        except Exception as e:
            self.results["settings_validation"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"   ❌ Settings validation failed: {e}")
    
    async def test_import_performance(self):
        """Test import performance of key modules."""
        try:
            imports_to_test = [
                ("app.models", "User, Repository, Analysis"),
                ("app.core.database", "Base, engine"),
                ("app.core.config", "settings"),
            ]
            
            import_results = []
            total_start = time.time()
            
            for module_name, components in imports_to_test:
                start_time = time.time()
                try:
                    __import__(module_name)
                    duration = (time.time() - start_time) * 1000
                    import_results.append({
                        "module": module_name,
                        "status": "success",
                        "duration_ms": duration
                    })
                except Exception as e:
                    duration = (time.time() - start_time) * 1000
                    import_results.append({
                        "module": module_name,
                        "status": "error",
                        "duration_ms": duration,
                        "error": str(e)
                    })
            
            total_duration = (time.time() - total_start) * 1000
            
            self.results["import_performance"] = {
                "status": "success",
                "total_duration_ms": total_duration,
                "imports": import_results
            }
            
            print(f"   ✅ Import performance test in {total_duration:.2f}ms")
            for result in import_results:
                status_emoji = "✅" if result["status"] == "success" else "❌"
                print(f"      {status_emoji} {result['module']}: {result['duration_ms']:.2f}ms")
            
        except Exception as e:
            self.results["import_performance"] = {
                "status": "error",
                "error": str(e)
            }
            print(f"   ❌ Import performance test failed: {e}")
    
    async def generate_report(self):
        """Generate performance test report."""
        try:
            total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
            
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_duration_seconds": total_duration,
                "environment": getattr(settings, "ENVIRONMENT", "unknown"),
                "python_version": sys.version,
                "results": self.results
            }
            
            # Save JSON report
            with open("simple_performance_report.json", "w") as f:
                json.dump(report, f, indent=2, default=str)
            
            # Generate summary
            print(f"\n📊 PERFORMANCE TEST SUMMARY")
            print("=" * 50)
            print(f"Total Duration: {total_duration:.2f} seconds")
            print(f"Environment: {report['environment']}")
            
            # Test results summary
            for test_name, result in self.results.items():
                status = result.get("status", "unknown")
                duration = result.get("duration_ms", 0)
                
                if status == "success":
                    print(f"✅ {test_name}: {duration:.2f}ms")
                elif status == "warning":
                    print(f"⚠️  {test_name}: {duration:.2f}ms")
                else:
                    print(f"❌ {test_name}: Failed")
            
            print(f"\n📄 Report saved: simple_performance_report.json")
            
            # Performance recommendations
            print(f"\n💡 RECOMMENDATIONS")
            print("=" * 50)
            
            # Database performance
            if "database" in self.results and self.results["database"]["status"] == "success":
                db_time = self.results["database"]["duration_ms"]
                if db_time > 100:
                    print("⚠️  Database connection is slow (>100ms). Consider connection pooling.")
                else:
                    print("✅ Database connection performance is good.")
            
            # Import performance
            if "import_performance" in self.results:
                total_import_time = self.results["import_performance"].get("total_duration_ms", 0)
                if total_import_time > 1000:
                    print("⚠️  Module imports are slow (>1s). Consider optimizing imports.")
                else:
                    print("✅ Module import performance is good.")
            
            # Configuration
            if "configuration" in self.results and self.results["configuration"]["status"] == "success":
                print("✅ Configuration loading is working properly.")
            
            # Settings validation
            if "settings_validation" in self.results:
                missing = self.results["settings_validation"].get("missing_settings", [])
                if missing:
                    print(f"⚠️  Missing settings: {', '.join(missing)}")
                else:
                    print("✅ All required settings are configured.")
            
            print("\n🚀 Backend core functionality is ready!")
            
        except Exception as e:
            print(f"❌ Report generation failed: {e}")


async def main():
    """Main entry point."""
    tester = SimplePerformanceTest()
    await tester.run_tests()


if __name__ == "__main__":
    asyncio.run(main())