# Building the Chatbot Container Image

Instructions for building the Linux MCP Chatbot container with Podman or Docker.

## 🔧 Prerequisites

You need **one** of the following:
- **Podman** (recommended for Red Hat/Fedora users)
- **Docker** (with buildx support)

## 🚀 Quick Start (Single Architecture)

**Best for:** Building for your current platform only (fastest)

### Step 1: Set Environment Variables

```bash
export IMAGE_REGISTRY=quay.io/your-username
export IMAGE_NAME=linux-mcp-chatbot
export IMAGE_TAG=latest
```

### Step 2: Login to Registry

```bash
# For Quay.io
podman login quay.io
# Or for Docker Hub
podman login docker.io
```

### Step 3: Build and Push

```bash
./build-single-arch.sh
```

This builds for your current architecture (amd64 or arm64) and pushes to the registry.

---

## 🌐 Multi-Architecture Build

**Best for:** Building for multiple platforms (amd64 + arm64)

### With Podman

```bash
export IMAGE_REGISTRY=quay.io/your-username
export IMAGE_NAME=linux-mcp-chatbot
export IMAGE_TAG=latest

# Optional: specify platforms (default: linux/amd64,linux/arm64)
export PLATFORMS=linux/amd64,linux/arm64

./build-chatbot.sh
```

**How it works:**
1. Builds separate images for each platform
2. Creates a manifest list
3. Pushes manifest to registry
4. Cleans up platform-specific tags

**Time:** ~5-10 minutes (builds each platform sequentially)

### With Docker

```bash
export IMAGE_REGISTRY=quay.io/your-username
export IMAGE_NAME=linux-mcp-chatbot
export IMAGE_TAG=latest

./build-chatbot.sh
```

**How it works:**
1. Uses Docker buildx
2. Builds all platforms in parallel
3. Pushes multi-arch image

**Time:** ~3-5 minutes (parallel builds)

---

## 📝 Build Script Reference

### build-single-arch.sh

**Purpose:** Quick single-platform build

**Supports:**
- ✅ Podman
- ✅ Docker

**Use when:**
- Testing/development
- Building for one platform only
- Want fastest build time

**Example:**
```bash
export IMAGE_REGISTRY=quay.io/your-org
export IMAGE_NAME=linux-mcp-chatbot
export IMAGE_TAG=v1.0.0

./build-single-arch.sh
```

### build-chatbot.sh

**Purpose:** Multi-architecture production build

**Supports:**
- ✅ Podman (manifest)
- ✅ Docker (buildx)

**Use when:**
- Production deployment
- Need multi-arch support
- Deploying to mixed clusters (amd64 + arm64)

**Example:**
```bash
export IMAGE_REGISTRY=quay.io/your-org
export IMAGE_NAME=linux-mcp-chatbot
export IMAGE_TAG=latest
export PLATFORMS=linux/amd64,linux/arm64

./build-chatbot.sh
```

---

## 🔐 Registry Authentication

### Quay.io

```bash
# Login
podman login quay.io

# Or with credentials
podman login -u="your-username" -p="your-password" quay.io
```

### Docker Hub

```bash
podman login docker.io
```

### Private Registry

```bash
podman login your-registry.example.com
```

---

## 🧪 Testing the Image Locally

### Test Single-Architecture Image

```bash
# Run locally
podman run -p 8501:8501 \
  -e MCP_SERVER_URL=http://host.containers.internal:8000 \
  -e MODEL_ENDPOINT=https://vertex-ai-anthropic \
  -e MODEL_NAME=claude-sonnet-4-5@20250929 \
  -e GOOGLE_PROJECT_ID=your-project \
  -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/creds.json \
  -v /path/to/gcp-credentials.json:/tmp/creds.json:ro \
  quay.io/your-username/linux-mcp-chatbot:latest

# Open browser
firefox http://localhost:8501
```

### Test Multi-Architecture Image

