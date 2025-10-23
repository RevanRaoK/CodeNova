# CodeNova Quick Reference Guide

## 🚀 Quick Start

### For Users
```bash
1. Sign up at https://codenova.com
2. Upload a file or paste code
3. Review analysis results
4. Provide feedback on suggestions
```

### For Admins
```bash
1. Log in with admin account
2. Navigate to Admin Dashboard
3. Manage users and teams
4. Monitor platform analytics
```

### For Developers
```bash
1. Get API token: POST /api/v1/auth/login
2. Upload file: POST /api/v1/files/upload-batch
3. Get results: GET /api/v1/analysis/direct/{id}
4. Submit feedback: POST /api/v1/feedback/submit
```

## 📚 Documentation Links

| Document | Purpose | Link |
|----------|---------|------|
| User Guide | End-user features | [USER_GUIDE.md](USER_GUIDE.md) |
| Admin Guide | Platform management | [ADMIN_GUIDE.md](ADMIN_GUIDE.md) |
| API Docs | API reference | [API_DOCUMENTATION.md](../backend/docs/API_DOCUMENTATION.md) |
| Deployment | Deployment procedures | [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) |
| Configuration | Environment setup | [ENVIRONMENT_CONFIGURATION.md](../backend/docs/ENVIRONMENT_CONFIGURATION.md) |

## 🔑 Common Commands

### Database Migrations
```bash
# Check status
python backend/migrations/run_migrations.py status

# Apply migrations
python backend/migrations/run_migrations.py upgrade

# Rollback
python backend/migrations/run_migrations.py downgrade

# Verify
python backend/migrations/run_migrations.py verify
```

### Application Management
```bash
# Start backend
python backend/app/main.py

# Start workers
celery -A app.core.celery_app worker -l info

# Run tests
pytest backend/tests/

# Check health
curl http://localhost:8000/health
```

### Database Operations
```bash
# Backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql

# Connect
psql $DATABASE_URL
```

## 🌐 API Endpoints

### Authentication
```bash
POST /api/v1/auth/login
POST /api/v1/auth/signup
POST /api/v1/auth/refresh
```

### File Upload
```bash
POST /api/v1/files/upload-batch
GET /api/v1/files/batch/{batch_id}/status
GET /api/v1/files/list
```

### Analysis
```bash
POST /api/v1/analysis/analyze-code
GET /api/v1/analysis/direct/history
GET /api/v1/analysis/direct/{id}
GET /api/v1/analysis/direct/{id}/issues
WS /api/v1/ws/analysis/{id}
```

### Feedback
```bash
POST /api/v1/feedback/submit
GET /api/v1/feedback/history
```

### Analytics
```bash
GET /api/v1/analytics/issue-trends
GET /api/v1/analytics/criticality-distribution
```

### Admin - Teams
```bash
POST /api/v1/admin/teams
GET /api/v1/admin/teams
GET /api/v1/admin/teams/{id}
PUT /api/v1/admin/teams/{id}
DELETE /api/v1/admin/teams/{id}
```

### Admin - Users
```bash
GET /api/v1/admin/users
GET /api/v1/admin/users/{id}
PUT /api/v1/admin/users/{id}/role
PUT /api/v1/admin/users/{id}/status
PUT /api/v1/admin/users/{id}/team/{team_id}
```

### Admin - Analytics
```bash
GET /api/v1/admin/analytics/platform
GET /api/v1/admin/analytics/global-trends
GET /api/v1/admin/analytics/team-comparison
GET /api/v1/admin/analytics/all-reviews
GET /api/v1/admin/analytics/all-feedback
```

### Admin - Audit Logs
```bash
GET /api/v1/admin/audit-logs
```

## 🔧 Configuration

### Required Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-api-key
```

### Optional Environment Variables
```bash
DEBUG=false
LOG_LEVEL=INFO
STORAGE_TYPE=local
SMTP_ENABLED=false
SENTRY_ENABLED=false
```

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Can't connect to database | Check DATABASE_URL, verify PostgreSQL is running |
| Can't upload files | Check file size (<5MB), verify file type is supported |
| Analysis stuck | Check worker status, restart workers if needed |
| API returns 401 | Check token, re-authenticate if expired |
| Migration failed | Check error, rollback if needed, restore from backup |

### Quick Fixes
```bash
# Restart backend
sudo systemctl restart codenova-backend

# Restart workers
sudo systemctl restart codenova-worker

# Clear Redis cache
redis-cli -u $REDIS_URL FLUSHDB

# Check logs
tail -f /var/log/codenova/app.log
```

## 📊 Monitoring

### Health Checks
```bash
# Application health
curl http://localhost:8000/health

# Database health
psql $DATABASE_URL -c "SELECT 1"

# Redis health
redis-cli -u $REDIS_URL PING
```

### Key Metrics
- API response time: < 200ms
- Error rate: < 1%
- Queue processing time: < 30s
- Database connections: < 80% of pool

## 🔐 Security

### Best Practices
- Use strong passwords (12+ characters)
- Enable 2FA for admin accounts
- Rotate secrets every 90 days
- Review audit logs weekly
- Keep dependencies updated

### Emergency Contacts
- Security issues: security@codenova.com
- System down: emergency@codenova.com
- 24/7 hotline: +1-555-CODE-911

## 📝 Useful SQL Queries

```sql
-- Check migration status
SELECT * FROM schema_migrations ORDER BY applied_at DESC;

-- Count users by role
SELECT role, COUNT(*) FROM users GROUP BY role;

-- Recent analyses
SELECT * FROM direct_analyses ORDER BY created_at DESC LIMIT 10;

-- Active teams
SELECT t.name, COUNT(u.id) as members 
FROM teams t 
LEFT JOIN users u ON t.id = u.team_id 
GROUP BY t.id, t.name;

-- Audit log summary
SELECT action, COUNT(*) 
FROM audit_logs 
WHERE timestamp > NOW() - INTERVAL '7 days' 
GROUP BY action;
```

## 🎯 Performance Tips

### For Users
- Keep files under 5MB
- Use batch upload for multiple files
- Provide feedback to improve AI accuracy
- Check visualizations regularly

### For Admins
- Monitor queue status daily
- Review audit logs weekly
- Keep teams organized (5-10 members)
- Set up alerts for critical issues

### For Developers
- Implement retry logic
- Cache responses when appropriate
- Use WebSockets for real-time updates
- Monitor rate limits

## 📞 Support

| Type | Contact |
|------|---------|
| Users | support@codenova.com |
| Admins | admin-support@codenova.com |
| Developers | api-support@codenova.com |
| Emergency | +1-555-CODE-911 |

## 🔗 Resources

- Documentation: https://docs.codenova.com
- API Reference: https://api.codenova.com/docs
- Status Page: https://status.codenova.com
- Community Forum: https://forum.codenova.com
- GitHub: https://github.com/codenova

---

**Last Updated**: 2025-10-22  
**Version**: 1.0

For detailed information, see the full documentation in the [docs](.) directory.
