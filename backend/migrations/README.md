# Database Migrations

This directory contains database migration scripts for the CodeNova platform.

## Overview

Migrations are used to:
- Create new database tables
- Modify existing table structures
- Add or remove columns
- Create indexes for performance
- Maintain database schema version history

## Migration Files

### Current Migrations

- **migration_001_platform_enhancements.py** - Platform enhancements migration
  - Creates Teams, FileBatches, BatchFiles, and AuditLogs tables
  - Adds team_id, role, is_active to Users table
  - Adds filename, batch_id to DirectAnalyses table
  - Creates necessary indexes

### Migration Runner

- **run_migrations.py** - Script to manage migrations
  - Apply migrations
  - Rollback migrations
  - Check migration status
  - Verify database schema

## Usage

### Check Migration Status

```bash
python backend/migrations/run_migrations.py status
```

This shows:
- Which migrations have been applied
- Which migrations are pending
- When each migration was applied

### Apply Migrations

```bash
# Apply all pending migrations
python backend/migrations/run_migrations.py upgrade
```

This will:
1. Check for pending migrations
2. Apply each migration in order
3. Mark migrations as applied
4. Verify the changes

### Rollback Last Migration

```bash
# Rollback the most recent migration
python backend/migrations/run_migrations.py downgrade
```

This will:
1. Identify the last applied migration
2. Run the downgrade function
3. Remove the migration from applied list
4. Verify the rollback

### Verify Database Schema

```bash
# Verify current database schema
python backend/migrations/run_migrations.py verify
```

This checks:
- All expected tables exist
- Required columns are present
- Indexes are created

## Migration Workflow

### Development Environment

1. **Check status**:
   ```bash
   python backend/migrations/run_migrations.py status
   ```

2. **Apply migrations**:
   ```bash
   python backend/migrations/run_migrations.py upgrade
   ```

3. **Verify**:
   ```bash
   python backend/migrations/run_migrations.py verify
   ```

4. **Test application**:
   ```bash
   python backend/app/main.py
   ```

### Staging Environment

1. **Backup database**:
   ```bash
   pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > backup_$(date +%Y%m%d).sql
   ```

2. **Check status**:
   ```bash
   python backend/migrations/run_migrations.py status
   ```

3. **Apply migrations**:
   ```bash
   python backend/migrations/run_migrations.py upgrade
   ```

4. **Verify**:
   ```bash
   python backend/migrations/run_migrations.py verify
   ```

5. **Test application thoroughly**

6. **Test rollback** (optional but recommended):
   ```bash
   python backend/migrations/run_migrations.py downgrade
   python backend/migrations/run_migrations.py upgrade
   ```

### Production Environment

1. **Schedule maintenance window**

2. **Backup database**:
   ```bash
   pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

3. **Verify backup**:
   ```bash
   pg_restore --list backup_*.sql
   ```

4. **Check migration status**:
   ```bash
   python backend/migrations/run_migrations.py status
   ```

5. **Apply migrations**:
   ```bash
   python backend/migrations/run_migrations.py upgrade
   ```

6. **Verify schema**:
   ```bash
   python backend/migrations/run_migrations.py verify
   ```

7. **Start application**:
   ```bash
   sudo systemctl start codenova-backend
   ```

8. **Verify application health**:
   ```bash
   curl http://localhost:8000/health
   ```

9. **Monitor logs**:
   ```bash
   tail -f /var/log/codenova/app.log
   ```

## Creating New Migrations

### Migration Template

```python
"""
Migration XXX: Description
- What this migration does
- Tables affected
- Columns added/removed

Created: YYYY-MM-DD
"""

from alembic import op
import sqlalchemy as sa

revision = 'XXX_migration_name'
down_revision = 'previous_migration'

def upgrade():
    """Apply migration changes."""
    # Add your upgrade logic here
    pass

def downgrade():
    """Rollback migration changes."""
    # Add your downgrade logic here
    pass
