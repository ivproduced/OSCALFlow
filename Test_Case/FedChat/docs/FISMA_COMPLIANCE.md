# FISMA Moderate Compliance Guide

## Overview

This system is designed to meet FISMA Moderate security controls and federal compliance requirements. This document maps system features to specific NIST 800-53 Rev 5 controls.

## Classification

- **System Classification**: FISMA Moderate
- **Data Classification**: CUI (Controlled Unclassified Information)
- **Deployment Environment**: On-premise or FedRAMP High cloud

## Security Control Families

### Access Control (AC)

| Control | Requirement | Implementation |
|---------|-------------|----------------|
| AC-2 | Account Management | User authentication via SAML/local auth, role-based access |
| AC-3 | Access Enforcement | Middleware-based authorization, API endpoint protection |
| AC-7 | Unsuccessful Login Attempts | Failed login lockout after 5 attempts, 30-minute lockout |
| AC-8 | System Use Notification | Terms of Service acceptance required, usage banner |
| AC-11 | Session Lock | 8-hour session timeout, refresh token mechanism |
| AC-12 | Session Termination | Automatic logout, manual logout capability |
| AC-14 | Permitted Actions | Role-based permissions, least privilege |

**Evidence**: 
- User authentication logs: `/var/log/fedchat/audit.log`
- Session management: JWT with expiration
- Access control config: `backend/middleware/security.py`

### Audit and Accountability (AU)

| Control | Requirement | Implementation |
|---------|-------------|----------------|
| AU-2 | Audit Events | All API requests, authentication, data access logged |
| AU-3 | Content of Audit Records | Timestamp, user ID, action, resource, IP, status |
| AU-4 | Audit Storage Capacity | 7-year retention (2555 days) configurable |
| AU-6 | Audit Review | JSON format for SIEM integration, searchable |
| AU-8 | Time Stamps | UTC timestamps on all audit records |
| AU-9 | Protection of Audit Information | Append-only logs, file permissions restricted |
| AU-12 | Audit Generation | Comprehensive logging via middleware |

**Evidence**:
- Audit middleware: `backend/middleware/audit.py`
- Log format: JSON structured logging
- Retention policy: `AUDIT_RETENTION_DAYS=2555` in `.env`

### Security Assessment and Authorization (CA)

| Control | Requirement | Implementation |
|---------|-------------|----------------|
| CA-2 | Security Assessments | Regular vulnerability scanning recommended |
| CA-7 | Continuous Monitoring | Prometheus metrics, health checks |
| CA-9 | Internal System Connections | Docker network isolation, TLS enforcement |

**Evidence**:
- Health checks: `backend/api/v1/health.py`
- Metrics endpoint: `/metrics` (Prometheus format)

### Configuration Management (CM)

| Control | Requirement | Implementation |
|---------|-------------|----------------|
| CM-2 | Baseline Configuration | Infrastructure as Code (Docker Compose) |
| CM-3 | Configuration Change Control | Version control (Git), changelog |
| CM-6 | Configuration Settings | Environment variables, documented defaults |
| CM-7 | Least Functionality | Minimal services, disabled unused features |

**Evidence**:
- Config management: `.env.example`, `docker-compose.yml`
- Disabled features: `ENABLE_API_DOCS=false`, social login disabled

### Identification and Authentication (IA)

| Control | Requirement | Implementation |
|---------|-------------|----------------|
| IA-2 | Identification and Authentication | JWT tokens, SAML/SSO support |
| IA-4 | Identifier Management | Unique UUIDs for users, sessions |
| IA-5 | Authenticator Management | Password hashing (bcrypt), MFA-ready |
| IA-8 | Identification and Authentication (Non-Org Users) | PIV/CAC support via SAML |

**Evidence**:
- Auth configuration: `librechat/config/librechat.yaml`
- SAML setup: `.env` SAML configuration

### System and Communications Protection (SC)

| Control | Requirement | Implementation |
|---------|-------------|----------------|
| SC-7 | Boundary Protection | Docker network isolation, nginx reverse proxy |
| SC-8 | Transmission Confidentiality | TLS 1.3 required, HSTS enabled |
| SC-12 | Cryptographic Key Establishment | JWT secrets, session encryption |
| SC-13 | Cryptographic Protection | Industry-standard algorithms (AES-256, RSA-2048) |
| SC-28 | Protection of Information at Rest | PostgreSQL encryption, encrypted volumes |

