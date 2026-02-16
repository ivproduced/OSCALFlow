# NIST 800-53 AC-2 Implementation - Quick Start Guide

## Summary

This implementation adds comprehensive NIST 800-53 AC-2 (Account Management) compliance to the FedChat backend. All features are production-ready and include full audit logging.

## What Was Implemented

### ✅ Core Features
1. **Account Lifecycle Management** - Create, modify, disable, enable, delete with audit logs
2. **Automated Inactive Account Detection** - Find and auto-disable accounts after 90 days
3. **Account Lockout** - Auto-lock after 5 failed login attempts
4. **Comprehensive Audit Logging** - All operations logged with NIST control references
5. **Background Jobs** - Scheduled tasks for compliance automation
6. **Admin API Endpoints** - Full RESTful API for account management

### 📁 Files Created
- `services/account_service.py` - Account lifecycle management service
- `api/v1/accounts.py` - RESTful API endpoints
- `services/background_jobs.py` - Scheduled compliance tasks
- `alembic_migration_ac2.py` - Database migration script
- `crontab.example` - Cron configuration
- `scheduler.sh` - Docker scheduler script
- `AC2_IMPLEMENTATION.md` - Complete implementation guide
- `AC2_DEPLOYMENT_CHECKLIST.md` - Deployment checklist

### 📝 Files Modified
- `models/__init__.py` - Added AC-2 fields to User model
- `core/config.py` - Added AC-2 configuration settings
- `main.py` - Registered account management routes
- `services/auth_service.py` - Integrated account lockout

## Quick Start (5 Steps)

### 1. Install Dependencies (Already Done)
All required dependencies are already in `requirements.txt`:
- FastAPI, SQLAlchemy, Alembic
- passlib (bcrypt), python-jose (JWT)
- structlog (audit logging)

### 2. Run Database Migration

```bash
cd backend

# Option A: Using Alembic (recommended)
# 1. Move migration to alembic versions directory
mv alembic_migration_ac2.py alembic/versions/001_ac2_account_management.py

# 2. Edit the file and set down_revision to your last migration ID
# down_revision = 'previous_migration_id'  # Update this line

# 3. Run migration
alembic upgrade head

# Option B: Manual SQL (if Alembic not set up)
psql -d your_database << EOF
ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0 NOT NULL;
ALTER TABLE users ADD COLUMN account_locked_until TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN account_status VARCHAR(50) DEFAULT 'active' NOT NULL;
ALTER TABLE users ADD COLUMN disabled_reason TEXT;
ALTER TABLE users ADD COLUMN disabled_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN disabled_by UUID;
ALTER TABLE users ADD COLUMN last_activity TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN password_expires_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN account_expires_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN last_modified TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN last_modified_by UUID;
CREATE INDEX ix_users_account_status ON users(account_status);
CREATE INDEX ix_users_last_activity ON users(last_activity);
EOF
```

### 3. Update Environment Variables

Add to your `.env` file:

```bash
# AC-2 Account Management Settings
ACCOUNT_INACTIVITY_DAYS=90
MAX_FAILED_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=30
PASSWORD_MAX_AGE_DAYS=90
ACCOUNT_REVIEW_DAYS=365
ENABLE_AUTO_DISABLE_INACTIVE=true
```

### 4. Restart Application

```bash
# If using Docker
docker-compose restart backend

# If using systemd
systemctl restart fedchat-backend

# If running directly
pkill -f "python.*main.py"
python main.py
```

### 5. Set Up Background Jobs

**Option A: Using Cron (VMs/Bare Metal)**
```bash
# Copy and configure crontab
sudo cp crontab.example /etc/cron.d/fedchat-backend

# Update paths in the file
sudo nano /etc/cron.d/fedchat-backend
# Change /app to your actual installation path

# Restart cron
sudo systemctl restart cron

# Verify
sudo tail -f /var/log/fedchat/cron.log
```

**Option B: Using Docker**
```bash
# Make scheduler executable
chmod +x scheduler.sh

# Add to docker-compose.yml:
# (See AC2_IMPLEMENTATION.md for full example)

# Start scheduler
docker-compose up -d backend-scheduler
docker-compose logs -f backend-scheduler
```

## Testing the Implementation

### Create Admin User (if needed)
```bash
cd backend
python << EOF
import asyncio
from services.auth_service import AuthService
from services.account_service import AccountService
from core.database import AsyncSessionLocal

async def create_admin():
    async with AsyncSessionLocal() as db:
        user = await AccountService.create_account(
            db=db,
            email="admin@agency.gov",
            username="admin",
            password_hash=AuthService.hash_password("ChangeMe123!"),
            full_name="System Administrator",
            role="admin",
            created_by_user_id="system",
            ip_address="localhost",
            metadata={"initial_setup": True}
        )
        print(f"Admin created: {user.username} (ID: {user.id})")

asyncio.run(create_admin())
EOF
```

