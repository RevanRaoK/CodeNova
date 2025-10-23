"""
Migration 001: Platform Enhancements
- Add Teams table
- Add FileBatches and BatchFiles tables
- Add AuditLogs table
- Modify Users table (team_id, role, is_active)
- Modify DirectAnalyses table (filename, batch_id)

Created: 2025-10-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime


# Revision identifiers
revision = '001_platform_enhancements'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Apply migration changes."""
    
    print("Starting migration 001: Platform Enhancements")
    
    # 1. Create Teams table
    print("Creating teams table...")
    op.create_table(
        'teams',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime, nullable=True, onupdate=datetime.utcnow),
        sa.Column('admin_id', sa.Integer, sa.ForeignKey('users.id'), nullable=True),
    )
    
    # Create indexes for teams
    op.create_index('idx_team_name', 'teams', ['name'])
    op.create_index('idx_team_admin', 'teams', ['admin_id'])
    
    # 2. Create FileBatches table
    print("Creating file_batches table...")
    op.create_table(
        'file_batches',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('total_files', sa.Integer, nullable=False),
        sa.Column('completed_files', sa.Integer, nullable=False, default=0),
        sa.Column('failed_files', sa.Integer, nullable=False, default=0),
        sa.Column('status', sa.String(50), nullable=False, default='processing'),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )
    
    # Create indexes for file_batches
    op.create_index('idx_batch_user', 'file_batches', ['user_id'])
    op.create_index('idx_batch_status', 'file_batches', ['status'])
    
    # 3. Create BatchFiles table
    print("Creating batch_files table...")
    op.create_table(
        'batch_files',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('batch_id', sa.String(36), sa.ForeignKey('file_batches.id'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_size', sa.Integer, nullable=False),
        sa.Column('language', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='queued'),
        sa.Column('analysis_id', sa.String(36), sa.ForeignKey('direct_analyses.id'), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('processed_at', sa.DateTime, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
    )
    
    # Create indexes for batch_files
    op.create_index('idx_batch_file_batch', 'batch_files', ['batch_id'])
    op.create_index('idx_batch_file_status', 'batch_files', ['status'])
    
    # 4. Create AuditLogs table
    print("Creating audit_logs table...")
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, default=datetime.utcnow),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('details', postgresql.JSONB, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
    )
    
    # Create indexes for audit_logs
    op.create_index('idx_audit_user', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_audit_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_resource', 'audit_logs', ['resource_type', 'resource_id'])
    
    # 5. Modify Users table
    print("Modifying users table...")
    
    # Add new columns to users table
    op.add_column('users', sa.Column('team_id', sa.String(36), sa.ForeignKey('teams.id'), nullable=True))
    op.add_column('users', sa.Column('role', sa.String(50), nullable=False, server_default='user'))
    op.add_column('users', sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'))
    
    # Create indexes for users
    op.create_index('idx_user_team', 'users', ['team_id'])
    op.create_index('idx_user_role', 'users', ['role'])
    op.create_index('idx_user_is_active', 'users', ['is_active'])
    
    # 6. Modify DirectAnalyses table
    print("Modifying direct_analyses table...")
    
    # Add new columns to direct_analyses table
    op.add_column('direct_analyses', sa.Column('filename', sa.String(255), nullable=True))
    op.add_column('direct_analyses', sa.Column('batch_id', sa.String(36), sa.ForeignKey('file_batches.id'), nullable=True))
    
    # Create indexes for direct_analyses
    op.create_index('idx_analysis_filename', 'direct_analyses', ['filename'])
    op.create_index('idx_analysis_batch', 'direct_analyses', ['batch_id'])
    
    print("Migration 001 completed successfully!")


def downgrade():
    """Rollback migration changes."""
    
    print("Rolling back migration 001: Platform Enhancements")
    
    # Rollback in reverse order
    
    # 6. Remove columns from DirectAnalyses table
    print("Removing columns from direct_analyses table...")
    op.drop_index('idx_analysis_batch', 'direct_analyses')
    op.drop_index('idx_analysis_filename', 'direct_analyses')
    op.drop_column('direct_analyses', 'batch_id')
    op.drop_column('direct_analyses', 'filename')
    
    # 5. Remove columns from Users table
    print("Removing columns from users table...")
    op.drop_index('idx_user_is_active', 'users')
    op.drop_index('idx_user_role', 'users')
    op.drop_index('idx_user_team', 'users')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'role')
    op.drop_column('users', 'team_id')
    
    # 4. Drop AuditLogs table
    print("Dropping audit_logs table...")
    op.drop_index('idx_audit_resource', 'audit_logs')
    op.drop_index('idx_audit_action', 'audit_logs')
    op.drop_index('idx_audit_timestamp', 'audit_logs')
    op.drop_index('idx_audit_user', 'audit_logs')
    op.drop_table('audit_logs')
    
    # 3. Drop BatchFiles table
    print("Dropping batch_files table...")
    op.drop_index('idx_batch_file_status', 'batch_files')
    op.drop_index('idx_batch_file_batch', 'batch_files')
    op.drop_table('batch_files')
    
    # 2. Drop FileBatches table
    print("Dropping file_batches table...")
    op.drop_index('idx_batch_status', 'file_batches')
    op.drop_index('idx_batch_user', 'file_batches')
    op.drop_table('file_batches')
    
    # 1. Drop Teams table
    print("Dropping teams table...")
    op.drop_index('idx_team_admin', 'teams')
    op.drop_index('idx_team_name', 'teams')
    op.drop_table('teams')
    
    print("Migration 001 rollback completed successfully!")


def verify_upgrade():
    """Verify that the migration was applied correctly."""
    
    from sqlalchemy import inspect
    from app.db.session import engine
    
    inspector = inspect(engine)
    
    print("\nVerifying migration 001...")
    
    # Check that all tables exist
    tables = inspector.get_table_names()
    required_tables = ['teams', 'file_batches', 'batch_files', 'audit_logs']
    
    for table in required_tables:
        if table in tables:
            print(f"✓ Table '{table}' exists")
        else:
            print(f"✗ Table '{table}' missing")
            return False
    
    # Check that users table has new columns
    users_columns = [col['name'] for col in inspector.get_columns('users')]
    required_user_columns = ['team_id', 'role', 'is_active']
    
    for column in required_user_columns:
        if column in users_columns:
            print(f"✓ Column 'users.{column}' exists")
        else:
            print(f"✗ Column 'users.{column}' missing")
            return False
    
    # Check that direct_analyses table has new columns
    analyses_columns = [col['name'] for col in inspector.get_columns('direct_analyses')]
    required_analysis_columns = ['filename', 'batch_id']
    
    for column in required_analysis_columns:
        if column in analyses_columns:
            print(f"✓ Column 'direct_analyses.{column}' exists")
        else:
            print(f"✗ Column 'direct_analyses.{column}' missing")
            return False
    
    print("\n✓ Migration verification passed!")
    return True


def verify_downgrade():
    """Verify that the migration was rolled back correctly."""
    
    from sqlalchemy import inspect
    from app.db.session import engine
    
    inspector = inspect(engine)
    
    print("\nVerifying migration 001 rollback...")
    
    # Check that tables were removed
    tables = inspector.get_table_names()
    removed_tables = ['teams', 'file_batches', 'batch_files', 'audit_logs']
    
    for table in removed_tables:
        if table not in tables:
            print(f"✓ Table '{table}' removed")
        else:
            print(f"✗ Table '{table}' still exists")
            return False
    
    # Check that users columns were removed
    users_columns = [col['name'] for col in inspector.get_columns('users')]
    removed_user_columns = ['team_id', 'role', 'is_active']
    
    for column in removed_user_columns:
        if column not in users_columns:
            print(f"✓ Column 'users.{column}' removed")
        else:
            print(f"✗ Column 'users.{column}' still exists")
            return False
    
    # Check that direct_analyses columns were removed
    analyses_columns = [col['name'] for col in inspector.get_columns('direct_analyses')]
    removed_analysis_columns = ['filename', 'batch_id']
    
    for column in removed_analysis_columns:
        if column not in analyses_columns:
            print(f"✓ Column 'direct_analyses.{column}' removed")
        else:
            print(f"✗ Column 'direct_analyses.{column}' still exists")
            return False
    
    print("\n✓ Rollback verification passed!")
    return True


if __name__ == '__main__':
    """
    Run migration manually for testing.
    
    Usage:
        python migration_001_platform_enhancements.py upgrade
        python migration_001_platform_enhancements.py downgrade
        python migration_001_platform_enhancements.py verify
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migration_001_platform_enhancements.py [upgrade|downgrade|verify]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'upgrade':
        upgrade()
        verify_upgrade()
    elif command == 'downgrade':
        downgrade()
        verify_downgrade()
    elif command == 'verify':
        verify_upgrade()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python migration_001_platform_enhancements.py [upgrade|downgrade|verify]")
        sys.exit(1)
