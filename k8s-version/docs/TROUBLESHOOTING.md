# Troubleshooting Guide

Common issues and solutions for the Kubernetes deployment.

## Container Issues

### Pod Won't Start

**Symptoms:**
```bash
$ kubectl get pods -n linux-mcp-chatbot
NAME                                   READY   STATUS             RESTARTS
linux-mcp-chatbot-xxx-yyy              0/1     CrashLoopBackOff   5
```

**Diagnosis:**

```bash
# Check events
kubectl describe pod -n linux-mcp-chatbot <pod-name>

# View logs
kubectl logs -n linux-mcp-chatbot <pod-name>
```

**Common Causes:**

**1. Missing secrets:**
```
Error: FileNotFoundError: gcp-credentials.json
```

**Solution:**
```bash
kubectl create secret generic chatbot-secrets \
  --from-file=gcp-credentials.json=/path/to/sa.json \
  -n linux-mcp-chatbot
```

**2. Invalid image:**
```
Error: ImagePullBackOff
```

**Solution:**
```bash
# Check image exists
docker pull quay.io/your-org/linux-mcp-chatbot:latest

# Update kustomization.yaml with correct image
```

**3. Insufficient resources:**
```
Error: OutOfMemory
```

**Solution:**
```yaml
# Increase resource limits in deployment-patch.yaml
resources:
  limits:
    memory: 2Gi  # Increased from 1Gi
```

---

## Model Connection Issues

### Cannot Connect to Model

**Symptoms:**
```
Error: Connection refused to http://model-service:8000
```

**Diagnosis:**

```bash
# Test from pod
kubectl exec -n linux-mcp-chatbot <pod> -- \
  curl -v http://model-service:8000/health

# Check DNS
kubectl exec -n linux-mcp-chatbot <pod> -- \
  nslookup model-service.namespace.svc.cluster.local
```

**Solutions:**

**1. Wrong service name:**
```yaml
# Verify service exists
kubectl get svc -n opendatahub | grep model

# Update configmap with correct name
MODEL_ENDPOINT: "http://granite-vllm.opendatahub.svc.cluster.local:8000"
```

**2. Network policy blocking:**
```bash
# Check network policies
kubectl get networkpolicies -n linux-mcp-chatbot

# Create policy allowing egress
```

**3. Model service not ready:**
```bash
# Check model pod status
kubectl get pods -n opendatahub

# Wait for model to be ready
kubectl wait --for=condition=ready pod -l app=granite-vllm -n opendatahub
```

---

## SSH Issues

### Cannot SSH to Remote Hosts

**Symptoms:**
```
Error: Permission denied (publickey)
Error: ssh: connect to host demo.example.local port 22: Connection refused
```

**Diagnosis:**

```bash
# Check SSH key mounted
kubectl exec -n linux-mcp-chatbot <pod> -- ls -la /home/appuser/.ssh/

# Test SSH manually
kubectl exec -it -n linux-mcp-chatbot <pod> -- \
  ssh -vvv -i /home/appuser/.ssh/id_rsa user@remotehost
```

**Solutions:**

**1. SSH key not mounted:**
```bash
# Verify secret exists
kubectl get secret chatbot-secrets -n linux-mcp-chatbot -o yaml | grep ssh-privatekey

# Create if missing
kubectl create secret generic chatbot-secrets \
  --from-file=ssh-privatekey=~/.ssh/id_rsa \
  -n linux-mcp-chatbot
```

**2. Wrong permissions:**
```bash
# SSH key should be 600
# If showing 644, recreate secret with correct mode
```

**3. Wrong username:**
```yaml
# Update configmap
LINUX_MCP_USER: "correct-username"
```

**4. Network not reachable:**
```bash
# Test network from pod
kubectl exec -n linux-mcp-chatbot <pod> -- \
  ping remotehost

# Check if firewall/network policy blocks SSH port 22
```

---

## Tool Calling Issues

### Tools Not Being Called

**Symptoms:**
- Chatbot hallucinates responses instead of using tools
- No [DEBUG] tool call messages in logs

**Diagnosis:**

```bash
# Check logs for tool binding
kubectl logs -n linux-mcp-chatbot <pod> | grep "DEBUG.*tools"

# Should see:
# [DEBUG] Creating agent with 19 tools
# [DEBUG] Tool names: ['get_system_information', ...]
```

**Solutions:**

**1. Model doesn't support tools:**
```yaml
# For smaller models, try:
TOOL_CHOICE: "none"
```

**2. Context window too small:**
```yaml
# Reduce tool output
MAX_TOOL_OUTPUT_CHARS: "1200"
```

