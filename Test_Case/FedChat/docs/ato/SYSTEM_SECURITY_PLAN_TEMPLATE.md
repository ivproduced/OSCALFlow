# System Security Plan (SSP) Template
## FedChat System - FISMA Moderate

> **Note**: This is a template to accelerate ATO preparation. Replace all `[PLACEHOLDER]` fields with your agency-specific information.

---

## Document Information

| Field | Value |
|-------|-------|
| **System Name** | FedChat Chatbot System |
| **System Abbreviation** | FedChat |
| **Information System Owner** | [AGENCY NAME], [OFFICE] |
| **Authorizing Official** | [NAME, TITLE] |
| **System Security Plan Version** | 1.0 |
| **Date Prepared** | [DATE] |
| **Classification** | FISMA Moderate / CUI |

---

## Section 1: System Identification

### 1.1 System Name and Identifier
- **System Name**: FedChat Chatbot System
- **Unique Identifier**: [AGENCY-FEDCHAT-001]
- **System Abbreviation**: FedChat

### 1.2 System Categorization
Per FIPS 199, this system is categorized as:

| Security Objective | Confidentiality | Integrity | Availability | Overall |
|-------------------|-----------------|-----------|--------------|---------|
| **Impact Level** | Moderate | Moderate | Moderate | **MODERATE** |

**Rationale**: 
- **Confidentiality (Moderate)**: System processes CUI and internal communications
- **Integrity (Moderate)**: Unauthorized modification could affect operations and decisions
- **Availability (Moderate)**: System supports critical workflows but has acceptable downtime tolerance

### 1.3 System Type
- [x] Major Application
- [ ] General Support System
- [ ] Minor Application

### 1.4 Operational Status
- [ ] Operational
- [ ] Under Development
- [x] Major Modification
- [ ] Other: __________

---

## Section 2: System Description

### 2.1 General System Description

FedChat is a self-hosted, AI-powered chatbot system designed for federal government use. It provides secure conversational AI capabilities with integrated guardrails, retrieval-augmented generation (RAG), and multi-agent orchestration.

**Key Capabilities**:
- Natural language interaction with LLMs (local or FedRAMP-authorized)
- Document search and semantic retrieval (NIST standards, organizational policies)
- Integration with enterprise systems (ServiceNow, Splunk) via Model Context Protocol
- Content safety filtering and PII detection
- Role-based access control and audit logging

### 2.2 System Environment

**Deployment Model**: [SELECT ONE]
- [ ] On-Premise Data Center
- [ ] FedRAMP Authorized Cloud (specify: AWS GovCloud / Azure Government)
- [ ] Hybrid (on-premise + cloud)
- [ ] Air-Gapped Environment

**Infrastructure**:
- Container orchestration: [Docker Compose / Kubernetes / OpenShift]
- Operating System: [RHEL 9 / Ubuntu 22.04 LTS / Other]
- Network: [DMZ / Internal Enclave / Describe]

### 2.3 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Layer                           │
│  (CAC/PIV Authentication via SAML/SSO)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Presentation Layer                         │
│  - LibreChat Web UI (HTTPS/TLS 1.3)                        │
│  - Classification Banners                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Application Layer                          │
│  - FastAPI Backend (Rate Limited, Authenticated)            │
│  - LangChain/LangGraph Orchestration                        │
│  - NeMo Guardrails (Content Safety)                         │
│  - MCP Server Integration                                    │
└────────┬────────────────────────────────┬───────────────────┘
         │                                │
