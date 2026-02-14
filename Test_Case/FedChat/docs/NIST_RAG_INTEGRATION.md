# NIST RAG Agent Integration Guide

## Overview

FedChat now includes integrated access to 596 NIST cybersecurity publications with 530K+ training examples through the NIST RAG Agent. This provides automatic access to NIST SP 800 series, FIPS standards, CSF 2.0, Zero Trust Architecture, and more.

**Source:** https://github.com/euCann/nist-rag-agent  
**Dataset:** ethanolivertroy/nist-cybersecurity-training (HuggingFace)

## Features

### 📚 Content Coverage
- **596 NIST Publications** including:
  - SP 800 series (800-53, 800-171, 800-63B, etc.)
  - FIPS standards
  - Cybersecurity White Papers (CSWP)
  - Cybersecurity Framework (CSF) 2.0
  - Zero Trust Architecture guidance
- **530,000+ Training Examples** for comprehensive coverage
- **Semantic Search** using FAISS vector indexing
- **OpenAI Embeddings** (text-embedding-ada-002) for high-quality retrieval

### 🤖 Agent Integration
The FedChat agent automatically detects NIST-related queries and uses appropriate tools:

**Trigger Keywords:**
- "NIST", "control", "SP 800", "800-53", "800-171"
- "cybersecurity framework", "CSF"
- "zero trust", "ZTA"

**Available Tools:**
1. `search_nist_standards` - Query publications by topic/keyword
2. `get_nist_control` - Retrieve specific control details
3. `search_nist_csf` - Search CSF 2.0 framework
4. `search_zero_trust` - Find Zero Trust Architecture guidance

### 🔌 REST API Endpoints

All endpoints require authentication (`Authorization: Bearer YOUR_API_KEY`).

#### 1. General Search
```bash
POST /api/v1/nist/search
{
  "query": "multi-factor authentication requirements",
  "top_k": 5  # Optional, default 5
}
```

#### 2. Control Lookup
```bash
GET /api/v1/nist/control/{control_id}
# Examples: AC-2, IA-2, SC-7
```

#### 3. Document Details
```bash
GET /api/v1/nist/document/{document_id}
# Example: sp800-53r5
```

#### 4. CSF Search
```bash
POST /api/v1/nist/csf
{
  "query": "identity and access management",
  "top_k": 5
}
```

#### 5. Zero Trust Search
```bash
POST /api/v1/nist/zero-trust
{
  "query": "network segmentation",
  "top_k": 5
}
```

#### 6. Statistics
```bash
GET /api/v1/nist/stats
# Returns document count, index status
```

#### 7. Manual Initialization
```bash
POST /api/v1/nist/initialize
# Triggers background dataset download
```

## Setup Instructions

### Prerequisites
- OpenAI API key (or Azure OpenAI endpoint for FedRAMP)
- 15GB storage for dataset cache and FAISS index
- First initialization takes 10-20 minutes

### Configuration

#### 1. Environment Variables (.env)
```bash
# Enable NIST RAG
ENABLE_NIST_RAG=true

# HuggingFace dataset configuration
NIST_USE_HUGGINGFACE=true
NIST_DATASET_NAME=ethanolivertroy/nist-cybersecurity-training

# Cache directory (needs ~7GB for dataset + index)
NIST_RAG_CACHE_DIR=/app/.cache/nist_rag

# OpenAI embeddings (required)
OPENAI_API_KEY=sk-your-openai-api-key

# Or use Azure OpenAI for FedRAMP compliance
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_API_KEY=your-key
# AZURE_OPENAI_DEPLOYMENT=text-embedding-ada-002

# Embedding model
NIST_EMBEDDING_MODEL=text-embedding-ada-002

# Search parameters
NIST_TOP_K_RESULTS=5
NIST_MIN_SIMILARITY=0.7
```

#### 2. Docker Compose
The `docker-compose.yml` includes:
- NIST environment variables passed to backend service
- Volume mount: `nist_cache:/app/.cache/nist_rag`
- Persistent storage for downloaded dataset

#### 3. OpenShift Deployment
The OpenShift manifests include:
- **PVC**: `nist-cache-pvc` (15Gi storage)
- **Volume Mount**: `/app/.cache/nist_rag`
- **ConfigMap**: NIST RAG configuration variables
- **Secret**: `OPENAI_API_KEY`

### Initial Deployment

