"""
Migration Runner Script

This script manages database migrations for the CodeNova platform.
It provides commands to apply, rollback, and verify migrations.

Usage:
    python run_migrations.py upgrade    # Apply all pending migrations
    python run_migrations.py downgrade  # Rollback last migration
    python run_migrations.py status     # Show migration status
    python run_migrations.py verify     # Verify current state
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


class MigrationRunner:
    """Manages database migrations."""
    
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        self.migrations_dir = Path(__file__).parent
        self.ensure_migration_table()
    
    def ensure_migration_table(self):
        """Create migration tracking table if it doesn't exist."""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(100) NOT NULL UNIQUE,
                    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """))
            conn.commit()
    
    def get_applied_migrations(self):
        """Get list of applied migrations."""
        with self.engine.connect() as conn:
            result = conn.execute(text(
                "SELECT version, applied_at, description FROM schema_migrations ORDER BY applied_at"
            ))
            return [dict(row._mapping) for row in result]
    
    def get_available_migrations(self):
        """Get list of available migration files."""
        migrations = []
        for file in sorted(self.migrations_dir.glob("migration_*.py")):
            if file.name == "migration_template.py":
                continue
            
            # Extract version from filename
            version = file.stem.replace("migration_", "")
            migrations.append({
                'version': version,
                'file': file,
                'name': file.stem
            })
        
        return migrations
    
    def get_pending_migrations(self):
        """Get list of migrations that haven't been applied."""
        applied = {m['version'] for m in self.get_applied_migrations()}
        available = self.get_available_migrations()
        
        return [m for m in available if m['version'] not in applied]
    
    def mark_migration_applied(self, version, description=""):
        """Mark a migration as applied."""
        with self.engine.connect() as conn:
            conn.execute(
                text("INSERT INTO schema_migrations (version, description) VALUES (:version, :description)"),
                {"version": version, "description": description}
            )
            conn.commit()
    
    def mark_migration_reverted(self, version):
        """Mark a migration as reverted."""
        with self.engine.connect() as conn:
            conn.execute(
                text("DELETE FROM schema_migrations WHERE version = :version"),
                {"version": version}
            )
            conn.commit()
    
    def run_migration_upgrade(self, migration):
        """Run a migration's upgrade function."""
        print(f"\n{'='*60}")
        print(f"Applying migration: {migration['version']}")
        print(f"{'='*60}\n")
        
        # Import and run the migration
        import importlib.util
        spec = importlib.util.spec_from_file_location(migration['name'], migration['file'])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        try:
            # Run upgrade
            module.upgrade()
            
            # Mark as applied
            description = getattr(module, '__doc__', '').strip().split('\n')[0]
            self.mark_migration_applied(migration['version'], description)
            
            print(f"\n✓ Migration {migration['version']} applied successfully!")
            return True
            
        except Exception as e:
            print(f"\n✗ Migration {migration['version']} failed: {str(e)}")
            return False
    
    def run_migration_downgrade(self, migration):
        """Run a migration's downgrade function."""
        print(f"\n{'='*60}")
        print(f"Rolling back migration: {migration['version']}")
        print(f"{'='*60}\n")
        
        # Import and run the migration
        import importlib.util
        spec = importlib.util.spec_from_file_location(migration['name'], migration['file'])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        try:
            # Run downgrade
            module.downgrade()
            
            # Mark as reverted
            self.mark_migration_reverted(migration['version'])
            
            print(f"\n✓ Migration {migration['version']} rolled back successfully!")
            return True
            
        except Exception as e:
            print(f"\n✗ Migration {migration['version']} rollback failed: {str(e)}")
            return False
    
    def upgrade(self):
        """Apply all pending migrations."""
        pending = self.get_pending_migrations()
        
        if not pending:
            print("✓ No pending migrations. Database is up to date!")
            return True
        
        print(f"\nFound {len(pending)} pending migration(s):")
        for m in pending:
            print(f"  - {m['version']}")
        
        print("\nApplying migrations...\n")
        
        success = True
        for migration in pending:
            if not self.run_migration_upgrade(migration):
                success = False
                break
        
        if success:
            print("\n" + "="*60)
            print("✓ All migrations applied successfully!")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("✗ Migration failed. Database may be in inconsistent state.")
            print("  Please review errors and fix manually if needed.")
            print("="*60)
        
        return success
    
    def downgrade(self):
        """Rollback the last applied migration."""
        applied = self.get_applied_migrations()
        
        if not applied:
            print("✓ No migrations to rollback. Database is empty!")
            return True
        
        last_migration = applied[-1]
        version = last_migration['version']
        
        # Find the migration file
        available = self.get_available_migrations()
        migration = next((m for m in available if m['version'] == version), None)
        
        if not migration:
            print(f"✗ Migration file for version {version} not found!")
            return False
        
        print(f"\nRolling back last migration: {version}")
        
        success = self.run_migration_downgrade(migration)
        
        if success:
            print("\n" + "="*60)
            print("✓ Migration rolled back successfully!")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("✗ Rollback failed. Database may be in inconsistent state.")
            print("  Please review errors and fix manually if needed.")
            print("="*60)
        
        return success
    
    def status(self):
        """Show migration status."""
        print("\n" + "="*60)
        print("Migration Status")
        print("="*60 + "\n")
        
        applied = self.get_applied_migrations()
        available = self.get_available_migrations()
        pending = self.get_pending_migrations()
        
        print(f"Database: {settings.DATABASE_URL.split('@')[-1]}")
        print(f"Total migrations: {len(available)}")
        print(f"Applied: {len(applied)}")
        print(f"Pending: {len(pending)}")
        
        if applied:
            print("\n" + "-"*60)
            print("Applied Migrations:")
            print("-"*60)
            for m in applied:
                print(f"  ✓ {m['version']}")
                print(f"    Applied: {m['applied_at']}")
                if m['description']:
                    print(f"    Description: {m['description']}")
                print()
        
        if pending:
            print("-"*60)
            print("Pending Migrations:")
            print("-"*60)
            for m in pending:
                print(f"  ○ {m['version']}")
            print()
        
        print("="*60)
    
    def verify(self):
        """Verify database schema matches expected state."""
        print("\n" + "="*60)
        print("Verifying Database Schema")
        print("="*60 + "\n")
        
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        
        # Expected tables after all migrations
        expected_tables = [
            'users',
            'teams',
            'direct_analyses',
            'file_batches',
            'batch_files',
            'audit_logs',
            'schema_migrations'
        ]
        
        print("Checking tables...")
        all_good = True
        
        for table in expected_tables:
            if table in tables:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} (missing)")
                all_good = False
        
        # Check for unexpected tables
        unexpected = set(tables) - set(expected_tables)
        if unexpected:
            print("\nUnexpected tables found:")
            for table in unexpected:
                print(f"  ? {table}")
        
        print("\n" + "="*60)
        if all_good:
            print("✓ Database schema verification passed!")
        else:
            print("✗ Database schema verification failed!")
        print("="*60)
        
        return all_good


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    runner = MigrationRunner()
    
    try:
        if command == 'upgrade':
            success = runner.upgrade()
        elif command == 'downgrade':
            success = runner.downgrade()
        elif command == 'status':
            runner.status()
            success = True
        elif command == 'verify':
            success = runner.verify()
        else:
            print(f"Unknown command: {command}")
            print(__doc__)
            sys.exit(1)
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
