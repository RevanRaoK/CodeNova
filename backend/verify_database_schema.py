"""
Comprehensive database schema verification script.
Checks all tables, columns, indexes, and relationships.
"""
import asyncio
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.users import User
from app.models.github_integration import GitHubRepository, PRAnalysis
from app.models.feedback import Issue
from app.models.team import Team

# Expected schema definition
EXPECTED_SCHEMA = {
    "users": {
        "columns": [
            "id", "email", "hashed_password", "full_name", "role",
            "is_active", "is_verified", "team_id", "preferences",
            "first_name", "last_name", "job_title", "bio",
            "programming_languages", "gemini_api_key", "oauth_provider",
            "oauth_id", "oauth_email_verified", "profile_picture_url",
            "last_login", "created_at", "updated_at"
        ],
        "nullable": [
            "hashed_password", "full_name", "is_active", "is_verified",
            "team_id", "first_name", "last_name", "job_title", "bio",
            "programming_languages", "gemini_api_key", "oauth_provider",
            "oauth_id", "oauth_email_verified", "profile_picture_url",
            "last_login", "created_at", "updated_at"
        ],
        "indexes": ["email"]
    },
    "teams": {
        "columns": [
            "id", "name", "admin_id", "settings", "created_at", "updated_at"
        ],
        "nullable": ["created_at", "updated_at"],
        "indexes": ["name"]
    },
    "github_repositories": {
        "columns": [
            "id", "user_id", "repo_url", "repo_name", "webhook_id",
            "webhook_secret", "is_active", "default_branch", "repository_settings",
            "access_token", "permissions", "created_at", "updated_at",
            "last_webhook_received"
        ],
        "nullable": [
            "webhook_id", "webhook_secret", "access_token", "last_webhook_received",
            "created_at", "updated_at"
        ],
        "indexes": ["user_id", "repo_name", "repo_url", "is_active", "created_at"]
    },
    "pr_analyses": {
        "columns": [
            "id", "repository_id", "pr_number", "pr_title", "pr_author",
            "head_sha", "base_sha", "head_branch", "base_branch",
            "analysis_results", "issues_found", "errors_count", "warnings_count",
            "issues_created", "comments_posted", "status", "started_at",
            "completed_at", "error_message", "created_at", "updated_at"
        ],
        "nullable": [
            "pr_title", "pr_author", "analysis_results", "started_at",
            "completed_at", "error_message", "created_at", "updated_at"
        ],
        "indexes": ["repository_id", "pr_number", "status"]
    },
    "issues": {
        "columns": [
            "id", "analysis_id", "pattern_type", "severity", "category",
            "location", "suggestion_text", "code_context", "original_code",
            "suggested_fix", "ast_node_type", "ast_metadata", "status",
            "confidence_score", "created_at", "updated_at", "resolved_at"
        ],
        "nullable": [
            "category", "original_code", "suggested_fix", "ast_node_type",
            "ast_metadata", "status", "confidence_score", "resolved_at",
            "created_at", "updated_at"
        ],
        "indexes": ["analysis_id", "pattern_type", "severity", "status"]
    }
}


