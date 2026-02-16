# NIST 800-53 Control AU-2 Implementation Guide
# Event Logging for FedChat Backend

## 🎯 Implementation Overview

This guide documents the implementation of **NIST 800-53 Control AU-2 (Event Logging)** for the FedChat Backend application. The implementation provides comprehensive security event logging with structured JSON formatting to meet FISMA Moderate requirements.

---

## 📋 Control Requirements

**AU-2: Event Logging**
- **Description**: Identify the types of events the system is capable of logging in support of the audit function
- **Guidance**: 
  - Use structured logging (JSON format)
  - Log security-relevant events
  - Include comprehensive context (timestamp, user ID, action, resource, outcome, source IP)

---

## ✅ Implementation Status

### Components Created/Modified

1. **NEW: `services/security_events.py`** - Centralized security event logging service
2. **MODIFIED: `services/auth_service.py`** - Enhanced authentication logging
3. **MODIFIED: `middleware/audit.py`** - Improved user context extraction
4. **MODIFIED: `api/dependencies.py`** - Authorization failure logging
5. **MODIFIED: `core/logging.py`** - Security logger configuration

### Dependencies (Already Installed)

```bash
structlog==24.1.0          # Structured logging framework
python-json-logger==2.0.7  # JSON log formatting
```

✅ **No new dependencies required** - all necessary packages already in `requirements.txt`

---

## 🔑 Event Types Logged

### 1. Authentication Events (`EventType.AUTH_*`)
- ✅ Login success/failure
- ✅ Logout
- ✅ Session timeout
- ✅ Token creation/expiration/revocation
- ✅ MFA success/failure

### 2. Authorization Events (`EventType.AUTHZ_*`)
- ✅ Access granted/denied
- ✅ Permission changes
- ✅ Role assignment/revocation

### 3. Account Management (`EventType.ACCOUNT_*`)
- ✅ Account created/modified/deleted
- ✅ Account enabled/disabled/locked/unlocked
- ✅ Password changed/reset

### 4. Data Access (`EventType.DATA_*`)
- ✅ Read/Create/Update/Delete operations
- ✅ Data export/import

### 5. Configuration Changes (`EventType.CONFIG_*`)
- ✅ Configuration modifications
- ✅ Config export/import

### 6. Security Events (`EventType.SECURITY_*`)
- ✅ Policy violations
- ✅ Rate limit exceeded
- ✅ Suspicious activity
- ✅ Intrusion detection

### 7. File Operations (`EventType.FILE_*`)
- ✅ File upload/download/delete

### 8. API Key Operations (`EventType.API_KEY_*`)
- ✅ API key created/revoked/used

---

## 📊 Log Format

All security events are logged in **structured JSON format** with the following fields:

```json
{
  "event_type": "auth.login.success",
  "outcome": "success",
  "timestamp": "2024-02-16T02:53:28.984Z",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john.doe",
  "source_ip": "192.168.1.100",
  "resource": "api/v1/chat",
  "action": "authenticate",
  "session_id": "abc123...",
  "details": {
    "auth_method": "password"
  }
}
```

### Required Fields (Always Present)
- `event_type` - Type of event (see EventType enum)
- `outcome` - success/failure/error/denied
- `timestamp` - ISO 8601 UTC timestamp

### Optional Fields (Context-Dependent)
- `user_id` - User identifier (if authenticated)
- `username` - Username (if available)
- `source_ip` - Source IP address
- `resource` - Resource accessed/modified
- `action` - Action performed
- `session_id` - Session identifier
- `reason` - Reason for failure/denial
- `details` - Additional event-specific details

---

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Audit & Logging Configuration
AUDIT_LOG_LEVEL=comprehensive          # basic/detailed/comprehensive
AUDIT_LOG_PATH=/var/log/fedchat/audit.log
AUDIT_RETENTION_DAYS=2555              # 7 years for FISMA compliance
LOG_LEVEL=INFO
LOG_FORMAT=json                        # json/text
```

### Log File Locations

```bash
/var/log/fedchat/audit.log     # HTTP request/response audit logs
/var/log/fedchat/security.log  # Security event logs
```

### Create Log Directory

```bash
# Create log directory with proper permissions
sudo mkdir -p /var/log/fedchat
sudo chown -R appuser:appuser /var/log/fedchat
sudo chmod 750 /var/log/fedchat

# For Docker environments, mount as volume:
# docker-compose.yml:
#   volumes:
#     - ./logs:/var/log/fedchat
```

---

## 💻 Usage Examples

### Example 1: Log Authentication Success

```python
from services.security_events import log_login_success

# In your auth endpoint
log_login_success(
    username="john.doe",
    user_id="550e8400-e29b-41d4-a716-446655440000",
    source_ip="192.168.1.100"
)
```

### Example 2: Log Authentication Failure

```python
from services.security_events import log_login_failure

log_login_failure(
    username="john.doe",
    source_ip="192.168.1.100",
    reason="Invalid password"
)
```

### Example 3: Log Authorization Denial

```python
from services.security_events import log_access_denied

