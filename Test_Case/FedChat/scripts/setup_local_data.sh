#!/bin/bash
set -e

# FedChat Local Data Setup Script
# This script clones the NIST RAG and Policy repositories into the local data directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data"

echo "=================================================="
echo "FedChat Local Data Setup"
echo "=================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running from correct directory
if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    echo -e "${RED}Error: Must run from fedchat-system directory${NC}"
    exit 1
fi

# Create data directories
echo -e "${GREEN}Creating data directories...${NC}"
mkdir -p "$DATA_DIR/nist-rag/dataset"
mkdir -p "$DATA_DIR/nist-rag/faiss_index"
mkdir -p "$DATA_DIR/policies"
mkdir -p "$DATA_DIR/documents"

# Setup NIST RAG Dataset
echo ""
echo -e "${YELLOW}=== NIST RAG Dataset Setup ===${NC}"
echo ""
echo "The NIST RAG dataset is ~7-10GB and will take 10-30 minutes to download."
echo ""
read -p "Do you want to download the NIST RAG dataset? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$DATA_DIR/nist-rag"
    
    echo -e "${GREEN}Cloning NIST RAG Agent repository...${NC}"
    if [ -d "temp_nist" ]; then
        rm -rf temp_nist
    fi
    git clone https://github.com/euCann/nist-rag-agent.git temp_nist
    
    echo ""
    echo -e "${GREEN}Downloading NIST dataset from HuggingFace...${NC}"
    echo "This will take 10-30 minutes depending on your connection..."
    
    # Check if Python and datasets library are available
    if command -v python3 &> /dev/null; then
        python3 << 'EOF'
import sys
try:
    from datasets import load_dataset
    print("Loading NIST cybersecurity training dataset...")
    dataset = load_dataset("ethanolivertroy/nist-cybersecurity-training")
    dataset.save_to_disk("./dataset")
    print(f"✓ Dataset saved with {len(dataset['train'])} examples")
except ImportError:
    print("Error: 'datasets' library not found. Please install: pip install datasets==2.16.1")
    sys.exit(1)
except Exception as e:
    print(f"Error downloading dataset: {e}")
    sys.exit(1)
EOF
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ NIST dataset downloaded successfully${NC}"
        else
            echo -e "${RED}✗ Failed to download NIST dataset${NC}"
            echo "You can download it manually later. See data/nist-rag/README.md"
        fi
    else
        echo -e "${YELLOW}Python3 not found. Please download dataset manually.${NC}"
        echo "See data/nist-rag/README.md for instructions."
    fi
    
    # Clean up
    rm -rf temp_nist
    
else
    echo -e "${YELLOW}Skipping NIST dataset download${NC}"
    echo "You can download it later using: cd data/nist-rag && follow README.md"
fi

# Setup Policy Documents
echo ""
echo -e "${YELLOW}=== Policy Documents Setup ===${NC}"
echo ""
echo "Downloading demo policies from 0xdefendA/policies (MPL-2.0 licensed)"
echo ""
read -p "Do you want to download demo policy documents? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$DATA_DIR/policies"
    
    echo -e "${GREEN}Cloning policies repository...${NC}"
    if [ -d "temp_policies" ]; then
        rm -rf temp_policies
    fi
    git clone https://github.com/0xdefendA/policies.git temp_policies
    
    echo -e "${GREEN}Copying policy files...${NC}"
    cp temp_policies/*.md . 2>/dev/null || true
    cp temp_policies/*.png . 2>/dev/null || true
    
    # Clean up
    rm -rf temp_policies
    
    echo -e "${GREEN}✓ Demo policies downloaded successfully${NC}"
    echo ""
    echo "Files downloaded:"
    ls -lh *.md 2>/dev/null || echo "No markdown files found"
    
else
    echo -e "${YELLOW}Skipping policy documents download${NC}"
    echo "You can add your organization's policies later to data/policies/"
fi

# Update .env file
echo ""
echo -e "${YELLOW}=== Environment Configuration ===${NC}"
echo ""

if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Updating existing .env file..."
    
    # Check if local dataset config already exists
    if grep -q "NIST_LOCAL_DATASET_PATH" "$PROJECT_ROOT/.env"; then
        echo "NIST local dataset path already configured"
    else
        echo "" >> "$PROJECT_ROOT/.env"
        echo "# Local NIST Dataset (self-contained deployment)" >> "$PROJECT_ROOT/.env"
        echo "NIST_USE_HUGGINGFACE=false" >> "$PROJECT_ROOT/.env"
        echo "NIST_LOCAL_DATASET_PATH=/app/data/nist-rag/dataset" >> "$PROJECT_ROOT/.env"
    fi
    
    if grep -q "POLICY_LOCAL_PATH" "$PROJECT_ROOT/.env"; then
        echo "Policy local path already configured"
    else
        echo "" >> "$PROJECT_ROOT/.env"
        echo "# Local Policy Documents (self-contained deployment)" >> "$PROJECT_ROOT/.env"
        echo "POLICY_USE_GITHUB=false" >> "$PROJECT_ROOT/.env"
        echo "POLICY_LOCAL_PATH=/app/data/policies" >> "$PROJECT_ROOT/.env"
    fi
    
    echo -e "${GREEN}✓ Environment file updated${NC}"
else
    echo -e "${YELLOW}No .env file found. Copy .env.example to .env and configure.${NC}"
fi

# Update docker-compose.yml
echo ""
echo -e "${YELLOW}=== Docker Compose Configuration ===${NC}"
echo ""

if grep -q "./data/nist-rag:/app/data/nist-rag" "$PROJECT_ROOT/docker-compose.yml"; then
    echo -e "${GREEN}✓ Docker compose already configured for local data${NC}"
else
    echo -e "${YELLOW}Please update docker-compose.yml to mount local data directories:${NC}"
    echo ""
    echo "  backend:"
    echo "    volumes:"
    echo "      - ./data/nist-rag:/app/data/nist-rag:ro"
    echo "      - ./data/policies:/app/data/policies:ro"
    echo "      - ./data/documents:/app/data/documents"
    echo ""
fi

# Summary
echo ""
echo "=================================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "Data directories created:"
echo "  - data/nist-rag/       (NIST dataset)"
echo "  - data/policies/       (Policy documents)"
echo "  - data/documents/      (User uploads)"
echo ""
echo "Next steps:"
echo "  1. Verify .env configuration"
echo "  2. Update docker-compose.yml volume mounts (if needed)"
echo "  3. Start FedChat: docker-compose up -d"
echo ""
echo "Storage usage:"
du -sh "$DATA_DIR"/* 2>/dev/null || echo "  (directories created but empty)"
echo ""
echo "For more information:"
echo "  - data/README.md"
echo "  - data/nist-rag/README.md"
echo "  - data/policies/README.md"
echo ""
