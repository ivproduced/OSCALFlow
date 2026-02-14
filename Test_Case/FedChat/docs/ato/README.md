# ATO (Authority to Operate) Package

This directory contains templates and documentation to accelerate the Authority to Operate (ATO) process for the FedChat system.

## Contents

### Core ATO Documents

| Document | Purpose | Agency Action Required |
|----------|---------|----------------------|
| **[SYSTEM_SECURITY_PLAN_TEMPLATE.md](./SYSTEM_SECURITY_PLAN_TEMPLATE.md)** | Complete SSP per NIST SP 800-18 | Fill in [PLACEHOLDER] fields |
| **[CONTROLS_TRACEABILITY_MATRIX.md](./CONTROLS_TRACEABILITY_MATRIX.md)** | Map NIST 800-53 controls to implementation | Review/update status |
| **[PRIVACY_IMPACT_ASSESSMENT.md](./PRIVACY_IMPACT_ASSESSMENT.md)** | PIA per E-Gov Act | Complete with Privacy Officer |
| **[DATA_FLOW_DIAGRAM.md](./DATA_FLOW_DIAGRAM.md)** | System architecture and data flows | Verify for your deployment |
| **[POAM_TEMPLATE.md](./POAM_TEMPLATE.md)** | Plan of Action & Milestones | Track security weaknesses |
| **[RISK_ASSESSMENT.md](./RISK_ASSESSMENT.md)** | Risk analysis per NIST SP 800-30 | Update for agency environment |

### Supporting Documents (To Be Created by Agency)

- **Security Assessment Report (SAR)**: Results from independent security assessment
- **Penetration Test Report**: Third-party pentest findings
- **Contingency Plan**: System backup and disaster recovery procedures
- **Incident Response Plan**: Security incident handling procedures
- **Configuration Management Plan**: Change control and configuration baseline
- **Continuous Monitoring Plan**: Ongoing security monitoring strategy

## ATO Process Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    ATO Process Phases                        │
└──────────────────────────────────────────────────────────────┘

Phase 1: CATEGORIZE
├─ FIPS 199 Categorization ✓ (Documented in SSP)
├─ System Boundary Definition ✓ (Data Flow Diagrams)
└─ Information Types Identification ✓ (SSP Section 4)

Phase 2: SELECT
├─ Control Baseline Selection ✓ (NIST 800-53 Moderate)
├─ Control Tailoring ✓ (Controls Matrix)
└─ Supplemental Controls (Agency-specific)

Phase 3: IMPLEMENT
├─ Control Implementation ✓ (System built with controls)
├─ Documentation ✓ (SSP, policies, procedures)
└─ Evidence Collection (Screenshots, logs, configs)

Phase 4: ASSESS
├─ Security Assessment Plan (SAP)
├─ Security Control Assessment (Independent assessor)
├─ Security Assessment Report (SAR)
└─ POA&M Creation (For identified weaknesses)

Phase 5: AUTHORIZE
├─ Risk Determination (Authorizing Official decision)
├─ ATO Decision Letter
└─ Terms and Conditions

Phase 6: MONITOR
├─ Continuous Monitoring ✓ (Health checks, vulnerability scans)
├─ Security Status Reporting
├─ Configuration Management
└─ Ongoing Authorization
```

## Quick Start for Agencies

### 1. Initial Setup (Week 1-2)

```bash
# Clone the repository
git clone <your-fedchat-repo>
cd fedchat

# Review the ATO package
cd docs/ato
ls -la

# Start with the SSP template
open SYSTEM_SECURITY_PLAN_TEMPLATE.md
```

**Tasks**:
- [ ] Assign System Owner
- [ ] Assign ISSO (Information System Security Officer)
- [ ] Identify Authorizing Official
- [ ] Determine deployment environment (on-prem, cloud, hybrid)

### 2. Complete Core Documents (Week 3-6)

**SSP (System Security Plan)**:
```bash
# Copy template and customize
cp SYSTEM_SECURITY_PLAN_TEMPLATE.md SYSTEM_SECURITY_PLAN.md

# Fill in all [PLACEHOLDER] fields:
# - Agency name, contact information
# - Deployment environment details
# - Network architecture
# - Inherited controls from infrastructure
```

**Controls Traceability Matrix**:
- Review each control's implementation status
- Update inherited controls from your infrastructure
- Document agency-specific controls
- Identify gaps and create POA&M items

**Privacy Impact Assessment**:
- Complete with Privacy Officer
- Document PII handling
- Establish SORN (if applicable)
- Define data retention/disposal procedures

### 3. Security Assessment (Week 7-10)

**Prepare for Assessment**:
```bash
# Run vulnerability scans
./scripts/security/scan_vulnerabilities.sh

# Generate SBOM
./scripts/security/generate_sbom.sh

# Collect evidence
./scripts/compliance/collect_evidence.sh
```

**Assessment Activities**:
- [ ] Contract independent assessor (if required)
- [ ] Conduct security control testing
- [ ] Perform penetration testing
- [ ] Review findings and create POA&Ms

### 4. Authorization (Week 11-12)

- [ ] Submit ATO package to Authorizing Official
- [ ] Risk adjudication meeting
- [ ] Address any additional concerns
- [ ] Obtain ATO decision letter

### 5. Continuous Monitoring (Ongoing)

```bash
# Set up automated monitoring
./scripts/compliance/continuous_monitoring.sh