**3. Cache not cleared:**
```bash
# Delete pod to clear Streamlit cache
kubectl delete pod -n linux-mcp-chatbot <pod-name>
```

---

## Performance Issues

### Slow Response Times

**Symptoms:**
- Queries take > 30 seconds
- Timeout errors frequently

**Diagnosis:**

```bash
# Check pod resources
kubectl top pod -n linux-mcp-chatbot

# Check model server resources
kubectl top pod -n opendatahub -l app=granite-vllm
```

**Solutions:**

**1. Increase timeout:**
```yaml
REQUEST_TIMEOUT: "900"  # 15 minutes
```

**2. Increase resources:**
```yaml
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 4000m
    memory: 4Gi
```

**3. Use faster model:**
```yaml
# Switch from 13B to 7B model
MODEL_NAME: "ibm/granite-7b-instruct"
```

**4. Reduce context:**
```yaml
MODEL_CONTEXT_TOKENS: "2048"
MAX_TOOL_OUTPUT_CHARS: "1200"
```

---

## Authentication Issues

### GCP Credentials Invalid

**Symptoms:**
```
Error: Could not authenticate with Vertex AI
Error: Permission denied
```

**Solutions:**

**1. Verify service account has permissions:**
```bash
# Service account needs:
# - Vertex AI User role
# - Service Account Token Creator role (if using Workload Identity)
```

**2. Re-create secret:**
```bash
kubectl delete secret chatbot-secrets -n linux-mcp-chatbot
kubectl create secret generic chatbot-secrets \
  --from-file=gcp-credentials.json=/path/to/fresh-sa-key.json \
  --from-literal=GOOGLE_PROJECT_ID=your-project \
  -n linux-mcp-chatbot
```

**3. Check environment variable:**
```bash
# Verify GOOGLE_APPLICATION_CREDENTIALS is set
kubectl exec -n linux-mcp-chatbot <pod> -- \
  printenv GOOGLE_APPLICATION_CREDENTIALS

# Should show: /var/secrets/gcp/gcp-credentials.json
```

### OpenAI API Key Invalid

**Symptoms:**
```
Error: Invalid API key
```

**Solution:**
```bash
# Update secret with valid key
kubectl create secret generic chatbot-secrets \
  --from-literal=OPENAI_API_KEY=sk-correct-key \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart pod
kubectl rollout restart deployment/linux-mcp-chatbot -n linux-mcp-chatbot
```

---

## Route/Ingress Issues

### Cannot Access via External URL

**Symptoms:**
- Route/Ingress shows in `kubectl get`, but URL doesn't work
- 404 or 502 errors

**Diagnosis:**

**For OpenShift Route:**
```bash
oc get route -n linux-mcp-chatbot linux-mcp-chatbot

# Test route
ROUTE_URL=$(oc get route linux-mcp-chatbot -n linux-mcp-chatbot -o jsonpath='{.spec.host}')
curl -I https://${ROUTE_URL}
```

**For Kubernetes Ingress:**
```bash
kubectl get ingress -n linux-mcp-chatbot

# Check ingress controller
kubectl get pods -n ingress-nginx
```

**Solutions:**

**1. Ingress controller not installed:**
```bash
# Install nginx ingress
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

**2. TLS certificate missing:**
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

---

## Debug Mode

### Enable Detailed Logging

Add to deployment:

```yaml
env:
- name: PYTHONUNBUFFERED
  value: "1"
- name: STREAMLIT_LOG_LEVEL
  value: "debug"
```

Restart:

```bash
kubectl rollout restart deployment/linux-mcp-chatbot -n linux-mcp-chatbot
```

View detailed logs:

```bash
kubectl logs -f -n linux-mcp-chatbot deployment/linux-mcp-chatbot
```

---

## Getting Help

If issues persist:

1. **Check logs:**
   ```bash
   kubectl logs -n linux-mcp-chatbot <pod> --previous
   ```

2. **Describe resources:**
   ```bash
   kubectl describe pod -n linux-mcp-chatbot <pod>
   kubectl describe svc -n linux-mcp-chatbot linux-mcp-chatbot
   ```

3. **Test manually:**
   ```bash
   kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
     curl http://linux-mcp-chatbot.linux-mcp-chatbot:8501/_stcore/health
   ```

4. **Open issue:**
   - Include pod logs
   - Include resource descriptions
   - Include ConfigMap/Secret names (not values!)
   - Include platform (K8s, OpenShift, ODH, RHOAI)

---

**See also:**
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [MODELS.md](MODELS.md) - Model configuration
