# CodeNova Deployment Checklist

## Pre-Deployment Checklist

### Code Quality

- [ ] All tests passing (unit, integration, E2E)
- [ ] Code coverage meets minimum threshold (80% backend, 70% frontend)
- [ ] No critical security vulnerabilities (run `npm audit` and `safety check`)
- [ ] Code review completed and approved
- [ ] All linting errors resolved
- [ ] Documentation updated

### Database

- [ ] Database migrations tested in staging
- [ ] Migration rollback scripts tested
- [ ] Database backup created
- [ ] Migration verification scripts ready
- [ ] Database performance indexes reviewed
- [ ] Connection pool settings optimized

### Configuration

- [ ] Environment variables configured for production
- [ ] Secret keys generated and stored securely
- [ ] API keys validated and working
- [ ] CORS settings configured correctly
- [ ] Rate limiting configured
- [ ] File upload limits set appropriately

### Security

- [ ] SSL/TLS certificates installed and valid
- [ ] Security headers configured (HSTS, CSP, etc.)
- [ ] Authentication and authorization tested
- [ ] Password policies enforced
- [ ] API rate limiting enabled
- [ ] Input validation implemented
- [ ] SQL injection prevention verified
- [ ] XSS protection enabled
- [ ] CSRF protection enabled

### Infrastructure

- [ ] Server resources adequate (CPU, RAM, disk)
- [ ] Load balancer configured
- [ ] Auto-scaling rules set up
- [ ] CDN configured for static assets
- [ ] DNS records updated
- [ ] Firewall rules configured
- [ ] Backup systems in place
- [ ] Monitoring tools configured

### Dependencies

- [ ] All dependencies up to date
- [ ] No known vulnerabilities in dependencies
- [ ] Production dependencies only (no dev dependencies)
- [ ] Dependency licenses reviewed
- [ ] Package lock files committed

### Performance

- [ ] Load testing completed
- [ ] Performance benchmarks met
- [ ] Database queries optimized
- [ ] Caching strategy implemented
- [ ] Static assets minified and compressed
- [ ] Image optimization completed
- [ ] API response times acceptable

### Monitoring

- [ ] Application monitoring configured (Sentry, etc.)
- [ ] Server monitoring configured (CPU, RAM, disk)
- [ ] Log aggregation set up
- [ ] Alert rules configured
- [ ] Health check endpoints working
- [ ] Metrics collection enabled
- [ ] Dashboard created for key metrics

### Documentation

- [ ] API documentation complete and accurate
- [ ] User guide updated
- [ ] Admin guide updated
- [ ] Deployment documentation updated
- [ ] Runbook created for common issues
- [ ] Architecture diagrams updated

---

## Deployment Steps

### 1. Pre-Deployment

#### 1.1 Notify Stakeholders

- [ ] Send deployment notification email
- [ ] Update status page
- [ ] Schedule maintenance window (if needed)
- [ ] Notify support team

#### 1.2 Backup Current State

```bash
# Backup database
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup uploaded files
tar -czf uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz /var/codenova/uploads

# Backup configuration
cp .env .env.backup_$(date +%Y%m%d_%H%M%S)
```

- [ ] Database backup completed
- [ ] File storage backup completed
- [ ] Configuration backup completed
- [ ] Backup verification completed

#### 1.3 Prepare Deployment Package

```bash
# Pull latest code
git fetch origin
git checkout main
git pull origin main

# Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# Build frontend
npm run build

# Run tests
cd ../backend && pytest
cd ../frontend && npm test
```

- [ ] Code pulled from repository
- [ ] Dependencies installed
- [ ] Frontend built successfully
- [ ] Tests passing

### 2. Database Migration

#### 2.1 Test Migration in Staging

```bash
# Run migration in staging
python backend/migrations/run_migrations.py upgrade

# Verify migration
python backend/migrations/run_migrations.py verify

# Test application with new schema
python backend/app/main.py
```

- [ ] Migration tested in staging
- [ ] Migration verification passed
- [ ] Application working with new schema
- [ ] Rollback tested in staging

#### 2.2 Run Production Migration

