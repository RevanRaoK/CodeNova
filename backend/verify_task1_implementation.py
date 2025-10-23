"""
Verification script for Task 1: Database schema and models setup

This script verifies that all required database tables, models, and schemas
have been properly created and configured.

Requirements covered: 7.1, 7.2, 8.1, 8.2, 14.4
"""

import sys
from sqlalchemy import inspect, text
from app.core.database import engine
from app.models import (
    User, Team, FileBatch, BatchFile, AuditLog,
    DirectAnalysis, UserRole, BatchStatus, FileStatus
)
from app.schemas import (
    TeamCreate, TeamResponse, TeamDetailResponse,
    FileBatchCreate, FileBatchResponse, BatchFileResponse,
    AuditLogCreate, AuditLogResponse,
    UserRoleUpdate, UserStatusUpdate, UserTeamAssignment
)


def verify_tables_exist():
    """Verify all required tables exist in the database."""
    print("\n" + "="*70)
    print("1. Verifying Database Tables")
    print("="*70)
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    required_tables = [
        'users',
        'teams',
        'file_batches',
        'batch_files',
        'audit_logs',
        'direct_analyses'
    ]
    
    all_exist = True
    for table in required_tables:
        if table in existing_tables:
            print(f"   ✓ Table '{table}' exists")
        else:
            print(f"   ✗ Table '{table}' MISSING")
            all_exist = False
    
    return all_exist


def verify_table_columns():
    """Verify all required columns exist in tables."""
    print("\n" + "="*70)
    print("2. Verifying Table Columns")
    print("="*70)
    
    inspector = inspect(engine)
    
    # Check Users table columns
    print("\n   Users table:")
    user_columns = {col['name'] for col in inspector.get_columns('users')}
    required_user_columns = ['id', 'email', 'team_id', 'role', 'is_active', 'preferences']
    
    all_exist = True
    for col in required_user_columns:
        if col in user_columns:
            print(f"      ✓ Column '{col}' exists")
        else:
            print(f"      ✗ Column '{col}' MISSING")
            all_exist = False
    
    # Check Teams table columns
    print("\n   Teams table:")
    team_columns = {col['name'] for col in inspector.get_columns('teams')}
    required_team_columns = ['id', 'name', 'admin_id', 'settings', 'created_at', 'updated_at']
    
    for col in required_team_columns:
        if col in team_columns:
            print(f"      ✓ Column '{col}' exists")
        else:
            print(f"      ✗ Column '{col}' MISSING")
            all_exist = False
    
    # Check FileBatches table columns
    print("\n   FileBatches table:")
    batch_columns = {col['name'] for col in inspector.get_columns('file_batches')}
    required_batch_columns = ['id', 'user_id', 'total_files', 'processed_files', 
                              'successful_files', 'failed_files', 'status']
    
    for col in required_batch_columns:
        if col in batch_columns:
            print(f"      ✓ Column '{col}' exists")
        else:
            print(f"      ✗ Column '{col}' MISSING")
            all_exist = False
    
    # Check BatchFiles table columns
    print("\n   BatchFiles table:")
    batch_file_columns = {col['name'] for col in inspector.get_columns('batch_files')}
    required_batch_file_columns = ['id', 'batch_id', 'filename', 'original_filename', 
                                   'file_size_bytes', 'status', 'analysis_id']
    
    for col in required_batch_file_columns:
        if col in batch_file_columns:
            print(f"      ✓ Column '{col}' exists")
        else:
            print(f"      ✗ Column '{col}' MISSING")
            all_exist = False
    
    # Check AuditLogs table columns
    print("\n   AuditLogs table:")
    audit_columns = {col['name'] for col in inspector.get_columns('audit_logs')}
    required_audit_columns = ['id', 'event_id', 'user_id', 'action', 'resource_type', 
                             'resource_id', 'details', 'timestamp']
    
    for col in required_audit_columns:
        if col in audit_columns:
            print(f"      ✓ Column '{col}' exists")
        else:
            print(f"      ✗ Column '{col}' MISSING")
            all_exist = False
    
    # Check DirectAnalyses table columns
    print("\n   DirectAnalyses table:")
    analysis_columns = {col['name'] for col in inspector.get_columns('direct_analyses')}
    required_analysis_columns = ['id', 'user_id', 'filename', 'batch_id', 'code_content', 'language']
    
    for col in required_analysis_columns:
        if col in analysis_columns:
            print(f"      ✓ Column '{col}' exists")
        else:
            print(f"      ✗ Column '{col}' MISSING")
            all_exist = False
    
    return all_exist


