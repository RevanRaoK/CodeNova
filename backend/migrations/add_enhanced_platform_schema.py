"""
Enhanced Platform Schema Migration

This migration adds the new tables and fields required for the comprehensive platform enhancement:
- Teams table for user organization
- Enhanced feedback table for AI suggestions
- GitHub repositories and PR analyses tables
- Stored files table for Digital Ocean Spaces integration
- Enhanced user fields (team_id, preferences, new roles)

Requirements covered: 1.4, 3.2, 4.4, 6.2, 8.1
"""

import uuid
from sqlalchemy import text


def upgrade(connection):
    """Apply the enhanced platform schema changes."""
    
    # 1. Add new user roles to the existing enum
    connection.execute(text("""
        ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'user';
        ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'team_lead';
    """))
    
    # 2. Create teams table
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS teams (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            name VARCHAR(255) NOT NULL,
            admin_id INTEGER NOT NULL,
            settings JSONB DEFAULT '{}' NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """))
    
    # 3. Add enhanced user fields
    connection.execute(text("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS team_id VARCHAR(36),
        ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}' NOT NULL;
    """))
    
    # 4. Create enhanced feedback table
    connection.execute(text("""
        DO $$ BEGIN
            CREATE TYPE feedbackaction AS ENUM ('accept', 'reject');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        
        CREATE TABLE IF NOT EXISTS enhanced_feedback (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            suggestion_id VARCHAR(255) NOT NULL,
            user_id INTEGER NOT NULL,
            action feedbackaction NOT NULL,
            rejection_reasons JSONB,
            custom_reason VARCHAR(1000),
            suggestion_type VARCHAR(100),
            confidence_score VARCHAR(20),
            context_data JSONB,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """))
    
    # 5. Create GitHub repositories table
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS github_repositories (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            user_id INTEGER NOT NULL,
            repo_url VARCHAR(512) NOT NULL,
            repo_name VARCHAR(255) NOT NULL,
            webhook_id VARCHAR(255),
            webhook_secret VARCHAR(255),
            is_active BOOLEAN DEFAULT true NOT NULL,
            default_branch VARCHAR(100) DEFAULT 'main' NOT NULL,
            repository_settings JSONB DEFAULT '{}' NOT NULL,
            access_token VARCHAR(512),
            permissions JSONB DEFAULT '{}' NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_webhook_received TIMESTAMP
        );
    """))
    
    # 6. Create PR analyses table
    connection.execute(text("""
        DO $$ BEGIN
            CREATE TYPE analysisstatus AS ENUM ('pending', 'in_progress', 'completed', 'failed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        
        CREATE TABLE IF NOT EXISTS pr_analyses (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            repository_id VARCHAR(36) NOT NULL,
            pr_number INTEGER NOT NULL,
            pr_title VARCHAR(500),
            pr_author VARCHAR(255),
            head_sha VARCHAR(64) NOT NULL,
            base_sha VARCHAR(64) NOT NULL,
            head_branch VARCHAR(255) NOT NULL,
            base_branch VARCHAR(255) NOT NULL,
            analysis_results JSONB,
            issues_found INTEGER DEFAULT 0 NOT NULL,
            errors_count INTEGER DEFAULT 0 NOT NULL,
            warnings_count INTEGER DEFAULT 0 NOT NULL,
            issues_created JSONB DEFAULT '[]' NOT NULL,
            comments_posted JSONB DEFAULT '[]' NOT NULL,
            status analysisstatus DEFAULT 'pending' NOT NULL,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            error_message VARCHAR(1000),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """))
    
    # 7. Create stored files table
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS stored_files (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            user_id INTEGER NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(512) NOT NULL,
            file_size BIGINT NOT NULL,
            content_type VARCHAR(100) NOT NULL,
            spaces_url VARCHAR(512) NOT NULL,
            spaces_key VARCHAR(512) NOT NULL,
            bucket_name VARCHAR(100) NOT NULL,
            file_hash VARCHAR(64),
            is_public BOOLEAN DEFAULT false NOT NULL,
            access_permissions VARCHAR(500),
            is_analyzed BOOLEAN DEFAULT false NOT NULL,
            analysis_id VARCHAR(36),
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """))
    
    # 8. Add foreign key constraints (with proper error handling)
    constraints = [
        ("teams", "fk_teams_admin_id", "FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE"),
        ("users", "fk_users_team_id", "FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL"),
        ("enhanced_feedback", "fk_enhanced_feedback_user_id", "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"),
        ("github_repositories", "fk_github_repositories_user_id", "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"),
        ("pr_analyses", "fk_pr_analyses_repository_id", "FOREIGN KEY (repository_id) REFERENCES github_repositories(id) ON DELETE CASCADE"),
        ("stored_files", "fk_stored_files_user_id", "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"),
    ]
    
    for table_name, constraint_name, constraint_def in constraints:
        # Check if constraint already exists
        result = connection.execute(text(f"""
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_name = '{constraint_name}' 
            AND table_name = '{table_name}';
        """)).fetchone()
        
        if not result:
            try:
                connection.execute(text(f"""
                    ALTER TABLE {table_name} 
                    ADD CONSTRAINT {constraint_name} 
                    {constraint_def};
                """))
                print(f"Added constraint {constraint_name}")
            except Exception as e:
                print(f"Error adding constraint {constraint_name}: {e}")
        else:
            print(f"Constraint {constraint_name} already exists, skipping...")


def downgrade(connection):
    """Rollback the enhanced platform schema changes."""
    
    # Drop tables in reverse order due to foreign key constraints
    connection.execute(text("DROP TABLE IF EXISTS stored_files CASCADE;"))
    connection.execute(text("DROP TABLE IF EXISTS pr_analyses CASCADE;"))
    connection.execute(text("DROP TABLE IF EXISTS github_repositories CASCADE;"))
    connection.execute(text("DROP TABLE IF EXISTS enhanced_feedback CASCADE;"))
    
    # Remove user enhancements
    connection.execute(text("""
        ALTER TABLE users 
        DROP COLUMN IF EXISTS team_id,
        DROP COLUMN IF EXISTS preferences;
    """))
    
    # Drop teams table
    connection.execute(text("DROP TABLE IF EXISTS teams CASCADE;"))
    
    # Drop custom types
    connection.execute(text("DROP TYPE IF EXISTS feedbackaction CASCADE;"))
    connection.execute(text("DROP TYPE IF EXISTS analysisstatus CASCADE;"))


if __name__ == "__main__":
    # For manual execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app.core.database import engine
    
    with engine.connect() as connection:
        try:
            with connection.begin():
                upgrade(connection)
                print("Enhanced platform schema migration completed successfully!")
        except Exception as e:
            print(f"Migration failed: {e}")
            raise