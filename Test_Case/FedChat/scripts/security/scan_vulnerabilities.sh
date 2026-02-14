#!/bin/bash

# Vulnerability Scanning Script for FedChat System
# Scans containers, dependencies, and code for security vulnerabilities

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}FedChat Vulnerability Scanning${NC}"
echo -e "${GREEN}======================================${NC}"

# Configuration
OUTPUT_DIR="${OUTPUT_DIR:-./security-reports/vulnerabilities}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
SEVERITY_THRESHOLD="${SEVERITY_THRESHOLD:-MEDIUM}"

mkdir -p "$OUTPUT_DIR"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Trivy if not present
install_trivy() {
    echo -e "\n${YELLOW}Installing Trivy...${NC}"
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
}

# Install Grype if not present
install_grype() {
    echo -e "\n${YELLOW}Installing Grype...${NC}"
    curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
}

# Check tools
if ! command_exists trivy; then
    echo -e "${YELLOW}Trivy not found.${NC}"
    read -p "Install Trivy? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_trivy
    fi
fi

if ! command_exists grype; then
    echo -e "${YELLOW}Grype not found.${NC}"
    read -p "Install Grype? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_grype
    fi
fi

# Update vulnerability databases
echo -e "\n${GREEN}Updating vulnerability databases...${NC}"
if command_exists trivy; then
    trivy image --download-db-only
fi
if command_exists grype; then
    grype db update
fi

# Scan Docker images with Trivy
echo -e "\n${GREEN}Scanning Docker images with Trivy...${NC}"
IMAGES=(
    "fedchat-backend:latest"
    "fedchat-frontend:latest"
    "postgres:15"
    "redis:7"
    "ollama/ollama:latest"
)

for IMAGE in "${IMAGES[@]}"; do
    if docker images | grep -q "${IMAGE%%:*}"; then
        echo -e "${YELLOW}Scanning $IMAGE...${NC}"
        IMAGE_NAME=$(echo "$IMAGE" | tr ':/' '-')
        
        # Trivy scan
        if command_exists trivy; then
            trivy image \
                --severity "$SEVERITY_THRESHOLD,HIGH,CRITICAL" \
                --format json \
                --output "$OUTPUT_DIR/trivy-$IMAGE_NAME-$TIMESTAMP.json" \
                "$IMAGE"
            
            trivy image \
                --severity "$SEVERITY_THRESHOLD,HIGH,CRITICAL" \
                --format table \
                --output "$OUTPUT_DIR/trivy-$IMAGE_NAME-$TIMESTAMP.txt" \
                "$IMAGE"
            
            echo -e "${GREEN}✓ Trivy scan complete for $IMAGE${NC}"
        fi
        
        # Grype scan
        if command_exists grype; then
            grype "$IMAGE" \
                --only-fixed \
                -o json \
                --file "$OUTPUT_DIR/grype-$IMAGE_NAME-$TIMESTAMP.json"
            
            grype "$IMAGE" \
                --only-fixed \
                -o table \
                --file "$OUTPUT_DIR/grype-$IMAGE_NAME-$TIMESTAMP.txt"
            
            echo -e "${GREEN}✓ Grype scan complete for $IMAGE${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Image $IMAGE not found${NC}"
    fi
done

# Scan filesystem/code with Trivy
echo -e "\n${GREEN}Scanning filesystem for vulnerabilities...${NC}"
if command_exists trivy; then
    trivy fs \
        --severity "$SEVERITY_THRESHOLD,HIGH,CRITICAL" \
        --format json \
        --output "$OUTPUT_DIR/trivy-filesystem-$TIMESTAMP.json" \
        "$REPO_ROOT"
    
    trivy fs \
        --severity "$SEVERITY_THRESHOLD,HIGH,CRITICAL" \
        --format table \
        --output "$OUTPUT_DIR/trivy-filesystem-$TIMESTAMP.txt" \
        "$REPO_ROOT"
    
    echo -e "${GREEN}✓ Filesystem scan complete${NC}"
fi

# Scan Python dependencies
echo -e "\n${GREEN}Scanning Python dependencies...${NC}"
if [ -f "$REPO_ROOT/backend/requirements.txt" ] && command_exists safety; then
    safety check \
        --file "$REPO_ROOT/backend/requirements.txt" \
        --json \
        --output "$OUTPUT_DIR/safety-python-$TIMESTAMP.json" || true
    
    safety check \
        --file "$REPO_ROOT/backend/requirements.txt" \
        --output "$OUTPUT_DIR/safety-python-$TIMESTAMP.txt" || true
    
    echo -e "${GREEN}✓ Python dependency scan complete${NC}"
elif [ -f "$REPO_ROOT/backend/requirements.txt" ]; then
    echo -e "${YELLOW}⚠ safety not installed. Install with: pip install safety${NC}"
fi

# Scan Node.js dependencies
echo -e "\n${GREEN}Scanning Node.js dependencies...${NC}"
if [ -f "$REPO_ROOT/librechat/package.json" ]; then
    cd "$REPO_ROOT/librechat"
    
    if command_exists npm; then
        npm audit --json > "$OUTPUT_DIR/npm-audit-$TIMESTAMP.json" 2>&1 || true
        npm audit > "$OUTPUT_DIR/npm-audit-$TIMESTAMP.txt" 2>&1 || true
        echo -e "${GREEN}✓ npm audit complete${NC}"
    fi
    
    cd "$REPO_ROOT"
fi