**Evidence**:
- TLS config: `nginx/nginx.conf`
- Security headers: `backend/middleware/security.py`
- Database encryption: PostgreSQL configuration

### System and Information Integrity (SI)

| Control | Requirement | Implementation |
|---------|-------------|----------------|
| SI-3 | Malicious Code Protection | Guardrails, input validation, content filtering |
| SI-4 | Information System Monitoring | Prometheus metrics, audit logs, health checks |
| SI-7 | Software Integrity | Docker image verification, checksum validation |
| SI-10 | Information Input Validation | Input sanitization, guardrails, rate limiting |

**Evidence**:
- Guardrails: `guardrails/config.yml`
- Input validation: `backend/services/guardrails_service.py`
- Monitoring: Prometheus + Grafana

## Data Flow

```
User → HTTPS/TLS → Nginx → LibreChat (Frontend)
                              ↓
                         FastAPI Backend
                         (Audit Middleware)
                              ↓
                         Guardrails Check
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
              LLM Service          RAG Service
              (Local/Azure)       (PostgreSQL)
                    ↓                   ↓
                 Response ← Guardrails Check
                    ↓
              Audit Log → PostgreSQL
```

All communication within Docker network is isolated. External access only via HTTPS on port 443.

## Encryption

### Data in Transit
- TLS 1.3 for all external connections
- Internal Docker network isolation
- Certificate management via Let's Encrypt or agency CA

### Data at Rest
- PostgreSQL transparent data encryption (TDE)
- Docker volume encryption
- Document storage encryption at filesystem level

Configuration:
```yaml
# Enable PostgreSQL encryption
POSTGRES_INITDB_ARGS: "-E UTF8 --data-checksums"

# Docker volume encryption
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind,encryption=aes256
```

## Authentication

### Local Authentication
- Password requirements: 12+ chars, mixed case, numbers, symbols
- Bcrypt hashing with cost factor 12
- Account lockout after 5 failed attempts
- 8-hour session timeout

### SAML/SSO Integration
- SAML 2.0 compliant
- Supports PIV/CAC cards via IdP
- Attribute mapping for roles/permissions
- Session binding to prevent replay attacks

Configuration:
```bash
ENABLE_SAML=true
SAML_IDP_ENTITY_ID=https://idp.agency.gov/saml
SAML_IDP_SSO_URL=https://idp.agency.gov/sso
```

## Audit Logging

### Log Levels

**Standard** - Basic operations:
- Authentication events
- Failed login attempts
- Configuration changes

**Detailed** - Includes:
- All API requests
- Request bodies for state-changing operations
- Error details

**Comprehensive** - Everything:
- Request and response bodies
- Query parameters
- Full stack traces

Configuration: `AUDIT_LOG_LEVEL=comprehensive`

### Log Format

JSON structure:
```json
{
  "timestamp": "2024-01-09T10:30:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "user_ip": "10.0.1.50",
  "method": "POST",
  "path": "/api/v1/chat",
  "status_code": 200,
  "duration_ms": 245.3,
  "user_agent": "Mozilla/5.0...",
  "action": "chat_message",
  "success": true
}
```

### Log Retention

- **Audit logs**: 7 years (2555 days) - FISMA requirement
- **Application logs**: 90 days
- **Error logs**: 180 days
- **Access logs**: 1 year

Automated rotation and archival configured in `docker-compose.yml`.

## Incident Response

### Security Events

Monitored events:
- Failed authentication (> 5 attempts)
- Guardrails violations
- Rate limit violations
- Unauthorized access attempts
- PII detection
- Suspicious patterns (prompt injection, jailbreak)

### Alert Configuration

Prometheus alerting rules:
```yaml
groups:
  - name: security
    rules:
      - alert: HighFailedLoginRate
        expr: rate(failed_login_total[5m]) > 10
        for: 5m
        annotations:
          summary: "High rate of failed logins"
```

### Response Procedures