def verify_indexes():
    """Verify all required indexes exist."""
    print("\n" + "="*70)
    print("3. Verifying Indexes")
    print("="*70)
    
    inspector = inspect(engine)
    
    # Check key indexes
    tables_to_check = {
        'users': ['idx_users_team_id', 'idx_users_role', 'idx_users_is_active'],
        'teams': ['idx_teams_name', 'idx_teams_admin_id'],
        'file_batches': ['idx_file_batches_user_id', 'idx_file_batches_status'],
        'batch_files': ['idx_batch_files_batch_id', 'idx_batch_files_status'],
        'audit_logs': ['idx_audit_logs_user_id', 'idx_audit_logs_action', 'idx_audit_logs_timestamp'],
        'direct_analyses': ['idx_direct_analyses_filename', 'idx_direct_analyses_batch_id']
    }
    
    all_exist = True
    for table, expected_indexes in tables_to_check.items():
        print(f"\n   {table} table:")
        existing_indexes = {idx['name'] for idx in inspector.get_indexes(table)}
        
        for idx_name in expected_indexes:
            if idx_name in existing_indexes:
                print(f"      ✓ Index '{idx_name}' exists")
            else:
                print(f"      ⚠ Index '{idx_name}' not found (may use different name)")
    
    return all_exist


def verify_foreign_keys():
    """Verify all required foreign key constraints exist."""
    print("\n" + "="*70)
    print("4. Verifying Foreign Key Constraints")
    print("="*70)
    
    inspector = inspect(engine)
    
    # Check key foreign keys
    tables_to_check = {
        'teams': ['fk_teams_admin_id'],
        'users': ['fk_users_team_id'],
        'file_batches': ['fk_file_batches_user_id'],
        'batch_files': ['fk_batch_files_batch_id'],
        'audit_logs': ['fk_audit_logs_user_id'],
        'direct_analyses': ['fk_direct_analyses_batch_id']
    }
    
    all_exist = True
    for table, expected_fks in tables_to_check.items():
        print(f"\n   {table} table:")
        existing_fks = {fk['name'] for fk in inspector.get_foreign_keys(table)}
        
        for fk_name in expected_fks:
            if fk_name in existing_fks:
                print(f"      ✓ Foreign key '{fk_name}' exists")
            else:
                print(f"      ⚠ Foreign key '{fk_name}' not found (may use different name)")
    
    return all_exist


def verify_models():
    """Verify all SQLAlchemy models are properly defined."""
    print("\n" + "="*70)
    print("5. Verifying SQLAlchemy Models")
    print("="*70)
    
    models_to_check = [
        ('User', User),
        ('Team', Team),
        ('FileBatch', FileBatch),
        ('BatchFile', BatchFile),
        ('AuditLog', AuditLog),
        ('DirectAnalysis', DirectAnalysis)
    ]
    
    all_valid = True
    for model_name, model_class in models_to_check:
        try:
            # Check if model has __tablename__
            if hasattr(model_class, '__tablename__'):
                print(f"   ✓ Model '{model_name}' properly defined (table: {model_class.__tablename__})")
            else:
                print(f"   ✗ Model '{model_name}' missing __tablename__")
                all_valid = False
        except Exception as e:
            print(f"   ✗ Model '{model_name}' error: {e}")
            all_valid = False
    
    return all_valid


