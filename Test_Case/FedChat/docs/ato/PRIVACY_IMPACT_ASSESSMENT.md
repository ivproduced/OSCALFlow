# Privacy Impact Assessment (PIA)
## FedChat Chatbot System

> **Note**: This PIA template must be customized with agency-specific information and reviewed by your Privacy Officer before submission.

---

## Document Information

| Field | Value |
|-------|-------|
| **System Name** | FedChat Chatbot System |
| **Unique Identifier** | [AGENCY-FEDCHAT-001] |
| **Date** | [DATE] |
| **System Owner** | [NAME, TITLE] |
| **Privacy Officer** | [NAME, TITLE] |
| **SORN Number** | [If applicable] |
| **PIA Status** | [Draft / Final / Approved] |

---

## Section 1: System Overview

### 1.1 Purpose of System

FedChat is an AI-powered chatbot system designed to assist federal employees with:
- Answering questions about NIST cybersecurity standards and frameworks
- Searching organizational policies and procedures
- Providing natural language interaction with enterprise systems
- Supporting knowledge management and decision-making

### 1.2 Legal Authority

- [List specific statutory authorities]
- [Agency-specific regulations]
- Administrative requirements

### 1.3 PII Collection

The system collects and processes the following Personally Identifiable Information (PII):

| PII Element | Purpose | Source | Retention |
|-------------|---------|--------|-----------|
| **Username** | Authentication, audit logging | User registration / SSO | Account lifetime |
| **Email Address** | Account recovery, notifications | User registration / SSO | Account lifetime |
| **IP Address** | Security monitoring, audit trail | System logs | 7 years |
| **User ID** | System identification | Auto-generated | Account lifetime |
| **Session Data** | Authentication, activity tracking | System-generated | Session duration |

**Optional PII** (if enabled):
- Name (from SAML/SSO attributes)
- Employee ID (from SAML/SSO attributes)
- Organization/Department (from SAML/SSO attributes)

---

## Section 2: Data Collection and Use

### 2.1 What information is collected?

**Directly from individuals:**
- Username and email address (if local accounts used)
- User-generated queries and conversations
- User preferences and settings

**From other sources:**
- SAML/SSO provider (authentication attributes)
- System-generated metadata (timestamps, IP addresses, session IDs)
- Integrated systems (ServiceNow, Splunk) - user context for API calls

### 2.2 Why is the information collected?

| Purpose | Justification |
|---------|---------------|
| **Authentication** | Required to verify user identity and control access |
| **Authorization** | Determine appropriate access levels and permissions |
| **Audit/Compliance** | FISMA requires comprehensive audit logging for 7 years |
| **User Experience** | Personalize interactions, maintain conversation history |
| **Security Monitoring** | Detect unauthorized access, anomalous behavior |
| **System Administration** | Troubleshooting, support, performance optimization |

### 2.3 Is consent required?

- [x] Yes - Users must accept Terms of Service and Privacy Notice
- [ ] No consent required (explain exception):

**Consent Method**: 
- First-time login requires acknowledgment of system use notification
- Privacy notice provided at registration/first use
- Users can request data deletion (right to be forgotten)

### 2.4 How is the information used?

The information is used to:
1. Authenticate and authorize users
2. Provide chatbot services and maintain conversation context
3. Generate audit logs for security and compliance
4. Improve system performance and user experience
5. Comply with federal recordkeeping requirements

**Information is NOT used for**:
- Marketing or commercial purposes
- Profiling or behavior prediction outside system security
- Sharing with third parties (except as required by law)

---

## Section 3: Data Sharing and Disclosure

### 3.1 Internal Sharing

| Recipient | Purpose | Legal Authority | Safeguards |
|-----------|---------|-----------------|------------|
| System Administrators | System maintenance, troubleshooting | Official duties | Role-based access, audit logging |
| Security Personnel | Incident response, threat detection | Official duties | Need-to-know basis, clearances |
| Auditors | Compliance verification | FISMA, agency policy | Read-only access, escorted |

### 3.2 External Sharing

| Recipient | Purpose | Legal Authority | Safeguards |
|-----------|---------|-----------------|------------|
| SAML/SSO Provider | Authentication | Memorandum of Understanding | TLS encryption, ISA in place |
| [Agency SOC/CIRT] | Security incident reporting | Agency security policy | Encrypted channels, authorized personnel |
| None (by default) | - | - | - |

**Routine Uses** (if SORN applicable): [List routine uses from SORN]

