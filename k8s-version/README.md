# Linux MCP Server Chatbot - Kubernetes/OpenShift Version

AI-powered Linux diagnostics chatbot using Claude and MCP (Model Context Protocol).

## Architecture

```
┌─────────────────────────────────────────────┐
│         OpenShift/Kubernetes Pod            │
│  ┌───────────────────────────────────────┐  │
│  │     Chatbot Container (Streamlit)     │  │
│  │  - Claude Sonnet 4.5 via Vertex AI    │  │
│  │  - LangChain Agent                    │  │
│  │  - 19 diagnostic tools                │  │
│  │           ↓ stdio                     │  │
│  │  Linux MCP Server (subprocess)        │  │
│  │  - System info, processes, services   │  │
│  │  - Network, storage, logs             │  │
│  │  - Remote SSH support                 │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## Features

- **19 Linux Diagnostic Tools** via MCP
- **Remote SSH Support** for all tools
- **Claude Sonnet 4.5** for intelligent query understanding
- **Embedded MCP Server** using stdio transport
- **OpenShift Compatible** (no privileged mode required)

## Quick Start

### Prerequisites

- OpenShift/Kubernetes cluster access
- Google Cloud project with Vertex AI enabled
- Container registry access (e.g., quay.io)
- SSH keys for remote host access (optional)

### 1. Build Container

```bash
cd docker

export IMAGE_REGISTRY=quay.io/your-org
export IMAGE_NAME=linux-mcp-chatbot
export IMAGE_TAG=latest

# Single architecture (faster)
./build-single-arch.sh

# Multi-architecture (production)
./build-chatbot.sh
```

### 2. Update Image in Deployment

Edit `openshift/02-chatbot-deployment.yaml` and update:

```yaml
image: quay.io/your-org/linux-mcp-chatbot:latest
```

### 3. Create Secrets

```bash
# Google Cloud credentials for Vertex AI
oc create secret generic chatbot-gcp-credentials \
  --from-file=gcp-credentials.json=path/to/your-credentials.json \
  -n linux-mcp-server-chatbot

# Google Cloud project ID
oc create secret generic chatbot-api-keys \
  --from-literal=GOOGLE_PROJECT_ID=your-project-id \
  -n linux-mcp-server-chatbot

# SSH keys for remote access (optional)
oc create secret generic linux-mcp-ssh \
  --from-file=ssh-privatekey=path/to/your/id_ed25519 \
  --from-file=config=path/to/your/ssh_config \
  -n linux-mcp-server-chatbot
```

### 4. Deploy

```bash
cd openshift

# Deploy all resources
oc apply -f 00-namespace.yaml
oc apply -f 01-chatbot-configmap.yaml
oc apply -f 02-chatbot-deployment.yaml
oc apply -f 03-chatbot-service.yaml
oc apply -f 04-chatbot-route.yaml

# Or use the deploy script
chmod +x deploy.sh
./deploy.sh
```

### 5. Access

Get the route URL:

```bash
oc get route linux-mcp-chatbot -n linux-mcp-server-chatbot
```

Access the chatbot at the displayed URL.

## Configuration

Edit `openshift/01-chatbot-configmap.yaml`:

```yaml
MODEL_ENDPOINT: "https://vertex-ai-anthropic"
MODEL_NAME: "claude-sonnet-4-5@20250929"
GOOGLE_LOCATION: "us-east5"
REQUEST_TIMEOUT: "300"
TOOL_CHOICE: "auto"
```

## Available Tools

**System Information:**
- `get_system_information` - OS, kernel, uptime
- `get_cpu_information` - CPU details and load
- `get_memory_information` - RAM and swap usage
- `get_hardware_information` - Hardware details
- `get_disk_usage` - Filesystem usage

**Processes & Services:**
- `list_processes` - All running processes
- `get_process_info` - Details for specific PID
- `list_services` - All systemd services
- `get_service_status` - Service status details
- `get_service_logs` - Service logs

**Network:**
- `get_network_interfaces` - Interface details
- `get_network_connections` - Active connections
- `get_listening_ports` - Open ports and services

**Storage & Files:**
- `list_block_devices` - Disks and partitions
- `list_directories` - Directory listing
- `list_files` - File listing
- `read_file` - Read file contents

**Logs:**
- `get_journal_logs` - Systemd journal logs
- `read_log_file` - Read specific log files

All tools support optional `host` parameter for remote execution via SSH.

## Example Queries

```
"What services are running?"
"Show me disk usage"
"List the top 10 processes by CPU"
"Get system information"
"Check health status of demo.example.local"
"Show me journal logs from the last hour"
```

## Troubleshooting

### Check Pod Status

```bash
oc get pods -n linux-mcp-server-chatbot
oc logs -f deployment/linux-mcp-chatbot -n linux-mcp-server-chatbot
```

### Common Issues

**Permission Denied: /.local**
- Fixed by setting `HOME=/tmp` and `XDG_DATA_HOME=/tmp/.local/share` in deployment

**Tool Validation Errors**
- Tools use `StructuredTool` with Pydantic models for proper argument handling

**Image Not Updating**
- Delete pod to force pull: `oc delete pod -l app=linux-mcp-chatbot -n linux-mcp-server-chatbot`

## Project Structure

```
k8s-version/
├── docker/                    # Container build
│   ├── Dockerfile.chatbot     # Chatbot container
│   ├── requirements.txt       # Python dependencies
│   ├── build-chatbot.sh       # Multi-arch build
│   └── build-single-arch.sh   # Single-arch build
├── src/                       # Source code
│   ├── app.py                 # Main Streamlit application
│   ├── mcp_client_stdio.py    # MCP stdio transport client
│   ├── mcp_client_http.py     # MCP HTTP transport client (legacy)
│   └── claude_vertex_wrapper.py # Claude Vertex AI wrapper
├── openshift/                 # Deployment manifests
│   ├── 00-namespace.yaml      # Namespace
│   ├── 01-chatbot-configmap.yaml # Configuration
│   ├── 02-chatbot-deployment.yaml # Main deployment
│   ├── 03-chatbot-service.yaml # Service
│   └── 04-chatbot-route.yaml  # Route (HTTPS)
└── DEPLOYMENT_SUMMARY.md      # Detailed deployment guide
```

## Development

### Update Code

1. Modify source in `src/`
2. Rebuild container
3. Push to registry
4. Update deployment:

```bash
oc set image deployment/linux-mcp-chatbot \
  chatbot=quay.io/your-org/linux-mcp-chatbot:new-tag \
  -n linux-mcp-server-chatbot
```

### Debug

Enable verbose logging in `src/app.py` (already included):
- `[DEBUG]` - Application flow
- `[MCP STDOUT]` - MCP server JSON-RPC messages
- `[MCP STDERR]` - MCP server logs

## Security

- Container runs as non-root user `appuser`
- SSH keys mounted read-only from secrets
- No privileged mode required
- Complies with OpenShift Pod Security Standards

## Performance

- **Startup time:** ~10 seconds
- **Tool initialization:** ~2 seconds
- **Query response:** 5-15 seconds (tool + LLM)
- **Memory:** ~768 MB
- **CPU:** 0.2-2.0 cores (burst)

## References

- [Linux MCP Server](https://rhel-lightspeed.github.io/linux-mcp-server/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Claude API](https://docs.anthropic.com/)
- [OpenShift Documentation](https://docs.openshift.com/)
