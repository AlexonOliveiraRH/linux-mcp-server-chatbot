# 🐧 Linux MCP Server Chatbot - Kubernetes Version

Containerized deployment of the AI-powered Linux diagnostics chatbot for Kubernetes, OpenDataHub, and Red Hat OpenShift AI.

## ✨ Features

- **🐳 Containerized** - Runs in Kubernetes, OpenShift, OpenDataHub, RHOAI
- **🔄 Multiple Runtimes** - Support for 10+ inference server types
- **🤖 Multiple Models** - Works with Granite, Mistral, Llama, Gemma, Claude, GPT, and more
- **🌐 Remote Access** - SSH to any Linux host from containers
- **📊 Platform Optimized** - Specific configs for OpenDataHub, RHOAI, vanilla K8s
- **🔐 Secure** - Non-root containers, secrets management, RBAC

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│               Kubernetes/OpenShift Cluster               │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  linux-mcp-chatbot Pod                          │   │
│  │                                                  │   │
│  │  ┌──────────────────────────────────────────┐  │   │
│  │  │  Streamlit UI (Port 8501)                │  │   │
│  │  └──────────────────┬───────────────────────┘  │   │
│  │                     │                           │   │
│  │  ┌──────────────────▼───────────────────────┐  │   │
│  │  │  LangChain Agent + MCP Client            │  │   │
│  │  └──────────┬────────────────┬──────────────┘  │   │
│  │             │                │                  │   │
│  │  ┌──────────▼─────────┐  ┌──▼───────────────┐ │   │
│  │  │ Linux MCP Server   │  │ Inference Model  │ │   │
│  │  │ (subprocess)       │  │ (HTTP API)       │ │   │
│  │  └──────────┬─────────┘  └──────────────────┘ │   │
│  │             │                                   │   │
│  │  ┌──────────▼─────────┐                        │   │
│  │  │ SSH to Remote      │                        │   │
│  │  │ Linux Hosts        │                        │   │
│  │  └────────────────────┘                        │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  Inference Models (choose one):                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ vLLM Pod    │  │ Caikit Pod   │  │ Claude       │  │
│  │ (Granite)   │  │ (Mistral)    │  │ (Vertex AI)  │  │
│  └─────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure

```
k8s-version/
├── docker/                    # Container image files
│   ├── Dockerfile            # Multi-arch Dockerfile
│   ├── .dockerignore         # Build exclusions
│   └── build.sh              # Build script
│
├── k8s/                      # Kubernetes manifests
│   ├── base/                 # Base manifests (platform-agnostic)
│   │   ├── namespace.yaml
│   │   ├── serviceaccount.yaml
│   │   ├── configmap.yaml    # Model configuration
│   │   ├── secret.yaml       # Credentials template
│   │   ├── deployment.yaml   # Pod spec
│   │   ├── service.yaml
│   │   ├── route.yaml        # OpenShift Route
│   │   ├── ingress.yaml      # K8s Ingress
│   │   └── kustomization.yaml
│   │
│   └── overlays/             # Platform-specific overlays
│       ├── opendatahub/      # OpenDataHub deployment
│       ├── openshift-ai/     # Red Hat OpenShift AI
│       └── kubernetes/       # Vanilla Kubernetes
│
├── config/                   # Configuration helpers
│   ├── create-secrets.sh     # Secret creation script
│   └── examples/             # Example configurations
│       ├── claude-vertex.env
│       ├── vllm-granite.env
│       ├── caikit-tgis-granite.env
│       ├── ollama.env
│       └── openai.env
│
└── docs/                     # Documentation
    ├── DEPLOYMENT.md         # Deployment guide
    ├── MODELS.md             # Model configuration
    └── TROUBLESHOOTING.md    # Common issues
```

## 🚀 Quick Start

### Prerequisites

- Kubernetes 1.24+ or OpenShift 4.12+
- kubectl or oc CLI configured
- Container registry access (for pushing images)
- Model inference service deployed (or cloud API credentials)

### Option 1: Deploy with Claude via Vertex AI (Recommended)

