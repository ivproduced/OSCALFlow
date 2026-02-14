# Data Flow Diagrams
## FedChat System

These diagrams illustrate how data flows through the FedChat system and across system boundaries.

---

## High-Level System Data Flow

```
┌──────────────────────────────────────────────────────────────┐
│                     EXTERNAL ENTITIES                         │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   Users     │    │   SAML/SSO   │    │   External   │   │
│  │ (Browser)   │    │   Provider   │    │   LLM APIs   │   │
│  └──────┬──────┘    └──────┬───────┘    └──────┬───────┘   │
│         │                   │                    │            │
└─────────┼───────────────────┼────────────────────┼───────────┘
          │ HTTPS/TLS 1.3     │ SAML               │ HTTPS/TLS
          │                   │                    │
┌─────────▼───────────────────▼────────────────────▼───────────┐
│                    SYSTEM BOUNDARY                            │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              PRESENTATION LAYER                       │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │         LibreChat Frontend                   │    │  │
│  │  │  - User authentication                       │    │  │
│  │  │  - Conversation UI                           │    │  │
│  │  │  - Session management                        │    │  │
│  │  └─────────────────┬────────────────────────────┘    │  │
│  └────────────────────┼──────────────────────────────────┘  │
│                       │ Internal API (HTTPS)                 │
│  ┌────────────────────▼──────────────────────────────────┐  │
│  │              APPLICATION LAYER                        │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐    │  │
│  │  │         FastAPI Backend                      │    │  │
│  │  │                                               │    │  │
│  │  │  ┌────────────┐  ┌─────────────┐            │    │  │
│  │  │  │ Auth       │  │ Guardrails  │            │    │  │
│  │  │  │ Service    │  │ Service     │            │    │  │
│  │  │  └────────────┘  └─────────────┘            │    │  │
│  │  │                                               │    │  │
│  │  │  ┌────────────┐  ┌─────────────┐            │    │  │
│  │  │  │ LLM        │  │ Agent       │            │    │  │
│  │  │  │ Service    │  │ Service     │            │    │  │
│  │  │  └────────────┘  └─────────────┘            │    │  │
│  │  │                                               │    │  │
│  │  │  ┌────────────┐  ┌─────────────┐            │    │  │
│  │  │  │ RAG        │  │ MCP         │            │    │  │
│  │  │  │ Service    │  │ Service     │            │    │  │
│  │  │  └────────────┘  └─────────────┘            │    │  │
│  │  └────────┬──────────────┬──────────────────────┘    │  │
│  └───────────┼──────────────┼───────────────────────────┘  │
│              │              │                               │
│  ┌───────────▼──────────────▼───────────────────────────┐  │
│  │              DATA LAYER                              │  │
│  │                                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │  │
│  │  │ PostgreSQL  │  │   Redis     │  │  Ollama    │  │  │
│  │  │ + pgvector  │  │   Cache     │  │   (LLM)    │  │  │
│  │  └─────────────┘  └─────────────┘  └────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         EXTERNAL SYSTEM INTEGRATIONS                  │  │
│  │                                                        │  │
│  │  ┌────────────┐  ┌─────────────┐  ┌────────────┐    │  │
│  │  │ ServiceNow │  │   Splunk    │  │   Other    │    │  │
│  │  │  (ITSM)    │  │    (SIEM)   │  │  Systems   │    │  │
│  │  └────────────┘  └─────────────┘  └────────────┘    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## Authentication Data Flow

```
┌──────────┐                                    ┌──────────────┐
│  User    │                                    │  SAML/SSO    │
│ Browser  │                                    │  Provider    │
└────┬─────┘                                    └──────┬───────┘
     │                                                  │
     │ 1. Access FedChat                               │
     ├─────────────────────────────────────────────────┤
     │                                                  │
     │ 2. Redirect to SSO login                        │
     ├─────────────────────────────────────────────────>
     │                                                  │
     │ 3. User enters CAC/PIV + PIN                    │
     │────────────────────────────────────────────────>│
     │                                                  │
     │                    4. SAML assertion            │
     <─────────────────────────────────────────────────┤
     │                                                  │
     ├──────────────────────────────────┐              │
     │                                  │              │
┌────▼─────┐                    ┌──────▼──────────┐   │
│ LibreChat│                    │  FastAPI Backend│   │
│ Frontend │                    │  Auth Service   │   │
└────┬─────┘                    └──────┬──────────┘   │
     │                                  │              │
     │ 5. SAML response                │              │
     ├─────────────────────────────────>│              │
     │                                  │              │
     │                6. Validate SAML │              │
     │                                  │              │
     │              7. Create/update    │              │
     │                 user account     │              │
     │                                  │              │
     │           8. Issue JWT token     │              │
     <──────────────────────────────────┤              │
     │                                  │              │
     │ 9. Subsequent requests           │              │
     │    (Authorization: Bearer token) │              │
     ├─────────────────────────────────>│              │
     │                                  │              │
     │        10. Validate JWT          │              │
     │                                  │              │
     │        11. Response              │              │
     <──────────────────────────────────┤              │
     │                                  │              │
