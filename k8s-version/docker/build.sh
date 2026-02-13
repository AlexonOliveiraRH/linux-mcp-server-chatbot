#!/bin/bash
# Build and push multi-architecture container image

set -e

# Configuration
IMAGE_NAME="${IMAGE_NAME:-linux-mcp-chatbot}"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-quay.io/your-org}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"

FULL_IMAGE="${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "Building container image..."
echo "Image: ${FULL_IMAGE}"
echo "Platforms: ${PLATFORMS}"
echo ""

# Copy source files to docker context
echo "Copying source files..."
cp ../../app.py .
cp ../../mcp_client.py .
cp ../../claude_vertex_wrapper.py .
cp ../../requirements.txt .

# Build multi-architecture image
echo "Building image..."
docker buildx build \
    --platform "${PLATFORMS}" \
    --tag "${FULL_IMAGE}" \
    --push \
    --file Dockerfile \
    .

echo ""
echo "✅ Image built and pushed: ${FULL_IMAGE}"
echo ""
echo "To use in Kubernetes:"
echo "  Update k8s/base/deployment.yaml with image: ${FULL_IMAGE}"
echo ""
echo "To run locally:"
echo "  docker run -p 8501:8501 ${FULL_IMAGE}"

# Cleanup
rm -f app.py mcp_client.py claude_vertex_wrapper.py requirements.txt
