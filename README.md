# 🐧 Linux MCP Server Chatbot

An AI-powered Linux diagnostics chatbot that uses **Claude via Google Vertex AI** to run system diagnostics on any Linux host (local or remote) through the [Linux MCP Server](https://rhel-lightspeed.github.io/linux-mcp-server/).

## ✨ Features

- **🤖 Claude Sonnet 4.5** - Same model and authentication as Claude Code CLI
- **🌐 Remote & Local Diagnostics** - SSH-based access to any Linux host
- **⚡ Fast Responses** - 2-3 second query responses with parallel tool execution
- **🔧 19 Diagnostic Tools** - System info, CPU, memory, disk, network, services, processes, logs, and more
- **💬 Natural Language Interface** - Ask questions in plain English
- **🔄 Multi-Step Reasoning** - LangChain ReAct agent for complex diagnostics

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Google Cloud credentials (Application Default Credentials)
- Linux MCP Server installed
- Access to Claude via Google Vertex AI (same as Claude Code CLI)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd linux-mcp-server-chatbot
   ```

2. **Create virtual environment and install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Install Linux MCP Server**
   ```bash
   pip install linux-mcp-server
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   nano .env  # Edit configuration
   ```

   **Minimum required configuration:**
   ```bash
   MODEL_ENDPOINT=https://vertex-ai-anthropic
   MODEL_NAME=claude-sonnet-4-5@20250929
   GOOGLE_PROJECT_ID=your-gcp-project-id
   GOOGLE_LOCATION=us-east5
   MCP_COMMAND=/path/to/linux-mcp-server
   LINUX_MCP_USER=remote-ssh-username  # For remote hosts
   ```

5. **Configure SSH for remote hosts (recommended)**
   ```bash
   mkdir -p ~/.ssh/controlmasters
   cat >> ~/.ssh/config << 'EOF'

   Host *
       ControlMaster auto
       ControlPath ~/.ssh/controlmasters/%r@%h:%p
       ControlPersist 10m
   EOF
   ```

   This enables SSH connection reuse, dramatically speeding up parallel diagnostic queries.

6. **Start the chatbot**
   ```bash
   ./start-chatbot.sh
   ```

   The chatbot will open in your browser at http://localhost:8501

## 📖 Usage

### Example Queries

**Local system diagnostics:**
```
What's the system hostname and OS version?
Show me CPU and memory usage
Check disk space
List running services
```

**Remote host diagnostics:**
```
Check health status of demo.example.local
Show me failed services on prod-server
What's using disk space on /var on web-server?
Find high memory processes on db-server
```

**Multi-step investigations:**
```
The web server is slow, investigate why
Find what's consuming the most CPU
Check for errors in the last hour
Diagnose network connectivity issues
```

For more examples, see [docs/EXAMPLE_QUERIES.md](docs/EXAMPLE_QUERIES.md)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         Streamlit Web UI (app.py)           │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  LangChain ReAct Agent (create_agent)       │
└──────────┬──────────────────────┬───────────┘
           │                      │
           ▼                      ▼
┌─────────────────────┐  ┌──────────────────┐
│ ClaudeVertexChat    │  │  19 MCP Tools    │
│ (Vertex AI wrapper) │  │  (Structured     │
│                     │  │   Tool)          │
└─────────┬───────────┘  └────────┬─────────┘
          │                       │
          ▼                       ▼
┌─────────────────────┐  ┌──────────────────┐
│ Anthropic Vertex    │  │ LinuxMCPClient   │
│ SDK                 │  │ (JSON-RPC/stdio) │
└─────────┬───────────┘  └────────┬─────────┘
          │                       │
          ▼                       ▼
┌─────────────────────┐  ┌──────────────────┐
│ Google Cloud ADC    │  │ Linux MCP Server │
└─────────┬───────────┘  └────────┬─────────┘
          │                       │
          ▼                       ▼
┌─────────────────────┐  ┌──────────────────┐
│ Vertex AI API       │  │ SSH to Remote    │
│ (us-east5)          │  │ Linux Hosts      │
└─────────────────────┘  └──────────────────┘
```

## 📁 Project Structure

```
linux-mcp-server-chatbot/
├── README.md                    # This file
├── QUICKSTART.md                # Quick start guide
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── .env                         # Your configuration (git-ignored)
├── .gitignore                   # Git ignore rules
│
├── app.py                       # Main Streamlit application
├── mcp_client.py                # MCP protocol client (thread-safe JSON-RPC)
├── claude_vertex_wrapper.py     # LangChain wrapper for Claude via Vertex AI
├── start-chatbot.sh             # Launcher script with verification
│
├── docs/                        # Documentation
│   ├── TROUBLESHOOTING.md       # Common issues and solutions
│   ├── EXAMPLE_QUERIES.md       # 100+ example queries
│   └── archive/                 # Historical documentation
│
├── tests/                       # Test scripts
│   ├── test_setup.py            # Setup verification (used by start-chatbot.sh)
│   ├── test_mcp_direct.py       # Test MCP client directly
│   ├── test_mcp_parallel.py     # Test parallel tool execution
│   └── ...                      # Other test scripts
│
└── scripts/                     # Utility scripts
    ├── port-forward.sh          # Port forwarding helper
    └── run-debug.sh             # Debug mode launcher
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `MODEL_ENDPOINT` | API endpoint identifier | `https://vertex-ai-anthropic` | Yes |
| `MODEL_NAME` | Claude model name | `claude-sonnet-4-5@20250929` | Yes |
| `GOOGLE_PROJECT_ID` | GCP project ID | `your-project-id` | Yes |
| `GOOGLE_LOCATION` | GCP region for Vertex AI | `us-east5` | Yes |
| `MCP_COMMAND` | Path to linux-mcp-server | `/home/user/.local/bin/linux-mcp-server` | Yes |
| `LINUX_MCP_USER` | SSH username for remote hosts | `localuser` | Optional |
| `REQUEST_TIMEOUT` | API request timeout (seconds) | `300` | Optional |

### Available Regions for Claude on Vertex AI

- ✅ **us-east5** (tested and working)
- **europe-west1** (may work)
- **asia-southeast1** (may work)

**Note:** Claude is NOT available in `us-central1` on Vertex AI.

## 🔍 Available Diagnostic Tools

The chatbot has access to 19 Linux diagnostic tools through the MCP server:

| Category | Tools |
|----------|-------|
| **System** | `get_system_information`, `get_hardware_information` |
| **CPU** | `get_cpu_information` |
| **Memory** | `get_memory_information` |
| **Disk** | `get_disk_usage`, `list_block_devices`, `list_directories`, `list_files` |
| **Network** | `get_network_interfaces`, `get_network_connections`, `get_listening_ports` |
| **Services** | `list_services`, `get_service_status`, `get_service_logs` |
| **Processes** | `list_processes`, `get_process_info` |
| **Logs** | `get_journal_logs`, `get_audit_logs`, `read_log_file`, `read_file` |

All tools support a `host` parameter for remote execution via SSH.

## 🛠️ Troubleshooting

### Common Issues

**1. Timeout errors on remote hosts**

*Symptoms:* Tools timeout when called in parallel, showing "Error: Timeout waiting for MCP response"

*Solution:*
- Configure SSH ControlMaster for connection reuse (see installation step 5)
- The chatbot now includes thread-safe parallel execution with 120s timeout

**2. "Permission denied" Vertex AI errors**

*Symptoms:* GCP authentication errors when starting the chatbot

*Solution:*
```bash
gcloud auth application-default login
```

**3. "Model not servable in region"**

*Symptoms:* Error when trying to use Claude in certain regions

*Solution:* Use `GOOGLE_LOCATION=us-east5` in .env (Claude is not available in us-central1)

**4. Claude hallucinating instead of calling tools**

*Symptoms:* Chatbot returns plausible-sounding but fake data

*Solution:* Clear Streamlit cache and restart:
```bash
pkill -f streamlit
rm -rf ~/.streamlit/cache
./start-chatbot.sh
```

**5. Tools not appearing in debug output**

*Symptoms:* `[DEBUG] Built 0 tools` in startup output

*Solution:* Verify MCP_COMMAND points to the correct linux-mcp-server binary

For more troubleshooting, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## 💡 How It Works

### Authentication

The chatbot uses the **same authentication as Claude Code CLI**:
- Google Cloud Application Default Credentials (ADC)
- No API keys needed
- Costs billed to your GCP organization

### Tool Calling Flow

1. **User** asks a question in natural language
2. **LangChain Agent** receives the question and plans which tools to call
3. **Claude (via Vertex AI)** makes tool call decisions (parallel when possible)
4. **MCP Client** executes tools via the Linux MCP Server subprocess (thread-safe)
5. **Linux MCP Server** runs commands locally or via SSH
6. **Results** are returned to Claude for synthesis
7. **Claude** generates a natural language response with analysis
8. **User** sees the formatted answer in the Streamlit UI

### Parallel Tool Execution

When Claude makes multiple tool calls simultaneously:
- All calls are sent to the MCP server in parallel threads
- The MCP client uses thread-safe request/response matching with unique IDs
- SSH ControlMaster reuses connections for speed (0.03s per call vs 1-2s)
- Typical 7-tool query completes in ~1.5-2 seconds total

## 📊 Performance

| Metric | Value |
|--------|-------|
| **Response time** | 2-3 seconds (with Claude Vertex) |
| **Tool execution** | 7 parallel tools in ~1.5s |
| **SSH overhead** | 0.03s per call (with ControlMaster) |
| **Model** | Same as Claude Code CLI |
| **Cost** | ~$0.01-0.03 per query (org billing) |

**Comparison with local model:**
- Previous: 30+ minutes per query (24B Mistral on CPU)
- Current: 2-3 seconds per query (Claude via Vertex AI)
- **~900x speedup!**

## 🎯 Key Implementation Details

### Thread-Safe MCP Client

The `mcp_client.py` includes critical fixes for parallel tool execution:
- Thread-safe stdin writes using a Lock
- Response dictionary with unique request IDs
- Polling-based response retrieval (avoids queue race conditions)
- 120-second timeout for remote SSH operations

### Claude Vertex Wrapper

The `claude_vertex_wrapper.py` provides LangChain integration:
- Implements `bind_tools()` for tool binding
- Converts LangChain tools to Anthropic format
- Handles tool call extraction from Claude responses
- Manages ToolMessage, AIMessage, HumanMessage conversions

### SSH Configuration

SSH ControlMaster dramatically improves performance:
- First connection: ~1-2 seconds
- Subsequent connections: ~0.03 seconds (reuses socket)
- Persists for 10 minutes after last use
- Enables true parallel execution

## 🙏 Acknowledgments

- [Linux MCP Server](https://rhel-lightspeed.github.io/linux-mcp-server/) - Red Hat Linux diagnostic tools via MCP
- [LangChain](https://python.langchain.com/) - Agent framework
- [Anthropic Claude](https://www.anthropic.com/claude) - AI model via Vertex AI
- [Streamlit](https://streamlit.io/) - Web UI framework
- [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai) - Managed AI platform

## 📞 Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Documentation**: See [QUICKSTART.md](QUICKSTART.md) and [docs/](docs/)
- **Examples**: See [docs/EXAMPLE_QUERIES.md](docs/EXAMPLE_QUERIES.md)
- **Tests**: Run `python tests/test_setup.py` to verify your setup

---

Built with ❤️ using Claude Sonnet 4.5 via Google Vertex AI
