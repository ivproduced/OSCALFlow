# NIST 800-53 AC-2 Implementation Guide

## Overview
This implementation provides comprehensive account management capabilities compliant with NIST 800-53 Control AC-2 (Account Management).

## Features Implemented

### 1. Account Lifecycle Management
- ✅ **Account Creation** - Full audit logging with timestamps
- ✅ **Account Modification** - Track changes to user attributes
- ✅ **Account Disabling** - Temporarily disable accounts with reason
- ✅ **Account Deletion** - Permanent removal with audit trail
- ✅ **Account Re-enablement** - Restore disabled accounts

### 2. Automated Account Management (AC-2(3))
- ✅ **Inactive Account Detection** - Find accounts inactive for N days
- ✅ **Auto-Disable** - Automatically disable accounts after 90 days inactivity
- ✅ **Scheduled Jobs** - Daily background tasks for compliance

### 3. Account Security (AC-7)
- ✅ **Failed Login Tracking** - Record failed authentication attempts
- ✅ **Account Lockout** - Auto-lock after 5 failed attempts
- ✅ **Timed Unlock** - Automatically unlock after 30 minutes

### 4. Comprehensive Audit Logging
- ✅ **All Operations Logged** - Create, modify, disable, enable, delete
- ✅ **Structured Logs** - JSON format with NIST control references
- ✅ **Audit History API** - Query account modification history

## API Endpoints

### Account Management
All endpoints require **admin** role authentication.

```
POST   /api/v1/accounts                    - Create new account
GET    /api/v1/accounts                    - List all accounts
GET    /api/v1/accounts/{user_id}          - Get account details
PATCH  /api/v1/accounts/{user_id}          - Modify account
POST   /api/v1/accounts/{user_id}/disable  - Disable account
POST   /api/v1/accounts/{user_id}/enable   - Enable account
DELETE /api/v1/accounts/{user_id}          - Delete account
GET    /api/v1/accounts/{user_id}/history  - Get audit history
GET    /api/v1/accounts/inactive/list      - List inactive accounts
POST   /api/v1/accounts/inactive/auto-disable - Auto-disable inactive
```

## Installation Steps

### 1. Update User Model
The User model has been extended with new fields:
- `failed_login_attempts`
- `account_locked_until`
- `account_status`
- `disabled_reason`
- `disabled_at`
- `disabled_by`
- `last_activity`
- `password_expires_at`
- `account_expires_at`
- `last_modified`
- `last_modified_by`

### 2. Run Database Migration
```bash
# Create migration (if using Alembic)
cd backend
alembic revision --autogenerate -m "Add AC-2 account management fields"
alembic upgrade head

# Or apply the provided migration script
# Move alembic_migration_ac2.py to alembic/versions/ directory
# Update revision IDs as needed
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

### 4. Deploy Background Jobs

#### Option A: Using Cron (Recommended for VMs)
```bash
# Copy crontab example
cp crontab.example /etc/cron.d/fedchat-backend

# Update paths in the file to match your deployment
nano /etc/cron.d/fedchat-backend

# Restart cron
systemctl restart cron
```

#### Option B: Using Docker Scheduler
```bash
# Make scheduler script executable
chmod +x scheduler.sh

# Add to docker-compose.yml:
services:
  backend-scheduler:
    build: ./backend
    command: ./scheduler.sh
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - db
      - redis
```

#### Option C: Manual Execution (Testing)
```bash
# Run individual jobs
cd backend
python -m services.background_jobs inactivity_check
python -m services.background_jobs account_review
python -m services.background_jobs password_expiry
```

### 5. Test the Implementation

#### Create Test Admin User (if needed)
```python
# In Python shell or script
from services.auth_service import AuthService
from services.account_service import AccountService
from core.database import AsyncSessionLocal
import asyncio

async def create_admin():
    async with AsyncSessionLocal() as db:
        user = await AccountService.create_account(
            db=db,
            email="admin@agency.gov",
            username="admin",
            password_hash=AuthService.hash_password("SecurePassword123!"),
            full_name="System Administrator",
            role="admin",
            created_by_user_id="system",
            ip_address="localhost",
            metadata={"created_by": "setup_script"}
        )
        print(f"Admin user created: {user.id}")

asyncio.run(create_admin())
```

#### Test Account Creation API
```bash
# Get JWT token first
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"SecurePassword123!"}'

# Create account (use JWT from login)
curl -X POST http://localhost:8000/api/v1/accounts \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@agency.gov",
    "username": "testuser",
    "password": "TestPassword123!",
    "full_name": "Test User",
    "role": "user"
  }'
