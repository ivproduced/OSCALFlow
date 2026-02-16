# NIST 800-53 AU-2 Quick Start Guide
## Event Logging Implementation

### 🚀 Quick Setup (5 Minutes)

#### 1. Verify Dependencies (Already Installed)
```bash
grep -E "structlog|python-json-logger" requirements.txt
# ✅ Should show both packages already present
```

#### 2. Create Log Directory
```bash
# Create log directory
sudo mkdir -p /var/log/fedchat
sudo chown -R $USER:$USER /var/log/fedchat
sudo chmod 750 /var/log/fedchat

# For Docker/local development
mkdir -p logs
chmod 750 logs
```

#### 3. Update Environment Variables
Add to your `.env` file:
```bash
# Audit & Logging
AUDIT_LOG_PATH=/var/log/fedchat/audit.log
LOG_FORMAT=json
LOG_LEVEL=INFO
AUDIT_LOG_LEVEL=comprehensive
```

For local development, use relative path:
```bash
AUDIT_LOG_PATH=./logs/audit.log
```

#### 4. Test the Implementation
```bash
# Start the application
python main.py

# In another terminal, make a test request
curl http://localhost:8000/health

# Check logs were created
ls -la logs/
cat logs/security.log
```

---

### 📝 Basic Usage Examples

#### Import the Logger
```python
from services.security_events import (
    log_login_success,
    log_login_failure,
    log_access_denied,
    SecurityEventLogger,
    EventType,
    EventOutcome
)
```

#### Log Authentication
```python
# Success
log_login_success("john.doe", "user-id-123", "192.168.1.100")

# Failure
log_login_failure("john.doe", "192.168.1.100", "Invalid password")
```

#### Log Authorization
```python
# Access denied
log_access_denied(
    user_id="user-id-123",
    resource="admin_panel",
    action="access",
    reason="Insufficient permissions"
)
```

#### Log Data Access
```python
# Data read
SecurityEventLogger.log_data_access(
    operation="read",
    resource="conversations",
    user_id="user-id-123",
    outcome=EventOutcome.SUCCESS,
    record_count=10
)
```

---

### 🔧 Docker Configuration

#### Update docker-compose.yml
```yaml
services:
  backend:
    build: ./backend
    volumes:
      - ./logs:/var/log/fedchat  # Mount logs directory
    environment:
      - AUDIT_LOG_PATH=/var/log/fedchat/audit.log
      - LOG_FORMAT=json
```

#### Update Dockerfile
```dockerfile
# Create log directory
RUN mkdir -p /var/log/fedchat && \
    chown -R appuser:appuser /var/log/fedchat && \
    chmod 750 /var/log/fedchat

# Set log directory as volume
VOLUME ["/var/log/fedchat"]
```

---

### 📊 View Logs

#### Real-time Monitoring
```bash
# Watch security events
tail -f logs/security.log | jq '.'

# Watch all logs
tail -f logs/audit.log | jq '.'
```

#### Filter by Event Type
```bash
# Failed logins
grep "auth.login.failure" logs/security.log | jq '.'

# Access denied
grep "authz.access.denied" logs/security.log | jq '.'

# Data operations
grep "data\." logs/security.log | jq '.'
```

#### Count Events
```bash
# Count by event type
grep -o '"event_type":"[^"]*"' logs/security.log | sort | uniq -c | sort -rn

# Count by outcome
grep -o '"outcome":"[^"]*"' logs/security.log | sort | uniq -c
```

---

### ✅ Integration Checklist

Copy this checklist for each new endpoint:

```python
# [ ] Import security event logger
# [ ] Extract source_ip from request
# [ ] Log operation with appropriate event_type
# [ ] Include user_id if authenticated
# [ ] Set correct outcome (success/failure/denied)
# [ ] Add relevant details dictionary
# [ ] Verify no sensitive data logged
```

---

### 🧪 Test Your Implementation

