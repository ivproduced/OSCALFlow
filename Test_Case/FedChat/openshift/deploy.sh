#!/bin/bash
# OpenShift Deployment Script for FedChat
# This script automates the deployment of FedChat on OpenShift

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="fedchat"
CLUSTER_DOMAIN="${OPENSHIFT_CLUSTER_DOMAIN:-apps.your-cluster.com}"
BACKEND_IMAGE="${BACKEND_IMAGE:-fedchat-backend:latest}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-fedchat-librechat:latest}"

echo -e "${GREEN}FedChat OpenShift Deployment Script${NC}"
echo "===================================="
echo ""

# Check if oc is installed
if ! command -v oc &> /dev/null; then
    echo -e "${RED}Error: oc CLI not found. Please install the OpenShift CLI.${NC}"
    exit 1
fi

# Check if logged in to OpenShift
if ! oc whoami &> /dev/null; then
    echo -e "${RED}Error: Not logged in to OpenShift. Please run 'oc login' first.${NC}"
    exit 1
fi

echo -e "${GREEN}Logged in as: $(oc whoami)${NC}"
echo -e "${GREEN}Current cluster: $(oc whoami --show-server)${NC}"
echo ""

# Function to wait for deployment
wait_for_deployment() {
    local deployment=$1
    local namespace=$2
    echo -e "${YELLOW}Waiting for deployment/$deployment to be ready...${NC}"
    oc rollout status deployment/$deployment -n $namespace --timeout=5m
}

# Function to wait for pods
wait_for_pods() {
    local label=$1
    local namespace=$2
    local count=${3:-1}
    echo -e "${YELLOW}Waiting for pods with label $label to be ready...${NC}"
    while [ $(oc get pods -l $label -n $namespace -o jsonpath='{.items[?(@.status.phase=="Running")].metadata.name}' | wc -w) -lt $count ]; do
        echo -n "."
        sleep 5
    done
    echo ""
}

# Step 1: Create namespace and configuration
echo -e "${YELLOW}Step 1: Creating namespace and configuration...${NC}"
oc apply -f 00-namespace-config.yaml
echo -e "${GREEN}✓ Namespace and configuration created${NC}"
echo ""

# Step 2: Check and update secrets
echo -e "${YELLOW}Step 2: Checking secrets...${NC}"
echo -e "${RED}WARNING: Please ensure you have updated the secrets in 00-namespace-config.yaml${NC}"
echo -e "${RED}Default passwords are NOT secure for production!${NC}"
read -p "Have you updated the secrets? (yes/no): " secrets_updated

if [ "$secrets_updated" != "yes" ]; then
    echo -e "${RED}Please update secrets before continuing. Exiting.${NC}"
    exit 1
fi
echo ""

# Step 3: Create SCC (requires cluster-admin)
echo -e "${YELLOW}Step 3: Creating Security Context Constraints...${NC}"
if oc auth can-i create scc &> /dev/null; then
    oc apply -f 07-security-policies.yaml
    echo -e "${GREEN}✓ Security policies created${NC}"
else
    echo -e "${YELLOW}! You don't have permission to create SCCs. Skipping...${NC}"
    echo -e "${YELLOW}! Ask your cluster admin to apply 07-security-policies.yaml${NC}"
fi
echo ""

# Step 4: Deploy PostgreSQL
echo -e "${YELLOW}Step 4: Deploying PostgreSQL...${NC}"
oc apply -f 01-postgres.yaml
wait_for_deployment "fedchat-postgres" "$NAMESPACE"
echo -e "${GREEN}✓ PostgreSQL deployed${NC}"
echo ""

# Step 5: Deploy Redis
echo -e "${YELLOW}Step 5: Deploying Redis...${NC}"
oc apply -f 02-redis.yaml
wait_for_deployment "fedchat-redis" "$NAMESPACE"
echo -e "${GREEN}✓ Redis deployed${NC}"
echo ""