#### Docker Compose
```bash
# 1. Configure environment
cp .env.example .env
# Add OPENAI_API_KEY to .env

# 2. Start services
docker-compose up -d

# 3. Monitor first initialization (downloads ~7GB)
docker-compose logs -f backend

# Look for: "NIST RAG initialized successfully"
# First run takes 10-20 minutes
```

#### OpenShift
```bash
# 1. Update namespace configuration with API key
oc edit configmap backend-config -n fedchat

# 2. Create secret for OpenAI key
oc create secret generic nist-rag-secret \
  --from-literal=OPENAI_API_KEY=sk-your-key \
  -n fedchat

# 3. Deploy backend (includes NIST PVC)
oc apply -f openshift/04-backend.yaml

# 4. Monitor initialization
oc logs -f deployment/backend -n fedchat
```

## Usage Examples

### 1. Direct API Queries

#### Find MFA Requirements
```bash
curl -X POST http://localhost:8000/api/v1/nist/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "multi-factor authentication requirements for federal systems",
    "top_k": 5
  }'
```

#### Get Specific Control
```bash
curl http://localhost:8000/api/v1/nist/control/IA-2 \
  -H "Authorization: Bearer YOUR_API_KEY"
```

#### Search CSF 2.0
```bash
curl -X POST http://localhost:8000/api/v1/nist/csf \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "supply chain risk management"}'
```

#### Zero Trust Guidance
```bash
curl -X POST http://localhost:8000/api/v1/nist/zero-trust \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "microsegmentation strategies"}'
```

### 2. Agent Integration (Automatic)

The agent automatically uses NIST tools when it detects relevant queries:

```bash
curl -X POST http://localhost:8000/api/v1/agents/execute \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "What are the NIST 800-53 controls for incident response?",
    "use_rag": true
  }'
```

**Example Queries That Trigger NIST Tools:**
- "Find NIST controls for encryption"
- "What does SP 800-63B say about password requirements?"
- "Show me Zero Trust Architecture principles from NIST"
- "Explain NIST CSF 2.0 Identify function"
- "What are 800-171 requirements for audit logging?"

### 3. Chat Interface

Users can ask natural language questions in LibreChat:

> "What are the NIST 800-53 controls for access control?"

> "Show me Zero Trust Architecture guidance from NIST"

> "What does the Cybersecurity Framework say about supply chain risk?"

The agent automatically retrieves and cites relevant NIST documentation.

## Architecture

### Service Layer
**File:** `backend/services/nist_rag_service.py`

```python
class NistRagService:
    def initialize()           # Lazy load dataset and FAISS index
    def search()              # General semantic search
    def search_by_control()   # Lookup specific controls
    def search_csf()          # CSF 2.0 queries
    def search_zero_trust()   # Zero Trust Architecture
    def get_document()        # Retrieve full document
    def get_stats()           # Index statistics
```

### API Layer
**File:** `backend/api/v1/nist.py`

- 7 REST endpoints
- Pydantic request/response models
- Background task support for initialization
- Audit logging integration
- Authentication required

### Agent Tools
**File:** `backend/services/nist_tools.py`

- 4 LangChain async tools
- Automatic tool selection based on query keywords
- Integrated into agent execution flow
- Error handling and logging

### Integration Points
**File:** `backend/services/agent_service.py`

```python
# Tools loaded in __init__
if settings.ENABLE_NIST_RAG:
    from backend.services.nist_tools import NIST_TOOLS
    self.nist_tools = NIST_TOOLS

# Automatic detection in _execute_node
nist_keywords = ["nist", "control", "sp 800", "csf", "zero trust"]
if any(keyword in query for keyword in nist_keywords):
    result = await search_nist_standards(query)
```

## Storage Requirements

### Local Development (Docker Compose)
- **Dataset Download:** ~7GB (HuggingFace cache)
- **FAISS Index:** ~500MB (computed vectors)
- **Total:** ~8GB minimum, 15GB recommended
- **Volume:** `nist_cache` (named volume, persistent)

### Production (OpenShift)
- **PVC:** `nist-cache-pvc` (15Gi)
- **StorageClass:** Use fast storage (SSD recommended)
- **Access Mode:** ReadWriteOnce (single pod)
- **Mount Path:** `/app/.cache/nist_rag`

## Performance Considerations

### Initial Load
- First run downloads ~7GB dataset (10-20 minutes)
- FAISS index built on first search (~2-3 minutes)
- Subsequent starts use cached data (instant)

### Search Performance
- FAISS vector search: <100ms for 530K documents
- Embedding generation: ~200ms per query (OpenAI API)
- Total query time: ~300-500ms

