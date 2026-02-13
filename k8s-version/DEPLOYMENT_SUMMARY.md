# Linux MCP Server Chatbot - Deployment Summary

## ✅ Final Working Configuration

Successfully deployed on OpenShift with **embedded MCP server** using **stdio transport**.

### Architecture

```
User → Route → Service → Pod {
    Chatbot Container (Streamlit + Claude):
    - Runs on port 8501
    - Spawns MCP server as subprocess
    - Communicates via stdio (stdin/stdout)
    - MCP server provides 19 Linux diagnostic tools
}
```

### Key Components

**Container Image:** `quay.io/your-org/linux-mcp-chatbot:debug-1771012653`
- Base: `python:3.11-slim`
- Includes: `linux-mcp-server-1.3.1`, Streamlit, LangChain, Claude SDK
- Size: ~1.02 GB

**Transport Method:** Stdio (subprocess)
- Avoids HTTP protocol complexity
- Simple stdin/stdout JSON-RPC communication
- No network overhead

**Model:** Claude Sonnet 4.5 via Google Vertex AI
- Endpoint: `https://vertex-ai-anthropic`
- Model ID: `claude-sonnet-4-5@20250929`
- Region: `us-east5`

### Deployment Files

**Primary Deployment:**
- `openshift/14-chatbot-deployment-embedded.yaml` - Single container with embedded MCP server

**Supporting Resources:**
- `openshift/11-chatbot-configmap.yaml` - Model and runtime configuration
- `openshift/04-chatbot-route.yaml` - HTTPS external access
- `openshift/05-chatbot-service.yaml` - Internal service (port 8501)
- Secrets: `chatbot-api-keys`, `chatbot-gcp-credentials`, `linux-mcp-ssh`

### Environment Variables

**MCP Configuration:**
```yaml
- MCP_COMMAND: "python3"
- MCP_ARGS: "-m,linux_mcp_server"
- LINUX_MCP_USER: "root"
- SSH_CONFIG_PATH: "/tmp/ssh-keys/config"
```

**Directory Permissions (Critical):**
```yaml
- HOME: "/tmp"
- XDG_DATA_HOME: "/tmp/.local/share"
- XDG_STATE_HOME: "/tmp/.local/state"
```

These allow the non-root user `appuser` to write MCP server logs.

**Model Configuration:**
```yaml
- MODEL_ENDPOINT: "https://vertex-ai-anthropic"
- MODEL_NAME: "claude-sonnet-4-5@20250929"
- GOOGLE_LOCATION: "us-east5"
- REQUEST_TIMEOUT: "300"
- TOOL_CHOICE: "auto"
```

### Available Tools (19 total)

**Logs & Troubleshooting:**
- `get_journal_logs` - Systemd journal with filtering
- `read_log_file` - Read specific log files
- `get_service_logs` - Service-specific logs

**Network Diagnostics:**
- `get_network_interfaces` - Interface details and statistics
- `get_network_connections` - Active connections
- `get_listening_ports` - Open ports and services

**Process Management:**
- `list_processes` - All running processes
- `get_process_info` - Details for specific PID

**Service Management:**
- `list_services` - All systemd services
- `get_service_status` - Service status details

**Storage & Files:**
- `list_block_devices` - Disks and partitions
- `list_directories` - Directory listing with sorting
- `list_files` - File listing with sorting
- `read_file` - Read file contents
- `get_disk_usage` - Filesystem usage

**System Information:**
- `get_system_information` - OS, kernel, uptime
- `get_cpu_information` - CPU details and load
- `get_memory_information` - RAM and swap usage
- `get_hardware_information` - Hardware details

**Remote SSH Support:**
All tools accept optional `host` parameter for remote execution via SSH.

## Deployment Commands

```bash
# Login to OpenShift
oc login --token=<your-token> --server=https://api.your-openshift-cluster.com:6443

# Deploy all resources
oc apply -f openshift/00-namespace.yaml
oc apply -f openshift/11-chatbot-configmap.yaml
oc apply -f openshift/14-chatbot-deployment-embedded.yaml
oc apply -f openshift/05-chatbot-service.yaml
oc apply -f openshift/04-chatbot-route.yaml

# Create secrets (if not already created)
oc create secret generic chatbot-api-keys \
  --from-literal=GOOGLE_PROJECT_ID=<project-id>

oc create secret generic chatbot-gcp-credentials \
  --from-file=gcp-credentials.json=<path-to-credentials>

oc create secret generic linux-mcp-ssh \
  --from-file=ssh-privatekey=<path-to-ssh-key> \
  --from-file=config=<path-to-ssh-config>

# Check status
oc get pods -n linux-mcp-server-chatbot
oc logs -f deployment/linux-mcp-chatbot -n linux-mcp-server-chatbot

# Access URL
https://linux-mcp-chatbot-<namespace>.apps.your-openshift-cluster.com
```

