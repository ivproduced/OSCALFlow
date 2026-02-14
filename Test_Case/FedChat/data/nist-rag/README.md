# NIST RAG Dataset

> **⚠️ Dataset Not Included**: The NIST cybersecurity training dataset is not included in this repository due to its size (~10GB). Follow the setup instructions below to download and configure the dataset for local deployment.

## Overview

This directory is configured to hold the NIST Cybersecurity Training dataset, which powers the RAG (Retrieval-Augmented Generation) capabilities for NIST cybersecurity queries in FedChat.

### Dataset Specifications

| Property | Details |
|----------|---------|
| **Source Repository** | [euCann/nist-rag-agent](https://github.com/euCann/nist-rag-agent) |
| **HuggingFace Dataset** | [ethanolivertroy/nist-cybersecurity-training](https://huggingface.co/datasets/ethanolivertroy/nist-cybersecurity-training) |
| **Compressed Size** | ~7GB |
| **Uncompressed Size** | ~10GB |
| **NIST Publications** | 596 documents |
| **Training Examples** | 530,000+ |
| **Format** | HuggingFace Datasets (Apache Arrow) |

## Expected Directory Structure

Once the dataset is downloaded, the directory should look like this:

```
data/nist-rag/
├── README.md              # This file
├── .gitignore             # Git ignore configuration
├── data.arrow             # Main dataset in Apache Arrow format (download required)
├── dataset_info.json      # Dataset metadata
├── state.json             # Dataset state information
├── index.faiss            # FAISS similarity search index (auto-generated)
└── index.pkl              # Pickled index metadata (auto-generated)
```

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- pip package manager
- At least 15GB free disk space
- Internet connection (for initial download)

### Method 1: Download from HuggingFace (Recommended)

This is the simplest and most reliable method for obtaining the dataset.

```bash
# Navigate to the FedChat system root directory
cd fedchat-system

# Install HuggingFace datasets library
pip install datasets==2.16.1

# Run the download script
python3 << 'EOF'
from datasets import load_dataset

# Download and cache dataset
print("Downloading NIST cybersecurity training dataset...")
dataset = load_dataset("ethanolivertroy/nist-cybersecurity-training")

# Save to local directory
dataset.save_to_disk("./data/nist-rag")
print(f"✓ Dataset downloaded successfully: {len(dataset['train'])} examples")
EOF
```

### Method 2: Clone from NIST RAG Agent Repository

If the dataset is bundled with the NIST RAG Agent repository:

```bash
# Navigate to the NIST RAG directory
cd data/nist-rag

# Clone the NIST RAG Agent repository
git clone https://github.com/euCann/nist-rag-agent.git temp_nist

# Copy dataset files (adjust path as needed based on repo structure)
cp temp_nist/dataset/* ./

# Clean up temporary clone
rm -rf temp_nist

# Verify dataset
ls -lh *.arrow *.json
```

### Method 3: Manual Download from HuggingFace Hub

For air-gapped or restricted environments:

1. Visit the [HuggingFace dataset page](https://huggingface.co/datasets/ethanolivertroy/nist-cybersecurity-training)
2. Click on "Files and versions" tab
3. Download all files in the dataset
4. Extract and place files directly in `data/nist-rag/`
5. Verify the structure matches the expected layout above

## Configuration

### Environment Variables

Update your `.env` file with the following configuration:

```bash
# Use local dataset instead of downloading from HuggingFace on startup
NIST_USE_HUGGINGFACE=false

# Path to local dataset (container path)
NIST_LOCAL_DATASET_PATH=/app/data/nist-rag

# Cache directory for FAISS index and embeddings
NIST_RAG_CACHE_DIR=/app/data/nist-rag

# Optional: Embedding model configuration
NIST_EMBEDDING_MODEL=all-MiniLM-L6-v2
NIST_CHUNK_SIZE=512
NIST_CHUNK_OVERLAP=50
```

### Docker Compose Volume Mapping

Ensure your `docker-compose.yml` includes the proper volume mount:

```yaml
services:
  backend:
    volumes:
      # Read-only mount for dataset security
      - ./data/nist-rag:/app/data/nist-rag:ro
      # ... other volumes
```

For development environments where you need write access (e.g., to build indices):

```yaml
services:
  backend:
    volumes:
      # Read-write mount for development
      - ./data/nist-rag:/app/data/nist-rag:rw
      # ... other volumes
```

## Verification

After setup, verify the dataset is properly configured:

```bash
# Check dataset files exist
ls -lh data/nist-rag/

# Expected output should show:
# data.arrow (several GB)
# dataset_info.json
# state.json

# Test loading the dataset (optional)
python3 << 'EOF'
from datasets import load_from_disk

dataset = load_from_disk("./data/nist-rag")
print(f"✓ Dataset loaded: {len(dataset['train'])} examples")
print(f"✓ Sample keys: {list(dataset['train'][0].keys())}")
EOF
```

## Benefits of Local Dataset Deployment

| Benefit | Description |
|---------|-------------|
| **🔒 Air-gapped Deployments** | No internet connection required after initial download |
| **⚡ Faster Startup** | Eliminates 10-20 minute download on first container start |
| **📌 Version Control** | Pin to specific dataset version for reproducibility |
| **🔄 Reproducibility** | Consistent dataset across all environments (dev, staging, prod) |
| **✅ Compliance** | Keep sensitive data within authorized network boundaries |
| **💾 Resource Efficiency** | Download once, use across multiple deployments |

## Troubleshooting

### Dataset fails to load

```bash
# Check file permissions
ls -l data/nist-rag/

# Ensure files are readable (chmod if needed)
chmod 644 data/nist-rag/*.arrow data/nist-rag/*.json
chmod 755 data/nist-rag/
```

### FAISS index build fails

```bash
# Clear existing index files and rebuild
rm -f data/nist-rag/index.faiss data/nist-rag/index.pkl

# Restart the backend container to rebuild
docker-compose restart backend

# Check logs
docker-compose logs -f backend
```

### Out of disk space

The dataset requires approximately 15GB of space (including working space for index building). Free up disk space or use external storage:

```bash
# Check available space
df -h

# Move to external drive (example)
mv data/nist-rag /mnt/external/nist-rag
ln -s /mnt/external/nist-rag data/nist-rag
```

## Support

For issues or questions:

- **Dataset Issues**: [euCann/nist-rag-agent Issues](https://github.com/euCann/nist-rag-agent/issues)
- **FedChat Integration**: [FedChat Issues](https://github.com/euCann/fedchat-system/issues)
- **HuggingFace Dataset**: [Dataset page](https://huggingface.co/datasets/ethanolivertroy/nist-cybersecurity-training)

## License

The NIST publications and training data are subject to their respective licenses. Refer to the [NIST RAG Agent repository](https://github.com/euCann/nist-rag-agent) for licensing details.

## Notes

- Dataset files are large (~7-10GB) - may want to use Git LFS
- Add `data/nist-rag/dataset/` to `.gitignore` if not using LFS
- Pre-building FAISS index saves 2-3 minutes on first query
- For production, consider building index during image build
