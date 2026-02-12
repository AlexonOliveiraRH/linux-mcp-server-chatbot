# Configuration Guide

This guide helps you configure the Linux MCP Server Chatbot for your specific environment.

## Quick Configuration Checklist

Before starting, gather these values for your environment:

- [ ] Google Cloud Project ID
- [ ] Google Cloud Region (use `us-east5` for Claude)
- [ ] Path to linux-mcp-server binary
- [ ] SSH username for remote hosts (if using remote diagnostics)

---

## Step 1: Copy Configuration Template

```bash
cp .env.example .env
```

## Step 2: Find Your Configuration Values

### A. Google Cloud Project ID

```bash
# If you have gcloud CLI installed:
gcloud config get-value project

# Output example: my-company-gcp-project
```

Copy this value for `GOOGLE_PROJECT_ID` in `.env`

### B. Google Cloud Region

For Claude via Vertex AI, use: **`us-east5`**

Other supported regions:
- `europe-west1` (may work)
- `asia-southeast1` (may work)

**Note:** `us-central1` does NOT support Claude on Vertex AI

### C. Linux MCP Server Path

```bash
# Find where linux-mcp-server is installed:
which linux-mcp-server

# Common locations:
# - ~/.local/bin/linux-mcp-server
# - /usr/local/bin/linux-mcp-server
# - /opt/homebrew/bin/linux-mcp-server (macOS)
```

Copy this path for `MCP_COMMAND` in `.env`

### D. SSH Username for Remote Hosts

This is the username you use to SSH to remote Linux servers.

**Example:**
- If you run: `ssh admin@server.example.com`
- Then use: `LINUX_MCP_USER=admin`

**Multiple hosts with different users?**
Configure SSH config instead (see SSH Configuration section below)

## Step 3: Edit .env File

```bash
nano .env
```

Update these values with what you found above:

```bash
MODEL_ENDPOINT=https://vertex-ai-anthropic
MODEL_NAME=claude-sonnet-4-5@20250929
GOOGLE_PROJECT_ID=your-project-id-from-step-2a
GOOGLE_LOCATION=us-east5
MCP_COMMAND=/your/path/from-step-2c
LINUX_MCP_USER=your-ssh-username-from-step-2d
```

**Example (filled in):**
```bash
MODEL_ENDPOINT=https://vertex-ai-anthropic
MODEL_NAME=claude-sonnet-4-5@20250929
GOOGLE_PROJECT_ID=acme-corp-prod-123
GOOGLE_LOCATION=us-east5
MCP_COMMAND=/home/john/.local/bin/linux-mcp-server
LINUX_MCP_USER=sysadmin
```

## Step 4: Verify Google Cloud Authentication

```bash
# Test if you're already authenticated:
gcloud auth application-default print-access-token

# If that fails, authenticate:
gcloud auth application-default login
```

This will open a browser for authentication. Use the same Google account that has access to your GCP project.

## Step 5: SSH Configuration (Recommended)

### Why SSH Configuration?

SSH ControlMaster makes remote queries **30x faster** by reusing connections.

### Option A: Global SSH Configuration (All Hosts)

```bash
mkdir -p ~/.ssh/controlmasters

cat >> ~/.ssh/config << 'EOF'

# Speed up all SSH connections
Host *
    ControlMaster auto
    ControlPath ~/.ssh/controlmasters/%r@%h:%p
    ControlPersist 10m
EOF
```

### Option B: Per-Host SSH Configuration (Recommended)

```bash
cat >> ~/.ssh/config << 'EOF'

# Production servers
Host prod-web-*.example.com
    User webapp
    ControlMaster auto
    ControlPath ~/.ssh/controlmasters/%r@%h:%p
    ControlPersist 10m

# Development servers
Host dev-*.example.com
    User devuser
    ControlMaster auto
    ControlPath ~/.ssh/controlmasters/%r@%h:%p
    ControlPersist 10m

# Demo/test host
Host demo.example.local
    User localuser
    ControlMaster auto
    ControlPath ~/.ssh/controlmasters/%r@%h:%p
    ControlPersist 10m
EOF
```

### Option C: Skip SSH Configuration

If you only use local diagnostics, you can skip this step.

Set in `.env`:
```bash
# Leave LINUX_MCP_USER commented out or empty
# LINUX_MCP_USER=
```

## Step 6: Test Configuration

```bash
# Activate virtual environment
source .venv/bin/activate

# Run setup verification
python tests/test_setup.py
```

**Expected output:**
```
✓ Python Dependencies
✓ Environment Configuration
✓ Linux MCP Server
✓ Inference Server (may show warning - that's OK)
```