async def verify_database_schema():
    """Verify the database schema matches expected structure."""
    
    print("=" * 80)
    print("DATABASE SCHEMA VERIFICATION")
    print("=" * 80)
    print()
    
    async with AsyncSessionLocal() as session:
        connection = await session.connection()

        # Use synchronous inspector calls via run_sync to stay within async context
        def get_tables(sync_conn):
            return inspect(sync_conn).get_table_names()

        tables = await connection.run_sync(get_tables)
        print(f"Found {len(tables)} tables in database:")
        for table in sorted(tables):
            print(f"  - {table}")
        print()
        
        # Track schema details for follow-up checks
        issues_found = []
        table_columns = {}

        for table_name, expected in EXPECTED_SCHEMA.items():
            print(f"\n{'=' * 80}")
            print(f"Checking table: {table_name}")
            print(f"{'=' * 80}")
            
            # Check if table exists
            if table_name not in tables:
                issue = f"❌ CRITICAL: Table '{table_name}' does not exist!"
                print(issue)
                issues_found.append(issue)
                continue
            
            print(f"✓ Table exists")
            
            # Get actual columns
            def get_columns(sync_conn, name):
                return inspect(sync_conn).get_columns(name)

            columns = await connection.run_sync(get_columns, table_name)
            column_names = [col['name'] for col in columns]
            column_details = {col['name']: col for col in columns}
            table_columns[table_name] = set(column_names)
            
            print(f"\nColumns ({len(column_names)}):")
            
            # Check expected columns
            missing_columns = []
            for expected_col in expected['columns']:
                if expected_col in column_names:
                    col_info = column_details[expected_col]
                    nullable = "NULL" if col_info['nullable'] else "NOT NULL"
                    col_type = str(col_info['type'])
                    print(f"  ✓ {expected_col:30} {col_type:20} {nullable}")
                else:
                    missing_columns.append(expected_col)
                    issue = f"  ❌ MISSING: {expected_col}"
                    print(issue)
                    issues_found.append(f"{table_name}.{expected_col} is missing")
            
            # Check for unexpected columns
            unexpected_columns = set(column_names) - set(expected['columns'])
            if unexpected_columns:
                print(f"\n  ⚠️  Unexpected columns (not in schema):")
                for col in unexpected_columns:
                    print(f"    - {col}")
            
            # Check nullable constraints
            print(f"\nNullable constraints:")
            for col_name in expected['columns']:
                if col_name not in column_names:
                    continue
                    
                col_info = column_details[col_name]
                should_be_nullable = col_name in expected.get('nullable', [])
                is_nullable = col_info['nullable']
                
                if should_be_nullable and not is_nullable:
                    issue = f"  ⚠️  {col_name} should be nullable but is NOT NULL"
                    print(issue)
                    issues_found.append(f"{table_name}.{col_name} nullable constraint mismatch")
                elif not should_be_nullable and is_nullable:
                    issue = f"  ⚠️  {col_name} should be NOT NULL but is nullable"
                    print(issue)
                    issues_found.append(f"{table_name}.{col_name} nullable constraint mismatch")
                else:
                    status = "NULL" if is_nullable else "NOT NULL"
                    print(f"  ✓ {col_name:30} {status}")
            
            # Check indexes
            def get_indexes(sync_conn, name):
                return inspect(sync_conn).get_indexes(name)

            indexes = await connection.run_sync(get_indexes, table_name)
            print(f"\nIndexes ({len(indexes)}):")
            for idx in indexes:
                cols = ', '.join(idx['column_names'])
                unique = "UNIQUE" if idx.get('unique') else ""
                print(f"  - {idx['name']:40} ({cols}) {unique}")
            
            # Check foreign keys
            def get_foreign_keys(sync_conn, name):
                return inspect(sync_conn).get_foreign_keys(name)

            foreign_keys = await connection.run_sync(get_foreign_keys, table_name)
            if foreign_keys:
                print(f"\nForeign Keys ({len(foreign_keys)}):")
                for fk in foreign_keys:
                    print(f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
        
        # Summary
        print(f"\n\n{'=' * 80}")
        print("VERIFICATION SUMMARY")
        print(f"{'=' * 80}")
        
        if issues_found:
            print(f"\n❌ Found {len(issues_found)} issues:\n")
            for i, issue in enumerate(issues_found, 1):
                print(f"{i}. {issue}")
            print("\n⚠️  Database schema has issues that need to be fixed!")
        else:
            print("\n✓ All checks passed! Database schema is correct.")
        
        # Check for orphaned records
        print(f"\n\n{'=' * 80}")
        print("CHECKING FOR DATA ISSUES")
        print(f"{'=' * 80}")
        
        # Check for issues without corresponding direct analysis
        issue_cols = table_columns.get("issues", set())
        if "analysis_id" in issue_cols:
            result = await session.execute(text("""
                SELECT COUNT(*) as count 
                FROM issues 
                WHERE analysis_id NOT IN (SELECT id FROM direct_analyses)
            """))
            orphaned_issues = result.scalar()
            if orphaned_issues > 0:
                print(f"⚠️  Found {orphaned_issues} orphaned issues (analysis_id doesn't exist)")
                issues_found.append(f"{orphaned_issues} orphaned issues")
            else:
                print("✓ No orphaned issues")
        else:
            print("⚠️  Skipping orphaned issues check (column 'analysis_id' not found)")
        
        # Check for pr_analyses without repository
        pr_analysis_cols = table_columns.get("pr_analyses", set())
        if "repository_id" in pr_analysis_cols:
            result = await session.execute(text("""
                SELECT COUNT(*) as count 
                FROM pr_analyses 
                WHERE repository_id NOT IN (SELECT id FROM github_repositories)
            """))
            orphaned_analyses = result.scalar()
            if orphaned_analyses > 0:
                print(f"⚠️  Found {orphaned_analyses} orphaned pr_analyses (repository_id doesn't exist)")
                issues_found.append(f"{orphaned_analyses} orphaned pr_analyses")
            else:
                print("✓ No orphaned pr_analyses")
        else:
            print("⚠️  Skipping orphaned pr_analysis check (column 'repository_id' not found)")
        
        # Check for duplicate issue IDs (should never happen with PK constraint)
        result = await session.execute(text("""
            SELECT id, COUNT(*) as count
            FROM issues
            GROUP BY id
            HAVING COUNT(*) > 1
        """))
        duplicate_issues = result.fetchall()
        if duplicate_issues:
            print(f"⚠️  Found {len(duplicate_issues)} duplicate issue IDs")
            issues_found.append(f"{len(duplicate_issues)} duplicate issue IDs")
        else:
            print("✓ No duplicate issue IDs")
        
        # Count records in each table
        print(f"\n\n{'=' * 80}")
        print("RECORD COUNTS")
        print(f"{'=' * 80}\n")
        
        for table in sorted(tables):
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"  {table:30} {count:>10} records")
        
        print(f"\n{'=' * 80}")
        if issues_found:
            print(f"❌ VERIFICATION FAILED - {len(issues_found)} issues found")
        else:
            print("✓ VERIFICATION PASSED - Database is healthy")
        print(f"{'=' * 80}\n")
        
        return len(issues_found) == 0


if __name__ == "__main__":
    success = asyncio.run(verify_database_schema())
    exit(0 if success else 1)
