# Model Configuration Guide

Complete guide to configuring different AI models and inference runtimes with the Linux MCP Chatbot.

## Table of Contents

- [Supported Models](#supported-models)
- [Inference Runtimes](#inference-runtimes)
- [Configuration Examples](#configuration-examples)
- [Performance Tuning](#performance-tuning)
- [Model Selection Guide](#model-selection-guide)

---

## Supported Models

### Cloud-Based Models

| Model | Provider | Best For | Tool Support | Cost |
|-------|----------|----------|--------------|------|
| **Claude 3.5 Sonnet** | Anthropic (Vertex) | Production | ✅ Excellent | $$$ |
| **GPT-4 Turbo** | OpenAI | Complex tasks | ✅ Excellent | $$$$ |
| **Gemini 1.5 Pro** | Google | Multi-modal | ✅ Good | $$ |

### Open Source Models (Self-Hosted)

| Model | Size | Best For | Tool Support | Hardware |
|-------|------|----------|--------------|----------|
| **IBM Granite 7B/13B** | 7-13B | Enterprise | ✅ Good | GPU/CPU |
| **Mistral 7B** | 7B | General purpose | ✅ Good | GPU/CPU |
| **Mixtral 8x7B** | 47B | High quality | ✅ Excellent | GPU |
| **Meta Llama 3 8B/70B** | 8-70B | General purpose | ✅ Good | GPU |
| **DeepSeek Coder 6.7B** | 6.7B | Code generation | ⚠️ Limited | GPU/CPU |
| **Google Gemma 2B/7B** | 2-7B | Low resource | ⚠️ Limited | CPU |
| **Phi-3 Mini/Small** | 3-7B | Edge devices | ⚠️ Limited | CPU |

**Tool Support Legend:**
- ✅ Excellent: Native function calling, reliable
- ✅ Good: Works with TOOL_CHOICE=none
- ⚠️ Limited: May require prompt engineering
- ❌ Poor: Not recommended for tool use

---

## Inference Runtimes

### 1. vLLM ServingRuntime

**Best for:** NVIDIA GPUs, high throughput, production

**Supported Platforms:**
- OpenDataHub
- Red Hat OpenShift AI
- Standalone Kubernetes

**Configuration:**

```yaml
MODEL_ENDPOINT: "http://vllm-service:8000"
MODEL_NAME: "ibm/granite-7b-instruct"
REQUEST_TIMEOUT: "300"
TOOL_CHOICE: "none"
```

**Deployment:**

```bash
# In RHOAI Dashboard:
# 1. Create ServingRuntime: vLLM
# 2. Deploy model: ibm/granite-7b-instruct
# 3. Note the service URL
```

**Models tested:**
- IBM Granite 7B/13B ✅
- Mistral 7B ✅
- Meta Llama 3 8B/70B ✅
- Mixtral 8x7B ✅

### 2. Caikit-TGIS ServingRuntime

**Best for:** Enterprise production, Red Hat support

**Supported Platforms:**
- Red Hat OpenShift AI

**Configuration:**

```yaml
MODEL_ENDPOINT: "http://granite-caikit:8085"
MODEL_NAME: "ibm/granite-13b-chat-v2"
REQUEST_TIMEOUT: "600"
TOOL_CHOICE: "none"
```

**Models tested:**
- IBM Granite 13B Chat ✅
- Mistral 7B Instruct ✅

### 3. TGIS Standalone ServingRuntime

**Best for:** Text generation, CPU/GPU support

**Configuration:**

```yaml
MODEL_ENDPOINT: "http://tgis-service:8033"
MODEL_NAME: "mistralai/Mistral-7B-Instruct-v0.2"
REQUEST_TIMEOUT: "600"
```

**Models tested:**
- Mistral 7B ✅
- IBM Granite variants ✅

### 4. OpenVINO Model Server

**Best for:** Intel CPUs/GPUs, optimized inference

**Configuration:**

```yaml
MODEL_ENDPOINT: "http://openvino-service:8000"
MODEL_NAME: "llama-2-7b-chat"
REQUEST_TIMEOUT: "300"
```

**Hardware:**
- Intel Xeon CPUs ✅
- Intel Gaudi accelerators ✅
- Intel Arc GPUs ✅

### 5. NVIDIA Triton Inference Server

**Best for:** NVIDIA hardware, multiple frameworks

**Configuration:**

```yaml
MODEL_ENDPOINT: "http://triton-service:8000"
MODEL_NAME: "llama-2-13b-chat"
REQUEST_TIMEOUT: "300"
```

### 6. Ollama

**Best for:** Local development, quick testing

**Configuration:**

```yaml
MODEL_ENDPOINT: "http://ollama:11434"
MODEL_NAME: ""  # Leave empty for auto-detection
REQUEST_TIMEOUT: "300"
```

**Models tested:**
- Mistral 7B ✅
- Llama 3 8B ✅
- Gemma 2B ✅

### 7. Llama.cpp

**Best for:** CPU-only environments, GGUF models

**Configuration:**

```yaml
MODEL_ENDPOINT: "http://llamacpp-server:8080"
MODEL_NAME: "llama-2-7b-chat-q4.gguf"
REQUEST_TIMEOUT: "600"
```

### 8. Claude via Google Vertex AI

**Best for:** Production, best quality

**Configuration:**

```yaml
MODEL_ENDPOINT: "https://vertex-ai-anthropic"
MODEL_NAME: "claude-sonnet-4-5@20250929"
GOOGLE_LOCATION: "us-east5"
REQUEST_TIMEOUT: "120"
```

**Requires:**
- GCP Service Account with Vertex AI User role
- `gcp-credentials.json` secret

### 9. OpenAI API

**Best for:** Quick setup, high quality

**Configuration:**

```yaml
MODEL_ENDPOINT: "https://api.openai.com"
MODEL_NAME: "gpt-4-turbo"
REQUEST_TIMEOUT: "120"
TOOL_CHOICE: "auto"
```

**Requires:**
- OPENAI_API_KEY secret

### 10. Google Gemini

**Best for:** Multi-modal tasks

**Configuration:**

```yaml
MODEL_ENDPOINT: "https://genai.googleapis.com"
MODEL_NAME: "gemini-1.5-pro"
REQUEST_TIMEOUT: "120"
```

**Requires:**
- GOOGLE_API_KEY secret

---

## Configuration Examples

### Example 1: Claude via Vertex AI (Production)

**ConfigMap:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: chatbot-config
data:
  MODEL_ENDPOINT: "https://vertex-ai-anthropic"
  MODEL_NAME: "claude-sonnet-4-5@20250929"
  GOOGLE_LOCATION: "us-east5"
  REQUEST_TIMEOUT: "300"
  TOOL_CHOICE: "none"
  MODEL_CONTEXT_TOKENS: "200000"
```

**Secret:**

```bash
kubectl create secret generic chatbot-secrets \
  --from-file=gcp-credentials.json=/path/to/sa.json \
  --from-literal=GOOGLE_PROJECT_ID=your-project \
  -n linux-mcp-chatbot
```

**Performance:**
- Response time: 2-3 seconds
- Tool support: Excellent
- Cost: ~$0.01-0.03 per query
- Reliability: 99.9%

### Example 2: IBM Granite 7B via vLLM (Self-Hosted)

**ConfigMap:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: chatbot-config
data:
  MODEL_ENDPOINT: "http://granite-vllm.opendatahub.svc.cluster.local:8000"
  MODEL_NAME: "ibm/granite-7b-instruct"
  REQUEST_TIMEOUT: "600"
  TOOL_CHOICE: "none"
  MODEL_CONTEXT_TOKENS: "8192"
```

**Hardware Requirements:**
- 1x NVIDIA GPU (16GB VRAM minimum)
- 32GB RAM
- 100GB storage

**Performance:**
- Response time: 5-10 seconds
- Tool support: Good
- Cost: Infrastructure only
- Reliability: Depends on infrastructure

### Example 3: Mistral 7B via Ollama (Development)

**ConfigMap:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: chatbot-config
data:
  MODEL_ENDPOINT: "http://ollama.models.svc.cluster.local:11434"
  MODEL_NAME: ""  # Auto-detect
  REQUEST_TIMEOUT: "300"
  TOOL_CHOICE: "none"
  MODEL_CONTEXT_TOKENS: "4096"
```

**Deploy Ollama:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        command: ["ollama", "serve"]
        env:
        - name: OLLAMA_MODELS
          value: "/models"
        volumeMounts:
        - name: models
          mountPath: /models
      volumes:
      - name: models
        persistentVolumeClaim:
          claimName: ollama-models
```

Pull model:

```bash
kubectl exec -it ollama-pod -- ollama pull mistral
```

### Example 4: Mixtral 8x7B via Caikit-TGIS (Production)

**ConfigMap:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: chatbot-config
data:
  MODEL_ENDPOINT: "http://mixtral-caikit.redhat-ods-applications.svc.cluster.local:8085"
  MODEL_NAME: "mistralai/Mixtral-8x7B-Instruct-v0.1"
  REQUEST_TIMEOUT: "900"
  TOOL_CHOICE: "none"
  MODEL_CONTEXT_TOKENS: "32768"
  MAX_TOOL_OUTPUT_CHARS: "8000"
```

**Hardware Requirements:**
- 4x NVIDIA A100 80GB (or similar)
- 256GB RAM
- 500GB storage

**Performance:**
- Response time: 10-15 seconds
- Tool support: Excellent
- Quality: Very high

---

## Performance Tuning

### Timeout Settings

| Model Size | Recommended Timeout |
|------------|---------------------|
| < 7B params | 300s (5 min) |
| 7-13B params | 600s (10 min) |
| > 13B params | 900s (15 min) |
| Cloud APIs | 120s (2 min) |

### Context Window

```yaml
# For models with large context
MODEL_CONTEXT_TOKENS: "32768"
MAX_TOOL_OUTPUT_CHARS: "8000"

# For models with small context
MODEL_CONTEXT_TOKENS: "4096"
MAX_TOOL_OUTPUT_CHARS: "2400"
```

### Resource Allocation

**For Cloud API Models:**

```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 1000m
    memory: 1Gi
```

**For Self-Hosted Large Models:**

```yaml
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 4000m
    memory: 4Gi
```

---

## Model Selection Guide

### When to Use Claude (Vertex AI)

✅ **Use when:**
- Need best quality responses
- Have GCP infrastructure
- Budget allows (~$0.01-0.03/query)
- Require reliable tool calling
- Production deployment

❌ **Don't use when:**
- No GCP access
- Strict data privacy requirements (cloud)
- Budget constrained
- High query volume (cost)

### When to Use IBM Granite

✅ **Use when:**
- Enterprise deployment on RHOAI
- Need Red Hat support
- On-premise requirements
- Cost-conscious
- 7B-13B size sweet spot

❌ **Don't use when:**
- No GPU available
- Need highest quality (use Claude/GPT-4)
- Very limited resources (use smaller)

### When to Use Mistral/Mixtral

✅ **Use when:**
- Good balance of quality/performance
- Have GPU resources
- Open source requirement
- European data residency

❌ **Don't use when:**
- CPU-only (too slow)
- Need extremely reliable tools (use Claude)

### When to Use Ollama

✅ **Use when:**
- Development/testing
- Quick prototyping
- Local deployment
- Learning/experimentation

❌ **Don't use when:**
- Production workload
- High concurrency needed
- Require best quality

---

## Troubleshooting

### Model Not Responding

```bash
# Test model endpoint
kubectl exec -n linux-mcp-chatbot <pod> -- \
  curl -X POST http://model-service:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"...", "messages":[{"role":"user","content":"test"}]}'
```

### Tool Calls Failing

Try setting:

```yaml
TOOL_CHOICE: "none"  # Force manual tool use
```

### Out of Memory

Reduce context or tool output:

```yaml
MODEL_CONTEXT_TOKENS: "2048"
MAX_TOOL_OUTPUT_CHARS: "1200"
```

---

**See also:**
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
