"""
Add performance indexes for analytics queries.

This migration adds database indexes to optimize analytics queries on:
- user_id, created_at, and status fields for DirectAnalysis
- user_id, created_at, and feedback_type fields for FeedbackRecord
- analysis_id, pattern_type, and severity fields for Issue
- Composite indexes for common query patterns

Requirements covered: 6.1, 6.2
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def create_analytics_indexes():
    """Create performance indexes for analytics queries."""
    
    engine = create_engine(settings.DATABASE_URL)
    
    # Index creation statements
    indexes = [
        # DirectAnalysis indexes for analytics queries
        """
        CREATE INDEX IF NOT EXISTS idx_direct_analyses_user_created 
        ON direct_analyses(user_id, created_at DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_direct_analyses_user_status_created 
        ON direct_analyses(user_id, status, created_at DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_direct_analyses_status_created 
        ON direct_analyses(status, created_at DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_direct_analyses_language_created 
        ON direct_analyses(language, created_at DESC);
        """,
        
        # FeedbackRecord indexes for analytics queries
        """
        CREATE INDEX IF NOT EXISTS idx_feedback_records_user_created 
        ON feedback_records(user_id, created_at DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_feedback_records_user_type_created 
        ON feedback_records(user_id, feedback_type, created_at DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_feedback_records_type_created 
        ON feedback_records(feedback_type, created_at DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_feedback_records_validated_created 
        ON feedback_records(is_validated, created_at DESC);
        """,
        
        # Issue indexes for analytics queries
        """
        CREATE INDEX IF NOT EXISTS idx_issues_analysis_pattern_severity 
        ON issues(analysis_id, pattern_type, severity);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_issues_pattern_severity_created 
        ON issues(pattern_type, severity, created_at DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_issues_severity_status_created 
        ON issues(severity, status, created_at DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_issues_category_created 
        ON issues(category, created_at DESC) WHERE category IS NOT NULL;
        """,
        
        # ModelVersion indexes for learning progress queries
        """
        CREATE INDEX IF NOT EXISTS idx_model_versions_active_created 
        ON model_versions(is_active, created_at DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_model_versions_status_created 
        ON model_versions(deployment_status, created_at DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_model_versions_performance 
        ON model_versions(accuracy_score DESC, acceptance_rate DESC) 
        WHERE accuracy_score IS NOT NULL AND acceptance_rate IS NOT NULL;
        """,
        
        # Composite indexes for complex analytics queries
        """
        CREATE INDEX IF NOT EXISTS idx_direct_analyses_user_lang_status_created 
        ON direct_analyses(user_id, language, status, created_at DESC);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_feedback_issue_user_type 
        ON feedback_records(issue_id, user_id, feedback_type);
        """,
        
        # Covering indexes for frequently accessed columns
        """
        CREATE INDEX IF NOT EXISTS idx_direct_analyses_analytics_covering 
        ON direct_analyses(user_id, created_at DESC) 
        INCLUDE (status, issues_count, complexity_score, completed_at);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_feedback_records_analytics_covering 
        ON feedback_records(user_id, created_at DESC) 
        INCLUDE (feedback_type, feedback_value, is_validated);
        """,
    ]
    
    try:
        with engine.connect() as connection:
            # Start transaction
            trans = connection.begin()
            
            try:
                logger.info("Creating analytics performance indexes...")
                
                for i, index_sql in enumerate(indexes, 1):
                    logger.info(f"Creating index {i}/{len(indexes)}...")
                    connection.execute(text(index_sql))
                
                # Commit transaction
                trans.commit()
                logger.info("Successfully created all analytics performance indexes")
                
                # Analyze tables to update statistics
                analyze_statements = [
                    "ANALYZE direct_analyses;",
                    "ANALYZE feedback_records;", 
                    "ANALYZE issues;",
                    "ANALYZE model_versions;"
                ]
                
                logger.info("Updating table statistics...")
                for analyze_sql in analyze_statements:
                    connection.execute(text(analyze_sql))
                
                logger.info("Analytics performance optimization completed successfully")
                
            except Exception as e:
                trans.rollback()
                logger.error(f"Error creating indexes: {e}")
                raise
                
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def drop_analytics_indexes():
    """Drop analytics performance indexes (for rollback)."""
    
    engine = create_engine(settings.DATABASE_URL)
    
    # Index drop statements (reverse order)
    drop_statements = [
        "DROP INDEX IF EXISTS idx_feedback_records_analytics_covering;",
        "DROP INDEX IF EXISTS idx_direct_analyses_analytics_covering;",
        "DROP INDEX IF EXISTS idx_feedback_issue_user_type;",
        "DROP INDEX IF EXISTS idx_direct_analyses_user_lang_status_created;",
        "DROP INDEX IF EXISTS idx_model_versions_performance;",
        "DROP INDEX IF EXISTS idx_model_versions_status_created;",
        "DROP INDEX IF EXISTS idx_model_versions_active_created;",
        "DROP INDEX IF EXISTS idx_issues_category_created;",
        "DROP INDEX IF EXISTS idx_issues_severity_status_created;",
        "DROP INDEX IF EXISTS idx_issues_pattern_severity_created;",
        "DROP INDEX IF EXISTS idx_issues_analysis_pattern_severity;",
        "DROP INDEX IF EXISTS idx_feedback_records_validated_created;",
        "DROP INDEX IF EXISTS idx_feedback_records_type_created;",
        "DROP INDEX IF EXISTS idx_feedback_records_user_type_created;",
        "DROP INDEX IF EXISTS idx_feedback_records_user_created;",
        "DROP INDEX IF EXISTS idx_direct_analyses_language_created;",
        "DROP INDEX IF EXISTS idx_direct_analyses_status_created;",
        "DROP INDEX IF EXISTS idx_direct_analyses_user_status_created;",
        "DROP INDEX IF EXISTS idx_direct_analyses_user_created;",
    ]
    
    try:
        with engine.connect() as connection:
            trans = connection.begin()
            
            try:
                logger.info("Dropping analytics performance indexes...")
                
                for drop_sql in drop_statements:
                    connection.execute(text(drop_sql))
                
                trans.commit()
                logger.info("Successfully dropped all analytics performance indexes")
                
            except Exception as e:
                trans.rollback()
                logger.error(f"Error dropping indexes: {e}")
                raise
                
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def check_index_usage():
    """Check index usage statistics."""
    
    engine = create_engine(settings.DATABASE_URL)
    
    usage_query = """
    SELECT 
        schemaname,
        tablename,
        indexname,
        idx_tup_read,
        idx_tup_fetch,
        idx_scan
    FROM pg_stat_user_indexes 
    WHERE indexname LIKE 'idx_%analytics%' 
       OR indexname LIKE 'idx_direct_analyses%'
       OR indexname LIKE 'idx_feedback_records%'
       OR indexname LIKE 'idx_issues%'
       OR indexname LIKE 'idx_model_versions%'
    ORDER BY idx_scan DESC;
    """
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text(usage_query))
            rows = result.fetchall()
            
            if rows:
                logger.info("Analytics Index Usage Statistics:")
                logger.info("=" * 80)
                for row in rows:
                    logger.info(f"Index: {row.indexname}")
                    logger.info(f"  Table: {row.schemaname}.{row.tablename}")
                    logger.info(f"  Scans: {row.idx_scan}")
                    logger.info(f"  Tuples Read: {row.idx_tup_read}")
                    logger.info(f"  Tuples Fetched: {row.idx_tup_fetch}")
                    logger.info("-" * 40)
            else:
                logger.info("No analytics indexes found or statistics not available")
                
    except Exception as e:
        logger.error(f"Error checking index usage: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage analytics performance indexes")
    parser.add_argument("action", choices=["create", "drop", "check"], 
                       help="Action to perform")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if args.action == "create":
        create_analytics_indexes()
    elif args.action == "drop":
        drop_analytics_indexes()
    elif args.action == "check":
        check_index_usage()