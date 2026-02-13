# Deployment Guide

Complete guide for deploying the Linux MCP Server Chatbot in Kubernetes environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Building the Container Image](#building-the-container-image)
- [Creating Secrets](#creating-secrets)
- [Deployment Options](#deployment-options)
- [Post-Deployment](#post-deployment)
- [Scaling](#scaling)
- [Updating](#updating)

---

## Prerequisites

### Infrastructure

- **Kubernetes 1.24+** or **OpenShift 4.12+**
- **kubectl** or **oc** CLI configured
- **Container registry** with push access (quay.io, Docker Hub, etc.)
- **4GB RAM** minimum for cluster nodes
- **2 CPU cores** minimum for cluster nodes

### Model Inference

You need ONE of the following:

**Option A: Cloud API Access**
- Google Cloud account with Vertex AI enabled (for Claude)
- OpenAI API key (for GPT-4)
- Anthropic API key (for direct Claude access)

**Option B: Self-Hosted Model**
- Model server deployed (vLLM, Ollama, TGIS, etc.)
- Model weights downloaded
- GPU/CPU resources allocated

### SSH Access (For Remote Linux Hosts)

- SSH private key for remote systems
- SSH user account on target hosts
- Network connectivity from pods to hosts

---

## Building the Container Image

### Step 1: Prepare Build Environment

```bash
cd k8s-version/docker/

# Set your registry
export IMAGE_REGISTRY=quay.io/your-org
export IMAGE_NAME=linux-mcp-chatbot
export IMAGE_TAG=v1.0.0
```

### Step 2: Login to Registry

```bash
# For Quay.io
docker login quay.io

# For Docker Hub
docker login

# For OpenShift internal registry
oc registry login
```

### Step 3: Build Multi-Architecture Image

```bash
# Build for AMD64 and ARM64
./build.sh

# Or build manually
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag ${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} \
  --push \
  .
```

### Step 4: Verify Image

```bash
# Pull and test locally
docker pull ${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}

docker run -p 8501:8501 \
  -e MODEL_ENDPOINT=http://host.docker.internal:11434 \
  -e MODEL_NAME=mistral \
  ${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
```

---

## Creating Secrets

### Option 1: Using the Helper Script

```bash
cd k8s-version/config/

# For Claude via Vertex AI
export GOOGLE_PROJECT_ID=your-project-id
./create-secrets.sh

# Then manually add GCP credentials
kubectl create secret generic chatbot-secrets \
  --from-file=gcp-credentials.json=/path/to/service-account.json \
  --from-literal=GOOGLE_PROJECT_ID=${GOOGLE_PROJECT_ID} \
  -n linux-mcp-chatbot
```

### Option 2: Manual Secret Creation

**For Claude via Vertex AI:**

```bash
# Create secret with GCP service account
kubectl create secret generic chatbot-secrets \
  --from-file=gcp-credentials.json=<(cat <<EOF
{
  "type": "service_account",
  "project_id": "your-project",
  "private_key_id": "...",
  "private_key": "...",
  ...
}
EOF
) \
  --from-literal=GOOGLE_PROJECT_ID=your-project-id \
  -n linux-mcp-chatbot
```

**For OpenAI:**

```bash
kubectl create secret generic chatbot-secrets \
  --from-literal=OPENAI_API_KEY=sk-your-api-key \
  -n linux-mcp-chatbot
```

**For Anthropic Direct:**

```bash
kubectl create secret generic chatbot-secrets \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-your-key \
  -n linux-mcp-chatbot
```

**SSH Private Key:**

```bash
kubectl create secret generic chatbot-secrets \
  --from-file=ssh-privatekey=~/.ssh/id_rsa \
  -n linux-mcp-chatbot
```

---

## Deployment Options

### Option 1: Standard Kubernetes

**1. Update ConfigMap:**

```bash
cd k8s-version/k8s/overlays/kubernetes/

# Edit configmap-patch.yaml
nano configmap-patch.yaml
```

Set your model configuration:

```yaml
data:
  MODEL_ENDPOINT: "https://vertex-ai-anthropic"
  MODEL_NAME: "claude-sonnet-4-5@20250929"
  GOOGLE_LOCATION: "us-east5"
```

**2. Update Image Reference:**

```bash
cd ../../base/
nano kustomization.yaml
```

Update the image:

```yaml
images:
- name: quay.io/your-org/linux-mcp-chatbot
  newTag: v1.0.0
```

**3. Deploy:**

```bash
# Apply base + overlay
kubectl apply -k ../overlays/kubernetes/

# Or just base (no overlay)
kubectl apply -k .
```

**4. Create Ingress (optional):**

```bash
# Edit ingress.yaml with your domain
nano ingress.yaml

# Apply
kubectl apply -f ingress.yaml
```

### Option 2: OpenDataHub

**1. Ensure OpenDataHub is installed:**

```bash
# Check if ODH is running
kubectl get pods -n opendatahub
```

**2. Deploy model via ODH dashboard:**

- Go to OpenDataHub dashboard
- Deploy model (e.g., Granite via vLLM)
- Note the service URL

**3. Update overlay:**

```bash
cd k8s-version/k8s/overlays/opendatahub/

# Edit configmap-patch.yaml
nano configmap-patch.yaml
```

Update with your model service:

```yaml
data:
  MODEL_ENDPOINT: "http://granite-vllm.opendatahub.svc.cluster.local:8000"
  MODEL_NAME: "ibm/granite-7b-instruct"
```

**4. Deploy:**

```bash
kubectl apply -k .
```

**5. Access via Route:**

```bash
kubectl get route -n opendatahub linux-mcp-chatbot
```

### Option 3: Red Hat OpenShift AI

**1. Deploy model via RHOAI:**

- Open RHOAI dashboard
- Deploy model (Caikit-TGIS or vLLM)
- Get internal service name

**2. Configure overlay:**

```bash
cd k8s-version/k8s/overlays/openshift-ai/

# Edit configmap
nano configmap-patch.yaml
```

Example for Caikit-TGIS:

```yaml
data:
  MODEL_ENDPOINT: "http://granite-13b-caikit.redhat-ods-applications.svc.cluster.local:8085"
  MODEL_NAME: "ibm/granite-13b-chat-v2"
```

**3. Deploy:**

```bash
oc apply -k .
```

**4. Access:**

```bash
oc get route -n redhat-ods-applications linux-mcp-chatbot
```

---

## Post-Deployment

### Verify Deployment

```bash
# Check pod status
kubectl get pods -n linux-mcp-chatbot

# Should show:
# NAME                                  READY   STATUS    RESTARTS
# linux-mcp-chatbot-xxxxxxxxxx-xxxxx   1/1     Running   0
```

### View Logs

```bash
# Stream logs
kubectl logs -f -n linux-mcp-chatbot deployment/linux-mcp-chatbot

# Look for:
# [DEBUG] Using ClaudeVertexChat...
# [DEBUG] Creating agent with 19 tools
# [DEBUG] Agent created successfully
```

### Test Connectivity

```bash
# Port forward to local machine
kubectl port-forward -n linux-mcp-chatbot svc/linux-mcp-chatbot 8501:8501
```

Open browser to http://localhost:8501 and try a query:

```
What is the hostname of the local system?
```

### Access via Ingress/Route

**For Ingress (Kubernetes):**

```bash
kubectl get ingress -n linux-mcp-chatbot

# Access at configured domain
curl https://chatbot.example.com/_stcore/health
```

**For Route (OpenShift):**

```bash
oc get route -n linux-mcp-chatbot

# Access at route URL
ROUTE_URL=$(oc get route linux-mcp-chatbot -n linux-mcp-chatbot -o jsonpath='{.spec.host}')
curl https://${ROUTE_URL}/_stcore/health
```

---

## Scaling

### Horizontal Pod Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: linux-mcp-chatbot-hpa
  namespace: linux-mcp-chatbot
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: linux-mcp-chatbot
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

Apply:

```bash
kubectl apply -f hpa.yaml
```

### Manual Scaling

```bash
# Scale to 3 replicas
kubectl scale deployment/linux-mcp-chatbot \
  --replicas=3 \
  -n linux-mcp-chatbot
```

**Note:** When scaling >1 replica, user sessions may not persist across pods unless you implement session affinity or shared storage.

---

## Updating

### Update Model Configuration

```bash
# Edit ConfigMap
kubectl edit configmap chatbot-config -n linux-mcp-chatbot

# Rollout restart to apply changes
kubectl rollout restart deployment/linux-mcp-chatbot -n linux-mcp-chatbot
```

### Update Container Image

```bash
# Build new image
cd k8s-version/docker/
export IMAGE_TAG=v1.1.0
./build.sh

# Update kustomization
cd ../k8s/base/
nano kustomization.yaml

# Change newTag to v1.1.0
images:
- name: quay.io/your-org/linux-mcp-chatbot
  newTag: v1.1.0

# Apply update
kubectl apply -k .

# Watch rollout
kubectl rollout status deployment/linux-mcp-chatbot -n linux-mcp-chatbot
```

### Rollback

```bash
# View rollout history
kubectl rollout history deployment/linux-mcp-chatbot -n linux-mcp-chatbot

# Rollback to previous version
kubectl rollout undo deployment/linux-mcp-chatbot -n linux-mcp-chatbot

# Rollback to specific revision
kubectl rollout undo deployment/linux-mcp-chatbot \
  --to-revision=2 \
  -n linux-mcp-chatbot
```

---

## Troubleshooting

### Pod Crash Loop

```bash
# Check events
kubectl describe pod -n linux-mcp-chatbot <pod-name>

# Common issues:
# - Missing secrets (gcp-credentials.json)
# - Invalid MODEL_ENDPOINT
# - Memory limits too low
```

### Cannot Access Model

```bash
# Test from pod
kubectl exec -n linux-mcp-chatbot <pod-name> -- \
  curl -v http://model-service:8000/health

# Check DNS
kubectl exec -n linux-mcp-chatbot <pod-name> -- \
  nslookup model-service.namespace.svc.cluster.local
```

### SSH Failing

```bash
# Check SSH key permission
kubectl exec -n linux-mcp-chatbot <pod-name> -- \
  ls -la /home/appuser/.ssh/

# Should show:
# -rw------- 1 appuser appuser ... id_rsa

# Test SSH
kubectl exec -n linux-mcp-chatbot <pod-name> -- \
  ssh -vvv -i /home/appuser/.ssh/id_rsa user@remotehost
```

---

## Next Steps

- Configure monitoring with Prometheus
- Set up log aggregation (ELK, Loki)
- Implement backup/restore for configuration
- Enable HTTPS with cert-manager
- Configure NetworkPolicies

---

**See also:**
- [MODELS.md](MODELS.md) - Model configuration guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