# Step 6: Deploy Ollama (optional)
read -p "Do you want to deploy Ollama for local LLM? (yes/no): " deploy_ollama
if [ "$deploy_ollama" == "yes" ]; then
    echo -e "${YELLOW}Step 6: Deploying Ollama...${NC}"
    oc apply -f 03-ollama.yaml
    echo -e "${YELLOW}Note: Ollama may take a while to start, especially if pulling large models${NC}"
    echo -e "${GREEN}✓ Ollama deployment created${NC}"
else
    echo -e "${YELLOW}Step 6: Skipping Ollama deployment${NC}"
fi
echo ""

# Step 7: Update image references
echo -e "${YELLOW}Step 7: Updating image references...${NC}"
echo "Backend image: $BACKEND_IMAGE"
echo "Frontend image: $FRONTEND_IMAGE"

# Update backend image
oc set image deployment/fedchat-backend backend=$BACKEND_IMAGE -n $NAMESPACE --dry-run=client
read -p "Update backend image to $BACKEND_IMAGE? (yes/no): " update_backend
if [ "$update_backend" == "yes" ]; then
    sed -i.bak "s|image: fedchat-backend:latest|image: $BACKEND_IMAGE|g" 04-backend.yaml
fi

# Update frontend image
sed -i.bak "s|image: fedchat-librechat:latest|image: $FRONTEND_IMAGE|g" 05-frontend.yaml
echo ""

# Step 8: Deploy backend
echo -e "${YELLOW}Step 8: Deploying backend...${NC}"
oc apply -f 04-backend.yaml
wait_for_deployment "fedchat-backend" "$NAMESPACE"
echo -e "${GREEN}✓ Backend deployed${NC}"
echo ""

# Step 9: Deploy frontend
echo -e "${YELLOW}Step 9: Deploying frontend...${NC}"
oc apply -f 05-frontend.yaml
wait_for_deployment "fedchat-frontend" "$NAMESPACE"
echo -e "${GREEN}✓ Frontend deployed${NC}"
echo ""

# Step 10: Create routes
echo -e "${YELLOW}Step 10: Creating routes...${NC}"
# Update cluster domain in routes
sed -i.bak "s|fedchat.apps.your-cluster.com|fedchat.$CLUSTER_DOMAIN|g" 06-routes.yaml
sed -i.bak "s|fedchat-metrics.apps.your-cluster.com|fedchat-metrics.$CLUSTER_DOMAIN|g" 06-routes.yaml

oc apply -f 06-routes.yaml
echo -e "${GREEN}✓ Routes created${NC}"
echo ""

# Step 11: Display deployment information
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Application URLs:"
echo -e "  Frontend: ${GREEN}https://$(oc get route fedchat -n $NAMESPACE -o jsonpath='{.spec.host}')${NC}"
echo -e "  API: ${GREEN}https://$(oc get route fedchat-api -n $NAMESPACE -o jsonpath='{.spec.host}')${NC}"
echo -e "  Metrics: ${GREEN}https://$(oc get route fedchat-metrics -n $NAMESPACE -o jsonpath='{.spec.host}')${NC}"
echo ""
echo "Pod Status:"
oc get pods -n $NAMESPACE
echo ""
echo "Services:"
oc get svc -n $NAMESPACE
echo ""
echo "Routes:"
oc get routes -n $NAMESPACE
echo ""

# Step 12: Post-deployment tasks
echo -e "${YELLOW}Post-deployment tasks:${NC}"
echo "1. Create an admin user:"
echo "   oc exec -it deployment/fedchat-backend -n $NAMESPACE -- python scripts/create_admin.py"
echo ""
echo "2. Generate API keys:"
echo "   oc exec -it deployment/fedchat-backend -n $NAMESPACE -- python scripts/create_api_key.py"
echo ""
echo "3. Check logs:"
echo "   oc logs -f deployment/fedchat-backend -n $NAMESPACE"
echo "   oc logs -f deployment/fedchat-frontend -n $NAMESPACE"
echo ""
echo "4. Monitor health:"
echo "   curl https://$(oc get route fedchat-api -n $NAMESPACE -o jsonpath='{.spec.host}')/health"
echo ""

echo -e "${GREEN}Deployment script completed successfully!${NC}"
