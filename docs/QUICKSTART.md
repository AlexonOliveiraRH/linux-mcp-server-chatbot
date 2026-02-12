# 🚀 Quick Start Guide

Get the Linux MCP Server Chatbot running in 5 minutes!

## What You'll Get

An AI-powered chatbot that uses **Claude Sonnet 4.5** (same as Claude Code CLI) to run Linux diagnostics on any host (local or remote) with natural language queries.

**Example queries:**
```
Check health status of demo.example.local
Show me failed services
What's using disk space on /var?
Find high CPU processes
```

---

## Prerequisites

Before starting, ensure you have:

1. ✅ **Python 3.10+**
2. ✅ **Google Cloud credentials** (same as Claude Code CLI)
3. ✅ **Linux MCP Server** installed
4. ✅ **Access to Claude via Vertex AI**

---

## Step-by-Step Setup

### 1. Install Linux MCP Server

```bash
pip install linux-mcp-server

# Verify it works
linux-mcp-server
# Press Ctrl+C to stop
```

### 2. Clone and Setup Project

```bash
git clone <repository-url>
cd linux-mcp-server-chatbot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit with your settings
nano .env
```

**Minimum configuration needed:**
```bash
MODEL_ENDPOINT=https://vertex-ai-anthropic
MODEL_NAME=claude-sonnet-4-5@20250929
GOOGLE_PROJECT_ID=your-gcp-project-id
GOOGLE_LOCATION=us-east5
MCP_COMMAND=/home/user/.local/bin/linux-mcp-server
LINUX_MCP_USER=your-remote-ssh-username
```

**How to find your values:**

- `GOOGLE_PROJECT_ID`: Run `gcloud config get-value project`
- `MCP_COMMAND`: Run `which linux-mcp-server`
- `LINUX_MCP_USER`: Your SSH username for remote hosts (e.g., `localuser`)

### 4. Verify Google Cloud Authentication

```bash
# Check if already authenticated
gcloud auth application-default print-access-token

# If that fails, authenticate
gcloud auth application-default login
```

### 5. Configure SSH (Recommended for Speed)

This enables connection reuse, making remote queries **30x faster**:

```bash
mkdir -p ~/.ssh/controlmasters
cat >> ~/.ssh/config << 'EOF'

Host *
    ControlMaster auto
    ControlPath ~/.ssh/controlmasters/%r@%h:%p
    ControlPersist 10m
EOF
```

### 6. Test Your Setup

```bash
# Run verification script
python tests/test_setup.py

# Test MCP client directly
python tests/test_mcp_direct.py
```

### 7. Start the Chatbot

```bash
./start-chatbot.sh
```

The chatbot will open in your browser at **http://localhost:8501**

---

## First Query

Try this in the chatbot:

**Local system:**
```
What is my system hostname and OS version?
```

**Remote host:**
```
Check health status of demo.example.local
```

You should see a response in **2-3 seconds** with real system data!

---

## Troubleshooting

### "Permission denied" when starting

**Fix:**
```bash
gcloud auth application-default login
```

### "Model not servable in region"

**Fix:** Change region in `.env`:
```bash
GOOGLE_LOCATION=us-east5
```

### Timeout errors on remote hosts

**Fix:** Make sure you configured SSH ControlMaster (step 5)

### Chatbot shows hallucinated data

**Fix:** Clear cache and restart:
```bash
pkill -f streamlit
rm -rf ~/.streamlit/cache
./start-chatbot.sh
```

### Tools not loading

**Fix:** Verify MCP_COMMAND path in `.env`:
```bash
which linux-mcp-server
# Copy this path to .env
```

---

## What's Next?

- **Try more queries**: See [docs/EXAMPLE_QUERIES.md](docs/EXAMPLE_QUERIES.md)
- **Remote hosts**: Add more hosts by configuring SSH keys
- **Troubleshooting**: See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Understanding**: Read the full [README.md](README.md)

---

## Performance Tips

1. **Use SSH ControlMaster** (step 5) - Makes parallel queries 30x faster
2. **Set up SSH keys** - Eliminates password prompts
3. **Use specific hosts** - Better than wildcards in SSH config
4. **Monitor costs** - Typical query is ~$0.01-0.03

---

## Quick Reference

**Start chatbot:**
```bash
./start-chatbot.sh
```

**Stop chatbot:**
```bash
# Press Ctrl+C in terminal, or:
pkill -f streamlit
```

**Test setup:**
```bash
python tests/test_setup.py
```

**Clear cache:**
```bash
rm -rf ~/.streamlit/cache
```

**Update dependencies:**
```bash
source .venv/bin/activate
pip install --upgrade -r requirements.txt
```

---

## Support

- **Issues**: See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Examples**: See [docs/EXAMPLE_QUERIES.md](docs/EXAMPLE_QUERIES.md)
- **Details**: See [README.md](README.md)

---

**🎉 You're ready to go!** Start with simple queries and work your way up to complex multi-step diagnostics.