# Generate consolidated report
echo -e "\n${GREEN}Generating consolidated report...${NC}"

cat > "$OUTPUT_DIR/vulnerability-report-$TIMESTAMP.md" << EOF
# Vulnerability Scan Report
**Generated**: $(date)
**System**: FedChat Chatbot System
**Severity Threshold**: $SEVERITY_THRESHOLD and above

## Scan Tools
- Trivy: $(trivy --version 2>/dev/null | head -1 || echo "Not available")
- Grype: $(grype version 2>/dev/null | head -1 || echo "Not available")
- Safety: $(safety --version 2>/dev/null || echo "Not available")
- npm audit: $(npm --version 2>/dev/null || echo "Not available")

## Scanned Components

### Docker Images
$(for IMAGE in "${IMAGES[@]}"; do
    IMAGE_NAME=$(echo "$IMAGE" | tr ':/' '-')
    echo "- **$IMAGE**"
    if [ -f "$OUTPUT_DIR/trivy-$IMAGE_NAME-$TIMESTAMP.json" ]; then
        CRITICAL=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity=="CRITICAL")] | length' "$OUTPUT_DIR/trivy-$IMAGE_NAME-$TIMESTAMP.json" 2>/dev/null || echo "0")
        HIGH=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity=="HIGH")] | length' "$OUTPUT_DIR/trivy-$IMAGE_NAME-$TIMESTAMP.json" 2>/dev/null || echo "0")
        MEDIUM=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity=="MEDIUM")] | length' "$OUTPUT_DIR/trivy-$IMAGE_NAME-$TIMESTAMP.json" 2>/dev/null || echo "0")
        echo "  - Critical: $CRITICAL, High: $HIGH, Medium: $MEDIUM"
    fi
done)

### Dependencies
- Python (requirements.txt): \`safety-python-$TIMESTAMP.json\`
- Node.js (package.json): \`npm-audit-$TIMESTAMP.json\`
- Filesystem scan: \`trivy-filesystem-$TIMESTAMP.json\`

## Summary

EOF

# Count total vulnerabilities
TOTAL_CRITICAL=0
TOTAL_HIGH=0
TOTAL_MEDIUM=0

for file in "$OUTPUT_DIR"/trivy-*-$TIMESTAMP.json; do
    if [ -f "$file" ]; then
        CRITICAL=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity=="CRITICAL")] | length' "$file" 2>/dev/null || echo "0")
        HIGH=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity=="HIGH")] | length' "$file" 2>/dev/null || echo "0")
        MEDIUM=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity=="MEDIUM")] | length' "$file" 2>/dev/null || echo "0")
        
        TOTAL_CRITICAL=$((TOTAL_CRITICAL + CRITICAL))
        TOTAL_HIGH=$((TOTAL_HIGH + HIGH))
        TOTAL_MEDIUM=$((TOTAL_MEDIUM + MEDIUM))
    fi
done

cat >> "$OUTPUT_DIR/vulnerability-report-$TIMESTAMP.md" << EOF
| Severity | Count |
|----------|-------|
| Critical | $TOTAL_CRITICAL |
| High     | $TOTAL_HIGH |
| Medium   | $TOTAL_MEDIUM |

## Recommendations

1. **Critical Vulnerabilities**: Address immediately (within 15 days)
2. **High Vulnerabilities**: Address within 30 days
3. **Medium Vulnerabilities**: Address within 90 days

## Next Steps

1. Review detailed reports in \`$OUTPUT_DIR\`
2. Create POA&M items for unmitigated vulnerabilities
3. Schedule patching and updates
4. Re-scan after remediation
5. Update SBOM after dependency changes

## Reports Location

All scan results are in: \`$OUTPUT_DIR\`

- Trivy scans: \`trivy-*-$TIMESTAMP.*\`
- Grype scans: \`grype-*-$TIMESTAMP.*\`
- Dependency scans: \`safety-*-$TIMESTAMP.*\`, \`npm-audit-$TIMESTAMP.*\`

EOF

echo -e "${GREEN}✓ Consolidated report generated${NC}"

# Create latest symlinks
for file in "$OUTPUT_DIR"/*-$TIMESTAMP.*; do
    if [ -f "$file" ]; then
        basename=$(basename "$file" | sed "s/-$TIMESTAMP//")
        ln -sf "$(basename "$file")" "$OUTPUT_DIR/latest-$basename"
    fi
done

# Print summary
echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}Vulnerability Scan Complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "\n${YELLOW}Summary:${NC}"
echo -e "  Critical: ${RED}$TOTAL_CRITICAL${NC}"
echo -e "  High:     ${YELLOW}$TOTAL_HIGH${NC}"
echo -e "  Medium:   $TOTAL_MEDIUM"
echo -e "\nReports saved to: ${YELLOW}$OUTPUT_DIR${NC}"
echo -e "View report: ${YELLOW}cat $OUTPUT_DIR/vulnerability-report-$TIMESTAMP.md${NC}"

# Exit with error if critical vulnerabilities found
if [ "$TOTAL_CRITICAL" -gt 0 ]; then
    echo -e "\n${RED}⚠ CRITICAL VULNERABILITIES FOUND!${NC}"
    echo -e "${RED}Immediate remediation required.${NC}"
    exit 1
elif [ "$TOTAL_HIGH" -gt 10 ]; then
    echo -e "\n${YELLOW}⚠ High number of HIGH severity vulnerabilities found.${NC}"
    exit 1
fi

echo -e "\n${GREEN}Done!${NC}"