```

**Data Elements in Flow**:
- **Step 3**: User credentials (CAC/PIV certificate)
- **Step 4**: SAML assertion (username, email, attributes)
- **Step 8**: JWT token (user_id, role, expiration)
- **Step 9**: JWT token in Authorization header

**PII Handling**:
- User credentials never stored by FedChat
- SAML attributes (username, email) stored in PostgreSQL
- JWT contains user_id (UUID), not PII

---

## Conversation Data Flow

```
┌──────────┐
│  User    │
│ Browser  │
└────┬─────┘
     │
     │ 1. User submits query (+ JWT token)
     │
┌────▼─────────┐
│  LibreChat   │
│  Frontend    │
└────┬─────────┘
     │
     │ 2. API call: POST /api/v1/chat
     │    Headers: Authorization: Bearer <JWT>
     │    Body: {message: "What is NIST 800-53?"}
     │
┌────▼──────────────┐
│  FastAPI Backend  │
│  Security         │
│  Middleware       │
└────┬──────────────┘
     │
     │ 3. Validate JWT, rate limit check
     │
┌────▼──────────────┐
│  Audit Logging    │ ───────> Audit log: user_id, timestamp,
│  Middleware       │          endpoint, IP address
└────┬──────────────┘
     │
┌────▼──────────────┐
│  Guardrails       │
│  Service          │ 4. Content filtering, PII detection
└────┬──────────────┘
     │
     │ 5. Clean query (PII redacted if found)
     │
┌────▼──────────────┐
│  Agent Service    │ 6. Agent workflow:
└────┬──────────────┘    - Parse query intent
     │                   - Decide on tools (RAG, MCP)
     │
     ├─────────────────┐
     │                 │
┌────▼──────────┐  ┌──▼──────────────┐
│  RAG Service  │  │  MCP Service    │
│               │  │                 │
│ 7. Search     │  │ 8. Execute tool │
│    NIST docs  │  │    (if needed)  │
└────┬──────────┘  └──┬──────────────┘
     │                 │
     │ 9. Query        │ 10. Tool result
     │    pgvector     │
     │                 │
┌────▼─────────────────▼───┐
│  PostgreSQL + pgvector   │
│  (NIST docs, policies)   │
└────┬─────────────────────┘
     │
     │ 11. Retrieved context
     │
┌────▼──────────────┐
│  LLM Service      │ 12. Call LLM with:
└────┬──────────────┘     - User query
     │                    - Retrieved context
     │                    - Conversation history
     │
     ├─────────────────────────┬──────────────────────────┐
     │                         │                          │
┌────▼──────────┐  ┌──────────▼──────────┐  ┌───────────▼────────┐
│  Ollama       │  │  Azure OpenAI       │  │  AWS Bedrock       │
│  (Local)      │  │  (FedRAMP High)     │  │  (FedRAMP)         │
└────┬──────────┘  └──────────┬──────────┘  └───────────┬────────┘
     │                         │                          │
     │                         │                          │
     │ 13. LLM response (no PII sent to external LLMs)   │
     └─────────────────────────┴──────────────────────────┘
                               │
┌──────────────────────────────▼───┐
│  Guardrails Service              │ 14. Output filtering
└──────────────────────────────┬───┘
                               │
┌──────────────────────────────▼───┐
│  Response Builder                │ 15. Format response
└──────────────────────────────┬───┘
                               │
┌──────────────────────────────▼───┐
│  PostgreSQL                      │ 16. Save conversation
│  (conversation_history table)    │     to database
└──────────────────────────────┬───┘
                               │
┌──────────────────────────────▼───┐
│  Audit Logging                   │ 17. Log response event
└──────────────────────────────┬───┘
                               │
                               │ 18. Return JSON response
                               │
┌──────────────────────────────▼───┐
│  LibreChat Frontend              │
└──────────────────────────────┬───┘
                               │
┌──────────────────────────────▼───┐
│  User Browser                    │ 19. Display response
└──────────────────────────────────┘
```

**Data at Rest**:
- PostgreSQL: user profiles, conversation history, RAG documents, vector embeddings
- Redis: session data, cache (temporary, encrypted)
- Audit logs: File system (`/var/log/fedchat/`)

**Data in Transit**:
- User ↔ Frontend: TLS 1.3 (HTTPS)
- Frontend ↔ Backend: TLS 1.3 (internal network)
- Backend ↔ External APIs: TLS 1.3 (HTTPS)
- Backend ↔ ServiceNow/Splunk: TLS 1.3 (HTTPS)

---

## MCP Tool Execution Data Flow

```
┌──────────┐
│  User    │
│          │ "Show me open incidents in ServiceNow"
└────┬─────┘
     │