```bash
# Pull specific platform
podman pull --platform linux/amd64 quay.io/your-username/linux-mcp-chatbot:latest
podman pull --platform linux/arm64 quay.io/your-username/linux-mcp-chatbot:latest

# Inspect manifest
podman manifest inspect quay.io/your-username/linux-mcp-chatbot:latest
```

---

## 🐛 Troubleshooting

### Podman: "Error creating manifest"

**Issue:** Old manifest exists

**Fix:**
```bash
podman manifest rm quay.io/your-username/linux-mcp-chatbot:latest
./build-chatbot.sh
```

### Podman: "Error building for platform"

**Issue:** QEMU not installed for cross-platform builds

**Fix:**
```bash
# Fedora/RHEL
sudo dnf install qemu-user-static

# Ubuntu/Debian
sudo apt-get install qemu-user-static

# Verify
podman run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

### Docker: "buildx not found"

**Issue:** Docker doesn't have buildx

**Fix:**
```bash
# Use Podman instead
sudo dnf install podman

# Or update Docker to include buildx
```

### Push Failed: "Authentication required"

**Issue:** Not logged in to registry

**Fix:**
```bash
podman login quay.io
# Enter username and password
```

### Build Fails: "Cannot find Dockerfile.chatbot"

**Issue:** Running from wrong directory

**Fix:**
```bash
cd /path/to/k8s-version/docker
./build-chatbot.sh
```

---

## 📊 Build Performance

### Single Architecture (build-single-arch.sh)

| Runtime | Platform | Time | Disk |
|---------|----------|------|------|
| Podman  | amd64    | ~2m  | 1.2GB |
| Podman  | arm64    | ~2m  | 1.2GB |
| Docker  | amd64    | ~2m  | 1.2GB |

### Multi Architecture (build-chatbot.sh)

| Runtime | Platforms | Time | Disk |
|---------|-----------|------|------|
| Podman  | amd64+arm64 | ~5m | 2.4GB |
| Docker  | amd64+arm64 | ~3m | 2.4GB |

**Note:** Times are approximate and depend on CPU, network, and whether layers are cached.

---

## 📁 What Gets Built

### Image Layers

```
FROM python:3.11-slim
├─ System packages (curl, git)
├─ Python dependencies (requirements.txt)
│  ├─ streamlit
│  ├─ langchain
│  ├─ requests
│  └─ google-cloud-aiplatform
└─ Application code
   ├─ app.py
   ├─ mcp_client_http.py
   └─ claude_vertex_wrapper.py
```

### Image Size

- **Compressed:** ~400MB
- **Uncompressed:** ~1.2GB

### Included Platforms (multi-arch)

- `linux/amd64` - Intel/AMD x86_64
- `linux/arm64` - ARM 64-bit (Apple Silicon, AWS Graviton)

---

## ✅ Production Build Checklist

Before building for production:

- [ ] Set correct `IMAGE_REGISTRY` (your registry)
- [ ] Set appropriate `IMAGE_TAG` (use version tags, not `latest`)
- [ ] Logged in to container registry
- [ ] Tested build locally first
- [ ] Verified application code is latest version
- [ ] Requirements.txt is up to date
- [ ] Multi-arch build if deploying to mixed clusters

**Example production build:**

```bash
export IMAGE_REGISTRY=quay.io/your-org
export IMAGE_NAME=linux-mcp-chatbot
export IMAGE_TAG=v1.0.0  # Use semantic versioning

./build-chatbot.sh

# Tag as latest too
podman tag quay.io/your-org/linux-mcp-chatbot:v1.0.0 \
            quay.io/your-org/linux-mcp-chatbot:latest
podman push quay.io/your-org/linux-mcp-chatbot:latest
```

---

## 🎯 Quick Reference

### Single Platform (Fastest)
```bash
export IMAGE_REGISTRY=quay.io/your-username
podman login quay.io
./build-single-arch.sh
```

### Multi Platform (Production)
```bash
export IMAGE_REGISTRY=quay.io/your-username
export IMAGE_TAG=v1.0.0
podman login quay.io
./build-chatbot.sh
```

---

**Ready to build!** 🚀
