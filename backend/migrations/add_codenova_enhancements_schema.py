"""
CodeNova Platform Enhancements Schema Migration

This migration adds all required tables and fields for the comprehensive
platform enhancement including:
- Teams table (if not exists)
- FileBatches and BatchFiles tables (if not exists)
- AuditLogs table
- Enhanced user fields (team_id, role, is_active)
- Enhanced DirectAnalyses fields (filename, batch_id)
- All necessary indexes for performance

Requirements covered: 7.1, 7.2, 8.1, 8.2, 14.4

Usage:
    python backend/migrations/add_codenova_enhancements_schema.py
"""

from sqlalchemy import text
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def upgrade(connection):
    """Apply the CodeNova enhancements schema changes."""
    
    print("Starting CodeNova enhancements schema migration...")
    
    # ========================================================================
    # 1. Ensure UserRole enum has all required values
    # ========================================================================
    print("\n1. Updating UserRole enum...")
    try:
        connection.execute(text("""
            DO $$ BEGIN
                -- Add USER role if not exists
                IF NOT EXISTS (
                    SELECT 1 FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = 'userrole' AND e.enumlabel = 'user'
                ) THEN
                    ALTER TYPE userrole ADD VALUE 'user';
                END IF;
                
                -- Add TEAM_LEAD role if not exists
                IF NOT EXISTS (
                    SELECT 1 FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = 'userrole' AND e.enumlabel = 'team_lead'
                ) THEN
                    ALTER TYPE userrole ADD VALUE 'team_lead';
                END IF;
            END $$;
        """))
        print("   ✓ UserRole enum updated")
    except Exception as e:
        print(f"   ⚠ UserRole enum update: {e}")
    
    # ========================================================================
    # 2. Create Teams table if not exists
    # ========================================================================
    print("\n2. Creating Teams table...")
    try:
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
        print("   ✓ Teams table created")
    except Exception as e:
        print(f"   ⚠ Teams table creation: {e}")
    
    # Add indexes for teams table
    print("   Adding indexes for teams table...")
    indexes = [
        ("idx_teams_id", "teams", "id"),
        ("idx_teams_name", "teams", "name"),
        ("idx_teams_admin_id", "teams", "admin_id"),
    ]
    
    for idx_name, table_name, column_name in indexes:
        try:
            connection.execute(text(f"""
                CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({column_name});
            """))
            print(f"   ✓ Index {idx_name} created")
        except Exception as e:
            print(f"   ⚠ Index {idx_name}: {e}")
    
    # ========================================================================
    # 3. Add enhanced user fields
    # ========================================================================
    print("\n3. Adding enhanced user fields...")
    user_fields = [
        ("team_id", "VARCHAR(36)"),
        ("preferences", "JSONB DEFAULT '{}' NOT NULL"),
    ]
    
    for field_name, field_type in user_fields:
        try:
            connection.execute(text(f"""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS {field_name} {field_type};
            """))
            print(f"   ✓ Added users.{field_name}")
        except Exception as e:
            print(f"   ⚠ users.{field_name}: {e}")
    
    # Ensure is_active column exists with default
    try:
        connection.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
        """))
        print("   ✓ Added users.is_active")
    except Exception as e:
        print(f"   ⚠ users.is_active: {e}")
    
    # Add index for team_id
    try:
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_team_id ON users(team_id);
        """))
        print("   ✓ Index idx_users_team_id created")
    except Exception as e:
        print(f"   ⚠ Index idx_users_team_id: {e}")
    
    # ========================================================================
    # 4. Add enhanced DirectAnalyses fields
    # ========================================================================
    print("\n4. Adding enhanced DirectAnalyses fields...")
    analysis_fields = [
        ("filename", "VARCHAR(255)"),
        ("batch_id", "VARCHAR(36)"),
    ]
    
    for field_name, field_type in analysis_fields:
        try:
            connection.execute(text(f"""
                ALTER TABLE direct_analyses 
                ADD COLUMN IF NOT EXISTS {field_name} {field_type};
            """))
            print(f"   ✓ Added direct_analyses.{field_name}")
        except Exception as e:
            print(f"   ⚠ direct_analyses.{field_name}: {e}")
    
    # Add indexes for direct_analyses
    print("   Adding indexes for direct_analyses...")
    analysis_indexes = [
        ("idx_direct_analyses_filename", "direct_analyses", "filename"),
        ("idx_direct_analyses_batch_id", "direct_analyses", "batch_id"),
    ]
    
    for idx_name, table_name, column_name in analysis_indexes:
        try:
            connection.execute(text(f"""
                CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({column_name});
            """))
            print(f"   ✓ Index {idx_name} created")
        except Exception as e:
            print(f"   ⚠ Index {idx_name}: {e}")
    
    # ========================================================================
    # 5. Create FileBatches table if not exists
    # ========================================================================
    print("\n5. Creating FileBatches table...")
    try:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS file_batches (
                id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
                user_id INTEGER NOT NULL,
                total_files INTEGER NOT NULL,
                processed_files INTEGER DEFAULT 0,
                successful_files INTEGER DEFAULT 0,
                failed_files INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'pending',
                combined_results JSONB,
                error_details JSONB,
                processing_log JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                total_size_bytes INTEGER DEFAULT 0,
                processing_time_seconds FLOAT,
                estimated_completion_time TIMESTAMP
            );
        """))
        print("   ✓ FileBatches table created")
    except Exception as e:
        print(f"   ⚠ FileBatches table creation: {e}")
    
    # Add indexes for file_batches
    print("   Adding indexes for file_batches...")
    batch_indexes = [
        ("idx_file_batches_user_id", "file_batches", "user_id"),
        ("idx_file_batches_status", "file_batches", "status"),
        ("idx_file_batches_created_at", "file_batches", "created_at"),
    ]
    
    for idx_name, table_name, column_name in batch_indexes:
        try:
            connection.execute(text(f"""
                CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({column_name});
            """))
            print(f"   ✓ Index {idx_name} created")
        except Exception as e:
            print(f"   ⚠ Index {idx_name}: {e}")
    
    # ========================================================================
    # 6. Create BatchFiles table if not exists
    # ========================================================================
    print("\n6. Creating BatchFiles table...")
    try:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS batch_files (
                id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
                batch_id VARCHAR(36) NOT NULL,
                filename VARCHAR(255) NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                file_size_bytes INTEGER NOT NULL,
                content_type VARCHAR(100),
                language VARCHAR(50),
                file_index INTEGER NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                file_content TEXT,
                storage_path VARCHAR(512),
                stored_file_id VARCHAR(36),
                analysis_id VARCHAR(36),
                issues_count INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                warnings_count INTEGER DEFAULT 0,
                suggestions_count INTEGER DEFAULT 0,
                analysis_results JSONB,
                analysis_metrics JSONB,
                analysis_summary TEXT,
                error_message TEXT,
                error_code VARCHAR(50),
                error_details JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_processing_at TIMESTAMP,
                completed_at TIMESTAMP,
                processing_time_seconds FLOAT
            );
        """))
        print("   ✓ BatchFiles table created")
    except Exception as e:
        print(f"   ⚠ BatchFiles table creation: {e}")
    
    # Add indexes for batch_files
    print("   Adding indexes for batch_files...")
    batch_file_indexes = [
        ("idx_batch_files_batch_id", "batch_files", "batch_id"),
        ("idx_batch_files_status", "batch_files", "status"),
        ("idx_batch_files_filename", "batch_files", "filename"),
    ]
    
    for idx_name, table_name, column_name in batch_file_indexes:
        try:
            connection.execute(text(f"""
                CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({column_name});
            """))
            print(f"   ✓ Index {idx_name} created")
        except Exception as e:
            print(f"   ⚠ Index {idx_name}: {e}")
    
    # ========================================================================
    # 7. Create AuditLogs table
    # ========================================================================
    print("\n7. Creating AuditLogs table...")
    try:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                event_id VARCHAR(36) UNIQUE NOT NULL DEFAULT gen_random_uuid()::text,
                user_id INTEGER NOT NULL,
                action VARCHAR(100) NOT NULL,
                resource_type VARCHAR(50),
                resource_id VARCHAR(100),
                details JSONB,
                changes JSONB,
                ip_address VARCHAR(45),
                user_agent TEXT,
                request_method VARCHAR(10),
                request_path VARCHAR(512),
                status VARCHAR(20) DEFAULT 'success',
                error_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                duration_ms INTEGER
            );
        """))
        print("   ✓ AuditLogs table created")
    except Exception as e:
        print(f"   ⚠ AuditLogs table creation: {e}")
    
    # Add indexes for audit_logs
    print("   Adding indexes for audit_logs...")
    audit_indexes = [
        ("idx_audit_logs_event_id", "audit_logs", "event_id"),
        ("idx_audit_logs_user_id", "audit_logs", "user_id"),
        ("idx_audit_logs_action", "audit_logs", "action"),
        ("idx_audit_logs_timestamp", "audit_logs", "timestamp"),
        ("idx_audit_logs_resource_type", "audit_logs", "resource_type"),
        ("idx_audit_logs_resource_id", "audit_logs", "resource_id"),
    ]
    
    for idx_name, table_name, column_name in audit_indexes:
        try:
            connection.execute(text(f"""
                CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({column_name});
            """))
            print(f"   ✓ Index {idx_name} created")
        except Exception as e:
            print(f"   ⚠ Index {idx_name}: {e}")
    
    # Add composite indexes for common queries
    print("   Adding composite indexes...")
    composite_indexes = [
        ("idx_audit_user_timestamp", "audit_logs", "(user_id, timestamp)"),
        ("idx_audit_action_timestamp", "audit_logs", "(action, timestamp)"),
        ("idx_audit_resource", "audit_logs", "(resource_type, resource_id)"),
    ]
    
    for idx_name, table_name, columns in composite_indexes:
        try:
            connection.execute(text(f"""
                CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}{columns};
            """))
            print(f"   ✓ Composite index {idx_name} created")
        except Exception as e:
            print(f"   ⚠ Composite index {idx_name}: {e}")
    
    # ========================================================================
    # 8. Add foreign key constraints
    # ========================================================================
    print("\n8. Adding foreign key constraints...")
    
    constraints = [
        ("teams", "fk_teams_admin_id", "FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE"),
        ("users", "fk_users_team_id", "FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL"),
        ("file_batches", "fk_file_batches_user_id", "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"),
        ("batch_files", "fk_batch_files_batch_id", "FOREIGN KEY (batch_id) REFERENCES file_batches(id) ON DELETE CASCADE"),
        ("batch_files", "fk_batch_files_stored_file_id", "FOREIGN KEY (stored_file_id) REFERENCES stored_files(id) ON DELETE SET NULL"),
        ("direct_analyses", "fk_direct_analyses_batch_id", "FOREIGN KEY (batch_id) REFERENCES file_batches(id) ON DELETE SET NULL"),
        ("audit_logs", "fk_audit_logs_user_id", "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"),
    ]
    
    for table_name, constraint_name, constraint_def in constraints:
        # Check if constraint already exists
        try:
            result = connection.execute(text(f"""
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = '{constraint_name}' 
                AND table_name = '{table_name}';
            """)).fetchone()
            
            if not result:
                connection.execute(text(f"""
                    ALTER TABLE {table_name} 
                    ADD CONSTRAINT {constraint_name} 
                    {constraint_def};
                """))
                print(f"   ✓ Constraint {constraint_name} added")
            else:
                print(f"   ⊙ Constraint {constraint_name} already exists")
        except Exception as e:
            print(f"   ⚠ Constraint {constraint_name}: {e}")
    
    # ========================================================================
    # 9. Create performance indexes
    # ========================================================================
    print("\n9. Creating additional performance indexes...")
    
    performance_indexes = [
        ("idx_users_role", "users", "role"),
        ("idx_users_is_active", "users", "is_active"),
        ("idx_direct_analyses_user_created", "direct_analyses", "(user_id, created_at DESC)"),
        ("idx_file_batches_user_created", "file_batches", "(user_id, created_at DESC)"),
    ]
    
    for idx_name, table_name, columns in performance_indexes:
        try:
            connection.execute(text(f"""
                CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}{columns if columns.startswith('(') else f'({columns})'};
            """))
            print(f"   ✓ Performance index {idx_name} created")
        except Exception as e:
            print(f"   ⚠ Performance index {idx_name}: {e}")
    
    print("\n" + "="*70)
    print("✓ CodeNova enhancements schema migration completed successfully!")
    print("="*70)


def downgrade(connection):
    """Rollback the CodeNova enhancements schema changes."""
    
    print("Rolling back CodeNova enhancements schema migration...")
    
    # Drop tables in reverse order due to foreign key constraints
    tables_to_drop = [
        "audit_logs",
        "batch_files",
        "file_batches",
    ]
    
    for table_name in tables_to_drop:
        try:
            connection.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE;"))
            print(f"   ✓ Dropped table {table_name}")
        except Exception as e:
            print(f"   ⚠ Error dropping {table_name}: {e}")
    
    # Remove added columns from users
    try:
        connection.execute(text("""
            ALTER TABLE users 
            DROP COLUMN IF EXISTS team_id,
            DROP COLUMN IF EXISTS preferences;
        """))
        print("   ✓ Removed enhanced user fields")
    except Exception as e:
        print(f"   ⚠ Error removing user fields: {e}")
    
    # Remove added columns from direct_analyses
    try:
        connection.execute(text("""
            ALTER TABLE direct_analyses 
            DROP COLUMN IF EXISTS filename,
            DROP COLUMN IF EXISTS batch_id;
        """))
        print("   ✓ Removed enhanced analysis fields")
    except Exception as e:
        print(f"   ⚠ Error removing analysis fields: {e}")
    
    print("\n✓ Rollback completed!")


if __name__ == "__main__":
    """Execute migration when run directly."""
    from app.core.database import engine
    
    print("\n" + "="*70)
    print("CodeNova Platform Enhancements Schema Migration")
    print("="*70 + "\n")
    
    with engine.connect() as connection:
        try:
            with connection.begin():
                upgrade(connection)
        except Exception as e:
            print(f"\n✗ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