## Step 7: Test MCP Client

```bash
# Test local system
python tests/test_mcp_direct.py
```

**Expected output:**
```
✓ MCP client created
✓ Found 19 tools
✓ Success! Result length: 245 chars
✓ Success! Result length: 217 chars
```

---

## Advanced Configuration

### Multiple Cloud Providers

You can configure different providers in `.env.example` and switch by commenting/uncommenting:

**Claude via Vertex AI (Recommended):**
```bash
MODEL_ENDPOINT=https://vertex-ai-anthropic
MODEL_NAME=claude-sonnet-4-5@20250929
GOOGLE_PROJECT_ID=your-project
GOOGLE_LOCATION=us-east5
```

**Gemini via Vertex AI:**
```bash
MODEL_ENDPOINT=https://vertex-ai
MODEL_NAME=gemini-1.5-pro
GOOGLE_PROJECT_ID=your-project
GOOGLE_LOCATION=us-central1
```

**Direct Claude API:**
```bash
MODEL_ENDPOINT=https://api.anthropic.com
MODEL_NAME=claude-sonnet-4-20250514
ANTHROPIC_API_KEY=sk-ant-your-key
```

### Custom Timeouts

For slow networks or large queries:

```bash
REQUEST_TIMEOUT=600  # 10 minutes
```

### Debug Mode

Enable debug logging in app.py (already enabled by default):

```bash
./start-chatbot.sh
# Look for [DEBUG] lines in terminal output
```

---

## Environment-Specific Examples

### Corporate Environment

```bash
# Large enterprise with centralized GCP
MODEL_ENDPOINT=https://vertex-ai-anthropic
MODEL_NAME=claude-sonnet-4-5@20250929
GOOGLE_PROJECT_ID=acme-corp-ai-platform
GOOGLE_LOCATION=us-east5
MCP_COMMAND=/opt/company/bin/linux-mcp-server
LINUX_MCP_USER=svc-diagnostics
REQUEST_TIMEOUT=300
```

### Startup/Small Team

```bash
# Using personal GCP account
MODEL_ENDPOINT=https://vertex-ai-anthropic
MODEL_NAME=claude-sonnet-4-5@20250929
GOOGLE_PROJECT_ID=mystartup-dev
GOOGLE_LOCATION=us-east5
MCP_COMMAND=/home/admin/.local/bin/linux-mcp-server
LINUX_MCP_USER=admin
```

### Development/Testing

```bash
# Local Ollama for testing (no cloud costs)
MODEL_ENDPOINT=http://localhost:11434
MODEL_NAME=  # Auto-detect Ollama models
MCP_COMMAND=/usr/local/bin/linux-mcp-server
# LINUX_MCP_USER=  # Only local testing
```

---

## Troubleshooting Configuration

### "Permission denied" Error

**Cause:** Google Cloud credentials not configured or expired

**Fix:**
```bash
gcloud auth application-default login
```

### "Model not servable in region"

**Cause:** Claude not available in your configured region

**Fix:** Change to `us-east5`:
```bash
GOOGLE_LOCATION=us-east5
```

### "MCP Server not found"

**Cause:** Incorrect path in `MCP_COMMAND`

**Fix:**
```bash
# Find the correct path:
which linux-mcp-server

# Update .env with the output
```

### "Timeout waiting for MCP response"

**Cause:** Remote hosts taking too long, no SSH ControlMaster

**Fix:** Configure SSH ControlMaster (see Step 5)

### Tools showing as 0

**Cause:** MCP server not starting or PATH issue

**Fix:**
```bash
# Test MCP server directly:
~/.local/bin/linux-mcp-server

# If it works, use full path in .env
```

---

## Security Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Use service accounts** for production (not personal accounts)
3. **Rotate credentials** regularly
4. **Limit SSH key access** to specific hosts
5. **Use SSH key passphrases** for remote access
6. **Monitor GCP billing** for unexpected costs

---

## Verification Checklist

Before using in production:

- [ ] `.env` file configured with correct values
- [ ] Google Cloud authentication working
- [ ] `python tests/test_setup.py` passes
- [ ] `python tests/test_mcp_direct.py` succeeds
- [ ] SSH ControlMaster configured (if using remote hosts)
- [ ] Test query returns real data (not hallucinations)
- [ ] Response time under 5 seconds

---

## Getting Help

- **Configuration issues**: See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Setup questions**: See [QUICKSTART.md](QUICKSTART.md)
- **Feature questions**: See [README.md](README.md)

---

**Next:** Once configured, run `./start-chatbot.sh` to start!