### Memory Usage
- Dataset in memory: ~3-4GB
- FAISS index: ~1GB
- Total backend memory: ~6-8GB recommended

## Security & Compliance

### Data Handling
- **No External Data Transfer:** Dataset cached locally after first download
- **Embeddings:** OpenAI API calls (or Azure OpenAI for FedRAMP)
- **No User Data in Embeddings:** Only NIST publication content embedded

### FedRAMP Compliance
For FedRAMP High environments, use Azure OpenAI:

```bash
# .env configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Disable direct OpenAI
# OPENAI_API_KEY=
```

Update `backend/services/nist_rag_service.py` to use Azure OpenAI embeddings.

### Access Control
- All NIST endpoints require authentication
- API key or JWT token validation
- Audit logging for all searches
- No PII in search queries (NIST content only)

## Troubleshooting

### Dataset Download Issues
```bash
# Check logs
docker-compose logs -f backend

# Look for:
# "Downloading NIST dataset from HuggingFace..."
# "NIST dataset loaded: 530000 examples"

# Manual initialization
curl -X POST http://localhost:8000/api/v1/nist/initialize \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### FAISS Index Errors
```bash
# Clear cache and rebuild
docker-compose down
docker volume rm fedchat-system_nist_cache
docker-compose up -d

# Monitor rebuild
docker-compose logs -f backend
```

### OpenAI API Errors
```bash
# Verify API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check rate limits
# Embedding API: 3,000 requests/min (free tier)

# Switch to Azure OpenAI if needed
```

### Storage Issues (OpenShift)
```bash
# Check PVC status
oc get pvc nist-cache-pvc -n fedchat

# Verify mount
oc describe pod backend-xxx -n fedchat | grep nist-cache

# Check disk usage
oc exec deployment/backend -n fedchat -- df -h /app/.cache/nist_rag
```

### Search Not Working
```bash
# Verify initialization
curl http://localhost:8000/api/v1/nist/stats \
  -H "Authorization: Bearer YOUR_API_KEY"

# Expected response:
# {"status": "ready", "document_count": 530000, "indexed": true}

# Test basic search
curl -X POST http://localhost:8000/api/v1/nist/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication", "top_k": 1}'
```

## Maintenance

### Dataset Updates
The HuggingFace dataset may be updated periodically:

```bash
# Force dataset refresh
docker-compose down
docker volume rm fedchat-system_nist_cache
docker-compose up -d

# Or in OpenShift
oc delete pvc nist-cache-pvc -n fedchat
oc apply -f openshift/04-backend.yaml
```

### Index Rebuilding
FAISS index is automatically rebuilt if corrupted or missing.

### Monitoring
```bash
# Check NIST service health
curl http://localhost:8000/api/v1/nist/stats \
  -H "Authorization: Bearer YOUR_API_KEY"

# View backend logs
docker-compose logs backend | grep NIST

# Monitor OpenAI usage
# Check OpenAI dashboard for embedding API usage
```

## Best Practices

### Query Optimization
- **Be Specific:** Use technical terms (e.g., "IA-2" vs "authentication")
- **Include Context:** Mention framework (e.g., "800-53 R5 controls")
- **Use Keywords:** "NIST", "control", "CSF", "Zero Trust"

### Agent Usage
- Let agent automatically select NIST tools (triggers on keywords)
- Combine with RAG for organization-specific policies
- Review citations in agent responses

### Production Deployment
- Use dedicated PVC with fast storage (SSD)
- Monitor OpenAI API usage and rate limits
- Consider Azure OpenAI for FedRAMP compliance
- Set up alerts for initialization failures
- Cache dataset on shared storage for multi-pod deployments

## Related Documentation

- [NIST RAG Agent GitHub](https://github.com/euCann/nist-rag-agent)
- [FedChat Implementation Summary](../FedChat_IMPLEMENTATION_SUMMARY.md)
- [Quick Start Guide](../QUICKSTART.md)
- [OpenShift Deployment](../openshift/README.md)
- [FISMA Compliance Guide](./FISMA_COMPLIANCE.md)

## Support

For issues specific to NIST RAG integration:
1. Check logs: `docker-compose logs backend | grep NIST`
2. Verify configuration: Environment variables and volume mounts
3. Test endpoints: Use curl examples above
4. Review agent logs: Check tool selection and execution

For NIST dataset issues:
- Dataset source: https://huggingface.co/datasets/ethanolivertroy/nist-cybersecurity-training
- Original implementation: https://github.com/euCann/nist-rag-agent
