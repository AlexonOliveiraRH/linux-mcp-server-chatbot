#!/bin/bash
# Simple single-architecture build script
# Use this if you only need to build for your current platform

set -e

# Configuration
IMAGE_REGISTRY="${IMAGE_REGISTRY:-quay.io/your-org}"
IMAGE_NAME="${IMAGE_NAME:-linux-mcp-chatbot}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

FULL_IMAGE="${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "========================================"
echo "Building Linux MCP Chatbot Container"
echo "Single Architecture Build"
echo "========================================"
echo "Image: ${FULL_IMAGE}"
echo "========================================"

# Detect container runtime
if command -v podman &> /dev/null; then
    CONTAINER_RUNTIME="podman"
    echo "Using: Podman"
elif command -v docker &> /dev/null; then
    CONTAINER_RUNTIME="docker"
    echo "Using: Docker"
else
    echo "ERROR: Neither podman nor docker found"
    exit 1
fi

# Build for current platform
echo "Building image..."
${CONTAINER_RUNTIME} build \
    --tag "${FULL_IMAGE}" \
    --file Dockerfile.chatbot \
    ..

echo ""
echo "Pushing image..."
${CONTAINER_RUNTIME} push "${FULL_IMAGE}"

echo "========================================"
echo "Build complete!"
echo "Image: ${FULL_IMAGE}"
echo "========================================"
echo ""
echo "To run locally:"
echo "  ${CONTAINER_RUNTIME} run -p 8501:8501 \\"
echo "    -e MCP_SERVER_URL=http://mcp-server:8000 \\"
echo "    -e MODEL_ENDPOINT=https://vertex-ai-anthropic \\"
echo "    -e MODEL_NAME=claude-sonnet-4-5@20250929 \\"
echo "    -e GOOGLE_PROJECT_ID=your-project \\"
echo "    ${FULL_IMAGE}"
