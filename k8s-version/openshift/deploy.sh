#!/bin/bash
# Quick deployment script for Linux MCP Chatbot on OpenShift

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================"
echo "Linux MCP Chatbot - OpenShift Deployment"
echo -e "========================================${NC}"

# Configuration
NAMESPACE="${NAMESPACE:-linux-mcp-server-chatbot}"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-quay.io/your-org}"
CHATBOT_IMAGE="${IMAGE_REGISTRY}/linux-mcp-chatbot:latest"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v oc &> /dev/null; then
    echo -e "${RED}ERROR: oc CLI not found. Please install OpenShift CLI.${NC}"
    exit 1
fi

if ! oc whoami &> /dev/null; then
    echo -e "${RED}ERROR: Not logged in to OpenShift. Run 'oc login' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}"

# Step 1: Create namespace
echo -e "\n${YELLOW}Step 1: Creating namespace...${NC}"
oc apply -f 00-namespace.yaml
echo -e "${GREEN}✓ Namespace created${NC}"

# Step 2: Check for SSH secret
echo -e "\n${YELLOW}Step 2: Checking SSH secrets...${NC}"
if ! oc get secret linux-mcp-ssh -n ${NAMESPACE} &> /dev/null; then
    echo -e "${RED}WARNING: SSH secret 'linux-mcp-ssh' not found.${NC}"
    echo "Create it with:"
    echo "  oc create secret generic linux-mcp-ssh \\"
    echo "    --from-file=ssh-privatekey=\$HOME/.ssh/id_ed25519 \\"
    echo "    --from-file=config=\$HOME/.ssh/config \\"
    echo "    -n ${NAMESPACE}"
    read -p "Press Enter to continue or Ctrl+C to abort..."
else
    echo -e "${GREEN}✓ SSH secret found${NC}"
fi

# Step 3: Check for GCP credentials
echo -e "\n${YELLOW}Step 3: Checking GCP credentials...${NC}"
if ! oc get secret chatbot-gcp-credentials -n ${NAMESPACE} &> /dev/null; then
    echo -e "${RED}WARNING: GCP credentials secret not found.${NC}"
    echo "Create it with:"
    echo "  oc create secret generic chatbot-gcp-credentials \\"
    echo "    --from-file=gcp-credentials.json=/path/to/sa.json \\"
    echo "    -n ${NAMESPACE}"
    read -p "Press Enter to continue or Ctrl+C to abort..."
else
    echo -e "${GREEN}✓ GCP credentials found${NC}"
fi

# Step 4: Check for API keys
echo -e "\n${YELLOW}Step 4: Checking API keys...${NC}"
if ! oc get secret chatbot-api-keys -n ${NAMESPACE} &> /dev/null; then
    echo -e "${RED}WARNING: API keys secret not found.${NC}"
    echo "Create it with:"
    echo "  oc create secret generic chatbot-api-keys \\"
    echo "    --from-literal=GOOGLE_PROJECT_ID=your-project-id \\"
    echo "    -n ${NAMESPACE}"
    read -p "Press Enter to continue or Ctrl+C to abort..."
else
    echo -e "${GREEN}✓ API keys found${NC}"
fi

# Step 5: Deploy Chatbot ConfigMap
echo -e "\n${YELLOW}Step 5: Deploying Chatbot ConfigMap...${NC}"
oc apply -f 01-chatbot-configmap.yaml
echo -e "${GREEN}✓ ConfigMap deployed${NC}"

# Step 6: Deploy Chatbot
echo -e "\n${YELLOW}Step 6: Deploying Chatbot...${NC}"
echo "Using image: ${CHATBOT_IMAGE}"

# Update image in deployment
sed "s|image: quay.io/your-org/linux-mcp-chatbot:latest|image: ${CHATBOT_IMAGE}|g" \
  02-chatbot-deployment.yaml | oc apply -f -

oc apply -f 03-chatbot-service.yaml
oc apply -f 04-chatbot-route.yaml
echo -e "${GREEN}✓ Chatbot deployed${NC}"

# Wait for chatbot to be ready
echo -e "\n${YELLOW}Waiting for chatbot to be ready...${NC}"
oc wait --for=condition=available --timeout=180s \
  deployment/linux-mcp-chatbot -n ${NAMESPACE} || {
  echo -e "${RED}WARNING: Chatbot not ready after 180s${NC}"
  echo "Check logs with: oc logs deployment/linux-mcp-chatbot -n ${NAMESPACE}"
}

# Get the route URL
echo -e "\n${GREEN}========================================"
echo "Deployment Complete!"
echo -e "========================================${NC}"

ROUTE_URL=$(oc get route linux-mcp-chatbot -n ${NAMESPACE} -o jsonpath='{.spec.host}')
if [ -n "$ROUTE_URL" ]; then
    echo -e "\n${GREEN}Access the chatbot at:${NC}"
    echo -e "  ${GREEN}https://${ROUTE_URL}${NC}"
else
    echo -e "\n${YELLOW}Route not found. Get it with:${NC}"
    echo "  oc get route linux-mcp-chatbot -n ${NAMESPACE}"
fi

# Show pod status
echo -e "\n${YELLOW}Pod Status:${NC}"
oc get pods -n ${NAMESPACE}

# Show logs command
echo -e "\n${YELLOW}To view logs:${NC}"
echo "  oc logs -f deployment/linux-mcp-chatbot -n ${NAMESPACE}"

echo -e "\n${GREEN}✓ All done!${NC}"
