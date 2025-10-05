"""
Performance Indexes Migration

This migration adds database indexes for optimal performance of the enhanced platform features.
Indexes are created for frequently queried columns and foreign key relationships.

Requirements covered: Performance optimization for all enhanced features
"""

from sqlalchemy import text


def upgrade(connection):
    """Add performance indexes for the enhanced platform."""
    
    # Teams table indexes
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);
        CREATE INDEX IF NOT EXISTS idx_teams_admin_id ON teams(admin_id);
        CREATE INDEX IF NOT EXISTS idx_teams_created_at ON teams(created_at);
    """))
    
    # Enhanced user indexes
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_users_team_id ON users(team_id);
        CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
        CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
        CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
    """))
    
    # Enhanced feedback table indexes
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_enhanced_feedback_suggestion_id ON enhanced_feedback(suggestion_id);
        CREATE INDEX IF NOT EXISTS idx_enhanced_feedback_user_id ON enhanced_feedback(user_id);
        CREATE INDEX IF NOT EXISTS idx_enhanced_feedback_action ON enhanced_feedback(action);
        CREATE INDEX IF NOT EXISTS idx_enhanced_feedback_suggestion_type ON enhanced_feedback(suggestion_type);
        CREATE INDEX IF NOT EXISTS idx_enhanced_feedback_timestamp ON enhanced_feedback(timestamp);
        CREATE INDEX IF NOT EXISTS idx_enhanced_feedback_created_at ON enhanced_feedback(created_at);
        
        -- Composite indexes for analytics queries
        CREATE INDEX IF NOT EXISTS idx_enhanced_feedback_user_action_timestamp 
        ON enhanced_feedback(user_id, action, timestamp);
        CREATE INDEX IF NOT EXISTS idx_enhanced_feedback_action_timestamp 
        ON enhanced_feedback(action, timestamp);
    """))
    
    # GitHub repositories indexes
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_github_repositories_user_id ON github_repositories(user_id);
        CREATE INDEX IF NOT EXISTS idx_github_repositories_repo_url ON github_repositories(repo_url);
        CREATE INDEX IF NOT EXISTS idx_github_repositories_repo_name ON github_repositories(repo_name);
        CREATE INDEX IF NOT EXISTS idx_github_repositories_is_active ON github_repositories(is_active);
        CREATE INDEX IF NOT EXISTS idx_github_repositories_created_at ON github_repositories(created_at);
        CREATE INDEX IF NOT EXISTS idx_github_repositories_last_webhook ON github_repositories(last_webhook_received);
        
        -- Composite index for active repositories by user
        CREATE INDEX IF NOT EXISTS idx_github_repositories_user_active 
        ON github_repositories(user_id, is_active);
    """))
    
    # PR analyses indexes
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_pr_analyses_repository_id ON pr_analyses(repository_id);
        CREATE INDEX IF NOT EXISTS idx_pr_analyses_pr_number ON pr_analyses(pr_number);
        CREATE INDEX IF NOT EXISTS idx_pr_analyses_pr_author ON pr_analyses(pr_author);
        CREATE INDEX IF NOT EXISTS idx_pr_analyses_head_sha ON pr_analyses(head_sha);
        CREATE INDEX IF NOT EXISTS idx_pr_analyses_status ON pr_analyses(status);
        CREATE INDEX IF NOT EXISTS idx_pr_analyses_created_at ON pr_analyses(created_at);
        
        -- Composite indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_pr_analyses_repo_status 
        ON pr_analyses(repository_id, status);
        CREATE INDEX IF NOT EXISTS idx_pr_analyses_repo_pr_number 
        ON pr_analyses(repository_id, pr_number);
        CREATE INDEX IF NOT EXISTS idx_pr_analyses_status_created 
        ON pr_analyses(status, created_at);
    """))
    
    # Stored files indexes
    connection.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_stored_files_user_id ON stored_files(user_id);
        CREATE INDEX IF NOT EXISTS idx_stored_files_filename ON stored_files(filename);
        CREATE INDEX IF NOT EXISTS idx_stored_files_content_type ON stored_files(content_type);
        CREATE INDEX IF NOT EXISTS idx_stored_files_file_hash ON stored_files(file_hash);
        CREATE INDEX IF NOT EXISTS idx_stored_files_is_analyzed ON stored_files(is_analyzed);
        CREATE INDEX IF NOT EXISTS idx_stored_files_analysis_id ON stored_files(analysis_id);
        CREATE INDEX IF NOT EXISTS idx_stored_files_uploaded_at ON stored_files(uploaded_at);
        CREATE INDEX IF NOT EXISTS idx_stored_files_expires_at ON stored_files(expires_at);
        
        -- Composite indexes for file management queries
        CREATE INDEX IF NOT EXISTS idx_stored_files_user_uploaded 
        ON stored_files(user_id, uploaded_at);
        CREATE INDEX IF NOT EXISTS idx_stored_files_user_analyzed 
        ON stored_files(user_id, is_analyzed);
        CREATE INDEX IF NOT EXISTS idx_stored_files_content_uploaded 
        ON stored_files(content_type, uploaded_at);
    """))
    
    # Existing tables - add missing performance indexes
    connection.execute(text("""
        -- Direct analyses performance indexes
        CREATE INDEX IF NOT EXISTS idx_direct_analyses_user_created 
        ON direct_analyses(user_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_direct_analyses_language_status 
        ON direct_analyses(language, status);
        CREATE INDEX IF NOT EXISTS idx_direct_analyses_status_created 
        ON direct_analyses(status, created_at);
        
        -- Issues performance indexes  
        CREATE INDEX IF NOT EXISTS idx_issues_analysis_created 
        ON issues(analysis_id, created_at) WHERE analysis_id IS NOT NULL;
        
        -- Feedback records performance indexes
        CREATE INDEX IF NOT EXISTS idx_feedback_records_user_created 
        ON feedback_records(user_id, created_at);
    """))