```bash
# Set production environment
export ENVIRONMENT=production

# Run migration
python backend/migrations/run_migrations.py upgrade

# Verify migration
python backend/migrations/run_migrations.py verify
```

- [ ] Production migration completed
- [ ] Migration verification passed
- [ ] No errors in migration logs

### 3. Application Deployment

#### 3.1 Backend Deployment

```bash
# Stop current backend
sudo systemctl stop codenova-backend

# Deploy new code
sudo cp -r backend /opt/codenova/backend

# Update environment variables
sudo cp .env.production /opt/codenova/backend/.env

# Start backend
sudo systemctl start codenova-backend

# Check status
sudo systemctl status codenova-backend
```

- [ ] Backend stopped gracefully
- [ ] New code deployed
- [ ] Environment variables updated
- [ ] Backend started successfully
- [ ] Health check passing

#### 3.2 Frontend Deployment

```bash
# Build frontend
cd frontend && npm run build

# Deploy to CDN/web server
aws s3 sync dist/ s3://codenova-frontend/ --delete

# Invalidate CDN cache
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
```

- [ ] Frontend built successfully
- [ ] Static files deployed
- [ ] CDN cache invalidated
- [ ] Frontend accessible

#### 3.3 Background Workers

```bash
# Restart Celery workers
sudo systemctl restart codenova-worker

# Check worker status
celery -A app.core.celery_app inspect active
```

- [ ] Workers restarted
- [ ] Workers processing jobs
- [ ] No stuck jobs in queue

### 4. Post-Deployment Verification

#### 4.1 Smoke Tests

```bash
# Test health endpoint
curl https://api.codenova.com/health

# Test authentication
curl -X POST https://api.codenova.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test@example.com","password":"test"}'

# Test file upload
curl -X POST https://api.codenova.com/api/v1/files/upload-batch \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@test.py"

# Test analysis
curl https://api.codenova.com/api/v1/analysis/direct/history \
  -H "Authorization: Bearer $TOKEN"
```

- [ ] Health check passing
- [ ] Authentication working
- [ ] File upload working
- [ ] Analysis working
- [ ] Frontend loading correctly

#### 4.2 Critical Path Testing

- [ ] User can sign up
- [ ] User can log in
- [ ] User can upload files
- [ ] User can analyze code
- [ ] User can view results
- [ ] User can provide feedback
- [ ] Admin can access dashboard
- [ ] Admin can manage users
- [ ] Admin can manage teams
- [ ] Analytics displaying correctly

#### 4.3 Performance Verification

```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s https://api.codenova.com/health

# Check database connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity"

# Check Redis connections
redis-cli -u $REDIS_URL INFO clients
```

- [ ] API response times acceptable (< 200ms)
- [ ] Database connections healthy
- [ ] Redis connections healthy
- [ ] No memory leaks detected
- [ ] CPU usage normal

#### 4.4 Monitoring Verification

- [ ] Application logs flowing
- [ ] Error tracking working (Sentry)
- [ ] Metrics being collected
- [ ] Alerts configured and working
- [ ] Dashboard showing data

### 5. Rollback Plan (If Needed)

#### 5.1 Rollback Database

```bash
# Rollback migration
python backend/migrations/run_migrations.py downgrade

# Restore from backup if needed
psql $DATABASE_URL < backup_YYYYMMDD_HHMMSS.sql
```

#### 5.2 Rollback Application

```bash
# Revert to previous version
git checkout <previous-commit>

# Rebuild and redeploy
# ... (follow deployment steps)
```

#### 5.3 Rollback Checklist

- [ ] Database rolled back
- [ ] Application rolled back
- [ ] Frontend rolled back
- [ ] Verification tests passing
- [ ] Stakeholders notified

---

## Post-Deployment Tasks

### Immediate (Within 1 Hour)

- [ ] Monitor error rates
- [ ] Monitor response times
- [ ] Check user feedback
- [ ] Review logs for errors
- [ ] Verify all critical features working

### Short-term (Within 24 Hours)

- [ ] Review monitoring dashboards
- [ ] Check for any performance degradation
- [ ] Review user support tickets
- [ ] Analyze usage patterns
- [ ] Document any issues encountered