**1. Build and push container image:**

```bash
cd docker/
export IMAGE_REGISTRY=quay.io/your-org
export IMAGE_NAME=linux-mcp-chatbot
export IMAGE_TAG=v1.0.0
./build.sh
```

**2. Create secrets:**

```bash
cd ../config/

# Set your GCP project ID
export GOOGLE_PROJECT_ID=your-gcp-project-id

# Create secrets with GCP credentials
kubectl create secret generic chatbot-secrets \
  --from-file=gcp-credentials.json=/path/to/service-account.json \
  --from-literal=GOOGLE_PROJECT_ID=${GOOGLE_PROJECT_ID} \
  -n linux-mcp-chatbot

# Create SSH key secret (for remote host access)
kubectl create secret generic chatbot-secrets \
  --from-file=ssh-privatekey=~/.ssh/id_rsa \
  -n linux-mcp-chatbot
```

**3. Deploy to Kubernetes:**

```bash
cd ../k8s/

# Edit base/configmap.yaml - ensure it has:
# MODEL_ENDPOINT: "https://vertex-ai-anthropic"
# MODEL_NAME: "claude-sonnet-4-5@20250929"
# GOOGLE_LOCATION: "us-east5"

# Deploy
kubectl apply -k base/
```

**4. Access the chatbot:**

```bash
# Port forward
kubectl port-forward -n linux-mcp-chatbot svc/linux-mcp-chatbot 8501:8501

# Open browser to http://localhost:8501
```

### Option 2: Deploy to OpenDataHub with vLLM + Granite

**1. Deploy Granite model via vLLM in OpenDataHub:**

```bash
# Create ServingRuntime and InferenceService
# (See OpenDataHub documentation)
```

**2. Update configuration:**

```bash
# Use the OpenDataHub overlay
cd k8s/overlays/opendatahub/

# Edit configmap-patch.yaml to point to your vLLM service:
# MODEL_ENDPOINT: "http://granite-vllm.opendatahub.svc.cluster.local:8000"
# MODEL_NAME: "ibm/granite-7b-instruct"
```

**3. Deploy:**

```bash
kubectl apply -k k8s/overlays/opendatahub/
```

### Option 3: Deploy to Red Hat OpenShift AI

**1. Deploy model via RHOAI dashboard**

**2. Use RHOAI overlay:**

```bash
cd k8s/overlays/openshift-ai/

# Edit configmap-patch.yaml with your model service endpoint

# Deploy
oc apply -k .
```

**3. Access via OpenShift Route:**

```bash
oc get route -n redhat-ods-applications linux-mcp-chatbot
```

## 🔧 Configuration

### Supported Inference Runtimes

| Runtime | Models | Example Endpoint |
|---------|--------|------------------|
| **vLLM** | Granite, Mistral, Llama, Mixtral | `http://vllm-svc:8000` |
| **Caikit+TGIS** | Granite, Mistral | `http://caikit-svc:8085` |
| **TGIS Standalone** | Granite, Mistral | `http://tgis-svc:8033` |
| **OpenVINO** | Gemma, Llama | `http://openvino-svc:8000` |
| **NVIDIA Triton** | Any | `http://triton-svc:8000` |
| **Ollama** | Mistral, Llama, Gemma | `http://ollama-svc:11434` |
| **Llama.cpp** | GGUF models | `http://llamacpp-svc:8080` |
| **Claude (Vertex)** | Claude 3.5 Sonnet | `https://vertex-ai-anthropic` |
| **OpenAI** | GPT-4, ChatGPT | `https://api.openai.com` |
| **Gemini** | Gemini 1.5 Pro | `https://genai.googleapis.com` |

### Example Configurations

See `config/examples/` for complete examples:

- `claude-vertex.env` - Claude via GCP Vertex AI
- `vllm-granite.env` - IBM Granite via vLLM
- `caikit-tgis-granite.env` - Granite via Caikit-TGIS
- `ollama.env` - Self-hosted Ollama
- `openai.env` - OpenAI ChatGPT/GPT-4

### ConfigMap Options

