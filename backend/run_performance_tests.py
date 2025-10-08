#!/usr/bin/env python3
"""
Comprehensive performance testing runner for the backend application.

This script runs all performance tests, generates reports, and provides
optimization recommendations for production deployment.

Requirements covered: Performance and scalability for all features
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests.performance.test_performance_suite import LoadTestRunner
from app.core.production_config import ProductionReadinessChecker, ProductionOptimizer
from app.core.monitoring import performance_monitor, system_monitor
from app.core.cache import check_cache_health


class PerformanceTestOrchestrator:
    """Orchestrates comprehensive performance testing and optimization."""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    async def run_comprehensive_tests(self, base_url: str = "http://localhost:8000"):
        """Run all performance tests and generate comprehensive report."""
        print("🚀 Starting Comprehensive Performance Test Suite")
        print("=" * 60)
        
        self.start_time = time.time()
        
        try:
            # 1. Production Readiness Check
            print("\n📋 Step 1: Production Readiness Check")
            await self.run_production_readiness_check()
            
            # 2. Performance Benchmarks
            print("\n⚡ Step 2: Performance Benchmarks")
            await self.run_performance_benchmarks(base_url)
            
            # 3. Load Testing
            print("\n🔥 Step 3: Load Testing")
            await self.run_load_tests(base_url)
            
            # 4. System Health Check
            print("\n🏥 Step 4: System Health Check")
            await self.run_system_health_check()
            
            # 5. Generate Reports
            print("\n📊 Step 5: Generating Reports")
            await self.generate_comprehensive_report()
            
        except Exception as e:
            print(f"❌ Error during performance testing: {e}")
            self.results["error"] = str(e)
        
        finally:
            self.end_time = time.time()
            print(f"\n✅ Performance testing completed in {self.end_time - self.start_time:.2f} seconds")
    
    async def run_production_readiness_check(self):
        """Run production readiness assessment."""
        try:
            checker = ProductionReadinessChecker()
            readiness_results = await checker.run_production_readiness_check()
            
            self.results["production_readiness"] = readiness_results
            
            status = readiness_results["overall_status"]
            if status == "ready":
                print("✅ Production readiness: READY")
            elif status == "needs_attention":
                print("⚠️  Production readiness: NEEDS ATTENTION")
            else:
                print("❌ Production readiness: NOT READY")
            
            if readiness_results.get("critical_failures"):
                print(f"   Critical failures: {len(readiness_results['critical_failures'])}")
            
        except Exception as e:
            print(f"❌ Production readiness check failed: {e}")
            self.results["production_readiness"] = {"error": str(e)}
    
    async def run_performance_benchmarks(self, base_url: str):
        """Run performance benchmarks."""
        try:
            runner = LoadTestRunner()
            
            # Database performance
            print("   🗄️  Database performance tests...")
            db_results = await runner.run_database_tests()
            
            # Cache performance
            print("   💾 Cache performance tests...")
            cache_results = await runner.run_cache_tests()
            
            # Service performance
            print("   🔧 Service performance tests...")
            service_results = await runner.run_service_tests()
            
            self.results["benchmarks"] = {
                "database": db_results,
                "cache": cache_results,
                "services": service_results
            }
            
            # Print summary
            all_tests = list(db_results.values()) + list(cache_results.values()) + list(service_results.values())
            avg_response_time = sum(test.get("avg_response_time", 0) for test in all_tests) / len(all_tests)
            avg_success_rate = sum(test.get("success_rate", 0) for test in all_tests) / len(all_tests)
            
            print(f"   Average response time: {avg_response_time:.2f}ms")
            print(f"   Average success rate: {avg_success_rate:.2%}")
            
        except Exception as e:
            print(f"❌ Performance benchmarks failed: {e}")
            self.results["benchmarks"] = {"error": str(e)}
    
    async def run_load_tests(self, base_url: str):
        """Run load testing scenarios."""
        try:
            runner = LoadTestRunner()
            
            print("   🌐 API load tests...")
            api_results = await runner.run_api_tests(base_url)
            
            self.results["load_tests"] = {
                "api": api_results
            }
            
            # Print summary
            for test_name, stats in api_results.items():
                if isinstance(stats, dict) and "requests_per_second" in stats:
                    print(f"   {test_name}: {stats['requests_per_second']:.2f} req/s")
            
        except Exception as e:
            print(f"❌ Load tests failed: {e}")
            self.results["load_tests"] = {"error": str(e)}
    
    async def run_system_health_check(self):
        """Run system health and resource checks."""
        try:
            # System health
            system_health = system_monitor.get_system_health()
            
            # Cache health
            cache_health = check_cache_health()
            
            # Performance metrics summary
            perf_summary = performance_monitor.get_performance_summary()
            
            self.results["system_health"] = {
                "system": system_health,
                "cache": cache_health,
                "performance": perf_summary
            }
            
            print(f"   System status: {system_health.get('status', 'unknown')}")
            print(f"   Cache status: {cache_health.get('status', 'unknown')}")
            
        except Exception as e:
            print(f"❌ System health check failed: {e}")
            self.results["system_health"] = {"error": str(e)}
    
    async def generate_comprehensive_report(self):
        """Generate comprehensive performance report."""
        try:
            # Add metadata
            self.results["metadata"] = {
                "timestamp": datetime.utcnow().isoformat(),
                "duration_seconds": self.end_time - self.start_time if self.end_time and self.start_time else 0,
                "python_version": sys.version,
                "platform": sys.platform
            }
            
            # Save JSON report
            json_report_path = "performance_test_results.json"
            with open(json_report_path, "w") as f:
                json.dump(self.results, f, indent=2, default=str)
            
            print(f"   📄 JSON report saved: {json_report_path}")
            
            # Generate human-readable report
            markdown_report = self.generate_markdown_report()
            markdown_report_path = "performance_test_report.md"
            with open(markdown_report_path, "w") as f:
                f.write(markdown_report)
            
            print(f"   📖 Markdown report saved: {markdown_report_path}")
            
            # Print summary to console
            self.print_summary()
            
        except Exception as e:
            print(f"❌ Report generation failed: {e}")
    
    def generate_markdown_report(self) -> str:
        """Generate markdown performance report."""
        report = []
        
        report.append("# Performance Test Report")
        report.append("")
        report.append(f"**Generated:** {self.results['metadata']['timestamp']}")
        report.append(f"**Duration:** {self.results['metadata']['duration_seconds']:.2f} seconds")
        report.append("")
        
        # Production Readiness
        if "production_readiness" in self.results:
            pr = self.results["production_readiness"]
            if "error" not in pr:
                report.append("## Production Readiness")
                report.append("")
                report.append(f"**Status:** {pr['overall_status'].upper()}")
                report.append(f"**Success Rate:** {pr['summary']['success_rate']:.1%}")
                report.append(f"**Critical Failures:** {pr['summary']['critical_failures_count']}")
                report.append("")
                
                if pr.get("recommendations"):
                    report.append("### Recommendations")
                    for rec in pr["recommendations"][:10]:  # Top 10
                        report.append(f"- {rec}")
                    report.append("")
        
        # Performance Benchmarks
        if "benchmarks" in self.results:
            benchmarks = self.results["benchmarks"]
            report.append("## Performance Benchmarks")
            report.append("")
            
            for category, tests in benchmarks.items():
                if isinstance(tests, dict) and "error" not in tests:
                    report.append(f"### {category.title()}")
                    report.append("")
                    
                    for test_name, stats in tests.items():
                        if isinstance(stats, dict) and "avg_response_time" in stats:
                            report.append(f"**{test_name}:**")
                            report.append(f"- Average Response Time: {stats['avg_response_time']:.2f}ms")
                            report.append(f"- Success Rate: {stats['success_rate']:.2%}")
                            report.append(f"- Requests/Second: {stats.get('requests_per_second', 0):.2f}")
                            report.append("")
        
        # Load Tests
        if "load_tests" in self.results:
            load_tests = self.results["load_tests"]
            report.append("## Load Test Results")
            report.append("")
            
            for category, tests in load_tests.items():
                if isinstance(tests, dict) and "error" not in tests:
                    report.append(f"### {category.title()}")
                    report.append("")
                    
                    for test_name, stats in tests.items():
                        if isinstance(stats, dict) and "requests_per_second" in stats:
                            report.append(f"**{test_name}:**")
                            report.append(f"- Throughput: {stats['requests_per_second']:.2f} req/s")
                            report.append(f"- Average Response Time: {stats['avg_response_time']:.2f}ms")
                            report.append(f"- P95 Response Time: {stats['p95_response_time']:.2f}ms")
                            report.append(f"- Success Rate: {stats['success_rate']:.2%}")
                            report.append("")
        
        # System Health
        if "system_health" in self.results:
            health = self.results["system_health"]
            report.append("## System Health")
            report.append("")
            
            if "system" in health and isinstance(health["system"], dict):
                sys_health = health["system"]
                report.append(f"**System Status:** {sys_health.get('status', 'unknown')}")
                if "metrics" in sys_health:
                    metrics = sys_health["metrics"]
                    report.append(f"**CPU Usage:** {metrics.get('cpu_percent', 0):.1f}%")
                    report.append(f"**Memory Usage:** {metrics.get('memory_percent', 0):.1f}%")
                    report.append(f"**Disk Usage:** {metrics.get('disk_usage_percent', 0):.1f}%")
                report.append("")
            
            if "cache" in health and isinstance(health["cache"], dict):
                cache_health = health["cache"]
                report.append(f"**Cache Status:** {cache_health.get('status', 'unknown')}")
                report.append(f"**Cache Hit Rate:** {cache_health.get('hit_rate', 0):.2%}")
                report.append("")
        
        # Recommendations
        report.append("## Performance Recommendations")
        report.append("")
        report.append("### Database Optimization")
        report.append("- Ensure all performance indexes are created")
        report.append("- Monitor slow queries and optimize them")
        report.append("- Consider connection pooling for high load")
        report.append("")
        
        report.append("### Caching Strategy")
        report.append("- Implement Redis caching for frequently accessed data")
        report.append("- Use appropriate TTL values for different data types")
        report.append("- Monitor cache hit rates and optimize cache keys")
        report.append("")
        
        report.append("### API Performance")
        report.append("- Implement rate limiting to prevent abuse")
        report.append("- Use compression for API responses")
        report.append("- Consider API response caching for read-heavy endpoints")
        report.append("")
        
        report.append("### Production Deployment")
        report.append("- Use a reverse proxy (nginx) for static file serving")
        report.append("- Enable gzip compression")
        report.append("- Implement proper logging and monitoring")
        report.append("- Use environment-specific configurations")
        report.append("")
        
        return "\n".join(report)
    
    def print_summary(self):
        """Print performance test summary to console."""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE TEST SUMMARY")
        print("=" * 60)
        
        # Production readiness
        if "production_readiness" in self.results:
            pr = self.results["production_readiness"]
            if "error" not in pr:
                status = pr["overall_status"]
                emoji = "✅" if status == "ready" else "⚠️" if status == "needs_attention" else "❌"
                print(f"{emoji} Production Readiness: {status.upper()}")
                print(f"   Success Rate: {pr['summary']['success_rate']:.1%}")
        
        # Performance summary
        if "benchmarks" in self.results:
            benchmarks = self.results["benchmarks"]
            all_tests = []
            
            for category, tests in benchmarks.items():
                if isinstance(tests, dict) and "error" not in tests:
                    all_tests.extend(tests.values())
            
            if all_tests:
                valid_tests = [t for t in all_tests if isinstance(t, dict) and "avg_response_time" in t]
                if valid_tests:
                    avg_response = sum(t["avg_response_time"] for t in valid_tests) / len(valid_tests)
                    avg_success = sum(t["success_rate"] for t in valid_tests) / len(valid_tests)
                    
                    print(f"⚡ Performance Benchmarks:")
                    print(f"   Average Response Time: {avg_response:.2f}ms")
                    print(f"   Average Success Rate: {avg_success:.2%}")
        
        # Load test summary
        if "load_tests" in self.results:
            load_tests = self.results["load_tests"]
            print(f"🔥 Load Test Results:")
            
            for category, tests in load_tests.items():
                if isinstance(tests, dict) and "error" not in tests:
                    for test_name, stats in tests.items():
                        if isinstance(stats, dict) and "requests_per_second" in stats:
                            print(f"   {test_name}: {stats['requests_per_second']:.2f} req/s")
        
        # System health
        if "system_health" in self.results:
            health = self.results["system_health"]
            if "system" in health and isinstance(health["system"], dict):
                sys_status = health["system"].get("status", "unknown")
                emoji = "✅" if sys_status == "healthy" else "⚠️" if sys_status == "degraded" else "❌"
                print(f"{emoji} System Health: {sys_status.upper()}")
        
        print("\n📄 Detailed reports saved to:")
        print("   - performance_test_results.json")
        print("   - performance_test_report.md")
        print("")


async def main():
    """Main entry point for performance testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run comprehensive performance tests")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL for API testing (default: http://localhost:8000)")
    parser.add_argument("--setup", action="store_true",
                       help="Run production setup before testing")
    
    args = parser.parse_args()
    
    # Run production setup if requested
    if args.setup:
        print("🔧 Running production setup...")
        try:
            await ProductionOptimizer.run_production_setup()
        except Exception as e:
            print(f"❌ Production setup failed: {e}")
            return
    
    # Run performance tests
    orchestrator = PerformanceTestOrchestrator()
    await orchestrator.run_comprehensive_tests(args.url)


if __name__ == "__main__":
    asyncio.run(main())