#!/usr/bin/env python3
"""
Check queue status and diagnose issues with message processing
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

os.environ.setdefault('ENVIRONMENT', 'development')

async def check_queue_status():
    """Check the status of the queue system."""
    try:
        from app.core.hybrid_queue import hybrid_queue
        from app.services.background_job_service import background_job_service
        
        print("=" * 60)
        print("CodeNova Queue System Status Check")
        print("=" * 60)
        
        # Initialize systems
        print("\n1. Initializing queue systems...")
        try:
            await hybrid_queue.initialize()
            print("   ✅ Hybrid queue initialized")
        except Exception as e:
            print(f"   ❌ Hybrid queue initialization failed: {e}")
            return False
        
        try:
            await background_job_service.initialize()
            print("   ✅ Background job service initialized")
        except Exception as e:
            print(f"   ❌ Background job service initialization failed: {e}")
            return False
        
        # Check queue metrics
        print("\n2. Checking queue metrics...")
        try:
            metrics = await hybrid_queue.get_metrics()
            print(f"   Status: {metrics.get('status', 'unknown')}")
            print(f"   Redis tasks enqueued: {metrics.get('redis_tasks_enqueued', 0)}")
            print(f"   RabbitMQ tasks processed: {metrics.get('rabbitmq_tasks_processed', 0)}")
            print(f"   Redis queue depth: {metrics.get('redis_queue_depth', 0)}")
            print(f"   RabbitMQ queue depth: {metrics.get('rabbitmq_queue_depth', 0)}")
            print(f"   Forwarding rate: {metrics.get('forwarding_rate', 0):.2%}")
        except Exception as e:
            print(f"   ❌ Failed to get metrics: {e}")
        
        # Check background job statistics
        print("\n3. Checking background job statistics...")
        try:
            stats = await background_job_service.get_queue_statistics()
            print(f"   Total jobs: {stats.get('total_jobs', 0)}")
            print(f"   Queued jobs: {stats.get('queued_jobs', 0)}")
            print(f"   Processing jobs: {stats.get('processing_jobs', 0)}")
            print(f"   Completed jobs: {stats.get('completed_jobs', 0)}")
            print(f"   Failed jobs: {stats.get('failed_jobs', 0)}")
        except Exception as e:
            print(f"   ❌ Failed to get job statistics: {e}")
        
        # Check if worker is running
        print("\n4. Checking worker status...")
        print("   ⚠️  To check if workers are running, use:")
        print("      ps aux | grep background_job_worker")
        print("      ps aux | grep start_hybrid_queue")
        
        # Provide recommendations
        print("\n" + "=" * 60)
        print("RECOMMENDATIONS:")
        print("=" * 60)
        
        if metrics.get('redis_queue_depth', 0) > 0:
            print("⚠️  There are tasks in the Redis queue waiting to be processed")
            print("   Action: Start the hybrid queue forwarder")
            print("   Command: python start_hybrid_queue.py --mode forwarder")
        
        if metrics.get('rabbitmq_queue_depth', 0) > 0:
            print("⚠️  There are tasks in the RabbitMQ queue waiting to be processed")
            print("   Action: Start the hybrid queue worker")
            print("   Command: python start_hybrid_queue.py --mode worker")
        
        if stats.get('queued_jobs', 0) > 0:
            print("⚠️  There are background jobs queued but not processing")
            print("   Action: Start the background job worker")
            print("   Command: python -m app.workers.background_job_worker")
        
        if (metrics.get('redis_queue_depth', 0) == 0 and 
            metrics.get('rabbitmq_queue_depth', 0) == 0 and 
            stats.get('queued_jobs', 0) == 0):
            print("✅ All queues are empty - system is processing tasks correctly")
        
        print("\n" + "=" * 60)
        print("QUICK START COMMANDS:")
        print("=" * 60)
        print("Start all workers:")
        print("  python start_hybrid_queue.py --mode both")
        print("\nOr start separately:")
        print("  Terminal 1: python start_hybrid_queue.py --mode forwarder")
        print("  Terminal 2: python start_hybrid_queue.py --mode worker")
        print("  Terminal 3: python -m app.workers.background_job_worker")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error checking queue status: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(check_queue_status())