```

### Best Practices

1. **Always include downgrade**: Every migration must be reversible

2. **Test thoroughly**: Test both upgrade and downgrade in development

3. **Use transactions**: Wrap changes in transactions when possible

4. **Add indexes**: Create indexes for foreign keys and frequently queried columns

5. **Document changes**: Include clear comments and docstrings

6. **Backup first**: Always backup before running migrations in production

7. **Verify after**: Always verify the schema after migration

## Migration Tracking

Migrations are tracked in the `schema_migrations` table:

```sql
CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(100) NOT NULL UNIQUE,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);
```

## Troubleshooting

### Migration Failed

If a migration fails:

1. **Check error message**:
   ```bash
   # Review the error output
   ```

2. **Check database state**:
   ```bash
   psql $DATABASE_URL -c "\dt"  # List tables
   psql $DATABASE_URL -c "\d table_name"  # Describe table
   ```

3. **Rollback if needed**:
   ```bash
   python backend/migrations/run_migrations.py downgrade
   ```

4. **Restore from backup** (if necessary):
   ```bash
   psql $DATABASE_URL < backup_YYYYMMDD.sql
   ```

### Migration Stuck

If a migration appears stuck:

1. **Check for locks**:
   ```sql
   SELECT * FROM pg_locks WHERE NOT granted;
   ```

2. **Check active queries**:
   ```sql
   SELECT * FROM pg_stat_activity WHERE state = 'active';
   ```

3. **Kill blocking queries** (if safe):
   ```sql
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = <blocking_pid>;
   ```

### Schema Out of Sync

If schema doesn't match expected state:

1. **Check migration status**:
   ```bash
   python backend/migrations/run_migrations.py status
   ```

2. **Verify schema**:
   ```bash
   python backend/migrations/run_migrations.py verify
   ```

3. **Compare with expected**:
   ```bash
   psql $DATABASE_URL -c "\d+ table_name"
   ```

4. **Manual fix** (if needed):
   ```sql
   -- Add missing column
   ALTER TABLE table_name ADD COLUMN column_name TYPE;
   
   -- Create missing index
   CREATE INDEX idx_name ON table_name(column_name);
   ```

5. **Update migration tracking**:
   ```sql
   INSERT INTO schema_migrations (version, description) 
   VALUES ('XXX_migration_name', 'Manual fix applied');
   ```

## Safety Checks

### Before Running Migrations

- [ ] Database backup created
- [ ] Backup verified
- [ ] Migration tested in staging
- [ ] Rollback tested
- [ ] Maintenance window scheduled
- [ ] Team notified

### After Running Migrations

- [ ] Migration completed successfully
- [ ] Schema verification passed
- [ ] Application started successfully
- [ ] Health check passing
- [ ] No errors in logs
- [ ] Critical features tested

## Common Operations

### Add a Column

```python
def upgrade():
    op.add_column('table_name', 
        sa.Column('column_name', sa.String(255), nullable=True)
    )

def downgrade():
    op.drop_column('table_name', 'column_name')
```

### Create a Table

```python
def upgrade():
    op.create_table(
        'table_name',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow)
    )

def downgrade():
    op.drop_table('table_name')
```

### Add an Index

```python
def upgrade():
    op.create_index('idx_table_column', 'table_name', ['column_name'])

def downgrade():
    op.drop_index('idx_table_column', 'table_name')
```

### Add a Foreign Key

```python
def upgrade():
    op.add_column('table_name',
        sa.Column('foreign_id', sa.Integer, sa.ForeignKey('other_table.id'))
    )

def downgrade():
    op.drop_column('table_name', 'foreign_id')
```

## Resources

- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Alembic Documentation**: https://alembic.sqlalchemy.org/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/

## Support

For migration issues:
- Email: dba@codenova.com
- Slack: #codenova-database
- Emergency: +1-555-CODE-911

## Version History

| Migration | Version | Date | Description |
|-----------|---------|------|-------------|
| 001 | 1.0 | 2025-10-22 | Platform enhancements |

---

**Remember**: Always backup before running migrations in production!