Edit `k8s/base/configmap.yaml`:

```yaml
data:
  # Model configuration
  MODEL_ENDPOINT: "http://your-model-service:8000"
  MODEL_NAME: "your-model-name"

  # MCP configuration
  MCP_COMMAND: "/usr/local/bin/linux-mcp-server"
  LINUX_MCP_USER: "admin"

  # Advanced
  REQUEST_TIMEOUT: "300"
  TOOL_CHOICE: "none"
  MODEL_CONTEXT_TOKENS: "4096"
```

## 🔐 Security

### Non-Root Container

The container runs as user `appuser` (UID 1001) with:
- No root privileges
- Read-only root filesystem
- Dropped capabilities
- Security context constraints

### Secrets Management

Credentials are stored in Kubernetes Secrets:

```bash
# GCP credentials (for Vertex AI)
kubectl create secret generic chatbot-secrets \
  --from-file=gcp-credentials.json=/path/to/key.json

# API keys (for OpenAI, Anthropic, etc.)
kubectl create secret generic chatbot-secrets \
  --from-literal=OPENAI_API_KEY=sk-xxx

# SSH key (for remote hosts)
kubectl create secret generic chatbot-secrets \
  --from-file=ssh-privatekey=~/.ssh/id_rsa
```

### Network Policies

Example network policy (optional):

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: chatbot-netpol
spec:
  podSelector:
    matchLabels:
      app: linux-mcp-chatbot
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector: {}
    ports:
    - port: 8501
  egress:
  - to:
    - podSelector: {}  # Internal cluster
  - to:  # External APIs
    - ipBlock:
        cidr: 0.0.0.0/0
```

## 📊 Monitoring

### Health Checks

The deployment includes:

**Liveness Probe:**
```yaml
httpGet:
  path: /_stcore/health
  port: 8501
initialDelaySeconds: 30
periodSeconds: 10
```

**Readiness Probe:**
```yaml
httpGet:
  path: /_stcore/health
  port: 8501
initialDelaySeconds: 15
periodSeconds: 5
```

### Resource Limits

Default resource allocation:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 1000m
    memory: 1Gi
```

Adjust based on your model size and expected load.

## 🛠️ Troubleshooting

### Pod not starting

```bash
# Check pod status
kubectl get pods -n linux-mcp-chatbot

# View logs
kubectl logs -n linux-mcp-chatbot deployment/linux-mcp-chatbot

# Describe pod for events
kubectl describe pod -n linux-mcp-chatbot <pod-name>
```

### Cannot connect to model

```bash
# Test connectivity from pod
kubectl exec -n linux-mcp-chatbot <pod-name> -- curl -v <MODEL_ENDPOINT>

# Check service DNS
kubectl exec -n linux-mcp-chatbot <pod-name> -- nslookup <service-name>
```

### SSH to remote hosts failing

```bash
# Check SSH key mount
kubectl exec -n linux-mcp-chatbot <pod-name> -- ls -la /home/appuser/.ssh/

# Test SSH manually
kubectl exec -n linux-mcp-chatbot <pod-name> -- ssh -i /home/appuser/.ssh/id_rsa user@host
```

### Tool calls not working

Check the model configuration supports tool calling:
- Claude: ✅ Native tool support
- OpenAI GPT-4: ✅ Function calling
- Granite/Mistral: ⚠️ May need TOOL_CHOICE=none
- Smaller models: ❌ Limited tool support

## 📚 Additional Documentation

- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Detailed deployment guide
- [MODELS.md](docs/MODELS.md) - Model configuration guide
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Common issues

## 🙏 Related Projects

- [Linux MCP Server](https://rhel-lightspeed.github.io/linux-mcp-server/)
- [OpenDataHub](https://opendatahub.io/)
- [Red Hat OpenShift AI](https://www.redhat.com/en/technologies/cloud-computing/openshift/openshift-ai)
- [vLLM](https://github.com/vllm-project/vllm)
- [Ollama](https://ollama.ai/)

---

**Built with ❤️ for cloud-native AI diagnostics**
