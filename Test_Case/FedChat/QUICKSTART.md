# Quick Start Guide

Get FedChat System running in 10 minutes for development/testing.

## Prerequisites

- Docker and Docker Compose installed
- 16GB RAM minimum
- 50GB free disk space

## Steps

### 1. Clone and Configure

```bash
# Clone your fork or copy of the FedChat repository
git clone <your-repository-url>
cd fedchat-system

# Copy environment template
cp .env.example .env

# Generate secrets
export JWT_SECRET=$(openssl rand -hex 32)
export SESSION_SECRET=$(openssl rand -hex 32)
export POSTGRES_PASSWORD=$(openssl rand -hex 16)

# Update .env file
sed -i "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" .env
sed -i "s/SESSION_SECRET=.*/SESSION_SECRET=$SESSION_SECRET/" .env
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$POSTGRES_PASSWORD/" .env
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# Watch logs
docker-compose logs -f
```

Wait for all services to be healthy (2-3 minutes).

### 3. Load LLM Model

```bash
# Pull Llama 3 8B (smaller, faster for testing)
docker-compose exec ollama ollama pull llama3:8b

# Pull embedding model
docker-compose exec ollama ollama pull nomic-embed-text
```

### 4. Access Application

Open your browser:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/api/docs (if enabled)
- **Grafana**: http://localhost:3001 (admin/admin)

### 5. Test Chat

1. Go to http://localhost:3000
2. Create an account (email: test@agency.gov, password: Test123!)
3. Start chatting!

## Customization

### Change Agency Name and Branding

```bash
# Update agency name in .env
sed -i 's/AGENCY_NAME=.*/AGENCY_NAME="My Agency"/' .env

# Update colors
sed -i 's/AGENCY_PRIMARY_COLOR=.*/AGENCY_PRIMARY_COLOR="#003366"/' .env
sed -i 's/AGENCY_SECONDARY_COLOR=.*/AGENCY_SECONDARY_COLOR="#FFFFFF"/' .env

# Restart LibreChat to apply changes
docker-compose restart librechat
```

### Add Agency Logo

```bash
# 1. Prepare your logo
# - PNG format recommended
# - Size: 300x60px (or similar aspect ratio)
# - Transparent background works best

# 2. Copy logo to LibreChat public assets
# Create assets directory if it doesn't exist
mkdir -p librechat/public/assets

# Copy your logo file
cp /path/to/your/logo.png librechat/public/assets/agency-logo.png

# Optional: Add favicon
cp /path/to/your/favicon.ico librechat/public/favicon.ico

# 3. Update librechat.yaml to reference your logo
sed -i 's|logoPath: "/assets/agency-logo.png"|logoPath: "/assets/agency-logo.png"|' \
  librechat/config/librechat.yaml

# 4. Rebuild and restart LibreChat
docker-compose build librechat
docker-compose up -d librechat
```

**Logo appears in:**
- Top navigation bar
- Login page
- Chat interface header

**Quick test:** After restart, open http://localhost:3000 and your logo should appear in the header.

### Use Different Model

```bash
# Pull Mistral (faster)
docker-compose exec ollama ollama pull mistral:7b

# Update .env
sed -i 's/LOCAL_LLM_MODEL=.*/LOCAL_LLM_MODEL=mistral:7b/' .env

# Restart
docker-compose restart backend
```

### Enable RAG

```bash
# Upload a document
curl -X POST http://localhost:8000/api/v1/rag/upload \
  -F "file=@/path/to/document.pdf"

# Search
curl -X POST http://localhost:8000/api/v1/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "search terms", "top_k": 5}'
```

### Enable NIST Standards RAG

NIST RAG provides access to 596 NIST publications (SP 800, FIPS, CSF 2.0, Zero Trust).