### Medium-term (Within 1 Week)

- [ ] Conduct post-deployment review meeting
- [ ] Update deployment documentation
- [ ] Address any minor issues
- [ ] Optimize based on production data
- [ ] Plan next deployment

---

## Rollback Triggers

Immediately rollback if:

- [ ] Critical functionality broken
- [ ] Data corruption detected
- [ ] Security vulnerability introduced
- [ ] Performance degradation > 50%
- [ ] Error rate > 5%
- [ ] Database migration failed
- [ ] Multiple user reports of issues

---

## Communication Plan

### Before Deployment

**Email Template:**
```
Subject: Scheduled Maintenance - CodeNova Platform

Dear CodeNova Users,

We will be performing scheduled maintenance on [DATE] from [START TIME] to [END TIME] [TIMEZONE].

During this time:
- The platform may be briefly unavailable
- In-progress analyses will be queued and completed after maintenance
- No data will be lost

New features in this release:
- [Feature 1]
- [Feature 2]
- [Feature 3]

We apologize for any inconvenience.

Best regards,
CodeNova Team
```

### During Deployment

**Status Page Update:**
```
Status: Maintenance in Progress
We are currently deploying updates to the CodeNova platform.
Expected completion: [TIME]
```

### After Deployment

**Email Template:**
```
Subject: Maintenance Complete - CodeNova Platform

Dear CodeNova Users,

The scheduled maintenance has been completed successfully.

The platform is now fully operational with the following new features:
- [Feature 1]
- [Feature 2]
- [Feature 3]

For more information, see our release notes: [LINK]

If you experience any issues, please contact support@codenova.com

Thank you for your patience.

Best regards,
CodeNova Team
```

---

## Emergency Contacts

### Deployment Team

- **Lead**: deployment-lead@codenova.com
- **Backend**: backend-team@codenova.com
- **Frontend**: frontend-team@codenova.com
- **DevOps**: devops@codenova.com
- **Database**: dba@codenova.com

### Escalation

- **Level 1**: Support Team
- **Level 2**: Engineering Team
- **Level 3**: Engineering Manager
- **Level 4**: CTO

### 24/7 Hotline

- **Phone**: +1-555-CODE-911
- **Slack**: #codenova-incidents
- **PagerDuty**: codenova-oncall

---

## Tools and Resources

### Deployment Tools

- **CI/CD**: GitHub Actions / Jenkins
- **Container Registry**: Docker Hub / AWS ECR
- **Infrastructure**: Terraform / CloudFormation
- **Monitoring**: Datadog / New Relic / Prometheus
- **Error Tracking**: Sentry
- **Log Aggregation**: ELK Stack / CloudWatch

### Useful Commands

```bash
# Check application status
sudo systemctl status codenova-backend
sudo systemctl status codenova-worker

# View logs
sudo journalctl -u codenova-backend -f
tail -f /var/log/codenova/app.log

# Check database
psql $DATABASE_URL -c "SELECT version()"
psql $DATABASE_URL -c "SELECT * FROM schema_migrations ORDER BY applied_at DESC LIMIT 5"

# Check Redis
redis-cli -u $REDIS_URL INFO
redis-cli -u $REDIS_URL DBSIZE

# Check disk space
df -h

# Check memory
free -h

# Check processes
ps aux | grep codenova
```

---

## Sign-off

### Deployment Approval

- [ ] **Engineering Lead**: _________________ Date: _______
- [ ] **QA Lead**: _________________ Date: _______
- [ ] **DevOps Lead**: _________________ Date: _______
- [ ] **Product Manager**: _________________ Date: _______

### Deployment Completion

- [ ] **Deployment Lead**: _________________ Date: _______
- [ ] **Verification Complete**: _________________ Date: _______
- [ ] **Stakeholders Notified**: _________________ Date: _______

---

## Notes

Use this section to document any issues, deviations from the plan, or lessons learned:

```
[Add notes here]
```

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-22 | Initial deployment checklist | DevOps Team |

---

**Remember**: When in doubt, don't deploy. It's better to delay than to cause an outage.

**Good luck with your deployment! 🚀**