# Schedule regular scans
# - Weekly vulnerability scans
# - Monthly configuration audits
# - Quarterly POA&M reviews
# - Annual security assessment
```

## Control Implementation Summary

**200 NIST 800-53 Rev 5 controls** assessed:

- ✅ **128 Implemented** (64%)
- 🟡 **32 Partially Implemented** (16%)
- 📋 **24 Planned** (12%)
- 👤 **14 Inherited** (7%)
- ❌ **2 Not Applicable** (1%)

See [CONTROLS_TRACEABILITY_MATRIX.md](./CONTROLS_TRACEABILITY_MATRIX.md) for details.

## Key Security Features

| Feature | Implementation | Evidence |
|---------|----------------|----------|
| **Authentication** | SAML/SSO + MFA | `backend/services/auth_service.py` |
| **Authorization** | Role-based access control | `backend/middleware/security.py` |
| **Audit Logging** | Comprehensive, 7-year retention | `backend/middleware/audit.py` |
| **Encryption (Transit)** | TLS 1.3 | TLS configuration |
| **Encryption (Rest)** | PostgreSQL, volume-level | Database config (enable) |
| **Input Validation** | Pydantic models | API validators |
| **Content Filtering** | NeMo Guardrails + PII detection | `guardrails/config.yml` |
| **Rate Limiting** | 30 req/min (configurable) | `backend/middleware/rate_limit.py` |
| **Vulnerability Scanning** | Automated Trivy/Grype | `.github/workflows/security.yml` |
| **Container Hardening** | Minimal images, non-root | Dockerfiles |

## Common Gaps & How to Address

### Gap 1: Database Encryption at Rest

**Issue**: PostgreSQL TDE not enabled by default  
**POA&M**: POA&M-001  
**Solution**:
```yaml
# docker-compose.yml
postgres:
  environment:
    POSTGRES_INITDB_ARGS: "-E UTF8 --data-checksums"
  volumes:
    - postgres_encrypted:/var/lib/postgresql/data

volumes:
  postgres_encrypted:
    driver: local
    driver_opts:
      type: "encrypted"  # Use encrypted volume driver
```

### Gap 2: No Intrusion Detection

**Issue**: No HIDS on containers  
**POA&M**: POA&M-002  
**Solution**: Deploy Wazuh or integrate with agency IDS
```bash
# Install Wazuh agent in containers
# See: docs/operations/INTRUSION_DETECTION_SETUP.md
```

### Gap 3: MFA for Local Accounts

**Issue**: Local admin accounts lack MFA  
**POA&M**: POA&M-005  
**Solution**: Implement TOTP or disable local accounts entirely
```python
# Use agency SAML/SSO exclusively
ENABLE_LOCAL_AUTH=false  # Force SAML only
```

## Evidence Collection

For ATO assessment, collect:

1. **Configuration Files** (redacted secrets)
   - `docker-compose.yml`
   - `.env.example`
   - `librechat/config/librechat.yaml`

2. **Screenshots**
   - Login page with classification banner
   - Audit log sample
   - Admin interface (user management)
   - Security settings

3. **Scan Results**
   - Vulnerability scan reports (latest)
   - SBOM (Software Bill of Materials)
   - Penetration test report

4. **Logs** (sanitized samples)
   - Audit logs showing authentication
   - Security events
   - Error handling

5. **Test Results**
   - Security test cases passed
   - Integration test results
   - Performance/load test results

## Timeline Estimate

| Phase | Duration | Key Activities |
|-------|----------|----------------|
| **Preparation** | 2 weeks | Document customization, system setup |
| **Documentation** | 4 weeks | Complete SSP, PIA, risk assessment |
| **Assessment** | 4 weeks | Security testing, penetration testing |
| **Remediation** | 2-4 weeks | Address findings, create POA&Ms |
| **Authorization** | 2 weeks | AO review and decision |
| **Total** | **14-16 weeks** | From start to ATO |

*Note: Timeline varies by agency. Some agencies may have streamlined processes or additional requirements.*

## Resource Requirements

**Personnel**:
- System Owner (10% FTE for 4 months)
- ISSO (50% FTE for 4 months)
- Developers (for any remediation)
- Independent Assessor (contracted)

**Budget** (Estimated):
- Security assessment: $30,000 - $60,000
- Penetration testing: $20,000 - $40,000
- Tools/licenses: $5,000 - $15,000
- Contingency: 20%

## Agency-Specific Considerations

### DoD Components
- Use Iron Bank hardened images
- Follow DISA STIG requirements
- Deploy to NIPR/SIPR networks
- See: [docs/HARDENED_IMAGES.md](../HARDENED_IMAGES.md)

### Civilian Agencies
- Follow agency-specific policies
- Integrate with agency CDM program
- Use FedRAMP-authorized services
- Coordinate with agency SOC

### Intelligent Community
- Additional controls for IC environment
- Classification level considerations
- Cross-domain solution integration
- SAMI/JAFAN compliance

## Support and Resources

**FedChat Documentation**:
- Main README: [../../README.md](../../README.md)
- Deployment Guide: [../DEPLOYMENT.md](../DEPLOYMENT.md)
- FISMA Compliance: [../FISMA_COMPLIANCE.md](../FISMA_COMPLIANCE.md)

**NIST Resources**:
- [NIST RMF](https://csrc.nist.gov/projects/risk-management/risk-management-framework-(RMF)-Overview)
- [NIST SP 800-53 Rev 5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [NIST SP 800-37 Rev 2](https://csrc.nist.gov/publications/detail/sp/800-37/rev-2/final)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

**FedRAMP Resources**:
- [FedRAMP.gov](https://www.fedramp.gov/)
- [FedRAMP Marketplace](https://marketplace.fedramp.gov/)

## Questions?

For FedChat-specific questions:
- Open an issue in your repository's issue tracker
- Contact your system administrator

For ATO process questions:
- Contact your agency ISSO
- Reach out to agency Authorizing Official
- Consult agency RMF/ATO guidance

---

**Last Updated**: January 2026  
**Version**: 1.0  
**Maintained by**: FedChat Development Team