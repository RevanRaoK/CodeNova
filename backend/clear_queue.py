#!/usr/bin/env python3
"""
Clear RabbitMQ queues and Redis task data.

Usage:
    python backend/clear_queue.py
"""

import asyncio
import aio_pika
import redis.asyncio as redis
from app.core.queue_config import queue_config, QueuePriority

async def clear_rabbitmq_queues():
    """Clear all RabbitMQ queues."""
    print("Connecting to RabbitMQ...")
    connection = await aio_pika.connect_robust(queue_config.RABBITMQ_URL)
    channel = await connection.channel()
    
    print("Clearing RabbitMQ queues...")
    for priority in QueuePriority:
        queue_name = f"codenova.queue.{priority.value}"
        try:
            queue = await channel.get_queue(queue_name)
            purged = await queue.purge()
            print(f"  ✓ Purged {purged} messages from {queue_name}")
        except Exception as e:
            print(f"  ✗ Failed to purge {queue_name}: {e}")
    
    await connection.close()
    print("RabbitMQ queues cleared!")

async def clear_redis_tasks():
    """Clear Redis task data."""
    print("\nConnecting to Redis...")
    redis_client = redis.Redis.from_url(
        queue_config.REDIS_URL,
        db=queue_config.REDIS_DB_QUEUE,
        decode_responses=False
    )
    
    print("Clearing Redis task data...")
    
    # Clear task queues
    for priority in QueuePriority:
        queue_key = f"hybrid:queue:{priority.value}"
        deleted = await redis_client.delete(queue_key)
        if deleted:
            print(f"  ✓ Cleared queue: {queue_key}")
    
    # Clear task results (scan and delete)
    cursor = 0
    total_deleted = 0
    while True:
        cursor, keys = await redis_client.scan(cursor, match="hybrid:result:*", count=100)
        if keys:
            deleted = await redis_client.delete(*keys)
            total_deleted += deleted
        if cursor == 0:
            break
    
    if total_deleted > 0:
        print(f"  ✓ Cleared {total_deleted} task results")
    
    await redis_client.close()
    print("Redis task data cleared!")

async def main():
    """Main function."""
    print("=" * 50)
    print("CodeNova Queue Cleaner")
    print("=" * 50)
    print("\nThis will clear all pending tasks from:")
    print("  - RabbitMQ queues")
    print("  - Redis task data")
    print("\nWARNING: This cannot be undone!")
    
    response = input("\nContinue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Aborted.")
        return
    
    print()
    
    try:
        await clear_rabbitmq_queues()
        await clear_redis_tasks()
        print("\n" + "=" * 50)
        print("✓ Queue cleanup complete!")
        print("=" * 50)
    except Exception as e:
        print(f"\n✗ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