Create `test_au2.py`:
```python
"""Test AU-2 implementation"""
from services.security_events import *

# Test 1: Login success
log_login_success("test_user", "user-123", "127.0.0.1")
print("✅ Login success logged")

# Test 2: Login failure
log_login_failure("test_user", "127.0.0.1", "Invalid password")
print("✅ Login failure logged")

# Test 3: Access denied
log_access_denied("user-123", "admin", "access", "Not admin")
print("✅ Access denied logged")

# Test 4: Data access
SecurityEventLogger.log_data_access(
    operation="read",
    resource="conversations",
    user_id="user-123",
    outcome=EventOutcome.SUCCESS,
    record_count=5
)
print("✅ Data access logged")

print("\n📝 Check logs/security.log for entries")
```

Run the test:
```bash
python test_au2.py
cat logs/security.log | jq '.'
```

---

### 🎯 Common Integration Points

#### 1. Authentication Endpoints
```python
# After successful login
log_login_success(username, str(user.id), source_ip)

# After failed login
log_login_failure(username, source_ip, reason)
```

#### 2. Protected Endpoints
```python
# When access is denied
log_access_denied(str(user.id), resource, action, reason)
```

#### 3. Data Operations
```python
# After any CRUD operation
SecurityEventLogger.log_data_access(
    operation="read|create|update|delete",
    resource="resource_name",
    user_id=str(user.id),
    outcome=EventOutcome.SUCCESS
)
```

#### 4. Admin Operations
```python
# After account management
SecurityEventLogger.log_account_management(
    event_type=EventType.ACCOUNT_MODIFIED,
    target_user_id=target_id,
    target_username=target_username,
    admin_user_id=admin_id,
    outcome=EventOutcome.SUCCESS
)
```

---

### 📋 Verification Steps

1. **Start Application**
   ```bash
   python main.py
   ```

2. **Generate Test Events**
   ```bash
   # Test health endpoint
   curl http://localhost:8000/health
   
   # Test login (will fail without valid creds)
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"test","password":"test"}'
   ```

3. **Verify Logs Created**
   ```bash
   ls -la logs/
   # Should see: audit.log, security.log
   ```

4. **Check Log Format**
   ```bash
   cat logs/security.log | jq '.'
   # Should see JSON formatted events
   ```

5. **Verify Required Fields**
   ```bash
   cat logs/security.log | jq '.event_type, .outcome, .timestamp'
   # Should show event_type, outcome, timestamp for each entry
   ```

---

### 🔥 Troubleshooting

#### Logs not being created?
```bash
# Check directory exists and is writable
ls -la logs/
mkdir -p logs
chmod 750 logs

# Check environment variable
echo $AUDIT_LOG_PATH
# or in Python:
python -c "from core.config import settings; print(settings.AUDIT_LOG_PATH)"
```

#### Import errors?
```bash
# Verify security_events.py exists
ls -la services/security_events.py

# Check for syntax errors
python -m py_compile services/security_events.py
```

#### No events in logs?
```bash
# Check if logging is working at all
python -c "from services.security_events import log_login_success; log_login_success('test', 'id', '127.0.0.1')"

# Check log file
cat logs/security.log
```

---

### 📚 Next Steps

1. **Review Implementation Guide**: See `AU2_IMPLEMENTATION_GUIDE.md` for comprehensive documentation
2. **Review Examples**: See `EXAMPLE_AU2_USAGE.py` for code examples
3. **Configure Log Rotation**: Set up logrotate for production
4. **Integrate with SIEM**: Configure log forwarding to your SIEM system
5. **Set Up Monitoring**: Configure alerts for security events

---

### 🆘 Need Help?

- **Full Documentation**: `AU2_IMPLEMENTATION_GUIDE.md`
- **Code Examples**: `EXAMPLE_AU2_USAGE.py`
- **NIST 800-53 AU-2**: https://nvd.nist.gov/800-53/Rev4/control/AU-2

---

### ✅ Success Criteria

Your AU-2 implementation is complete when:

- [x] SecurityEventLogger service is created
- [x] Log directory is created and writable
- [x] Environment variables are configured
- [x] Application starts without errors
- [x] Test events are logged successfully
- [x] Logs are in JSON format
- [x] Required fields are present (event_type, outcome, timestamp)
- [x] Authentication events are logged
- [x] Authorization events are logged
- [x] Data access events are logged

**Congratulations! You've successfully implemented NIST 800-53 AU-2! 🎉**
