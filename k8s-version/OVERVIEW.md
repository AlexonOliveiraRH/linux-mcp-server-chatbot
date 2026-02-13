# Kubernetes Version - Overview

Complete Kubernetes/containerized deployment package for the Linux MCP Server Chatbot.

## 🎯 What's Included

This directory contains everything needed to deploy the chatbot on:
- ✅ **Kubernetes** (vanilla, any distro)
- ✅ **OpenDataHub** (community AI/ML platform)
- ✅ **Red Hat OpenShift AI** (enterprise AI platform)
- ✅ **OpenShift** (Red Hat container platform)

## 📦 Package Contents

### 1. Container Image (`docker/`)

- **Dockerfile** - Multi-architecture (amd64/arm64) container image
- **build.sh** - Automated build script
- **.dockerignore** - Build optimizations

**Features:**
- Non-root user (UID 1001)
- Security hardened
- Multi-platform support
- Health checks included

### 2. Kubernetes Manifests (`k8s/`)

**Base Manifests (`base/`):**
- Namespace
- ServiceAccount + RBAC
- ConfigMap (model configuration)
- Secret (credentials template)
- Deployment (pod spec)
- Service (ClusterIP)
- Route (OpenShift)
- Ingress (Kubernetes)

**Platform Overlays (`overlays/`):**
- `opendatahub/` - OpenDataHub specific configs
- `openshift-ai/` - RHOAI specific configs
- `kubernetes/` - Vanilla K8s configs

### 3. Configuration (`config/`)

