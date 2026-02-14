# Build script for hardened Docker images
# Supports Iron Bank, Red Hat UBI, and Distroless variants

#!/bin/bash
set -e

# Configuration
REGISTRY="${REGISTRY:-}"
IMAGE_PREFIX="${IMAGE_PREFIX:-fedchat}"
VERSION="${VERSION:-latest}"
HARDENED_TYPE="${1:-ubi}"  # ironbank, ubi, or distroless

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=================================================="
echo "Building Hardened FedChat Images"
echo "=================================================="
echo ""
echo "Type: ${HARDENED_TYPE}"
echo "Registry: ${REGISTRY:-<none>}"
echo "Version: ${VERSION}"
echo ""

# Validate hardened type
if [[ ! "$HARDENED_TYPE" =~ ^(ironbank|ubi|distroless)$ ]]; then
    echo -e "${RED}Error: Invalid hardened type. Use: ironbank, ubi, or distroless${NC}"
    exit 1
fi

# Check registry authentication for Iron Bank
if [ "$HARDENED_TYPE" == "ironbank" ]; then
    echo -e "${YELLOW}Note: Iron Bank requires authentication to registry1.dso.mil${NC}"
    echo "Make sure you're logged in: docker login registry1.dso.mil"
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

# Build backend
echo -e "${GREEN}Building backend (${HARDENED_TYPE})...${NC}"
docker build \
    -f backend/Dockerfile.${HARDENED_TYPE} \
    -t ${REGISTRY:+$REGISTRY/}${IMAGE_PREFIX}-backend:${VERSION}-${HARDENED_TYPE} \
    -t ${REGISTRY:+$REGISTRY/}${IMAGE_PREFIX}-backend:${HARDENED_TYPE} \
    ./backend

echo -e "${GREEN}✓ Backend built successfully${NC}"
echo ""

# Build frontend
echo -e "${GREEN}Building frontend (${HARDENED_TYPE})...${NC}"
docker build \
    -f librechat/Dockerfile.${HARDENED_TYPE} \
    -t ${REGISTRY:+$REGISTRY/}${IMAGE_PREFIX}-frontend:${VERSION}-${HARDENED_TYPE} \
    -t ${REGISTRY:+$REGISTRY/}${IMAGE_PREFIX}-frontend:${HARDENED_TYPE} \
    --build-arg AGENCY_NAME="${AGENCY_NAME:-Federal Agency}" \
    --build-arg AGENCY_PRIMARY_COLOR="${AGENCY_PRIMARY_COLOR:-#002868}" \
    ./librechat

echo -e "${GREEN}✓ Frontend built successfully${NC}"
echo ""

# Scan images for vulnerabilities
echo -e "${YELLOW}Scanning images for vulnerabilities...${NC}"

if command -v trivy &> /dev/null; then
    echo "Backend scan:"
    trivy image --severity HIGH,CRITICAL ${REGISTRY:+$REGISTRY/}${IMAGE_PREFIX}-backend:${VERSION}-${HARDENED_TYPE}
    echo ""
    echo "Frontend scan:"
    trivy image --severity HIGH,CRITICAL ${REGISTRY:+$REGISTRY/}${IMAGE_PREFIX}-frontend:${VERSION}-${HARDENED_TYPE}
else
    echo -e "${YELLOW}Trivy not installed. Skipping vulnerability scan.${NC}"
    echo "Install: https://github.com/aquasecurity/trivy"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}Build Complete!${NC}"
echo "=================================================="
echo ""
echo "Images created:"
echo "  - ${REGISTRY:+$REGISTRY/}${IMAGE_PREFIX}-backend:${VERSION}-${HARDENED_TYPE}"
echo "  - ${REGISTRY:+$REGISTRY/}${IMAGE_PREFIX}-frontend:${VERSION}-${HARDENED_TYPE}"
echo ""

if [ -n "$REGISTRY" ]; then
    read -p "Push images to registry? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Pushing images...${NC}"
        docker push ${REGISTRY}/${IMAGE_PREFIX}-backend:${VERSION}-${HARDENED_TYPE}
        docker push ${REGISTRY}/${IMAGE_PREFIX}-backend:${HARDENED_TYPE}
        docker push ${REGISTRY}/${IMAGE_PREFIX}-frontend:${VERSION}-${HARDENED_TYPE}
        docker push ${REGISTRY}/${IMAGE_PREFIX}-frontend:${HARDENED_TYPE}
        echo -e "${GREEN}✓ Images pushed successfully${NC}"
    fi
else
    echo "To push images, set REGISTRY environment variable:"
    echo "  export REGISTRY=registry1.dso.mil/yourorg"
    echo "  ./scripts/build_hardened.sh ${HARDENED_TYPE}"
fi

echo ""
echo "To use in docker-compose:"
echo "  sed -i 's|build:|image: ${REGISTRY:+$REGISTRY/}${IMAGE_PREFIX}-backend:${HARDENED_TYPE}\\n    #build:|' docker-compose.yml"
echo ""
