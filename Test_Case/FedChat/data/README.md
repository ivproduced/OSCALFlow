# FedChat Data Directory

This directory contains datasets and documents for RAG (Retrieval-Augmented Generation) integration.

## Directory Structure

```
data/
├── README.md (this file)
├── nist-rag/              # NIST cybersecurity standards dataset
│   ├── README.md
│   ├── dataset/           # HuggingFace dataset files (~7-10GB)
│   └── faiss_index/       # Pre-built FAISS vector index
├── policies/              # Organizational security policies
│   ├── README.md
│   └── *.md               # Policy documents
└── documents/             # User-uploaded documents for RAG
    └── README.md
```

## Quick Setup

### 1. NIST RAG Dataset

```bash
cd data/nist-rag

# Clone NIST RAG Agent repository
git clone https://github.com/euCann/nist-rag-agent.git temp
# Follow instructions in data/nist-rag/README.md
```

### 2. Policy Documents

```bash
cd data/policies

# Clone demo policies
git clone https://github.com/0xdefendA/policies.git temp
cp temp/*.md .
rm -rf temp
```

### 3. Configure Environment

```bash
# Add to .env
NIST_LOCAL_DATASET_PATH=/app/data/nist-rag/dataset
POLICY_LOCAL_PATH=/app/data/policies
```

### 4. Update Docker Compose

Ensure `docker-compose.yml` includes:

```yaml
services:
  backend:
    volumes:
      - ./data/nist-rag:/app/data/nist-rag:ro
      - ./data/policies:/app/data/policies:ro
      - ./data/documents:/app/data/documents
```

## Storage Requirements

| Component | Size | Description |
|-----------|------|-------------|
| NIST Dataset | ~10GB | HuggingFace dataset + FAISS index |
| NIST Index | ~1GB | Pre-built FAISS vector index |
| Policies | ~100MB | Markdown policy documents |
| Policy Index | ~50MB | FAISS vector index |
| **Total** | **~11GB** | For self-contained deployment |

## Benefits of Local Data

✅ **Air-gapped Deployment** - No internet required after initial setup
✅ **Faster Startup** - No downloads on first run (10-20 min savings)
✅ **Reproducibility** - Consistent dataset versions across environments
✅ **Compliance** - Data stays within authorized boundaries
✅ **Version Control** - Track changes to policies and datasets

## Git LFS Recommendation

Due to large file sizes, consider using Git LFS:

```bash
# Install Git LFS
git lfs install

# Track large files
git lfs track "data/nist-rag/dataset/**"
git lfs track "data/nist-rag/faiss_index/**"

# Add .gitattributes
git add .gitattributes
git commit -m "Configure Git LFS for large datasets"
```

## Alternative: External Storage

For very large deployments, consider:

- **S3/Object Storage**: Store datasets in S3-compatible storage
- **NFS/Shared Storage**: Mount shared volumes for multi-pod deployments
- **Container Registry**: Embed datasets in container images

## See Also

- [data/nist-rag/README.md](nist-rag/README.md) - NIST dataset setup
- [data/policies/README.md](policies/README.md) - Policy documents setup
- [docs/NIST_RAG_INTEGRATION.md](../docs/NIST_RAG_INTEGRATION.md) - NIST RAG documentation
- [QUICKSTART.md](../QUICKSTART.md) - Quick start guide
