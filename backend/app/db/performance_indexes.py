"""
Database performance optimization indexes and query strategies.

This module provides database indexes and query optimization strategies
for improved performance across all platform features.

Requirements covered: Performance and scalability for all features
"""

from sqlalchemy import Index, text
from sqlalchemy.orm import Session
from app.core.database import engine
from app.models import (
    User, EnhancedFeedback, GitHubRepository, PRAnalysis, 
    StoredFile, Team, Repository, Analysis, DirectAnalysis
)


# Performance indexes for frequently queried columns
PERFORMANCE_INDEXES = [
    # User-related indexes
    Index('idx_users_email_active', User.email, User.is_active),
    Index('idx_users_team_role', User.team_id, User.role),
    Index('idx_users_oauth_provider_id', User.oauth_provider, User.oauth_id),
    Index('idx_users_created_at', User.created_at),
    
    # Feedback system indexes
    Index('idx_feedback_user_timestamp', EnhancedFeedback.user_id, EnhancedFeedback.timestamp),
    Index('idx_feedback_suggestion_action', EnhancedFeedback.suggestion_id, EnhancedFeedback.action),
    Index('idx_feedback_type_confidence', EnhancedFeedback.suggestion_type, EnhancedFeedback.confidence_score),
    Index('idx_feedback_created_at', EnhancedFeedback.created_at),
    
    # GitHub integration indexes
    Index('idx_github_repos_user_active', GitHubRepository.user_id, GitHubRepository.is_active),
    Index('idx_github_repos_url', GitHubRepository.repo_url),
    Index('idx_github_repos_name_user', GitHubRepository.repo_name, GitHubRepository.user_id),
    Index('idx_github_repos_created_at', GitHubRepository.created_at),
    
    # PR Analysis indexes
    Index('idx_pr_analysis_repo_status', PRAnalysis.repository_id, PRAnalysis.status),
    Index('idx_pr_analysis_pr_number', PRAnalysis.pr_number, PRAnalysis.repository_id),
    Index('idx_pr_analysis_author_created', PRAnalysis.pr_author, PRAnalysis.created_at),
    Index('idx_pr_analysis_head_sha', PRAnalysis.head_sha),
    Index('idx_pr_analysis_completed_at', PRAnalysis.completed_at),
    
    # File storage indexes
    Index('idx_stored_files_user_created', StoredFile.user_id, StoredFile.created_at),
    Index('idx_stored_files_filename', StoredFile.filename),
    Index('idx_stored_files_content_type', StoredFile.content_type),
    
    # Repository and analysis indexes
    Index('idx_repositories_user_created', Repository.user_id, Repository.created_at),
    Index('idx_analysis_repo_created', Analysis.repository_id, Analysis.created_at),
    Index('idx_direct_analysis_user_created', DirectAnalysis.user_id, DirectAnalysis.created_at),
    
    # Composite indexes for common query patterns
    Index('idx_feedback_analytics', EnhancedFeedback.user_id, EnhancedFeedback.action, EnhancedFeedback.timestamp),
    Index('idx_pr_analysis_dashboard', PRAnalysis.repository_id, PRAnalysis.status, PRAnalysis.created_at),
]


def create_performance_indexes():
    """Create all performance indexes."""
    with engine.connect() as conn:
        for index in PERFORMANCE_INDEXES:
            try:
                index.create(conn, checkfirst=True)
                print(f"Created index: {index.name}")
            except Exception as e:
                print(f"Failed to create index {index.name}: {e}")


