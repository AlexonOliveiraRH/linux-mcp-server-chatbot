#!/bin/bash
# Script to create Kubernetes secrets for the chatbot

set -e

NAMESPACE="${NAMESPACE:-linux-mcp-chatbot}"

echo "Creating secrets for Linux MCP Chatbot"
echo "Namespace: ${NAMESPACE}"
echo ""

# Function to check if file exists
check_file() {
    if [ ! -f "$1" ]; then
        echo "Error: File not found: $1"
        exit 1
    fi
}

# ============================================================
# 1. Create namespace
# ============================================================
echo "1. Creating namespace..."
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# ============================================================
# 2. Create GCP credentials secret (for Vertex AI)
# ============================================================
if [ -f "gcp-credentials.json" ]; then
    echo "2. Creating GCP credentials secret..."
    kubectl create secret generic chatbot-secrets \
        --from-file=gcp-credentials.json=gcp-credentials.json \
        --from-literal=GOOGLE_PROJECT_ID=${GOOGLE_PROJECT_ID:-your-project-id} \
        --namespace=${NAMESPACE} \
        --dry-run=client -o yaml | kubectl apply -f -
    echo "   ✓ GCP credentials added"
else
    echo "2. Skipping GCP credentials (file not found)"
fi

# ============================================================
# 3. Create API keys secret (for OpenAI, Anthropic, etc.)
# ============================================================
echo "3. Creating API keys secret..."

# Check which keys are available
SECRET_DATA=""

if [ ! -z "${OPENAI_API_KEY}" ]; then
    SECRET_DATA="${SECRET_DATA} --from-literal=OPENAI_API_KEY=${OPENAI_API_KEY}"
    echo "   ✓ OpenAI API key added"
fi

if [ ! -z "${ANTHROPIC_API_KEY}" ]; then
    SECRET_DATA="${SECRET_DATA} --from-literal=ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}"
    echo "   ✓ Anthropic API key added"
fi

if [ ! -z "${GOOGLE_API_KEY}" ]; then
    SECRET_DATA="${SECRET_DATA} --from-literal=GOOGLE_API_KEY=${GOOGLE_API_KEY}"
    echo "   ✓ Google API key added"
fi

if [ ! -z "${GOOGLE_PROJECT_ID}" ]; then
    SECRET_DATA="${SECRET_DATA} --from-literal=GOOGLE_PROJECT_ID=${GOOGLE_PROJECT_ID}"
    echo "   ✓ GCP Project ID added"
fi

if [ ! -z "${SECRET_DATA}" ]; then
    kubectl create secret generic chatbot-secrets \
        ${SECRET_DATA} \
        --namespace=${NAMESPACE} \
        --dry-run=client -o yaml | kubectl apply -f -
else
    echo "   ⚠ No API keys provided"
fi

# ============================================================
# 4. Create SSH private key secret (for remote host access)
# ============================================================
if [ -f "${SSH_PRIVATE_KEY:-~/.ssh/id_rsa}" ]; then
    echo "4. Creating SSH private key secret..."
    SSH_KEY_FILE="${SSH_PRIVATE_KEY:-~/.ssh/id_rsa}"
    kubectl create secret generic chatbot-secrets \
        --from-file=ssh-privatekey=${SSH_KEY_FILE} \
        --namespace=${NAMESPACE} \
        --dry-run=client -o yaml | kubectl apply -f -
    echo "   ✓ SSH private key added"
else
    echo "4. Skipping SSH key (file not found at ${SSH_PRIVATE_KEY:-~/.ssh/id_rsa})"
fi

echo ""
echo "✅ Secrets created successfully!"
echo ""
echo "To verify:"
echo "  kubectl get secrets -n ${NAMESPACE}"
echo ""
echo "Next steps:"
echo "  1. Update k8s/base/configmap.yaml with your model configuration"
echo "  2. Deploy: kubectl apply -k k8s/base/"
echo "  3. Or use overlay: kubectl apply -k k8s/overlays/opendatahub/"
