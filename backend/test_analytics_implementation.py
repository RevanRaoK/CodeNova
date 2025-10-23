"""
Test script to verify analytics implementation for dashboard settings improvements.

This script tests the enhanced analytics service and API endpoints to ensure
they work correctly with the new caching layer and database optimizations.

Requirements covered: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 6.1, 6.2, 6.3
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.analytics_service import AnalyticsService
from app.core.cache import cache
import redis

logger = logging.getLogger(__name__)

async def test_analytics_service():
    """Test the enhanced analytics service functionality."""
    
    logger.info("Testing Analytics Service Implementation")
    logger.info("=" * 50)
    
    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)
    
    # Create Redis client for caching
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
        redis_client.ping()
        logger.info("✓ Redis connection successful")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        redis_client = None
    
    # Initialize analytics service
    analytics_service = AnalyticsService(db, redis_client)
    
    # Test user stats (using user_id = 1 for testing)
    test_user_id = 1
    
    try:
        logger.info(f"\n1. Testing get_user_stats for user {test_user_id}...")
        user_stats = await analytics_service.get_user_stats(test_user_id)
        
        logger.info("✓ User stats retrieved successfully")
        logger.info(f"  - Total Reviews: {user_stats.get('totalReviews', 0)}")
        logger.info(f"  - Total Analyses: {user_stats.get('totalAnalyses', 0)}")
        logger.info(f"  - Success Rate: {user_stats.get('successRate', 0)}%")
        logger.info(f"  - Acceptance Rate: {user_stats.get('acceptanceRate', 0)}%")
        logger.info(f"  - Recent Activity Items: {len(user_stats.get('recentActivity', []))}")
        
    except Exception as e:
        logger.error(f"✗ Error testing user stats: {e}")
    
    try:
        logger.info(f"\n2. Testing get_usage_trends for user {test_user_id}...")
        usage_trends = await analytics_service.get_usage_trends(test_user_id, "30d")
        
        logger.info("✓ Usage trends retrieved successfully")
        logger.info(f"  - Timeframe: {usage_trends.get('timeframe', 'N/A')}")
        logger.info(f"  - Trend Data Points: {len(usage_trends.get('trends', []))}")
        
        summary = usage_trends.get('summary', {})
        logger.info(f"  - Total Reviews: {summary.get('totalReviews', 0)}")
        logger.info(f"  - Avg Daily Reviews: {summary.get('avgDailyReviews', 0)}")
        
    except Exception as e:
        logger.error(f"✗ Error testing usage trends: {e}")
    
    try:
        logger.info(f"\n3. Testing get_feedback_distribution for user {test_user_id}...")
        feedback_dist = await analytics_service.get_feedback_distribution(test_user_id, "30d")
        
        logger.info("✓ Feedback distribution retrieved successfully")
        logger.info(f"  - Total Feedback: {feedback_dist.get('total', 0)}")
        
        distribution = feedback_dist.get('distribution', {})
        for feedback_type, count in distribution.items():
            logger.info(f"  - {feedback_type.title()}: {count}")
        
    except Exception as e:
        logger.error(f"✗ Error testing feedback distribution: {e}")
    
    try:
        logger.info(f"\n4. Testing get_dashboard_data for user {test_user_id}...")
        dashboard_data = await analytics_service.get_dashboard_data(test_user_id, "30d")
        
        logger.info("✓ Dashboard data retrieved successfully")
        logger.info(f"  - Generated At: {dashboard_data.get('generatedAt', 'N/A')}")
        logger.info(f"  - User ID: {dashboard_data.get('userId', 'N/A')}")
        logger.info(f"  - Timeframe: {dashboard_data.get('timeframe', 'N/A')}")
        
        # Check all components are present
        components = ['userStats', 'usageTrends', 'feedbackDistribution', 'performanceMetrics']
        for component in components:
            if component in dashboard_data:
                logger.info(f"  ✓ {component} component present")
            else:
                logger.warning(f"  ✗ {component} component missing")
        
    except Exception as e:
        logger.error(f"✗ Error testing dashboard data: {e}")
    
    # Test caching functionality
    if redis_client:
        try:
            logger.info("\n5. Testing cache functionality...")
            
            # Clear cache first
            analytics_service.invalidate_user_cache(test_user_id)
            logger.info("✓ Cache cleared for user")
            
            # First call (should miss cache)
            start_time = datetime.now()
            await analytics_service.get_user_stats(test_user_id)
            first_call_time = (datetime.now() - start_time).total_seconds()
            
            # Second call (should hit cache)
            start_time = datetime.now()
            await analytics_service.get_user_stats(test_user_id)
            second_call_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✓ Cache performance test completed")
            logger.info(f"  - First call (cache miss): {first_call_time:.3f}s")
            logger.info(f"  - Second call (cache hit): {second_call_time:.3f}s")
            
            if second_call_time < first_call_time:
                logger.info("  ✓ Cache is working - second call was faster")
            else:
                logger.warning("  ? Cache performance unclear")
            
        except Exception as e:
            logger.error(f"✗ Error testing cache: {e}")
    
    # Close database session
    db.close()
    
    logger.info("\n" + "=" * 50)
    logger.info("Analytics Service Testing Completed")

def test_database_indexes():
    """Test that the database indexes are working."""
    
    logger.info("\nTesting Database Index Performance")
    logger.info("=" * 50)
    
    from sqlalchemy import create_engine, text
    from app.core.config import settings
    
    engine = create_engine(settings.DATABASE_URL)
    
    # Test queries that should use the new indexes
    test_queries = [
        {
            "name": "User Analytics Query",
            "sql": """
            EXPLAIN (ANALYZE, BUFFERS)
            SELECT COUNT(*) as total, 
                   COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed
            FROM direct_analyses 
            WHERE user_id = 1 
            AND created_at >= NOW() - INTERVAL '30 days';
            """
        },
        {
            "name": "Feedback Distribution Query", 
            "sql": """
            EXPLAIN (ANALYZE, BUFFERS)
            SELECT feedback_type, COUNT(*) 
            FROM feedback_records 
            WHERE user_id = 1 
            AND created_at >= NOW() - INTERVAL '30 days'
            GROUP BY feedback_type;
            """
        }
    ]
    
    try:
        with engine.connect() as connection:
            for query in test_queries:
                logger.info(f"\n{query['name']}:")
                logger.info("-" * 30)
                
                try:
                    result = connection.execute(text(query['sql']))
                    rows = result.fetchall()
                    
                    # Look for index usage in explain output
                    explain_output = '\n'.join([str(row[0]) for row in rows])
                    
                    if 'Index Scan' in explain_output or 'Index Only Scan' in explain_output:
                        logger.info("✓ Query is using indexes")
                    elif 'Seq Scan' in explain_output:
                        logger.warning("? Query is using sequential scan")
                    else:
                        logger.info("? Query execution plan unclear")
                    
                    # Extract execution time if available
                    for line in explain_output.split('\n'):
                        if 'Execution Time' in line:
                            logger.info(f"  {line.strip()}")
                            break
                    
                except Exception as e:
                    logger.error(f"Error testing query: {e}")
    
    except Exception as e:
        logger.error(f"Database connection error: {e}")

async def main():
    """Main test function."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting Analytics Implementation Tests")
    logger.info("=" * 60)
    
    # Test analytics service
    await test_analytics_service()
    
    # Test database indexes
    test_database_indexes()
    
    logger.info("\n" + "=" * 60)
    logger.info("All Tests Completed")

if __name__ == "__main__":
    asyncio.run(main())