### 3.3 Third-Party Services

**External API Providers** (optional, agency-configured):
- Azure OpenAI (FedRAMP High authorized): No PII sent, only conversation content
- AWS Bedrock (FedRAMP authorized): No PII sent, only conversation content
- All connections encrypted via TLS 1.3

### 3.4 International Data Transfer

- [x] No international data transfer
- [ ] Data transferred to: [COUNTRY]

---

## Section 4: Data Retention and Disposal

### 4.1 Retention Schedule

| Data Type | Retention Period | Authority | Disposal Method |
|-----------|------------------|-----------|-----------------|
| **Audit Logs** | 7 years | NIST SP 800-53, FISMA | Secure deletion per NIST SP 800-88 |
| **User Accounts** | Account lifetime + 1 year | Agency policy | Secure deletion, audit log preserved |
| **Conversation History** | 90 days (default, configurable) | [Agency policy] | Automated deletion, overwrite |
| **System Logs** | 1 year | Agency policy | Secure deletion |
| **Backup Data** | 90 days | Agency policy | Encrypted deletion |

### 4.2 Disposal Methods

- **Electronic Data**: NIST SP 800-88 compliant secure deletion (overwrite/crypto-shred)
- **Database Records**: Permanent deletion with verification
- **Backup Media**: Cryptographic erasure or physical destruction
- **Audit Logs**: Archived to agency records management system before deletion

---

## Section 5: Data Security and Protection

### 5.1 Security Controls

**Access Controls:**
- Multi-factor authentication required (via SAML/SSO)
- Role-based access control (RBAC)
- Least privilege principle enforced
- Failed login protection (lockout after 5 attempts)

**Encryption:**
- TLS 1.3 for data in transit
- PostgreSQL encryption at rest (recommended)
- JWT token encryption
- Encrypted backup volumes

**Monitoring:**
- Comprehensive audit logging (all PII access logged)
- Real-time security monitoring
- Automated anomaly detection
- SIEM integration

**Incident Response:**
- 24/7 security monitoring
- Incident response plan in place
- Data breach notification procedures
- Forensic capabilities

### 5.2 Data Minimization

**Practices Implemented:**
- Only essential PII collected
- PII detection and redaction in guardrails
- Automatic deletion of old conversation data
- No unnecessary data retention
- Anonymization where possible (IP address hashing option)

### 5.3 Privacy Controls (NIST SP 800-53 Rev 5)

| Control Family | Key Controls | Status |
|----------------|--------------|--------|
| **Authority and Purpose (AP)** | AP-1, AP-2 | ✅ Implemented |
| **Accountability and Audit (AR)** | AR-1, AR-2, AR-4, AR-5 | ✅ Implemented |
| **Data Minimization (DM)** | DM-1, DM-2 | ✅ Implemented |
| **Individual Participation (IP)** | IP-1, IP-2, IP-4 | 🟡 Partial |
| **Security (SE)** | SE-1, SE-2 | ✅ Implemented |
| **Transparency (TR)** | TR-1, TR-2, TR-3 | ✅ Implemented |
| **Use Limitation (UL)** | UL-1, UL-2 | ✅ Implemented |

---

## Section 6: Individual Rights

### 6.1 Notice

**How are individuals notified?**
- Privacy notice displayed at first login
- Terms of Service acceptance required
- System use notification banner
- Privacy policy accessible at all times

### 6.2 Access

**Can individuals access their data?**
- [x] Yes - Users can view their profile, conversation history
- [ ] No

**Access Method**: 
- Self-service via user profile page
- API endpoint for data export: `/api/v1/users/me/export`
- Request to system administrator for full data package

### 6.3 Correction

**Can individuals correct their data?**
- [x] Yes - Users can update profile information
- [ ] No

**Correction Method**: User profile settings, or request to administrator

### 6.4 Consent and Opt-Out

**Can individuals opt out?**
- Essential system functions: No (authentication, audit logging required)
- Conversation history retention: Yes (can disable or request deletion)
- Optional features: Yes (can disable integrations, notifications)

### 6.5 Redress

**Complaint Process:**
1. Contact System Owner: [EMAIL]
2. Contact Agency Privacy Officer: [EMAIL]
3. File Privacy Act request
4. Contact agency Inspector General

---

## Section 7: Privacy Risk Analysis