```bash
# 1. Add OpenAI API key to .env (required for embeddings)
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
echo "ENABLE_NIST_RAG=true" >> .env

# 2. Restart backend (first run will download ~7GB dataset)
docker-compose restart backend

# Note: Initial dataset download takes 10-20 minutes
# Check progress: docker-compose logs -f backend

# 3. Test NIST search
curl -X POST http://localhost:8000/api/v1/nist/search \
  -H "Content-Type: application/json" \
  -d '{"query": "multi-factor authentication", "top_k": 5}'

# 4. Get specific NIST control
curl http://localhost:8000/api/v1/nist/control/AC-2

# 5. Use with agents (automatic NIST lookup)
curl -X POST http://localhost:8000/api/v1/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "Find NIST 800-53 controls for incident response"}'
```

**Storage Requirements:**
- Dataset cache: ~7GB
- FAISS index: ~500MB
- Total: ~15GB recommended for PVC

**For FedRAMP compliance:** Use Azure OpenAI embeddings endpoint instead of OpenAI API.

### Enable Policy RAG

Policy RAG provides access to organizational security policies for compliance and guidance.

```bash
# Policy RAG is enabled by default with demo policies (0xdefendA/policies)
# Uses same OPENAI_API_KEY as NIST RAG

# 1. Verify configuration in .env
grep "ENABLE_POLICY_RAG" .env  # Should be true

# 2. Restart backend (first run will clone policy repo)
docker-compose restart backend

# Note: Initial policy sync takes 1-2 minutes
# Check progress: docker-compose logs -f backend

# 3. Test policy search
curl -X POST http://localhost:8000/api/v1/policy/search \
  -H "Content-Type: application/json" \
  -d '{"query": "password requirements", "top_k": 3}'

# 4. Use with agents (automatic policy lookup)
curl -X POST http://localhost:8000/api/v1/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"task": "What are our incident response procedures?"}'
```

**Custom Policy Repository:**
To use your own organization's policies:
```bash
# 1. Update .env with your policy repo
echo "POLICY_REPO_URL=<your-organization-policy-repo-url>" >> .env

# 2. Restart backend
docker-compose restart backend
```

**Storage Requirements:**
- Policy repository: ~100MB (varies by org)
- FAISS index: ~50MB
- Total: ~1GB recommended for PVC

## Troubleshooting

### Services not starting

```bash
# Check status
docker-compose ps

# View specific service logs
docker-compose logs database
docker-compose logs backend

# Restart problematic service
docker-compose restart backend
```

### Out of memory

```bash
# Use smaller model
docker-compose exec ollama ollama pull llama3:8b

# Or reduce workers
echo "WORKERS=2" >> .env
docker-compose restart backend
```

### Can't connect to frontend

```bash
# Check if running
docker-compose ps librechat

# Check logs
docker-compose logs librechat

# Restart
docker-compose restart librechat nginx
```

## What's Next?

- [Full Deployment Guide](docs/DEPLOYMENT.md) - Production setup
- [FISMA Compliance](docs/FISMA_COMPLIANCE.md) - Security controls
- [API Documentation](backend/README.md) - Backend API
- [Customization Guide](librechat/README.md) - Frontend customization

## Stop and Cleanup

```bash
# Stop services
docker-compose down

# Remove volumes (deletes data!)
docker-compose down -v

# Remove images
docker rmi $(docker images -q fedchat-*)
```

## Development Mode

```bash
# Enable debug mode
echo "DEBUG_MODE=true" >> .env
echo "LOG_LEVEL=DEBUG" >> .env

# Enable API docs
echo "ENABLE_API_DOCS=true" >> .env

# Restart
docker-compose restart backend

# API docs now at: http://localhost:8000/api/docs
```

## Getting Help

Having issues? Check:
1. [Troubleshooting Guide](docs/DEPLOYMENT.md#troubleshooting)
2. Service logs: `docker-compose logs [service]`
3. System resources: `docker stats`
4. GitHub Issues: https://github.com/your-agency/fedchat-system/issues