def downgrade(connection):
    """Remove performance indexes."""
    
    # Teams indexes
    connection.execute(text("""
        DROP INDEX IF EXISTS idx_teams_name;
        DROP INDEX IF EXISTS idx_teams_admin_id;
        DROP INDEX IF EXISTS idx_teams_created_at;
    """))
    
    # User indexes
    connection.execute(text("""
        DROP INDEX IF EXISTS idx_users_team_id;
        DROP INDEX IF EXISTS idx_users_role;
        DROP INDEX IF EXISTS idx_users_is_active;
        DROP INDEX IF EXISTS idx_users_created_at;
    """))
    
    # Enhanced feedback indexes
    connection.execute(text("""
        DROP INDEX IF EXISTS idx_enhanced_feedback_suggestion_id;
        DROP INDEX IF EXISTS idx_enhanced_feedback_user_id;
        DROP INDEX IF EXISTS idx_enhanced_feedback_action;
        DROP INDEX IF EXISTS idx_enhanced_feedback_suggestion_type;
        DROP INDEX IF EXISTS idx_enhanced_feedback_timestamp;
        DROP INDEX IF EXISTS idx_enhanced_feedback_created_at;
        DROP INDEX IF EXISTS idx_enhanced_feedback_user_action_timestamp;
        DROP INDEX IF EXISTS idx_enhanced_feedback_action_timestamp;
    """))
    
    # GitHub repositories indexes
    connection.execute(text("""
        DROP INDEX IF EXISTS idx_github_repositories_user_id;
        DROP INDEX IF EXISTS idx_github_repositories_repo_url;
        DROP INDEX IF EXISTS idx_github_repositories_repo_name;
        DROP INDEX IF EXISTS idx_github_repositories_is_active;
        DROP INDEX IF EXISTS idx_github_repositories_created_at;
        DROP INDEX IF EXISTS idx_github_repositories_last_webhook;
        DROP INDEX IF EXISTS idx_github_repositories_user_active;
    """))
    
    # PR analyses indexes
    connection.execute(text("""
        DROP INDEX IF EXISTS idx_pr_analyses_repository_id;
        DROP INDEX IF EXISTS idx_pr_analyses_pr_number;
        DROP INDEX IF EXISTS idx_pr_analyses_pr_author;
        DROP INDEX IF EXISTS idx_pr_analyses_head_sha;
        DROP INDEX IF EXISTS idx_pr_analyses_status;
        DROP INDEX IF EXISTS idx_pr_analyses_created_at;
        DROP INDEX IF EXISTS idx_pr_analyses_repo_status;
        DROP INDEX IF EXISTS idx_pr_analyses_repo_pr_number;
        DROP INDEX IF EXISTS idx_pr_analyses_status_created;
    """))
    
    # Stored files indexes
    connection.execute(text("""
        DROP INDEX IF EXISTS idx_stored_files_user_id;
        DROP INDEX IF EXISTS idx_stored_files_filename;
        DROP INDEX IF EXISTS idx_stored_files_content_type;
        DROP INDEX IF EXISTS idx_stored_files_file_hash;
        DROP INDEX IF EXISTS idx_stored_files_is_analyzed;
        DROP INDEX IF EXISTS idx_stored_files_analysis_id;
        DROP INDEX IF EXISTS idx_stored_files_uploaded_at;
        DROP INDEX IF EXISTS idx_stored_files_expires_at;
        DROP INDEX IF EXISTS idx_stored_files_user_uploaded;
        DROP INDEX IF EXISTS idx_stored_files_user_analyzed;
        DROP INDEX IF EXISTS idx_stored_files_content_uploaded;
    """))
    
    # Additional performance indexes
    connection.execute(text("""
        DROP INDEX IF EXISTS idx_direct_analyses_user_created;
        DROP INDEX IF EXISTS idx_direct_analyses_language_status;
        DROP INDEX IF EXISTS idx_direct_analyses_status_created;
        DROP INDEX IF EXISTS idx_issues_analysis_created;
        DROP INDEX IF EXISTS idx_feedback_records_user_created;
    """))


if __name__ == "__main__":
    # For manual execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app.core.database import engine
    
    with engine.connect() as connection:
        with connection.begin():
            upgrade(connection)
            print("Performance indexes migration completed successfully!")