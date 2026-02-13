#!/bin/bash
# Build script for Linux MCP Chatbot container
# Supports both Docker (buildx) and Podman (manifest)

set -e

# Configuration
IMAGE_REGISTRY="${IMAGE_REGISTRY:-quay.io/your-org}"
IMAGE_NAME="${IMAGE_NAME:-linux-mcp-chatbot}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"

FULL_IMAGE="${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "========================================"
echo "Building Linux MCP Chatbot Container"
echo "========================================"
echo "Image: ${FULL_IMAGE}"
echo "Platforms: ${PLATFORMS}"
echo "========================================"

# Detect container runtime
if command -v podman &> /dev/null; then
    CONTAINER_RUNTIME="podman"
    echo "Detected: Podman"
elif command -v docker &> /dev/null; then
    CONTAINER_RUNTIME="docker"
    echo "Detected: Docker"
else
    echo "ERROR: Neither podman nor docker found"
    exit 1
fi

# Build based on runtime
if [ "$CONTAINER_RUNTIME" = "podman" ]; then
    echo "Building with Podman manifest..."

    # Parse platforms into array
    IFS=',' read -ra PLATFORM_ARRAY <<< "$PLATFORMS"

    # Build images for each platform
    MANIFEST_IMAGES=()
    for PLATFORM in "${PLATFORM_ARRAY[@]}"; do
        PLATFORM_TAG="${FULL_IMAGE}-${PLATFORM//\//-}"
        echo "Building for platform: ${PLATFORM}"

        podman build \
            --platform "${PLATFORM}" \
            --tag "${PLATFORM_TAG}" \
            --file Dockerfile.chatbot \
            --format docker \
            ..

        MANIFEST_IMAGES+=("${PLATFORM_TAG}")
    done

    # Create and push manifest
    echo "Creating manifest: ${FULL_IMAGE}"
    podman manifest rm "${FULL_IMAGE}" 2>/dev/null || true
    podman manifest create "${FULL_IMAGE}"

    for IMG in "${MANIFEST_IMAGES[@]}"; do
        echo "Adding to manifest: ${IMG}"
        podman manifest add "${FULL_IMAGE}" "${IMG}"
    done

    echo "Pushing manifest: ${FULL_IMAGE}"
    podman manifest push "${FULL_IMAGE}"

    # Optional: Clean up platform-specific images
    echo "Cleaning up platform-specific tags..."
    for IMG in "${MANIFEST_IMAGES[@]}"; do
        podman rmi "${IMG}" 2>/dev/null || true
    done

elif [ "$CONTAINER_RUNTIME" = "docker" ]; then
    echo "Building with Docker buildx..."

    # Check if buildx is available
    if ! docker buildx version &> /dev/null; then
        echo "ERROR: docker buildx is not available"
        echo "Please install Docker with buildx support"
        exit 1
    fi

    # Create buildx builder if it doesn't exist
    if ! docker buildx inspect multiarch-builder &> /dev/null; then
        echo "Creating multiarch builder..."
        docker buildx create --name multiarch-builder --use
    fi

    # Use the multiarch builder
    docker buildx use multiarch-builder

    # Build and push
    echo "Building and pushing image..."
    docker buildx build \
        --platform "${PLATFORMS}" \
        --tag "${FULL_IMAGE}" \
        --push \
        --file Dockerfile.chatbot \
        ..
fi

echo "========================================"
echo "Build complete!"
echo "Image: ${FULL_IMAGE}"
echo "========================================"
echo ""
echo "To use this image:"
echo "  ${CONTAINER_RUNTIME} pull ${FULL_IMAGE}"
echo ""
echo "To run locally:"
echo "  ${CONTAINER_RUNTIME} run -p 8501:8501 \\"
echo "    -e MCP_SERVER_URL=http://mcp-server:8000 \\"
echo "    -e MODEL_ENDPOINT=https://vertex-ai-anthropic \\"
echo "    -e MODEL_NAME=claude-sonnet-4-5@20250929 \\"
echo "    -e GOOGLE_PROJECT_ID=your-project \\"
echo "    ${FULL_IMAGE}"