log_access_denied(
    user_id=str(current_user.id),
    resource="admin_api",
    action="access",
    reason="Insufficient permissions",
    source_ip=request.client.host
)
```

### Example 4: Log Data Access

```python
from services.security_events import SecurityEventLogger, EventOutcome

SecurityEventLogger.log_data_access(
    operation="read",
    resource="conversations",
    user_id=str(current_user.id),
    outcome=EventOutcome.SUCCESS,
    source_ip=request.client.host,
    record_count=10
)
```

### Example 5: Log Account Management

```python
from services.security_events import SecurityEventLogger, EventType, EventOutcome

SecurityEventLogger.log_account_management(
    event_type=EventType.ACCOUNT_DISABLED,
    target_user_id=target_user_id,
    target_username=target_username,
    admin_user_id=str(admin_user.id),
    outcome=EventOutcome.SUCCESS,
    source_ip=request.client.host,
    changes={"reason": "Account inactive for 90 days"}
)
```

### Example 6: Log Configuration Change

```python
from services.security_events import SecurityEventLogger

SecurityEventLogger.log_config_change(
    config_key="RATE_LIMIT_REQUESTS_PER_MINUTE",
    old_value=30,
    new_value=60,
    user_id=str(admin_user.id),
    source_ip=request.client.host
)
```

### Example 7: Log Security Event

```python
from services.security_events import SecurityEventLogger, EventType

SecurityEventLogger.log_security_event(
    event_type=EventType.SECURITY_RATE_LIMIT_EXCEEDED,
    severity="high",
    description="User exceeded rate limit 5 times in 1 minute",
    user_id=str(user.id),
    source_ip=request.client.host,
    details={"attempts": 5, "period": "1 minute"}
)
```

---

## 🚀 Implementation Steps for New Code

### Step 1: Import Security Event Logger

```python
from services.security_events import (
    SecurityEventLogger,
    EventType,
    EventOutcome,
    log_login_success,
    log_login_failure,
    log_access_denied
)
```

### Step 2: Add Logging to Critical Operations

**Authentication:**
```python
# After successful authentication
log_login_success(username, user_id, source_ip)

# After failed authentication
log_login_failure(username, source_ip, "Invalid credentials")
```

**Authorization:**
```python
# When access is denied
log_access_denied(user_id, resource, action, reason, source_ip)
```

**Data Operations:**
```python
# After data access
SecurityEventLogger.log_data_access(
    operation="read",  # read/create/update/delete/export/import
    resource="resource_name",
    user_id=user_id,
    outcome=EventOutcome.SUCCESS,
    source_ip=source_ip,
    record_count=count
)
```

**Account Management:**
```python
# After account changes
SecurityEventLogger.log_account_management(
    event_type=EventType.ACCOUNT_MODIFIED,
    target_user_id=target_user_id,
    target_username=target_username,
    admin_user_id=admin_user_id,
    outcome=EventOutcome.SUCCESS,
    source_ip=source_ip,
    changes={"field": "value"}
)
```

---

## 🔍 Querying Logs

### View Recent Security Events

```bash
# View last 50 security events
tail -n 50 /var/log/fedchat/security.log | jq '.'

# Filter by event type
grep "auth.login.failure" /var/log/fedchat/security.log | jq '.'

# Filter by user
grep "user_id.*550e8400" /var/log/fedchat/security.log | jq '.'

# View failed authentication attempts
grep "auth.login.failure" /var/log/fedchat/security.log | jq '.username, .source_ip, .timestamp'
```

### Search for Authorization Failures

```bash
grep "authz.access.denied" /var/log/fedchat/security.log | jq '.'
```

### Monitor in Real-Time

```bash
tail -f /var/log/fedchat/security.log | jq '.'
```

---

## 📈 Integration with SIEM

### Splunk Integration

```bash
# Install Splunk Universal Forwarder
# Configure inputs.conf:

[monitor:///var/log/fedchat/*.log]
disabled = false
sourcetype = _json
index = fedchat_security
```

### ELK Stack Integration

```yaml
# Filebeat configuration
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/fedchat/*.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "fedchat-security-%{+yyyy.MM.dd}"
```

### CloudWatch Logs (AWS)

```python
# Install AWS CloudWatch agent
# Configure /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json:

{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/fedchat/security.log",
            "log_group_name": "/fedchat/security",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
```

---

## 🧪 Testing

### Test Security Event Logging

```bash
cd /path/to/backend

# Run pytest with security event tests
pytest tests/test_security_events.py -v

# Test authentication logging
pytest tests/test_auth_service.py::test_login_success_logging -v
pytest tests/test_auth_service.py::test_login_failure_logging -v
```

### Manual Testing

```python
# Create a test script: test_logging.py
from services.security_events import log_login_success, log_login_failure

# Test successful login
log_login_success("test_user", "test-id-123", "127.0.0.1")

# Test failed login
log_login_failure("test_user", "127.0.0.1", "Invalid password")

print("Check /var/log/fedchat/security.log for events")
```

Run the test:
```bash
python test_logging.py
cat /var/log/fedchat/security.log
```

---

## 📚 Best Practices

### 1. **Always Log Security-Relevant Events**
- Authentication attempts (success/failure)
- Authorization decisions (granted/denied)
- Account management operations
- Data access (especially sensitive data)
- Configuration changes
- Security policy violations

### 2. **Include Comprehensive Context**
- User ID and username
- Source IP address
- Resource accessed
- Action performed
- Outcome (success/failure/denied)
- Timestamp (UTC)
- Session ID (if available)

### 3. **Protect Sensitive Data**
- Never log passwords, tokens, or API keys
- Redact PII when necessary
- Use `[REDACTED]` for sensitive fields

### 4. **Use Appropriate Log Levels**
- `INFO` - Successful operations
- `WARNING` - Access denied, suspicious activity
- `ERROR` - Failed operations, exceptions

### 5. **Monitor and Alert**
- Set up alerts for multiple failed login attempts
- Monitor for unusual access patterns
- Alert on privilege escalation attempts

---

## 🔒 Security Considerations

1. **Log File Permissions**
   ```bash
   chmod 640 /var/log/fedchat/*.log
   chown appuser:appuser /var/log/fedchat/*.log
   ```

2. **Log Rotation**
   ```bash
   # /etc/logrotate.d/fedchat
   /var/log/fedchat/*.log {
       daily
       rotate 2555  # 7 years retention
       compress
       delaycompress
       notifempty
       create 0640 appuser appuser
       sharedscripts
   }
   ```

3. **Secure Transmission**
   - Use TLS for log forwarding to SIEM
   - Encrypt logs at rest if required

4. **Access Control**
   - Restrict log file access to authorized personnel
   - Implement audit trail for log access

---

## 📋 Compliance Mapping

| NIST 800-53 Control | Implementation | Status |
|---------------------|----------------|--------|
| AU-2 (Event Logging) | SecurityEventLogger with 60+ event types | ✅ Complete |
| AU-3 (Content of Audit Records) | Structured JSON with all required fields | ✅ Complete |
| AU-4 (Audit Storage) | File-based with 7-year retention | ✅ Complete |
| AU-5 (Audit Failure Response) | Exception handling and fallback logging | ✅ Complete |
| AU-6 (Audit Review) | JSON format for easy parsing/analysis | ✅ Complete |
| AU-8 (Time Stamps) | ISO 8601 UTC timestamps | ✅ Complete |
| AU-9 (Protection of Audit Information) | File permissions and rotation | ✅ Complete |
| AU-12 (Audit Generation) | Comprehensive event coverage | ✅ Complete |

---

## 🆘 Troubleshooting

### Issue: Logs not being written

**Solution:**
```bash
# Check directory permissions
ls -la /var/log/fedchat/

# Check if directory exists
sudo mkdir -p /var/log/fedchat
sudo chown -R appuser:appuser /var/log/fedchat

# Check disk space
df -h /var/log
```

### Issue: Duplicate log entries

**Solution:**
- Ensure `propagate = False` in logger configuration
- Check for duplicate handler registration

### Issue: Missing user context in logs

**Solution:**
- Verify JWT token is being passed in Authorization header
- Check `_get_user_id()` method in AuditMiddleware
- Ensure user is authenticated before logging

---

## 📞 Support and Maintenance

### Log Monitoring Commands

```bash
# Check log file size
du -sh /var/log/fedchat/*.log

# Count events by type
grep -o '"event_type":"[^"]*"' /var/log/fedchat/security.log | sort | uniq -c | sort -rn

# Find failed authentication attempts from specific IP
grep "auth.login.failure" /var/log/fedchat/security.log | grep "192.168.1.100"

# Summarize events by outcome
grep -o '"outcome":"[^"]*"' /var/log/fedchat/security.log | sort | uniq -c
```

### Performance Considerations

- Asynchronous logging for high-throughput scenarios
- Log sampling for very high-volume events
- Regular log rotation to prevent disk exhaustion
- Index logs in SIEM for fast searching

---

## 📝 Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2024-02-16 | 1.0.0 | Initial AU-2 implementation |

---

## ✅ Validation Checklist

- [x] SecurityEventLogger service created
- [x] 60+ event types defined
- [x] Authentication events logged (success/failure)
- [x] Authorization events logged (granted/denied)
- [x] Account management events logged
- [x] Data access events logged
- [x] Configuration change events logged
- [x] Security event logging implemented
- [x] Structured JSON logging format
- [x] UTC timestamps in ISO 8601 format
- [x] User context captured (ID, IP, session)
- [x] Resource and action details included
- [x] Sensitive data redaction in place
- [x] Log file permissions configured
- [x] Log rotation configured
- [x] Integration points documented
- [x] Testing procedures documented
- [x] SIEM integration guidance provided

---

## 🎓 Additional Resources

- [NIST 800-53 AU-2 Control](https://nvd.nist.gov/800-53/Rev4/control/AU-2)
- [structlog Documentation](https://www.structlog.org/)
- [Python JSON Logger](https://github.com/madzak/python-json-logger)
- [FISMA Audit Requirements](https://www.dhs.gov/fisma)

---

**Document Version:** 1.0.0  
**Last Updated:** 2024-02-16  
**Author:** FedChat Security Team  
**Classification:** FISMA Moderate