┌────────▼────────┐             ┌────────▼────────┐
│   Data Layer    │             │  External APIs  │
│  - PostgreSQL   │             │  - Ollama (LLM) │
│  - Redis Cache  │             │  - Azure OpenAI │
│  - Vector DB    │             │  - AWS Bedrock  │
└─────────────────┘             └─────────────────┘
```

### 2.4 System Functionality

| Function | Description | Users |
|----------|-------------|-------|
| **Conversational AI** | Natural language Q&A with LLMs | All authenticated users |
| **Document Search** | Semantic search across NIST standards and policies | All users |
| **Agent Workflows** | Multi-step reasoning with tool execution | All users |
| **System Integration** | ServiceNow/Splunk integration via MCP | Authorized power users |
| **Administration** | User management, audit review | System administrators |

---

## Section 3: System Boundaries

### 3.1 Authorization Boundary

**Included Components**:
- LibreChat frontend application
- FastAPI backend services
- PostgreSQL database (with pgvector extension)
- Redis cache
- Ollama LLM service (if self-hosted)
- NeMo Guardrails service
- MCP server components

**Excluded Components** (Out of Scope):
- External identity provider (SAML IdP)
- External monitoring systems (SIEM, log aggregator)
- External backup systems
- Cloud infrastructure (if FedRAMP-authorized provider)

### 3.2 Network Boundary

- **External Connections**: [List authorized external connections]
  - SAML/SSO Identity Provider: [URL]
  - Azure OpenAI (optional): *.openai.azure.com (FedRAMP High)
  - AWS Bedrock (optional): bedrock.[region].amazonaws.com (FedRAMP authorized)

- **Internal Connections**:
  - ServiceNow instance: [INSTANCE_URL]
  - Splunk instance: [SPLUNK_HOST]
  - LDAP/Active Directory (if applicable): [HOST]

### 3.3 Data Flow Diagram

See: `docs/ato/DATA_FLOW_DIAGRAM.md`

---

## Section 4: Information Types and Data Sensitivity

### 4.1 Information Types

> **Instructions**: Identify information types processed by this system using NIST SP 800-60 Volume II, Appendices C and D. Map each information type to its security categorization. Common categories for chatbot systems may include:
> - Information and Technology Management (C.2.8.x)
> - Security Management (C.2.8.11)
> - System and Network Monitoring (C.2.8.12)
> - Refer to your agency's data classification guide for specific mappings.

| Information Type (from NIST SP 800-60 Vol II) | Category Code | Confidentiality | Integrity | Availability |
|------------------------------------------------|---------------|-----------------|-----------|--------------|
| [IDENTIFY FROM NIST SP 800-60] | [e.g., C.2.8.x] | [Low/Mod/High] | [Low/Mod/High] | [Low/Mod/High] |
| [IDENTIFY FROM NIST SP 800-60] | [e.g., C.2.8.x] | [Low/Mod/High] | [Low/Mod/High] | [Low/Mod/High] |
| [IDENTIFY FROM NIST SP 800-60] | [e.g., C.2.8.x] | [Low/Mod/High] | [Low/Mod/High] | [Low/Mod/High] |
| [Add additional rows as needed] | | | | |

### 4.2 Sensitive Data Handling

- **CUI Handling**: System processes Controlled Unclassified Information per NIST SP 800-171
- **PII Processing**: Minimal PII (usernames, email addresses) - covered by SORN [NUMBER]
- **Export Controlled**: No export-controlled information processed

---

## Section 5: System Users and Roles

### 5.1 User Roles

| Role | Access Level | Authentication | Authorization |
|------|--------------|----------------|---------------|
| **System Administrator** | Full system access | CAC/PIV + MFA | Admin role in database |
| **Power User** | Extended features (MCP tools) | CAC/PIV + MFA | Power user role |
| **Standard User** | Basic chat and search | CAC/PIV | User role |
| **Auditor** | Read-only audit logs | CAC/PIV | Auditor role |
| **Service Account** | API integration | API key | Limited scope |

### 5.2 User Population

- **Expected Users**: [NUMBER]
- **Concurrent Users (peak)**: [NUMBER]
- **User Location**: [DESCRIPTION - e.g., CONUS, OCONUS, Remote]

---

## Section 6: System Interconnections

### 6.1 Interconnection Security Agreements (ISAs)

| Connected System | Purpose | Connection Type | ISA Status | Security Controls |
|------------------|---------|-----------------|------------|-------------------|
| [AGENCY SSO/IdP] | Authentication | HTTPS/SAML | [Executed/Pending] | Encrypted, MFA required |
| ServiceNow | ITSM integration | HTTPS REST API | [Executed/Pending] | TLS 1.3, API token auth |
| Splunk | Security monitoring | HTTPS REST API | [Executed/Pending] | TLS 1.3, token auth |
| [Other systems] | [Purpose] | [Type] | [Status] | [Controls] |

---

## Section 7: Laws, Regulations, and Policies

### 7.1 Applicable Laws and Regulations

- Federal Information Security Management Act (FISMA) of 2014
- Privacy Act of 1974
- E-Government Act of 2002 (Section 208)
- Clinger-Cohen Act of 1996
- OMB Circular A-130
- [AGENCY-SPECIFIC REGULATIONS]

### 7.2 Applicable Standards and Guidance

- FIPS 199: Standards for Security Categorization
- FIPS 200: Minimum Security Requirements
- NIST SP 800-53 Rev 5: Security and Privacy Controls
- NIST SP 800-171 Rev 2: Protecting CUI in Nonfederal Systems
- NIST SP 800-37 Rev 2: Risk Management Framework
- FedRAMP Moderate Baseline
- [AGENCY SECURITY POLICIES]

---

## Section 8: Security Controls

### 8.1 Control Baseline

This system implements the NIST SP 800-53 Rev 5 **MODERATE** baseline with tailoring.

**Control Summary**:
- Total baseline controls: 325
- Implemented: [NUMBER]
- Inherited: [NUMBER] (from cloud provider/infrastructure)
- Not Applicable: [NUMBER]
- Planned: [NUMBER]

### 8.2 Security Control Inheritance

**Inherited from [Cloud Provider / Data Center]**:
- Physical security controls (PE family)
- Environmental controls (PE-13, PE-14, PE-15)
- Data center infrastructure (AC-17, PE-*)

**Inherited from [Agency IT Infrastructure]**:
- Network perimeter security (SC-7)
- Intrusion detection (SI-4)
- Incident response (IR family - partially)

### 8.3 Control Implementation Summary

Detailed control implementation status is documented in the **Control Implementation Summary (CIS)** spreadsheet: `docs/ato/CONTROLS_TRACEABILITY_MATRIX.xlsx`

For detailed implementation by control family, see:
- Access Control (AC): `docs/FISMA_COMPLIANCE.md#access-control`
- Audit and Accountability (AU): `docs/FISMA_COMPLIANCE.md#audit-and-accountability`
- [Additional families documented in FISMA_COMPLIANCE.md]

