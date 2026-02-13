# OpenShift Deployment Manifests

Deployment files for Linux MCP Server Chatbot on OpenShift/Kubernetes.

## Files

- **00-namespace.yaml** - Creates the namespace
- **01-chatbot-configmap.yaml** - Model and runtime configuration
- **02-chatbot-deployment.yaml** - Main deployment (embedded MCP server)
- **03-chatbot-service.yaml** - Internal service (port 8501)
- **04-chatbot-route.yaml** - External HTTPS access
- **deploy.sh** - Automated deployment script

## Quick Deploy

```bash
# Create secrets first (see parent README.md)
oc create secret generic chatbot-gcp-credentials --from-file=gcp-credentials.json=path/to/file
oc create secret generic chatbot-api-keys --from-literal=GOOGLE_PROJECT_ID=your-project-id
oc create secret generic linux-mcp-ssh --from-file=ssh-privatekey=path/to/key

# Update image in 02-chatbot-deployment.yaml
# Then deploy all
./deploy.sh
```

## Configuration

Edit `01-chatbot-configmap.yaml` to configure:
- Model endpoint and name
- Timeouts
- Tool behavior

## Architecture

Single pod with embedded MCP server:
- Chatbot container runs Streamlit UI
- MCP server runs as subprocess (stdio transport)
- No separate MCP server deployment needed

See parent README.md for detailed documentation.
