"""
Query optimization script for analytics service.

This script analyzes and optimizes existing queries in the analytics service
for better performance with the new indexes.

Requirements covered: 6.1, 6.2
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def analyze_query_performance():
    """Analyze performance of key analytics queries."""
    
    engine = create_engine(settings.DATABASE_URL)
    
    # Key analytics queries to analyze
    queries = [
        {
            "name": "User Stats Query",
            "sql": """
            EXPLAIN ANALYZE
            SELECT COUNT(*) as total_analyses,
                   COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_analyses,
                   AVG(issues_count) as avg_issues,
                   AVG(complexity_score) as avg_complexity
            FROM direct_analyses 
            WHERE user_id = 1 
            AND created_at >= NOW() - INTERVAL '30 days';
            """
        },
        {
            "name": "Usage Trends Query",
            "sql": """
            EXPLAIN ANALYZE
            SELECT DATE(created_at) as date,
                   COUNT(*) as reviews,
                   COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                   SUM(issues_count) as total_issues
            FROM direct_analyses 
            WHERE user_id = 1 
            AND created_at >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(created_at)
            ORDER BY date;
            """
        },
        {
            "name": "Feedback Distribution Query",
            "sql": """
            EXPLAIN ANALYZE
            SELECT feedback_type,
                   COUNT(*) as count,
                   AVG(feedback_value) as avg_value
            FROM feedback_records 
            WHERE user_id = 1 
            AND created_at >= NOW() - INTERVAL '30 days'
            GROUP BY feedback_type;
            """
        },
        {
            "name": "Issue Pattern Analysis Query",
            "sql": """
            EXPLAIN ANALYZE
            SELECT i.pattern_type,
                   i.severity,
                   COUNT(*) as count,
                   AVG(i.confidence_score) as avg_confidence
            FROM issues i
            JOIN direct_analyses da ON i.analysis_id = da.id
            WHERE da.user_id = 1
            AND da.created_at >= NOW() - INTERVAL '30 days'
            GROUP BY i.pattern_type, i.severity
            ORDER BY count DESC;
            """
        },
        {
            "name": "Recent Activity Query",
            "sql": """
            EXPLAIN ANALYZE
            SELECT id, language, status, issues_count, created_at, completed_at
            FROM direct_analyses
            WHERE user_id = 1
            ORDER BY created_at DESC
            LIMIT 10;
            """
        }
    ]
    
    try:
        with engine.connect() as connection:
            logger.info("Analyzing analytics query performance...")
            logger.info("=" * 80)
            
            for query in queries:
                logger.info(f"\n{query['name']}:")
                logger.info("-" * 40)
                
                try:
                    result = connection.execute(text(query['sql']))
                    rows = result.fetchall()
                    
                    for row in rows:
                        logger.info(row[0])  # EXPLAIN ANALYZE output
                        
                except Exception as e:
                    logger.error(f"Error analyzing query '{query['name']}': {e}")
            
            logger.info("\nQuery analysis completed")
            
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def check_table_statistics():
    """Check table statistics for analytics tables."""
    
    engine = create_engine(settings.DATABASE_URL)
    
    stats_query = """
    SELECT 
        schemaname,
        tablename,
        n_tup_ins as inserts,
        n_tup_upd as updates,
        n_tup_del as deletes,
        n_live_tup as live_tuples,
        n_dead_tup as dead_tuples,
        last_vacuum,
        last_autovacuum,
        last_analyze,
        last_autoanalyze
    FROM pg_stat_user_tables 
    WHERE tablename IN ('direct_analyses', 'feedback_records', 'issues', 'model_versions')
    ORDER BY tablename;
    """
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text(stats_query))
            rows = result.fetchall()
            
            logger.info("Table Statistics:")
            logger.info("=" * 80)
            
            for row in rows:
                logger.info(f"\nTable: {row.schemaname}.{row.tablename}")
                logger.info(f"  Live Tuples: {row.live_tuples:,}")
                logger.info(f"  Dead Tuples: {row.dead_tuples:,}")
                logger.info(f"  Inserts: {row.inserts:,}")
                logger.info(f"  Updates: {row.updates:,}")
                logger.info(f"  Deletes: {row.deletes:,}")
                logger.info(f"  Last Analyze: {row.last_analyze}")
                logger.info(f"  Last Auto-Analyze: {row.last_autoanalyze}")
                
    except Exception as e:
        logger.error(f"Error checking table statistics: {e}")

def optimize_table_maintenance():
    """Run maintenance operations on analytics tables."""
    
    engine = create_engine(settings.DATABASE_URL)
    
    maintenance_operations = [
        "VACUUM ANALYZE direct_analyses;",
        "VACUUM ANALYZE feedback_records;",
        "VACUUM ANALYZE issues;",
        "VACUUM ANALYZE model_versions;",
        "REINDEX TABLE direct_analyses;",
        "REINDEX TABLE feedback_records;",
        "REINDEX TABLE issues;",
        "REINDEX TABLE model_versions;"
    ]
    
    try:
        with engine.connect() as connection:
            logger.info("Running table maintenance operations...")
            
            for operation in maintenance_operations:
                logger.info(f"Executing: {operation}")
                connection.execute(text(operation))
            
            logger.info("Table maintenance completed successfully")
            
    except Exception as e:
        logger.error(f"Error during table maintenance: {e}")
        raise

def generate_query_recommendations():
    """Generate recommendations for query optimization."""
    
    recommendations = [
        {
            "area": "User Stats Queries",
            "recommendations": [
                "Use covering indexes to avoid table lookups",
                "Consider materialized views for frequently accessed aggregations",
                "Implement query result caching with appropriate TTL",
                "Use LIMIT clauses for large result sets"
            ]
        },
        {
            "area": "Time-based Queries",
            "recommendations": [
                "Always include time range filters early in WHERE clause",
                "Use date partitioning for large historical data",
                "Consider pre-aggregated daily/hourly summaries",
                "Use appropriate date/time indexes"
            ]
        },
        {
            "area": "Join Operations",
            "recommendations": [
                "Ensure foreign key indexes exist",
                "Use INNER JOINs when possible instead of LEFT JOINs",
                "Consider denormalization for frequently joined data",
                "Use EXISTS instead of IN for subqueries"
            ]
        },
        {
            "area": "Aggregation Queries",
            "recommendations": [
                "Use partial indexes for filtered aggregations",
                "Consider window functions for running totals",
                "Implement incremental aggregation for real-time data",
                "Use appropriate GROUP BY ordering"
            ]
        }
    ]
    
    logger.info("Query Optimization Recommendations:")
    logger.info("=" * 80)
    
    for rec in recommendations:
        logger.info(f"\n{rec['area']}:")
        logger.info("-" * 40)
        for item in rec['recommendations']:
            logger.info(f"  • {item}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Optimize analytics queries")
    parser.add_argument("action", choices=["analyze", "stats", "maintain", "recommend", "all"], 
                       help="Action to perform")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if args.action == "analyze":
        analyze_query_performance()
    elif args.action == "stats":
        check_table_statistics()
    elif args.action == "maintain":
        optimize_table_maintenance()
    elif args.action == "recommend":
        generate_query_recommendations()
    elif args.action == "all":
        check_table_statistics()
        analyze_query_performance()
        generate_query_recommendations()
        logger.info("\nTo run maintenance operations, use: python optimize_analytics_queries.py maintain")