### 7.1 Identified Privacy Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Unauthorized access to PII** | Low | High | MFA, RBAC, encryption, audit logging |
| **PII disclosure in logs** | Low | Medium | PII redaction, log access controls |
| **PII in conversation history** | Medium | Medium | Content filtering, user controls, retention limits |
| **Data breach** | Low | High | Encryption, monitoring, IR plan, annual pentesting |
| **Inadequate data retention** | Low | Medium | Automated deletion, retention policies |
| **Third-party data sharing** | Low | Medium | ISAs, FedRAMP providers only, no PII in LLM calls |

### 7.2 Risk Mitigation Summary

**Technical Safeguards:**
- NeMo Guardrails PII detection and redaction
- Encrypted data storage and transmission
- Automated data lifecycle management
- Security monitoring and alerting

**Administrative Safeguards:**
- Privacy training for administrators
- Privacy impact assessments
- Regular privacy audits
- Data sharing agreements (ISAs)

**Physical Safeguards:**
- Controlled access to data center (inherited)
- Secure media disposal procedures
- Environmental controls (inherited)

### 7.3 Residual Risk

After mitigation, residual privacy risks are assessed as **LOW** for this system.

---

## Section 8: System of Records Notice (SORN)

### 8.1 SORN Applicability

- [ ] New SORN required
- [ ] Existing SORN covers this system: [SORN NUMBER and TITLE]
- [x] System qualifies for exemption (explain below)
- [ ] Not applicable (no retrievable records by personal identifier)

**Exemption Justification**: 
[If applicable, explain why system is exempt from SORN requirements - e.g., incidental collection, no retrieval by name or identifier, etc.]

### 8.2 Privacy Act Statement

Users are provided with a Privacy Act Statement that includes:
- Legal authority for collection
- Purpose and routine uses
- Whether disclosure is voluntary or mandatory
- Effects of not providing information

---

## Section 9: Privacy Officer Review

### 9.1 Privacy Officer Assessment

**Assessment Date**: [DATE]

**Findings**:
- [ ] Approved - No privacy concerns identified
- [ ] Approved with conditions (list conditions below)
- [ ] Not approved - Privacy concerns require resolution

**Conditions/Recommendations**:
1. [List any conditions for approval]
2. [List any recommendations for improvement]

**Privacy Officer Signature**: _________________________ Date: _______

### 9.2 Follow-Up Actions

| Action | Responsible Party | Due Date | Status |
|--------|-------------------|----------|--------|
| [Action item 1] | [Name] | [Date] | [Status] |
| [Action item 2] | [Name] | [Date] | [Status] |

---

## Section 10: Approval and Maintenance

### 10.1 PIA Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **System Owner** | [NAME] | ____________ | ______ |
| **Privacy Officer** | [NAME] | ____________ | ______ |
| **Chief Information Security Officer** | [NAME] | ____________ | ______ |
| **Authorizing Official** (if required) | [NAME] | ____________ | ______ |

### 10.2 PIA Maintenance

This PIA shall be reviewed and updated:
- Annually (no later than [DATE])
- When significant system changes occur affecting PII
- When new information sharing arrangements are established
- As required by the Privacy Officer

**Next Review Date**: [DATE]

---

## Appendices

### Appendix A: Privacy Act Statement (Sample)

**PRIVACY ACT STATEMENT**

**Authority**: [Cite specific authority, e.g., 5 U.S.C. § 301, agency-specific statute]

**Purpose**: The information you provide will be used to authenticate your identity, provide chatbot services, maintain audit logs for security compliance, and administer the FedChat system.

**Routine Uses**: Information may be shared in accordance with the routine uses published in the applicable System of Records Notice [SORN NUMBER]. This includes sharing with system administrators for system operation, security personnel for incident response, and auditors for compliance verification.

**Disclosure**: Disclosure of this information is [mandatory/voluntary]. If you choose not to provide this information, [consequences, e.g., "you will not be able to access the system"].

**Questions**: Contact the Agency Privacy Officer at [EMAIL] or [PHONE] with questions about this Privacy Act Statement.

### Appendix B: User Privacy Notice (Sample)

See: User-facing privacy notice in application UI

### Appendix C: Data Flow Diagrams

See: `docs/ato/DATA_FLOW_DIAGRAM.md`

### Appendix D: Privacy Training Materials

[Link to privacy training materials for system users and administrators]

---

**Document Classification**: [FOR OFFICIAL USE ONLY / CUI]  
**Last Updated**: [DATE]  
**Prepared by**: [ORGANIZATION]