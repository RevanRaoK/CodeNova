"""
Comprehensive database migration to add all feedback system tables
Run this script to create issues, feedback_records, and model_versions tables in the correct order
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from sqlalchemy import text
from app.core.database import SessionLocal, engine

def upgrade_database():
    """Create all feedback system tables in the correct order"""
    db = SessionLocal()
    
    try:
        print("Creating feedback system tables...")
        
        # 1. Create issues table first (depends on direct_analyses)
        print("1. Creating issues table...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS issues (
                id VARCHAR(64) PRIMARY KEY,
                analysis_id VARCHAR(36) NOT NULL,
                pattern_type VARCHAR(100) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                category VARCHAR(50),
                location JSON NOT NULL,
                suggestion_text TEXT NOT NULL,
                code_context TEXT NOT NULL,
                original_code TEXT,
                suggested_fix TEXT,
                ast_node_type VARCHAR(100),
                ast_metadata JSON,
                status VARCHAR(20) DEFAULT 'active',
                confidence_score FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                
                CONSTRAINT fk_issues_analysis_id 
                    FOREIGN KEY (analysis_id) 
                    REFERENCES direct_analyses(id) 
                    ON DELETE CASCADE
            );
        """))
        
        # 2. Create feedback_records table (depends on issues and users)
        print("2. Creating feedback_records table...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS feedback_records (
                id SERIAL PRIMARY KEY,
                issue_id VARCHAR(64) NOT NULL,
                user_id INTEGER NOT NULL,
                feedback_type VARCHAR(20) NOT NULL,
                feedback_value INTEGER NOT NULL,
                feedback_comment TEXT,
                modified_suggestion TEXT,
                context_data JSON,
                user_experience_level VARCHAR(20),
                code_review_context VARCHAR(50),
                is_validated BOOLEAN DEFAULT FALSE,
                validation_score FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                CONSTRAINT fk_feedback_issue_id 
                    FOREIGN KEY (issue_id) 
                    REFERENCES issues(id) 
                    ON DELETE CASCADE,
                    
                CONSTRAINT fk_feedback_user_id 
                    FOREIGN KEY (user_id) 
                    REFERENCES users(id) 
                    ON DELETE CASCADE,
                    
                CONSTRAINT chk_feedback_type 
                    CHECK (feedback_type IN ('accept', 'reject', 'modify', 'ignore')),
                    
                CONSTRAINT chk_feedback_value 
                    CHECK (feedback_value IN (-1, 0, 1)),
                    
                CONSTRAINT chk_experience_level 
                    CHECK (user_experience_level IS NULL OR 
                           user_experience_level IN ('beginner', 'intermediate', 'expert')),
                           
                CONSTRAINT chk_review_context 
                    CHECK (code_review_context IS NULL OR 
                           code_review_context IN ('personal', 'team', 'production', 'learning'))
            );
        """))
        
        # 3. Create model_versions table (independent)
        print("3. Creating model_versions table...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS model_versions (
                id SERIAL PRIMARY KEY,
                version_name VARCHAR(100) UNIQUE NOT NULL,
                version_number VARCHAR(20) NOT NULL,
                base_model VARCHAR(100) NOT NULL,
                model_type VARCHAR(50) NOT NULL DEFAULT 'gemini',
                training_data_size INTEGER NOT NULL,
                training_duration_minutes FLOAT,
                fine_tuning_job_id VARCHAR(255),
                performance_metrics JSON,
                accuracy_score FLOAT,
                precision_score FLOAT,
                recall_score FLOAT,
                f1_score FLOAT,
                acceptance_rate FLOAT,
                rejection_rate FLOAT,
                improvement_score FLOAT,
                is_active BOOLEAN DEFAULT FALSE,
                is_production_ready BOOLEAN DEFAULT FALSE,
                deployment_status VARCHAR(20) DEFAULT 'training',
                training_config JSON,
                model_metadata JSON,
                validation_results JSON,
                a_b_test_results JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                training_started_at TIMESTAMP,
                training_completed_at TIMESTAMP,
                deployed_at TIMESTAMP,
                retired_at TIMESTAMP,
                
                CONSTRAINT chk_deployment_status 
                    CHECK (deployment_status IN ('training', 'testing', 'deployed', 'retired')),
                    
                CONSTRAINT chk_accuracy_score 
                    CHECK (accuracy_score IS NULL OR (accuracy_score >= 0.0 AND accuracy_score <= 1.0)),
                    
                CONSTRAINT chk_precision_score 
                    CHECK (precision_score IS NULL OR (precision_score >= 0.0 AND precision_score <= 1.0)),
                    
                CONSTRAINT chk_recall_score 
                    CHECK (recall_score IS NULL OR (recall_score >= 0.0 AND recall_score <= 1.0)),
                    
                CONSTRAINT chk_f1_score 
                    CHECK (f1_score IS NULL OR (f1_score >= 0.0 AND f1_score <= 1.0)),
                    
                CONSTRAINT chk_acceptance_rate 
                    CHECK (acceptance_rate IS NULL OR (acceptance_rate >= 0.0 AND acceptance_rate <= 1.0)),
                    
                CONSTRAINT chk_rejection_rate 
                    CHECK (rejection_rate IS NULL OR (rejection_rate >= 0.0 AND rejection_rate <= 1.0))
            );
        """))
        
        # Create all indexes
        print("4. Creating indexes...")
        
        # Issues indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_issues_id ON issues (id);",
            "CREATE INDEX IF NOT EXISTS idx_issues_analysis_id ON issues (analysis_id);",
            "CREATE INDEX IF NOT EXISTS idx_issues_pattern_type ON issues (pattern_type);",
            "CREATE INDEX IF NOT EXISTS idx_issues_severity ON issues (severity);",
            "CREATE INDEX IF NOT EXISTS idx_issues_status ON issues (status);",
            "CREATE INDEX IF NOT EXISTS idx_issues_created_at ON issues (created_at);",
            "CREATE INDEX IF NOT EXISTS idx_issues_analysis_pattern ON issues (analysis_id, pattern_type);",
            "CREATE INDEX IF NOT EXISTS idx_issues_severity_status ON issues (severity, status);",
            
            # Feedback records indexes
            "CREATE INDEX IF NOT EXISTS idx_feedback_id ON feedback_records (id);",
            "CREATE INDEX IF NOT EXISTS idx_feedback_issue_id ON feedback_records (issue_id);",
            "CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback_records (user_id);",
            "CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback_records (feedback_type);",
            "CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON feedback_records (created_at);",
            "CREATE INDEX IF NOT EXISTS idx_feedback_validated ON feedback_records (is_validated);",
            "CREATE INDEX IF NOT EXISTS idx_feedback_issue_user ON feedback_records (issue_id, user_id);",
            "CREATE INDEX IF NOT EXISTS idx_feedback_type_value ON feedback_records (feedback_type, feedback_value);",
            "CREATE UNIQUE INDEX IF NOT EXISTS unique_user_issue_feedback ON feedback_records (issue_id, user_id);",
            
            # Model versions indexes
            "CREATE INDEX IF NOT EXISTS idx_model_versions_id ON model_versions (id);",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_model_versions_name ON model_versions (version_name);",
            "CREATE INDEX IF NOT EXISTS idx_model_versions_active ON model_versions (is_active);",
            "CREATE INDEX IF NOT EXISTS idx_model_versions_status ON model_versions (deployment_status);",
            "CREATE INDEX IF NOT EXISTS idx_model_versions_created ON model_versions (created_at);",
            "CREATE INDEX IF NOT EXISTS idx_model_versions_job_id ON model_versions (fine_tuning_job_id);",
            "CREATE INDEX IF NOT EXISTS idx_model_versions_performance ON model_versions (accuracy_score, acceptance_rate);",
            "CREATE UNIQUE INDEX IF NOT EXISTS unique_active_model ON model_versions (is_active) WHERE is_active = TRUE;",
        ]
        
        for index_sql in indexes:
            db.execute(text(index_sql))
        
        # Create triggers and functions
        print("5. Creating triggers and functions...")
        
        # Issues updated_at trigger
        db.execute(text("""
            CREATE OR REPLACE FUNCTION update_issues_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))
        
        db.execute(text("""
            DROP TRIGGER IF EXISTS trigger_issues_updated_at ON issues;
            CREATE TRIGGER trigger_issues_updated_at
                BEFORE UPDATE ON issues
                FOR EACH ROW
                EXECUTE FUNCTION update_issues_updated_at();
        """))
        
        # Feedback records updated_at trigger
        db.execute(text("""
            CREATE OR REPLACE FUNCTION update_feedback_records_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))
        
        db.execute(text("""
            DROP TRIGGER IF EXISTS trigger_feedback_records_updated_at ON feedback_records;
            CREATE TRIGGER trigger_feedback_records_updated_at
                BEFORE UPDATE ON feedback_records
                FOR EACH ROW
                EXECUTE FUNCTION update_feedback_records_updated_at();
        """))
        
        # Model versions timestamp management
        db.execute(text("""
            CREATE OR REPLACE FUNCTION update_model_version_timestamps()
            RETURNS TRIGGER AS $$
            BEGIN
                IF OLD.deployment_status != 'deployed' AND NEW.deployment_status = 'deployed' THEN
                    NEW.deployed_at = CURRENT_TIMESTAMP;
                END IF;
                
                IF OLD.deployment_status != 'retired' AND NEW.deployment_status = 'retired' THEN
                    NEW.retired_at = CURRENT_TIMESTAMP;
                END IF;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))
        
        db.execute(text("""
            DROP TRIGGER IF EXISTS trigger_model_version_timestamps ON model_versions;
            CREATE TRIGGER trigger_model_version_timestamps
                BEFORE UPDATE ON model_versions
                FOR EACH ROW
                EXECUTE FUNCTION update_model_version_timestamps();
        """))
        
        # Ensure single active model
        db.execute(text("""
            CREATE OR REPLACE FUNCTION ensure_single_active_model()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.is_active = TRUE THEN
                    UPDATE model_versions 
                    SET is_active = FALSE 
                    WHERE id != NEW.id AND is_active = TRUE;
                END IF;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """))
        
        db.execute(text("""
            DROP TRIGGER IF EXISTS trigger_ensure_single_active_model ON model_versions;
            CREATE TRIGGER trigger_ensure_single_active_model
                BEFORE INSERT OR UPDATE ON model_versions
                FOR EACH ROW
                WHEN (NEW.is_active = TRUE)
                EXECUTE FUNCTION ensure_single_active_model();
        """))
        
        db.commit()
        print("✅ All feedback system tables created successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def downgrade_database():
    """Drop all feedback system tables and related objects"""
    db = SessionLocal()
    
    try:
        print("Dropping feedback system tables...")
        
        # Drop triggers and functions
        db.execute(text("DROP TRIGGER IF EXISTS trigger_issues_updated_at ON issues;"))
        db.execute(text("DROP TRIGGER IF EXISTS trigger_feedback_records_updated_at ON feedback_records;"))
        db.execute(text("DROP TRIGGER IF EXISTS trigger_model_version_timestamps ON model_versions;"))
        db.execute(text("DROP TRIGGER IF EXISTS trigger_ensure_single_active_model ON model_versions;"))
        
        db.execute(text("DROP FUNCTION IF EXISTS update_issues_updated_at();"))
        db.execute(text("DROP FUNCTION IF EXISTS update_feedback_records_updated_at();"))
        db.execute(text("DROP FUNCTION IF EXISTS update_model_version_timestamps();"))
        db.execute(text("DROP FUNCTION IF EXISTS ensure_single_active_model();"))
        
        # Drop tables in reverse dependency order
        db.execute(text("DROP TABLE IF EXISTS feedback_records CASCADE;"))
        db.execute(text("DROP TABLE IF EXISTS issues CASCADE;"))
        db.execute(text("DROP TABLE IF EXISTS model_versions CASCADE;"))
        
        db.commit()
        print("✅ All feedback system tables dropped successfully!")
        
    except Exception as e:
        print(f"❌ Downgrade failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Feedback system database migration')
    parser.add_argument('--downgrade', action='store_true', help='Downgrade the migration')
    
    args = parser.parse_args()
    
    if args.downgrade:
        downgrade_database()
    else:
        upgrade_database()