# AC-2 Implementation Deployment Checklist

## Pre-Deployment
- [ ] Review all code changes
- [ ] Test in development environment
- [ ] Backup production database
- [ ] Document rollback procedure
- [ ] Schedule maintenance window

## Database Migration
- [ ] Review migration script `alembic_migration_ac2.py`
- [ ] Move to `alembic/versions/` directory
- [ ] Update revision IDs in migration
- [ ] Test migration on dev database
- [ ] Run migration on production:
  ```bash
  cd backend
  alembic upgrade head
  ```
- [ ] Verify new columns exist:
  ```sql
  \d users
  ```

## Configuration
- [ ] Add AC-2 settings to `.env`:
  ```bash
  ACCOUNT_INACTIVITY_DAYS=90
  MAX_FAILED_LOGIN_ATTEMPTS=5
  ACCOUNT_LOCKOUT_MINUTES=30
  PASSWORD_MAX_AGE_DAYS=90
  ACCOUNT_REVIEW_DAYS=365
  ENABLE_AUTO_DISABLE_INACTIVE=true
  ```
- [ ] Restart application to load new config
- [ ] Verify settings: `GET /api/v1/admin/config`

## Code Deployment
- [ ] Deploy new files:
  - `services/account_service.py`
  - `services/background_jobs.py`
  - `api/v1/accounts.py`
- [ ] Update existing files:
  - `models/__init__.py` (User model)
  - `core/config.py` (AC-2 settings)
  - `main.py` (register routes)
  - `services/auth_service.py` (integrate account lockout)
- [ ] Restart application services

## Background Jobs Setup

### Option 1: Cron (Recommended)
- [ ] Copy `crontab.example` to `/etc/cron.d/fedchat-backend`
- [ ] Update paths in crontab file
- [ ] Set correct permissions: `chmod 644 /etc/cron.d/fedchat-backend`
- [ ] Restart cron: `systemctl restart cron`
- [ ] Verify cron entries: `crontab -l`

### Option 2: Docker Scheduler
- [ ] Make `scheduler.sh` executable: `chmod +x scheduler.sh`
- [ ] Add scheduler service to `docker-compose.yml`
- [ ] Start scheduler container: `docker-compose up -d backend-scheduler`
- [ ] Check logs: `docker-compose logs -f backend-scheduler`

## Testing

### 1. Test Account Creation
```bash
curl -X POST http://localhost:8000/api/v1/accounts \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@agency.gov",
    "username": "testuser",
    "password": "TestPass123!",
    "role": "user"
  }'
```
- [ ] Account created successfully
- [ ] Audit log entry created
- [ ] New fields populated correctly

### 2. Test Account Modification
```bash
curl -X PATCH http://localhost:8000/api/v1/accounts/{user_id} \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Updated Name"}'
```
- [ ] Account modified successfully
- [ ] Audit log shows old and new values
- [ ] `last_modified` updated

### 3. Test Account Disabling
```bash
curl -X POST http://localhost:8000/api/v1/accounts/{user_id}/disable \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Test disable"}'
```
- [ ] Account disabled successfully
- [ ] User cannot log in
- [ ] Audit log records reason

### 4. Test Failed Login Lockout
```bash
# Attempt 6 failed logins
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser","password":"wrongpass"}'
done
```
- [ ] Account locked after 5 attempts
- [ ] Audit log shows lockout event
- [ ] User cannot login with correct password while locked

### 5. Test Inactive Account Detection
```bash
curl -X GET "http://localhost:8000/api/v1/accounts/inactive/list?days=90" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
- [ ] Returns list of inactive accounts
- [ ] Correct calculation of inactivity period

### 6. Test Background Jobs
```bash
# Run manually first
cd backend
python -m services.background_jobs inactivity_check
python -m services.background_jobs account_review
python -m services.background_jobs password_expiry
```
- [ ] Inactivity check runs without errors
- [ ] Account review generates report
- [ ] Password expiry check completes
- [ ] Logs written correctly

### 7. Test Audit History
```bash
curl -X GET http://localhost:8000/api/v1/accounts/{user_id}/history \
  -H "Authorization: Bearer ADMIN_TOKEN"
```
- [ ] Returns complete audit trail
- [ ] Includes all account operations
- [ ] Timestamps and details correct

## Monitoring

### Verify Audit Logs
```bash
# Check structured logs
tail -f /var/log/fedchat/audit.log | grep account_

# Check database audit table
psql -d fedchat -c "SELECT * FROM audit_log WHERE action LIKE 'account_%' ORDER BY timestamp DESC LIMIT 10;"
```
- [ ] All account operations logged
- [ ] NIST control references present
- [ ] No PII in logs

### Monitor Background Jobs
```bash
# Check cron logs
tail -f /var/log/fedchat/cron.log

# Check for scheduler errors
grep -i error /var/log/fedchat/cron.log
```
- [ ] Jobs running on schedule
- [ ] No errors in logs
- [ ] Success messages present

## Security Verification

- [ ] Only admins can access account management endpoints
- [ ] Test non-admin user access (should be denied)
- [ ] Passwords are hashed (bcrypt)
- [ ] Failed login attempts tracked
- [ ] Account lockout working
- [ ] Audit logs capture all required information
- [ ] No sensitive data exposed in API responses

## Documentation

- [ ] Update internal wiki/docs
- [ ] Train administrators on new features
- [ ] Document escalation procedures
- [ ] Update runbooks
- [ ] Share `AC2_IMPLEMENTATION.md` with team

## Compliance Verification

- [ ] Review NIST 800-53 AC-2 requirements
- [ ] Verify all sub-controls implemented
- [ ] Document evidence for assessors:
  - Audit log samples
  - API documentation
  - Configuration screenshots
  - Job scheduler proof
- [ ] Schedule compliance review meeting

## Post-Deployment

- [ ] Monitor application for 24 hours
- [ ] Check background jobs run successfully
- [ ] Review audit logs for anomalies
- [ ] Verify no performance degradation
- [ ] Collect feedback from administrators
- [ ] Document lessons learned

## Rollback Plan (If Needed)

1. Stop application
2. Revert code changes:
   ```bash
   git revert HEAD
   ```
3. Downgrade database:
   ```bash
   alembic downgrade -1
   ```
4. Remove cron jobs:
   ```bash
   rm /etc/cron.d/fedchat-backend
   systemctl restart cron
   ```
5. Restart application
6. Verify rollback successful
7. Investigate issues before retry

## Sign-Off

- [ ] Technical Lead: _________________ Date: _______
- [ ] Security Officer: ______________ Date: _______
- [ ] Compliance Officer: ____________ Date: _______
- [ ] Project Manager: _______________ Date: _______

---

**Notes:**
- Complete checklist items in order
- Mark completion with timestamp
- Document any issues encountered
- Keep this checklist for audit purposes