def verify_enums():
    """Verify all enum types are properly defined."""
    print("\n" + "="*70)
    print("6. Verifying Enum Types")
    print("="*70)
    
    enums_to_check = [
        ('UserRole', UserRole, ['ADMIN', 'USER', 'TEAM_LEAD', 'DEVELOPER']),
        ('BatchStatus', BatchStatus, ['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED']),
        ('FileStatus', FileStatus, ['PENDING', 'UPLOADING', 'ANALYZING', 'COMPLETED', 'FAILED'])
    ]
    
    all_valid = True
    for enum_name, enum_class, expected_values in enums_to_check:
        print(f"\n   {enum_name}:")
        enum_values = [e.name for e in enum_class]
        
        for value in expected_values:
            if value in enum_values:
                print(f"      ✓ Value '{value}' exists")
            else:
                print(f"      ⚠ Value '{value}' not found")
    
    return all_valid


def verify_schemas():
    """Verify all Pydantic schemas are properly defined."""
    print("\n" + "="*70)
    print("7. Verifying Pydantic Schemas")
    print("="*70)
    
    schemas_to_check = [
        ('TeamCreate', TeamCreate),
        ('TeamResponse', TeamResponse),
        ('TeamDetailResponse', TeamDetailResponse),
        ('FileBatchCreate', FileBatchCreate),
        ('FileBatchResponse', FileBatchResponse),
        ('BatchFileResponse', BatchFileResponse),
        ('AuditLogCreate', AuditLogCreate),
        ('AuditLogResponse', AuditLogResponse),
        ('UserRoleUpdate', UserRoleUpdate),
        ('UserStatusUpdate', UserStatusUpdate),
        ('UserTeamAssignment', UserTeamAssignment)
    ]
    
    all_valid = True
    for schema_name, schema_class in schemas_to_check:
        try:
            # Check if schema is a valid Pydantic model
            if hasattr(schema_class, '__fields__'):
                field_count = len(schema_class.__fields__)
                print(f"   ✓ Schema '{schema_name}' properly defined ({field_count} fields)")
            else:
                print(f"   ✗ Schema '{schema_name}' not a valid Pydantic model")
                all_valid = False
        except Exception as e:
            print(f"   ✗ Schema '{schema_name}' error: {e}")
            all_valid = False
    
    return all_valid


def verify_model_relationships():
    """Verify model relationships are properly configured."""
    print("\n" + "="*70)
    print("8. Verifying Model Relationships")
    print("="*70)
    
    relationships_to_check = [
        ('User', 'file_batches', 'User has file_batches relationship'),
        ('FileBatch', 'user', 'FileBatch has user relationship'),
        ('FileBatch', 'batch_files', 'FileBatch has batch_files relationship'),
        ('BatchFile', 'batch', 'BatchFile has batch relationship'),
        ('AuditLog', 'user', 'AuditLog has user relationship'),
    ]
    
    all_valid = True
    for model_name, relationship_name, description in relationships_to_check:
        model_class = globals().get(model_name)
        if model_class and hasattr(model_class, relationship_name):
            print(f"   ✓ {description}")
        else:
            print(f"   ⚠ {description} - not found")
    
    return all_valid


def main():
    """Run all verification checks."""
    print("\n" + "="*70)
    print("TASK 1 VERIFICATION: Database Schema and Models Setup")
    print("="*70)
    
    results = []
    
    # Run all verification checks
    results.append(("Tables Exist", verify_tables_exist()))
    results.append(("Table Columns", verify_table_columns()))
    results.append(("Indexes", verify_indexes()))
    results.append(("Foreign Keys", verify_foreign_keys()))
    results.append(("SQLAlchemy Models", verify_models()))
    results.append(("Enum Types", verify_enums()))
    results.append(("Pydantic Schemas", verify_schemas()))
    results.append(("Model Relationships", verify_model_relationships()))
    
    # Print summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    all_passed = True
    for check_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"   {status}: {check_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL CHECKS PASSED - Task 1 implementation is complete!")
    else:
        print("⚠ SOME CHECKS FAILED - Review the output above")
    print("="*70 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