┌────▼──────────────┐
│  Agent Service    │ 1. Parse intent, decide tool
└────┬──────────────┘    Tool: servicenow.search_incidents
     │
┌────▼──────────────┐
│  MCP Service      │ 2. Validate tool request:
└────┬──────────────┘    - User has permission?
     │                   - Domain in allowlist?
     │                   - Rate limit OK?
     │
     │ 3. Build tool request
     │
┌────▼────────────────────┐
│  MCP Server             │ 4. Execute tool
│  (ServiceNow)           │
└────┬────────────────────┘
     │
     │ 5. API call to ServiceNow
     │    GET /api/now/table/incident
     │    Authorization: Basic <credentials>
     │
┌────▼────────────────────┐
│  ServiceNow Instance    │ 6. Query incidents
│  (External System)      │
└────┬────────────────────┘
     │
     │ 7. Return incidents (JSON)
     │
┌────▼────────────────────┐
│  MCP Server             │ 8. Parse response
└────┬────────────────────┘
     │
┌────▼────────────────────┐
│  MCP Service            │ 9. Format tool result
└────┬────────────────────┘
     │
┌────▼────────────────────┐
│  Audit Logging          │ 10. Log MCP tool execution:
└────┬────────────────────┘     - user_id, tool, params, result
     │
┌────▼────────────────────┐
│  Agent Service          │ 11. Integrate tool result into
└────┬────────────────────┘     agent workflow
     │
┌────▼────────────────────┐
│  LLM Service            │ 12. Generate natural language
└────┬────────────────────┘     response with incident data
     │
     │ 13. Return to user
     │
┌────▼────────────────────┐
│  User Browser           │
└─────────────────────────┘
```

**Security Controls**:
- Tool allowlists: Only approved tools executable
- Domain allowlists: API calls restricted to approved domains
- Authentication: Service accounts with least privilege
- Audit logging: All MCP executions logged
- Rate limiting: Prevent abuse of external APIs

---

## Audit Log Data Flow

```
┌──────────────────────────────────────────────────────┐
│  All Application Components                          │
│  (API endpoints, services, middleware)               │
└───────────────────┬──────────────────────────────────┘
                    │
                    │ Audit events triggered
                    │
┌───────────────────▼──────────────────────────────────┐
│  Audit Logging Middleware                            │
│  (backend/middleware/audit.py)                       │
│                                                       │
│  Captures:                                            │
│  - Timestamp (UTC, ISO 8601)                         │
│  - User ID (UUID) [PII]                              │
│  - IP Address [PII]                                  │
│  - Action/Endpoint                                    │
│  - Request method                                     │
│  - Response status                                    │
│  - Resource accessed                                  │
│  - Session ID                                         │
└───────────────────┬──────────────────────────────────┘
                    │
                    │ Structured JSON log entry
                    │
┌───────────────────▼──────────────────────────────────┐
│  Audit Log Files                                     │
│  /var/log/fedchat/audit.log                         │
│                                                       │
│  - Append-only (no modification)                     │
│  - File permissions: 600 (owner read/write only)     │
│  - Rotation: Daily                                    │
│  - Retention: 7 years (2555 days)                    │
└───────────────────┬──────────────────────────────────┘
                    │
                    │ Log forwarding (optional)
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼──────────┐   ┌────────▼─────────┐
│  Splunk          │   │  ELK Stack       │
│  (External SIEM) │   │  (Log aggregator)│
└───────┬──────────┘   └────────┬─────────┘
        │                       │
        │  Analysts access      │
        │  via SIEM UI          │
        │  (RBAC enforced)      │
        │                       │
┌───────▼───────────────────────▼─────────┐
│  Security Analysts / Auditors           │
│  (Read-only access, authorized users)   │
└─────────────────────────────────────────┘
```

**Audit Log Contains PII**:
- User ID (UUID)
- IP address
- Potentially username in some events

**Protection**:
- Restricted file permissions
- Separate log volume in Docker
- Access limited to admin role
- Encryption at rest (volume-level)
- Forwarding via encrypted channel (TLS)

---

## Data Retention and Disposal Flow

```
┌──────────────────────────────────────────────────────┐
│  Data Lifecycle Management                           │
└───────────────────┬──────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
┌───────▼──────┐ ┌─▼──────────┐ ┌─▼───────────┐
│ Conversation │ │ Audit Logs │ │ User        │
│ History      │ │            │ │ Accounts    │
│ 90 days      │ │ 7 years    │ │ Lifetime+1yr│
└───────┬──────┘ └─┬──────────┘ └─┬───────────┘
        │           │              │
        │           │              │