1. **Detection**: Prometheus alerts or log analysis
2. **Investigation**: Review audit logs, identify affected users
3. **Containment**: Disable compromised accounts, block IPs
4. **Eradication**: Patch vulnerabilities, update configs
5. **Recovery**: Restore services, verify integrity
6. **Lessons Learned**: Update procedures, improve monitoring

## Backup and Recovery

### Backup Strategy

**Database Backups**:
- Automated daily at 2 AM (configurable)
- Full backup with incremental support
- 90-day retention
- Encrypted backups
- Off-site storage recommended

**Configuration Backups**:
- Git version control for code
- Environment variables exported securely
- Certificates backed up separately

### Recovery Procedures

**Database Recovery**:
```bash
# Restore from backup
docker-compose exec database pg_restore -U postgres -d fedchat /backups/backup-2024-01-09.dump

# Verify restoration
docker-compose exec database psql -U postgres -d fedchat -c "SELECT COUNT(*) FROM users;"
```

**Full System Recovery**:
1. Clone repository
2. Restore `.env` file
3. Restore database backup
4. Restore uploaded documents
5. Restore certificates
6. Run `docker-compose up -d`

**Recovery Time Objective (RTO)**: < 4 hours
**Recovery Point Objective (RPO)**: < 24 hours

## Testing

### Security Testing

**Required Tests**:
- [ ] Vulnerability scanning (OWASP ZAP, Nessus)
- [ ] Penetration testing
- [ ] Authentication testing
- [ ] Authorization bypass testing
- [ ] Input validation testing
- [ ] Session management testing
- [ ] Encryption verification

**Tools**:
```bash
# OWASP ZAP scan
docker run -t owasp/zap2docker-stable zap-baseline.py -t https://fedchat.agency.gov

# SQL injection testing
sqlmap -u "http://backend:8000/api/v1/chat" --data='{"messages":[]}'

# TLS testing
testssl.sh https://fedchat.agency.gov
```

### Compliance Testing

Verify:
- [ ] All audit events logged
- [ ] Log retention policy enforced
- [ ] Encryption in transit (TLS 1.3)
- [ ] Encryption at rest
- [ ] Authentication required
- [ ] Session timeout works
- [ ] Failed login lockout
- [ ] PII detection active
- [ ] Guardrails functioning

## Continuous Monitoring

### Metrics

Key metrics exposed at `/metrics`:
- Request rate and latency
- Error rates
- Authentication success/failure
- Guardrails violations
- Database connection pool
- Cache hit rates
- Document processing queue

### Dashboards

Grafana dashboards included:
- System overview
- Security events
- User activity
- Performance metrics
- Database health

Access: `http://grafana:3001` (default password in `.env`)

## Compliance Checklist

### Pre-Deployment

- [ ] Change all default passwords
- [ ] Configure agency-specific branding
- [ ] Set up SAML/SSO integration
- [ ] Configure TLS certificates
- [ ] Set strong JWT_SECRET and SESSION_SECRET
- [ ] Disable public registration
- [ ] Configure approved LLM provider
- [ ] Set data residency requirements
- [ ] Configure backup schedule
- [ ] Set up monitoring and alerting
- [ ] Review and update guardrails rules
- [ ] Configure MCP server permissions
- [ ] Set up log forwarding to SIEM
- [ ] Document system architecture
- [ ] Create incident response plan
- [ ] Train administrators

### Post-Deployment

- [ ] Verify all services healthy
- [ ] Test authentication flows
- [ ] Verify audit logging
- [ ] Test backup and restore
- [ ] Run security scans
- [ ] Verify encryption
- [ ] Test rate limiting
- [ ] Test guardrails
- [ ] Verify monitoring alerts
- [ ] Review access controls
- [ ] Document as-built configuration
- [ ] Complete security assessment
- [ ] Obtain ATO (Authority to Operate)

## Contact

For FISMA compliance questions:
- Security Team: security@agency.gov
- System Administrator: admin@agency.gov
- Incident Response: ir@agency.gov

## References

- NIST SP 800-53 Rev 5: Security and Privacy Controls
- NIST SP 800-171: Protecting CUI in Nonfederal Systems
- FedRAMP Security Assessment Framework
- FISMA Implementation Project