- **create-secrets.sh** - Helper script for secrets
- **examples/** - Configuration examples for:
  - Claude via Vertex AI
  - vLLM + Granite
  - Caikit-TGIS + Granite
  - Ollama
  - OpenAI

### 4. Documentation (`docs/`)

- **DEPLOYMENT.md** - Complete deployment guide
- **MODELS.md** - Model configuration reference
- **TROUBLESHOOTING.md** - Common issues & solutions

## 🚀 Quick Start

### 1. Build Container Image

```bash
cd docker/
export IMAGE_REGISTRY=quay.io/your-org
./build.sh
```

### 2. Create Secrets

```bash
cd ../config/

# For Claude via Vertex AI
export GOOGLE_PROJECT_ID=your-project-id
kubectl create secret generic chatbot-secrets \
  --from-file=gcp-credentials.json=/path/to/sa.json \
  --from-literal=GOOGLE_PROJECT_ID=${GOOGLE_PROJECT_ID} \
  -n linux-mcp-chatbot
```

### 3. Deploy

```bash
cd ../k8s/

# Standard Kubernetes
kubectl apply -k base/

# Or OpenDataHub
kubectl apply -k overlays/opendatahub/

# Or Red Hat OpenShift AI
oc apply -k overlays/openshift-ai/
```

### 4. Access

```bash
# Port forward
kubectl port-forward -n linux-mcp-chatbot svc/linux-mcp-chatbot 8501:8501

# Open http://localhost:8501
```

## 🔧 Supported Configurations

### Inference Runtimes

| Runtime | Platform | GPU | CPU | Status |
|---------|----------|-----|-----|--------|
| **vLLM** | ODH, RHOAI, K8s | ✅ | ⚠️ | ✅ Tested |
| **Caikit-TGIS** | RHOAI | ✅ | ✅ | ✅ Tested |
| **TGIS Standalone** | ODH, RHOAI | ✅ | ✅ | ✅ Tested |
| **OpenVINO** | K8s | ⚠️ | ✅ | ✅ Tested |
| **NVIDIA Triton** | K8s | ✅ | ❌ | ⚠️ Experimental |
| **Ollama** | K8s | ✅ | ✅ | ✅ Tested |
| **Llama.cpp** | K8s | ❌ | ✅ | ⚠️ Experimental |
| **Claude (Vertex)** | All | N/A | N/A | ✅ Tested |
| **OpenAI** | All | N/A | N/A | ✅ Tested |

### Models Tested

**Cloud:**
- ✅ Claude 3.5 Sonnet (Vertex AI)
- ✅ GPT-4 Turbo (OpenAI)
- ✅ Gemini 1.5 Pro (Google)

**Self-Hosted:**
- ✅ IBM Granite 7B/13B (vLLM, Caikit-TGIS)
- ✅ Mistral 7B (vLLM, TGIS, Ollama)
- ✅ Meta Llama 3 8B (vLLM, Ollama)
- ✅ Mixtral 8x7B (vLLM)
- ⚠️ Gemma 2B/7B (OpenVINO, Ollama)
- ⚠️ DeepSeek Coder 6.7B (vLLM)

## 📋 Requirements

### Minimum

- Kubernetes 1.24+ or OpenShift 4.12+
- 2 CPU cores
- 4GB RAM
- kubectl/oc CLI configured

### For Cloud Models

- Google Cloud credentials (Claude)
- OpenAI API key (GPT-4)

### For Self-Hosted Models

**Small Models (< 7B):**
- 1x GPU (16GB VRAM) OR
- 4x CPU cores + 16GB RAM

**Medium Models (7-13B):**
- 1x GPU (24GB VRAM) OR
- 8x CPU cores + 32GB RAM

**Large Models (> 13B):**
- 2-4x GPU (40-80GB VRAM)
- 16x CPU cores + 64GB RAM

## 🔍 Directory Tree

```
k8s-version/
├── README.md                  # Main documentation
├── OVERVIEW.md                # This file
│
├── docker/                    # Container image
│   ├── Dockerfile
│   ├── .dockerignore
│   └── build.sh               # Build script
│
├── k8s/                       # Kubernetes manifests
│   ├── base/                  # Base resources
│   │   ├── namespace.yaml
│   │   ├── serviceaccount.yaml
│   │   ├── configmap.yaml     # Model config
│   │   ├── secret.yaml
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── route.yaml         # OpenShift
│   │   ├── ingress.yaml       # Kubernetes
│   │   └── kustomization.yaml
│   │
│   └── overlays/              # Platform-specific
│       ├── opendatahub/
│       │   ├── kustomization.yaml
│       │   ├── configmap-patch.yaml
│       │   └── deployment-patch.yaml
│       ├── openshift-ai/
│       │   ├── kustomization.yaml
│       │   ├── configmap-patch.yaml
│       │   └── deployment-patch.yaml
│       └── kubernetes/
│           ├── kustomization.yaml
│           └── configmap-patch.yaml
│
├── config/                    # Configuration helpers
│   ├── create-secrets.sh      # Secret helper
│   └── examples/              # Example configs
│       ├── claude-vertex.env
│       ├── vllm-granite.env
│       ├── caikit-tgis-granite.env
│       ├── ollama.env
│       └── openai.env
│
└── docs/                      # Documentation
    ├── DEPLOYMENT.md          # How to deploy
    ├── MODELS.md              # Model config guide
    └── TROUBLESHOOTING.md     # Common issues
```

## 🎓 Getting Started

### For Beginners

1. **Read:** [README.md](README.md) - Overview and quick start
2. **Choose:** Pick your platform (K8s, ODH, RHOAI)
3. **Configure:** Use an example from `config/examples/`
4. **Deploy:** Follow [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
5. **Test:** Access chatbot and try a query

### For Experienced Users

1. **Build:** `cd docker/ && ./build.sh`
2. **Secrets:** `cd config/ && ./create-secrets.sh`
3. **Deploy:** `kubectl apply -k k8s/overlays/YOUR_PLATFORM/`
4. **Access:** Port-forward or use Route/Ingress

## 🔐 Security Features

- ✅ Non-root containers (UID 1001)
- ✅ Security contexts enforced
- ✅ Secrets management (no hardcoded credentials)
- ✅ Read-only root filesystem (where possible)
- ✅ Dropped capabilities
- ✅ Network policies ready
- ✅ RBAC with ServiceAccount
- ✅ SSH key permissions (0600)

## 📊 Monitoring

Built-in support for:
- Kubernetes health checks (liveness/readiness)
- Prometheus metrics (annotations included)
- Resource usage tracking (requests/limits)
- Log aggregation (stdout/stderr)

## 🔄 Updates

### Update Configuration

```bash
# Edit ConfigMap
kubectl edit configmap chatbot-config -n linux-mcp-chatbot

# Restart deployment
kubectl rollout restart deployment/linux-mcp-chatbot -n linux-mcp-chatbot
```

### Update Container Image

```bash
# Build new version
cd docker/
export IMAGE_TAG=v1.1.0
./build.sh

# Update and redeploy
cd ../k8s/base/
# Edit kustomization.yaml, change newTag
kubectl apply -k .
```

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Main documentation, quick start |
| [OVERVIEW.md](OVERVIEW.md) | This file - package overview |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Complete deployment guide |
| [docs/MODELS.md](docs/MODELS.md) | Model configuration reference |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues & solutions |

## 🤝 Support

### Common Issues

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

### Getting Help

1. Check pod logs: `kubectl logs -n linux-mcp-chatbot <pod>`
2. Review documentation in `docs/`
3. Test connectivity manually
4. Open issue with logs and configuration

## ✅ Validation Checklist

Before deploying to production:

- [ ] Container image built and pushed
- [ ] Secrets created (credentials, SSH key)
- [ ] ConfigMap updated with model endpoint
- [ ] Resource limits appropriate for load
- [ ] Health checks validated
- [ ] Network policies configured (if needed)
- [ ] Ingress/Route tested
- [ ] SSH to remote hosts working
- [ ] Test query successful
- [ ] Monitoring configured

## 🎯 Next Steps

1. **Deploy your first instance** - Follow [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
2. **Configure your model** - See [docs/MODELS.md](docs/MODELS.md)
3. **Test thoroughly** - Try example queries
4. **Scale if needed** - Add HPA, increase replicas
5. **Monitor** - Set up Prometheus, logs
6. **Secure** - Add NetworkPolicies, TLS

---

**Ready to deploy AI-powered Linux diagnostics in Kubernetes!** 🚀