def create_database_views():
    """Create database views for complex analytics queries."""
    views = [
        # User analytics view
        """
        CREATE OR REPLACE VIEW user_analytics_summary AS
        SELECT 
            u.id as user_id,
            u.email,
            u.role,
            u.team_id,
            COUNT(DISTINCT ef.id) as total_feedback,
            COUNT(DISTINCT CASE WHEN ef.action = 'accept' THEN ef.id END) as accepted_suggestions,
            COUNT(DISTINCT CASE WHEN ef.action = 'reject' THEN ef.id END) as rejected_suggestions,
            COUNT(DISTINCT gr.id) as connected_repos,
            COUNT(DISTINCT pr.id) as pr_analyses,
            u.created_at,
            u.last_login
        FROM users u
        LEFT JOIN enhanced_feedback ef ON u.id = ef.user_id
        LEFT JOIN github_repositories gr ON u.id = gr.user_id AND gr.is_active = true
        LEFT JOIN pr_analyses pr ON gr.id = pr.repository_id
        GROUP BY u.id, u.email, u.role, u.team_id, u.created_at, u.last_login;
        """,
        
        # Feedback analytics view
        """
        CREATE OR REPLACE VIEW feedback_analytics_summary AS
        SELECT 
            DATE_TRUNC('day', ef.timestamp) as date,
            ef.user_id,
            ef.suggestion_type,
            ef.action,
            COUNT(*) as count,
            AVG(CASE WHEN ef.confidence_score IS NOT NULL THEN ef.confidence_score::numeric END) as avg_confidence
        FROM enhanced_feedback ef
        WHERE ef.timestamp >= NOW() - INTERVAL '90 days'
        GROUP BY DATE_TRUNC('day', ef.timestamp), ef.user_id, ef.suggestion_type, ef.action;
        """,
        
        # GitHub repository performance view
        """
        CREATE OR REPLACE VIEW github_repo_performance AS
        SELECT 
            gr.id as repo_id,
            gr.repo_name,
            gr.user_id,
            COUNT(pr.id) as total_analyses,
            COUNT(CASE WHEN pr.status = 'completed' THEN pr.id END) as completed_analyses,
            COUNT(CASE WHEN pr.status = 'failed' THEN pr.id END) as failed_analyses,
            AVG(CASE WHEN pr.completed_at IS NOT NULL AND pr.started_at IS NOT NULL 
                THEN EXTRACT(EPOCH FROM (pr.completed_at - pr.started_at)) END) as avg_analysis_time_seconds,
            SUM(pr.issues_found) as total_issues_found,
            MAX(pr.created_at) as last_analysis_date,
            gr.created_at as repo_connected_date
        FROM github_repositories gr
        LEFT JOIN pr_analyses pr ON gr.id = pr.repository_id
        WHERE gr.is_active = true
        GROUP BY gr.id, gr.repo_name, gr.user_id, gr.created_at;
        """
    ]
    
    with engine.connect() as conn:
        for view_sql in views:
            try:
                conn.execute(text(view_sql))
                conn.commit()
                print("Created database view successfully")
            except Exception as e:
                print(f"Failed to create view: {e}")


def optimize_database_settings():
    """Apply database-level optimizations."""
    optimizations = [
        # Enable query plan caching
        "SET shared_preload_libraries = 'pg_stat_statements';",
        
        # Optimize memory settings for analytics workloads
        "ALTER SYSTEM SET work_mem = '256MB';",
        "ALTER SYSTEM SET maintenance_work_mem = '1GB';",
        "ALTER SYSTEM SET effective_cache_size = '4GB';",
        
        # Enable parallel query execution
        "ALTER SYSTEM SET max_parallel_workers_per_gather = 4;",
        "ALTER SYSTEM SET max_parallel_workers = 8;",
        
        # Optimize checkpoint settings
        "ALTER SYSTEM SET checkpoint_completion_target = 0.9;",
        "ALTER SYSTEM SET wal_buffers = '16MB';",
        
        # Enable auto-vacuum optimization
        "ALTER SYSTEM SET autovacuum_max_workers = 6;",
        "ALTER SYSTEM SET autovacuum_naptime = '30s';",
    ]
    
    print("Database optimization settings (apply manually in production):")
    for setting in optimizations:
        print(f"  {setting}")


class QueryOptimizer:
    """Query optimization utilities for common database operations."""
    
    @staticmethod
    def get_user_feedback_analytics(db: Session, user_id: int, days: int = 30):
        """Optimized query for user feedback analytics."""
        return db.execute(text("""
            SELECT 
                action,
                COUNT(*) as count,
                suggestion_type,
                DATE_TRUNC('day', timestamp) as date
            FROM enhanced_feedback 
            WHERE user_id = :user_id 
                AND timestamp >= NOW() - INTERVAL ':days days'
            GROUP BY action, suggestion_type, DATE_TRUNC('day', timestamp)
            ORDER BY date DESC
        """), {"user_id": user_id, "days": days}).fetchall()
    
    @staticmethod
    def get_team_performance_summary(db: Session, team_id: str):
        """Optimized query for team performance analytics."""
        return db.execute(text("""
            SELECT 
                u.id as user_id,
                u.email,
                uas.total_feedback,
                uas.accepted_suggestions,
                uas.rejected_suggestions,
                uas.connected_repos,
                uas.pr_analyses
            FROM user_analytics_summary uas
            JOIN users u ON uas.user_id = u.id
            WHERE u.team_id = :team_id
            ORDER BY uas.total_feedback DESC
        """), {"team_id": team_id}).fetchall()
    
    @staticmethod
    def get_github_repo_insights(db: Session, user_id: int):
        """Optimized query for GitHub repository insights."""
        return db.execute(text("""
            SELECT 
                repo_name,
                total_analyses,
                completed_analyses,
                failed_analyses,
                avg_analysis_time_seconds,
                total_issues_found,
                last_analysis_date
            FROM github_repo_performance
            WHERE user_id = :user_id
            ORDER BY last_analysis_date DESC
        """), {"user_id": user_id}).fetchall()


if __name__ == "__main__":
    print("Creating performance indexes...")
    create_performance_indexes()
    
    print("Creating database views...")
    create_database_views()
    
    print("Database optimization recommendations:")
    optimize_database_settings()