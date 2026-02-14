#!/bin/bash

# SBOM Generation Script for FedChat System
# Generates Software Bill of Materials using multiple tools

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}FedChat SBOM Generation${NC}"
echo -e "${GREEN}======================================${NC}"

# Configuration
OUTPUT_DIR="${OUTPUT_DIR:-./security-reports/sbom}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo -e "\n${YELLOW}Output directory: $OUTPUT_DIR${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install syft if not present
install_syft() {
    echo -e "\n${YELLOW}Installing Syft...${NC}"
    curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
}

# Install cdxgen if not present
install_cdxgen() {
    echo -e "\n${YELLOW}Installing cdxgen...${NC}"
    npm install -g @cyclonedx/cdxgen
}

# Check and install required tools
if ! command_exists syft; then
    echo -e "${YELLOW}Syft not found.${NC}"
    read -p "Install Syft? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_syft
    else
        echo -e "${RED}Syft is required. Exiting.${NC}"
        exit 1
    fi
fi

# Generate Python dependencies SBOM
echo -e "\n${GREEN}Generating Python dependencies SBOM...${NC}"
if [ -f "$REPO_ROOT/backend/requirements.txt" ]; then
    syft packages file:"$REPO_ROOT/backend/requirements.txt" \
        -o spdx-json="$OUTPUT_DIR/python-sbom-$TIMESTAMP.spdx.json" \
        -o cyclonedx-json="$OUTPUT_DIR/python-sbom-$TIMESTAMP.cdx.json" \
        -o table="$OUTPUT_DIR/python-sbom-$TIMESTAMP.txt"
    echo -e "${GREEN}✓ Python SBOM generated${NC}"
else
    echo -e "${YELLOW}⚠ requirements.txt not found${NC}"
fi

# Generate Node.js dependencies SBOM (LibreChat)
echo -e "\n${GREEN}Generating Node.js dependencies SBOM...${NC}"
if [ -f "$REPO_ROOT/librechat/package.json" ]; then
    syft packages dir:"$REPO_ROOT/librechat" \
        -o spdx-json="$OUTPUT_DIR/nodejs-sbom-$TIMESTAMP.spdx.json" \
        -o cyclonedx-json="$OUTPUT_DIR/nodejs-sbom-$TIMESTAMP.cdx.json" \
        -o table="$OUTPUT_DIR/nodejs-sbom-$TIMESTAMP.txt"
    echo -e "${GREEN}✓ Node.js SBOM generated${NC}"
else
    echo -e "${YELLOW}⚠ package.json not found${NC}"
fi

# Generate Docker image SBOMs
echo -e "\n${GREEN}Generating Docker image SBOMs...${NC}"

IMAGES=(
    "fedchat-backend:latest"
    "fedchat-frontend:latest"
)

for IMAGE in "${IMAGES[@]}"; do
    if docker images | grep -q "${IMAGE%%:*}"; then
        echo -e "${YELLOW}Scanning $IMAGE...${NC}"
        IMAGE_NAME=$(echo "$IMAGE" | tr ':' '-')
        syft packages "$IMAGE" \
            -o spdx-json="$OUTPUT_DIR/docker-$IMAGE_NAME-$TIMESTAMP.spdx.json" \
            -o cyclonedx-json="$OUTPUT_DIR/docker-$IMAGE_NAME-$TIMESTAMP.cdx.json" \
            -o table="$OUTPUT_DIR/docker-$IMAGE_NAME-$TIMESTAMP.txt"
        echo -e "${GREEN}✓ $IMAGE SBOM generated${NC}"
    else
        echo -e "${YELLOW}⚠ Image $IMAGE not found locally${NC}"
    fi
done

# Generate comprehensive repository SBOM
echo -e "\n${GREEN}Generating comprehensive repository SBOM...${NC}"
syft packages dir:"$REPO_ROOT" \
    -o spdx-json="$OUTPUT_DIR/fedchat-complete-$TIMESTAMP.spdx.json" \
    -o cyclonedx-json="$OUTPUT_DIR/fedchat-complete-$TIMESTAMP.cdx.json" \
    -o table="$OUTPUT_DIR/fedchat-complete-$TIMESTAMP.txt"
echo -e "${GREEN}✓ Complete SBOM generated${NC}"

# Generate SBOM summary report
echo -e "\n${GREEN}Generating SBOM summary...${NC}"
cat > "$OUTPUT_DIR/sbom-summary-$TIMESTAMP.md" << EOF
# SBOM Summary Report
**Generated**: $(date)
**System**: FedChat Chatbot System
**Tool**: Syft v$(syft version 2>/dev/null | head -1)

## Generated SBOMs

### Python Dependencies
- SPDX JSON: \`python-sbom-$TIMESTAMP.spdx.json\`
- CycloneDX JSON: \`python-sbom-$TIMESTAMP.cdx.json\`
- Human-readable: \`python-sbom-$TIMESTAMP.txt\`

### Node.js Dependencies  
- SPDX JSON: \`nodejs-sbom-$TIMESTAMP.spdx.json\`
- CycloneDX JSON: \`nodejs-sbom-$TIMESTAMP.cdx.json\`
- Human-readable: \`nodejs-sbom-$TIMESTAMP.txt\`

### Docker Images
$(for IMAGE in "${IMAGES[@]}"; do
    IMAGE_NAME=$(echo "$IMAGE" | tr ':' '-')
    echo "- **$IMAGE**: \`docker-$IMAGE_NAME-$TIMESTAMP.spdx.json\`"
done)

### Complete Repository
- SPDX JSON: \`fedchat-complete-$TIMESTAMP.spdx.json\`
- CycloneDX JSON: \`fedchat-complete-$TIMESTAMP.cdx.json\`
- Human-readable: \`fedchat-complete-$TIMESTAMP.txt\`

## Statistics

EOF

# Add package counts if available
if [ -f "$OUTPUT_DIR/fedchat-complete-$TIMESTAMP.txt" ]; then
    PACKAGE_COUNT=$(grep -c "NAME" "$OUTPUT_DIR/fedchat-complete-$TIMESTAMP.txt" || echo "N/A")
    echo "**Total Packages Identified**: $PACKAGE_COUNT" >> "$OUTPUT_DIR/sbom-summary-$TIMESTAMP.md"
fi

echo -e "${GREEN}✓ SBOM summary generated${NC}"

# Create latest symlinks
echo -e "\n${GREEN}Creating 'latest' symlinks...${NC}"
for file in "$OUTPUT_DIR"/*-$TIMESTAMP.*; do
    if [ -f "$file" ]; then
        basename=$(basename "$file" | sed "s/-$TIMESTAMP//")
        ln -sf "$(basename "$file")" "$OUTPUT_DIR/latest-$basename"
    fi
done

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}SBOM Generation Complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "\nReports saved to: ${YELLOW}$OUTPUT_DIR${NC}"
echo -e "\nView summary: ${YELLOW}cat $OUTPUT_DIR/sbom-summary-$TIMESTAMP.md${NC}"
echo -e "\nLatest SBOMs available at: ${YELLOW}$OUTPUT_DIR/latest-*${NC}"

# Optional: Upload to dependency tracking system
if [ -n "$DEPENDENCY_TRACK_URL" ] && [ -n "$DEPENDENCY_TRACK_API_KEY" ]; then
    echo -e "\n${YELLOW}Uploading SBOM to Dependency-Track...${NC}"
    curl -X "POST" "$DEPENDENCY_TRACK_URL/api/v1/bom" \
        -H "Content-Type: multipart/form-data" \
        -H "X-Api-Key: $DEPENDENCY_TRACK_API_KEY" \
        -F "project=fedchat-system" \
        -F "bom=@$OUTPUT_DIR/fedchat-complete-$TIMESTAMP.cdx.json"
    echo -e "${GREEN}✓ Uploaded to Dependency-Track${NC}"
fi

echo -e "\n${GREEN}Done!${NC}"
