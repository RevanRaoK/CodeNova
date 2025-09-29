"""
Database migration to add model_versions table for tracking fine-tuning iterations
Run this script to create the model_versions table with performance metrics and version management
"""

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from sqlalchemy import text
from app.core.database import SessionLocal, engine

def upgrade_database():
    """Create model_versions table with performance metrics and version management"""
    db = SessionLocal()
    
    try:
        print("Creating model_versions table...")
        
        # Create model_versions table
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
        
        # Create indexes for performance
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_model_versions_id ON model_versions (id);
        """))
        
        db.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_model_versions_name ON model_versions (version_name);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_model_versions_active ON model_versions (is_active);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_model_versions_status ON model_versions (deployment_status);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_model_versions_created ON model_versions (created_at);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_model_versions_job_id ON model_versions (fine_tuning_job_id);
        """))
        
        # Composite indexes for performance queries
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_model_versions_performance 
            ON model_versions (accuracy_score, acceptance_rate);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_model_versions_active_status 
            ON model_versions (is_active, deployment_status);
        """))
        
        # Ensure only one active model at a time
        db.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS unique_active_model 
            ON model_versions (is_active) 
            WHERE is_active = TRUE;
        """))
        
        # Create function to automatically set deployment timestamps
        db.execute(text("""
            CREATE OR REPLACE FUNCTION update_model_version_timestamps()
            RETURNS TRIGGER AS $$
            BEGIN
                -- Set deployed_at when status changes to deployed
                IF OLD.deployment_status != 'deployed' AND NEW.deployment_status = 'deployed' THEN
                    NEW.deployed_at = CURRENT_TIMESTAMP;
                END IF;
                
                -- Set retired_at when status changes to retired
                IF OLD.deployment_status != 'retired' AND NEW.deployment_status = 'retired' THEN
                    NEW.retired_at = CURRENT_TIMESTAMP;
                END IF;
                
                -- Set training_started_at when training begins
                IF OLD.training_started_at IS NULL AND NEW.training_started_at IS NOT NULL THEN
                    NEW.training_started_at = COALESCE(NEW.training_started_at, CURRENT_TIMESTAMP);
                END IF;
                
                -- Set training_completed_at when training finishes
                IF OLD.training_completed_at IS NULL AND NEW.training_completed_at IS NOT NULL THEN
                    NEW.training_completed_at = COALESCE(NEW.training_completed_at, CURRENT_TIMESTAMP);
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
        
        # Create function to ensure only one active model
        db.execute(text("""
            CREATE OR REPLACE FUNCTION ensure_single_active_model()
            RETURNS TRIGGER AS $$
            BEGIN
                -- If setting a model to active, deactivate all others
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
        print("✅ Model versions table created successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def downgrade_database():
    """Drop model_versions table and related objects"""
    db = SessionLocal()
    
    try:
        print("Dropping model_versions table...")
        
        # Drop triggers and functions
        db.execute(text("DROP TRIGGER IF EXISTS trigger_model_version_timestamps ON model_versions;"))
        db.execute(text("DROP TRIGGER IF EXISTS trigger_ensure_single_active_model ON model_versions;"))
        db.execute(text("DROP FUNCTION IF EXISTS update_model_version_timestamps();"))
        db.execute(text("DROP FUNCTION IF EXISTS ensure_single_active_model();"))
        
        # Drop table (indexes and constraints will be dropped automatically)
        db.execute(text("DROP TABLE IF EXISTS model_versions CASCADE;"))
        
        db.commit()
        print("✅ Model versions table dropped successfully!")
        
    except Exception as e:
        print(f"❌ Downgrade failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Model versions table database migration')
    parser.add_argument('--downgrade', action='store_true', help='Downgrade the migration')
    
    args = parser.parse_args()
    
    if args.downgrade:
        downgrade_database()
    else:
        upgrade_database()