---

## Section 9: System Security Plan Approval

### 9.1 Approval Signatures

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Information System Owner** | [NAME] | ____________ | ______ |
| **Information System Security Officer** | [NAME] | ____________ | ______ |
| **Authorizing Official** | [NAME] | ____________ | ______ |
| **Privacy Officer** (if PII processed) | [NAME] | ____________ | ______ |

### 9.2 Plan Maintenance

This SSP shall be reviewed and updated:
- Annually (no later than [DATE])
- When significant system changes occur
- When new threats or vulnerabilities are identified
- As required by the Authorizing Official

**Document Control**:
- Version control: Git repository
- Change management: Agency change control board
- Review cycle: Annual
- Next review date: [DATE]

---

## Appendices

### Appendix A: Acronyms and Definitions
See: `docs/ato/ACRONYMS.md`

### Appendix B: Security Controls Traceability Matrix
See: `docs/ato/CONTROLS_TRACEABILITY_MATRIX.xlsx`

### Appendix C: Data Flow Diagrams
See: `docs/ato/DATA_FLOW_DIAGRAM.md`

### Appendix D: Privacy Impact Assessment
See: `docs/ato/PRIVACY_IMPACT_ASSESSMENT.md`

### Appendix E: Incident Response Plan
See: `docs/operations/INCIDENT_RESPONSE_PLAN.md`

### Appendix F: Contingency Plan
See: `docs/operations/CONTINGENCY_PLAN.md`

### Appendix G: Configuration Management Plan
See: `docs/operations/CONFIGURATION_MANAGEMENT.md`

### Appendix H: Security Assessment Report (SAR)
To be completed during security assessment phase

### Appendix I: Plan of Action and Milestones (POA&M)
See: `docs/ato/POAM_TEMPLATE.md`

---

**Document Classification**: [FOR OFFICIAL USE ONLY / CUI]  
**Last Updated**: [DATE]  
**Prepared by**: [ORGANIZATION]