## Build Commands

```bash
cd k8s-version/docker

# Single architecture build (fastest)
export IMAGE_REGISTRY=quay.io/your-org
export IMAGE_NAME=linux-mcp-chatbot
export IMAGE_TAG=latest
./build-single-arch.sh

# Multi-architecture build (production)
./build-chatbot.sh
```

## Troubleshooting

### Common Issues

**1. Permission Denied: /.local**
- **Cause:** MCP server tries to write logs to read-only directory
- **Fix:** Set `HOME=/tmp` and `XDG_DATA_HOME=/tmp/.local/share` env vars

**2. Timeout waiting for MCP response**
- **Cause:** MCP subprocess crashed or not responding
- **Debug:** Check logs with `oc logs -f deployment/linux-mcp-chatbot`
- **Look for:** `[MCP STDERR]` lines showing errors

**3. 406 Not Acceptable (HTTP transport)**
- **Cause:** Streamable-http protocol incompatibility
- **Solution:** Use stdio transport instead (current configuration)

**4. Image not updating**
- **Cause:** Cached image with same tag
- **Fix:** Delete pod to force pull: `oc delete pod -l app=linux-mcp-chatbot`

### Checking Logs

```bash
# Follow logs
oc logs -f deployment/linux-mcp-chatbot -n linux-mcp-server-chatbot

# Show last 100 lines
oc logs deployment/linux-mcp-chatbot -n linux-mcp-server-chatbot --tail=100

# Check MCP server startup
oc logs deployment/linux-mcp-chatbot | grep "MCP"
```

### Debug Output

The current image includes extensive debug logging:
- `[DEBUG]` - Application flow
- `[MCP STDOUT]` - JSON-RPC messages from MCP server
- `[MCP STDERR]` - MCP server logs and errors

## Issues Resolved

1. ❌ **HTTP Transport 406 Errors** → ✅ Switched to stdio transport
2. ❌ **Privileged mode required** → ✅ Using simple subprocess (no privileges)
3. ❌ **Permission denied on /.local** → ✅ Set writable HOME=/tmp
4. ❌ **Sidecar complexity** → ✅ Single container with embedded server
5. ❌ **Image caching issues** → ✅ Use explicit digest or delete pods

## Architecture Evolution

### Attempted Approaches (Did Not Work)

1. **Separate HTTP Server (Sidecar)**
   - Two containers in one pod
   - MCP server using streamable-http
   - **Failed:** 406 Not Acceptable errors with protocol incompatibility

2. **Official MCP SDK Client**
   - Using `mcp==1.26.0` Python package
   - **Failed:** Version mismatch and async event loop complexity

3. **Podman-in-Podman (Privileged)**
   - Running MCP server via podman inside container
   - **Failed:** Blocked by OpenShift Pod Security Standards

### Final Working Approach

**Embedded Stdio Transport:**
- MCP server installed as Python package in same container
- Spawned as subprocess using `python3 -m linux_mcp_server`
- Communication via stdin/stdout (stdio transport)
- ✅ Simple, fast, no HTTP complexity
- ✅ No privileged mode required
- ✅ Works with OpenShift security policies

## Performance

- **Startup time:** ~10 seconds
- **Tool initialization:** ~2 seconds
- **Average query response:** 5-15 seconds (depends on tool + LLM)
- **Container memory:** ~768 MB
- **Container CPU:** 0.2-2.0 cores (burst)

## Security Considerations

- Container runs as non-root user `appuser`
- SSH keys mounted read-only from secrets
- MCP server runs in same security context (no privilege escalation)
- Remote SSH access requires proper key configuration
- All tool operations logged to `/tmp/.local/share/linux-mcp-server/logs`

## Future Enhancements

- [ ] Add more MCP tools (package management, configuration)
- [ ] Support multiple remote hosts
- [ ] Add tool output caching
- [ ] Implement streaming responses
- [ ] Add Prometheus metrics
- [ ] Support other LLM providers (OpenAI, local models)
- [ ] Add conversation history persistence

## References

- **Linux MCP Server:** https://rhel-lightspeed.github.io/linux-mcp-server/
- **MCP Protocol:** https://modelcontextprotocol.io/
- **Claude API:** https://docs.anthropic.com/
- **Google Vertex AI:** https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/claude
- **OpenShift Documentation:** https://docs.openshift.com/

---

**Last Updated:** February 13, 2026
**Status:** ✅ Production Ready
**Deployment URL:** https://linux-mcp-chatbot-<namespace>.apps.your-openshift-cluster.com