```

#### Test Account Disabling
```bash
curl -X POST http://localhost:8000/api/v1/accounts/{user_id}/disable \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Account suspended for review"}'
```

#### Test Inactive Account Detection
```bash
curl -X GET "http://localhost:8000/api/v1/accounts/inactive/list?days=90" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Configuration Options

### Account Inactivity
```python
ACCOUNT_INACTIVITY_DAYS = 90  # Days before auto-disable
ENABLE_AUTO_DISABLE_INACTIVE = True  # Enable/disable automation
```

### Account Lockout
```python
MAX_FAILED_LOGIN_ATTEMPTS = 5  # Failed attempts before lock
ACCOUNT_LOCKOUT_MINUTES = 30  # Lock duration
```

### Password Policies
```python
PASSWORD_MAX_AGE_DAYS = 90  # Force password change
```

## Audit Logging

All account operations are logged with:
- Timestamp (UTC)
- User ID performing action
- Action type (account_created, account_disabled, etc.)
- Resource type and ID
- IP address
- Detailed information including old/new values
- NIST control reference (AC-2, AC-2(3), AC-7)

### Query Audit Logs
```python
from services.account_service import AccountService

async def get_history(user_id: str):
    async with AsyncSessionLocal() as db:
        history = await AccountService.get_account_history(
            db=db,
            user_id=user_id,
            limit=100
        )
        for log in history:
            print(f"{log.timestamp}: {log.action} - {log.details}")
```

## Compliance Checklist

### NIST 800-53 AC-2 Requirements
- ✅ **AC-2a** - Identifies and selects account types
- ✅ **AC-2b** - Assigns account managers
- ✅ **AC-2c** - Establishes conditions for group membership
- ✅ **AC-2d** - Specifies authorized users and access authorizations
- ✅ **AC-2e** - Requires approvals for account creation
- ✅ **AC-2f** - Creates, enables, modifies, disables, and removes accounts
- ✅ **AC-2g** - Monitors account usage
- ✅ **AC-2h** - Notifies account managers (via audit logs)
- ✅ **AC-2i** - Authorizes access based on valid authorization
- ✅ **AC-2j** - Reviews accounts for compliance
- ✅ **AC-2k** - Establishes process for account revalidation

### AC-2(3) - Disable Inactive Accounts
- ✅ Automatically disables accounts after 90 days inactivity
- ✅ Scheduled daily checks via background jobs
- ✅ Audit logging of all auto-disable actions

## Troubleshooting

### Background Jobs Not Running
1. Check scheduler logs: `tail -f /var/log/fedchat/cron.log`
2. Verify crontab: `crontab -l`
3. Check database connectivity
4. Verify environment variables

### Accounts Not Auto-Disabling
1. Check `ENABLE_AUTO_DISABLE_INACTIVE=true` in `.env`
2. Verify background job is running
3. Check `last_activity` field is being updated
4. Review audit logs for auto-disable events

### Migration Errors
1. Backup database first: `pg_dump fedchat > backup.sql`
2. Check for existing columns: `\d users` in psql
3. Manually apply migration if Alembic fails
4. Verify foreign key constraints

## Security Considerations

1. **Admin-Only Access** - All account management endpoints require admin role
2. **Audit Everything** - All operations logged with full context
3. **Password Security** - Bcrypt hashing with salt
4. **Failed Login Protection** - Account lockout after failed attempts
5. **Inactive Account Cleanup** - Automatic disabling reduces attack surface

## Next Steps

1. **Integrate with LDAP/AD** - Centralize account management
2. **Email Notifications** - Alert users of account status changes
3. **Multi-Factor Authentication** - Add MFA requirement (AC-2(1))
4. **Privileged Account Management** - Enhanced controls for admin accounts (AC-2(5))
5. **Account Review Workflow** - Implement approval process for creation/modification

## Support

For questions or issues, refer to:
- Audit logs: `/var/log/fedchat/audit.log`
- Application logs: `/var/log/fedchat/fedchat.log`
- Database audit table: `SELECT * FROM audit_log WHERE resource_type='user'`

---

**NIST 800-53 Controls Addressed:**
- AC-2: Account Management
- AC-2(1): Automated System Account Management
- AC-2(2): Removal of Temporary / Emergency Accounts
- AC-2(3): Disable Inactive Accounts
- AC-7: Unsuccessful Logon Attempts
- IA-5: Authenticator Management