┌───────▼───────────▼──────────────▼──────────┐
│  Automated Retention Policy Enforcement     │
│  (Scheduled jobs, database triggers)        │
└───────────────────┬─────────────────────────┘
                    │
                    │ Deletion triggered
                    │
┌───────────────────▼─────────────────────────┐
│  Secure Deletion Process                    │
│  - Database: DELETE + VACUUM                │
│  - Files: NIST SP 800-88 secure deletion    │
│  - Backups: Cryptographic erasure           │
└───────────────────┬─────────────────────────┘
                    │
                    │ Verification
                    │
┌───────────────────▼─────────────────────────┐
│  Audit Log of Deletion                      │
│  (What, when, by whom, verification)        │
└─────────────────────────────────────────────┘
```

---

## Summary of Data Flows Containing PII

| Data Flow | PII Elements | Protection | Retention |
|-----------|--------------|------------|-----------|
| **Authentication** | Username, email, employee ID (from SSO) | TLS encryption, JWT tokens | Account lifetime |
| **Conversation** | User_id (UUID), potentially names/emails in queries | Guardrails PII detection, encryption | 90 days (configurable) |
| **Audit Logs** | User_id, IP address, username | Restricted access, encryption, append-only | 7 years |
| **Session Data** | User_id, session_id | Redis encryption, short-lived | Session duration (8 hours) |
| **MCP Tool Calls** | User_id (for authorization) | Audit logging, secure credentials | Logged 7 years, data not stored |
| **SAML Assertion** | Username, email, attributes | TLS encryption, processed and discarded | Not retained (JWT issued) |

---

## Network Diagram with Security Zones

```
┌──────────────────────────────────────────────────────────────┐
│                    INTERNET / DMZ                             │
│                                                               │
│  ┌──────────────┐          ┌─────────────────┐              │
│  │   Users      │          │   SAML/SSO      │              │
│  │  (CAC/PIV)   │          │   Provider      │              │
│  └──────┬───────┘          └────────┬────────┘              │
│         │ HTTPS/TLS 1.3             │ HTTPS/SAML            │
└─────────┼────────────────────────────┼──────────────────────┘
          │                            │
┌─────────▼────────────────────────────▼──────────────────────┐
│                    FIREWALL / VPN                             │
└─────────┬─────────────────────────────────────────────────────┘
          │
┌─────────▼─────────────────────────────────────────────────────┐
│                 APPLICATION ZONE (DMZ)                         │
│                                                                │
│  ┌───────────────────────────────────────────────────┐        │
│  │  Reverse Proxy / Load Balancer (nginx)            │        │
│  │  - TLS termination                                 │        │
│  │  - Rate limiting                                   │        │
│  └───────────────────┬───────────────────────────────┘        │
│                      │ Internal HTTPS                          │
│  ┌───────────────────▼───────────────────────────────┐        │
│  │  LibreChat Frontend (Container)                   │        │
│  └───────────────────┬───────────────────────────────┘        │
│                      │ Internal API                            │
│  ┌───────────────────▼───────────────────────────────┐        │
│  │  FastAPI Backend (Container)                      │        │
│  └───────────────────┬───────────────────────────────┘        │
│                      │                                         │
└──────────────────────┼─────────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────────┐
│                     DATA ZONE                                  │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ PostgreSQL   │  │    Redis     │  │   Ollama     │        │
│  │  (Database)  │  │    (Cache)   │  │   (LLM)      │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                │
│  Network Isolation:                                           │
│  - No direct external access                                  │
│  - Only backend can connect                                   │
│  - Private subnet                                              │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│              EXTERNAL INTEGRATIONS ZONE                        │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  ServiceNow  │  │    Splunk    │  │Azure OpenAI /│        │
│  │   (ITSM)     │  │    (SIEM)    │  │AWS Bedrock   │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                │
│  Access:                                                       │
│  - Outbound only from backend                                 │
│  - TLS 1.3 encryption                                         │
│  - Domain allowlists enforced                                 │
│  - ISAs in place                                               │
└────────────────────────────────────────────────────────────────┘
```

---

## Conclusion

These data flow diagrams map the movement of data through the FedChat system:

1. **PII is minimized** - Only essential identifiers collected
2. **Encryption in transit** - TLS 1.3 for all external communication
3. **Encryption at rest** - Available for databases and volumes
4. **Access controls** - RBAC enforced at every layer
5. **Audit logging** - Comprehensive logging of all data access
6. **Network isolation** - Layered security zones
7. **Data retention** - Automated lifecycle management

**For ATO Review**: These diagrams should be included in the System Security Plan (SSP) and reviewed during security assessment.

---

**Last Updated**: [DATE]  
**Prepared by**: [ORGANIZATION]  
**Classification**: [FOR OFFICIAL USE ONLY / CUI]