### Test API Endpoints

```bash
# 1. Login as admin
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"ChangeMe123!"}' \
  | jq -r .access_token)

# 2. Create test account
curl -X POST http://localhost:8000/api/v1/accounts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@agency.gov",
    "username": "testuser",
    "password": "TestPass123!",
    "full_name": "Test User",
    "role": "user"
  }'

# 3. List all accounts
curl -X GET http://localhost:8000/api/v1/accounts \
  -H "Authorization: Bearer $TOKEN"

# 4. List inactive accounts
curl -X GET "http://localhost:8000/api/v1/accounts/inactive/list?days=90" \
  -H "Authorization: Bearer $TOKEN"

# 5. View API documentation
# Visit: http://localhost:8000/api/docs
```

### Test Background Jobs Manually

```bash
cd backend

# Test inactivity check
python -m services.background_jobs inactivity_check

# Test account review
python -m services.background_jobs account_review

# Test password expiry check
python -m services.background_jobs password_expiry
```

## Verification Checklist

After deployment, verify:

- [ ] Application starts without errors
- [ ] New database columns exist
- [ ] API endpoints accessible at `/api/v1/accounts`
- [ ] Admin can create/modify/disable accounts
- [ ] Non-admin users denied access to account management
- [ ] Account creation logged to audit table
- [ ] Failed login attempts tracked
- [ ] Account locks after 5 failed attempts
- [ ] Background jobs run on schedule
- [ ] Audit logs contain NIST control references

## API Documentation

Once deployed, view interactive API docs:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

Navigate to "Account Management" section to see all endpoints.

## Key Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `ACCOUNT_INACTIVITY_DAYS` | 90 | Days before auto-disable |
| `MAX_FAILED_LOGIN_ATTEMPTS` | 5 | Failed logins before lockout |
| `ACCOUNT_LOCKOUT_MINUTES` | 30 | Account lock duration |
| `PASSWORD_MAX_AGE_DAYS` | 90 | Password expiration period |
| `ENABLE_AUTO_DISABLE_INACTIVE` | true | Auto-disable inactive accounts |

## Monitoring

### Check Audit Logs
```bash
# View recent account operations
tail -f /var/log/fedchat/audit.log | grep account_

# Query audit database
psql -d fedchat -c \
  "SELECT timestamp, action, details->>'username', details->>'nist_control' 
   FROM audit_log 
   WHERE action LIKE 'account_%' 
   ORDER BY timestamp DESC 
   LIMIT 20;"
```

### Monitor Background Jobs
```bash
# Check cron execution
tail -f /var/log/fedchat/cron.log

# Check for errors
grep -i error /var/log/fedchat/cron.log
```

## Troubleshooting

### Database Migration Fails
```bash
# Check current database schema
psql -d fedchat -c "\d users"

# If columns already exist, skip migration
# If missing, apply manually (see Step 2 above)
```

### Background Jobs Not Running
```bash
# Verify cron service
systemctl status cron

# Check crontab entries
crontab -l

# Run job manually to test
cd backend && python -m services.background_jobs inactivity_check
```

### API Returns 500 Error
```bash
# Check application logs
tail -f /var/log/fedchat/fedchat.log

# Verify database connection
psql -d fedchat -c "SELECT 1"

# Check imports
cd backend && python -c "from services.account_service import AccountService; print('OK')"
```

## Next Steps

1. **Review Documentation** - Read `AC2_IMPLEMENTATION.md` for full details
2. **Test in Dev** - Thoroughly test before production deployment
3. **Follow Checklist** - Use `AC2_DEPLOYMENT_CHECKLIST.md` for production
4. **Train Admins** - Educate team on new account management features
5. **Monitor** - Watch audit logs and background jobs for first week
6. **Compliance Review** - Schedule review with security/compliance team

## NIST 800-53 Controls Implemented

- ✅ **AC-2** - Account Management
- ✅ **AC-2(1)** - Automated System Account Management
- ✅ **AC-2(2)** - Removal of Temporary / Emergency Accounts
- ✅ **AC-2(3)** - Disable Inactive Accounts
- ✅ **AC-7** - Unsuccessful Logon Attempts
- ✅ **IA-5** - Authenticator Management (partial)

## Support

- Full Guide: `AC2_IMPLEMENTATION.md`
- Deployment: `AC2_DEPLOYMENT_CHECKLIST.md`
- Code: `services/account_service.py`, `api/v1/accounts.py`
- Issues: Check audit logs and application logs

---

**Ready to deploy?** Follow the 5 steps above, then use `AC2_DEPLOYMENT_CHECKLIST.md` for production deployment.
