# FedChat System - FISMA Moderate Federal Chatbot

A comprehensive, self-hosted chatbot system designed for FISMA Moderate federal environments, featuring agents, MCP, RAG, and guardrails.

## Architecture Overview

```
┌─────────────────┐
│   LibreChat UI  │  (Customizable federal interface)
└────────┬────────┘
         │
┌────────▼────────┐
│  FastAPI Backend│  (LangChain/LangGraph orchestration)
│                 │
│  - Agents       │
│  - MCP Servers  │
│  - RAG Pipeline │
└────────┬────────┘
         │
┌────────▼────────┐
│   Guardrails    │  (NeMo Guardrails - content safety)
└────────┬────────┘
         │
┌────────▼────────┐
│  PostgreSQL     │  (pgvector for RAG embeddings)
└─────────────────┘
```

## Components

### 1. LibreChat (Frontend)
- Customizable ChatGPT-like interface
- Multi-user support with authentication
- Conversation history and search
- Agency branding and customization

### 2. LangChain/LangGraph Backend
- Agent orchestration and tool calling
- Model Context Protocol (MCP) integration
- Custom workflow management
- Audit logging for compliance

### 3. RAG Pipeline
- Document ingestion and processing
- PostgreSQL with pgvector for semantic search
- Support for PDF, DOCX, TXT, and more
- Chunk optimization and metadata filtering

### 4. Guardrails
- Input/output content filtering
- PII detection and redaction
- Topic restrictions and safety rails
- Compliance policy enforcement

### 5. MCP Servers
- **Filesystem**: File system operations with security controls
- **Database**: PostgreSQL queries with SELECT-only enforcement
- **API Client**: HTTP requests to whitelisted domains
- **ServiceNow**: ITSM integration for incident/change management
- **Splunk**: Log search and security analytics
- Custom tool implementations

### 6. NIST Standards RAG
- **596 NIST Publications** including SP 800 series, FIPS, CSWP, CSF 2.0
- **530K+ Training Examples** from HuggingFace dataset
- **FAISS Vector Search** for fast semantic retrieval
- **Agent Integration** for automatic NIST control lookup
- **REST API** endpoints for direct document access
- Zero Trust Architecture and Cybersecurity Framework guidance

### 7. Policy RAG
- **Organizational Policy Integration** with GitHub repository syncing
- **Demo Policies** from 0xdefendA/policies (Information Security, Incident Response, Vulnerability Management)
- **Custom Policy Support** - point to your own policy repository
- **Semantic Policy Search** across all organizational policies
- **Agent Integration** for automatic policy lookup and compliance checking
- **REST API** endpoints for policy document access

## FISMA Moderate Compliance Features

- ✅ **Self-Hosted**: All components run on-premise or in FedRAMP infrastructure
- ✅ **Audit Logging**: Comprehensive logging of all interactions
- ✅ **Data Encryption**: At rest (PostgreSQL encryption) and in transit (TLS)
- ✅ **Authentication**: SSO/SAML integration ready
- ✅ **Access Controls**: Role-based access control (RBAC)
- ✅ **No External APIs**: Uses local LLMs (Llama, Mistral) or approved services
- ✅ **Data Residency**: All data remains within authorized boundaries
- ✅ **Security Monitoring**: Integrated logging and alerting
- ✅ **Hardened Container Images**: Iron Bank (DoD), Red Hat UBI, or Distroless base images
- ✅ **CVE Scanning**: Automated vulnerability scanning with Trivy/Grype
- ✅ **STIG Compliance**: Security Technical Implementation Guide ready

## Quick Start

### Prerequisites
- Docker 24.0+
- Docker Compose 2.20+
- 16GB RAM minimum (32GB recommended)
- GPU recommended for local LLM inference

### Installation

1. **Clone and configure**
```bash
cd fedchat-system
cp .env.example .env
# Edit .env with your configuration (OPENAI_API_KEY, etc.)
```

2. **(Optional) Setup local datasets for air-gapped deployment**
```bash
# Download NIST dataset (~10GB) and demo policies (~100MB)
./scripts/setup_local_data.sh

# This enables offline operation after initial setup
# See data/README.md for details
```

3. **Start services**
```bash
# Standard deployment
docker-compose up -d

# OR use hardened images (recommended for production)
./scripts/build_hardened.sh ubi  # or ironbank, distroless
docker-compose -f docker-compose.hardened.yml up -d

# First run downloads:
# - NIST dataset (~7GB) if not using local setup - takes 10-20 min
# - Policies from GitHub if not using local setup - takes 1-2 min
```

4. **Access LibreChat**
```
http://localhost:3000
```

5. **Configure admin user**
```bash
docker-compose exec backend python scripts/create_admin.py
```

For detailed setup instructions, see [QUICKSTART.md](./QUICKSTART.md).

## Configuration

### Environment Variables

See [.env.example](.env.example) for all available configuration options.

Key variables:
- `AGENCY_NAME`: Your federal agency name
- `LLM_PROVIDER`: local/azure/aws (FedRAMP approved)
- `ENABLE_GUARDRAILS`: true/false
- `AUDIT_LOG_LEVEL`: standard/detailed/comprehensive

### LLM Models

Supported local models (no external API calls):
- Llama 3 70B (recommended for quality)
- Mistral 7B (faster, lower resource)
- Llama 3 8B (balanced)

For FedRAMP environments:
- Azure OpenAI (FedRAMP High)
- AWS Bedrock (FedRAMP High in specific regions)

## Security Considerations

### Data Handling
- All user conversations stored in encrypted PostgreSQL
- Document embeddings stored with pgvector
- Audit trail maintained for 7 years (configurable)

### Network Security
- All services communicate over internal Docker network
- TLS required for external access
- Optional VPN/Zero Trust integration

### Authentication
- Built-in user management
- SAML 2.0 / OAuth 2.0 support
- LDAP/Active Directory integration

## Usage Examples

### Basic Chat
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the best practices for securing cloud infrastructure?",
    "conversation_id": "optional-conversation-id"
  }'
```

### NIST Standards Queries
```bash
# Search for specific NIST controls
curl -X POST http://localhost:8000/api/v1/nist/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "multi-factor authentication requirements",
    "top_k": 5
  }'

# Get specific control details
curl http://localhost:8000/api/v1/nist/control/AC-2 \
  -H "Authorization: Bearer YOUR_API_KEY"

# Search CSF 2.0 Framework
curl -X POST http://localhost:8000/api/v1/nist/csf \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "identity and access management"}'

# Zero Trust Architecture guidance
curl -X POST http://localhost:8000/api/v1/nist/zero-trust \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "network segmentation"}'
```

### Agent Tasks with NIST Integration
The agent automatically uses NIST tools when detecting relevant queries:
```bash
curl -X POST http://localhost:8000/api/v1/agents/execute \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Find NIST 800-53 controls related to incident response",
    "use_rag": true
  }'
```

### Policy Queries
```bash
# Search organizational policies
curl -X POST http://localhost:8000/api/v1/policy/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "password requirements and MFA policy",
    "top_k": 5
  }'

# Get incident response procedures
curl http://localhost:8000/api/v1/policy/category/incident_response \
  -H "Authorization: Bearer YOUR_API_KEY"

# Agent with policy integration
curl -X POST http://localhost:8000/api/v1/agents/execute \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "What are our incident response escalation procedures?",
    "use_rag": true
  }'
```

### Document Upload for RAG
```bash
curl -X POST http://localhost:8000/api/v1/rag/upload \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@policy_document.pdf" \
  -F "metadata={\"type\":\"policy\",\"department\":\"security\"}"
```

## Deployment Options

FedChat supports multiple deployment platforms:

### Docker Compose (Development/Small Deployments)
```bash
# Standard images
docker-compose up -d

# Hardened images (production)
./scripts/build_hardened.sh ubi
docker-compose -f docker-compose.hardened.yml up -d
```
See [QUICKSTART.md](./QUICKSTART.md) for details.

### Hardened Container Images (Federal/DoD Requirements)

For federal environments requiring approved base images:

**Available Hardened Variants:**
- **Iron Bank** (DoD Platform One) - Requires CAC/PKI authentication
- **Red Hat UBI** (Universal Base Image) - Free, FedRAMP compatible
- **Distroless** (Google) - Minimal attack surface, no shell

**Quick Build:**
```bash
# Red Hat UBI (recommended for most federal agencies)
./scripts/build_hardened.sh ubi

# DoD Iron Bank (requires registry1.dso.mil access)
./scripts/build_hardened.sh ironbank

# Distroless (maximum security)
./scripts/build_hardened.sh distroless
```

The build script automatically:
- ✅ Builds backend + frontend with hardened base images
- ✅ Runs Trivy vulnerability scans
- ✅ Tags images appropriately
- ✅ Optionally pushes to your registry

**Deploy with Hardened Images:**
```bash
export HARDENED_TYPE=ubi
export REGISTRY=registry.access.redhat.com/yourorg  # optional
docker-compose -f docker-compose.hardened.yml up -d
```

See [docs/HARDENED_IMAGES.md](./docs/HARDENED_IMAGES.md) for complete guide including:
- Registry authentication setup
- Security scanning with Trivy/Grype
- STIG compliance requirements
- CVE remediation processes

### Kubernetes (Production)
Full Kubernetes manifests with Ingress, NetworkPolicies, and SecurityPolicies.
```bash
cd kubernetes
kubectl apply -f .
```
See [kubernetes/README.md](./kubernetes/README.md) for details.

### OpenShift (Federal Cloud Environments)
OpenShift-optimized manifests with Routes, SCCs, and enhanced security.
```bash
cd openshift
./deploy.sh
```
See [openshift/README.md](./openshift/README.md) for details.

## Documentation

- [Backend API Documentation](./backend/README.md)
- [LibreChat Customization](./librechat/README.md)
- [RAG Pipeline Configuration](./docs/RAG_SETUP.md)
- [MCP Server Development](./mcp-servers/README.md)
- [Guardrails Configuration](./guardrails/README.md)
- [FISMA Compliance Guide](./docs/FISMA_COMPLIANCE.md)
- [Hardened Docker Images](./docs/HARDENED_IMAGES.md) - **Federal/DoD Requirements**
- [Deployment Guide](./docs/DEPLOYMENT.md)
- [Kubernetes Deployment](./kubernetes/README.md)
- [OpenShift Deployment](./openshift/README.md)
- [OpenShift Migration Guide](./openshift/MIGRATION_GUIDE.md)

## Maintenance

### Backups
```bash
docker-compose exec database pg_dump -U postgres chatbot > backup.sql
```

### Updates
```bash
docker-compose pull
docker-compose up -d
```

### Monitoring
- Logs: `docker-compose logs -f`
- Metrics: Prometheus endpoint at `:9090/metrics`
- Health: `curl http://localhost:8000/health`

## Support

For federal agency specific support and compliance questions, contact your security team or refer to the FISMA compliance documentation.

## License

[Specify your agency's licensing requirements]

## Contributing

Internal contributions welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.
