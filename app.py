"""
Linux MCP Server Chatbot — Streamlit UI + LangChain agent + Linux MCP Server.

Run diagnostics on any Linux host (local or remote) using the tools provided by
the Linux MCP Server. Works with any OpenAI-compatible inference server (vLLM,
KServe, Ollama, etc.) and any model (e.g. Mistral, Gemma, Granite).

Setup:
  - Install and run the Linux MCP Server: https://rhel-lightspeed.github.io/linux-mcp-server/install/
  - Configure .env (model endpoint, MCP command, LINUX_MCP_USER for remote hosts).
  - Use an instruction-tuned model for best tool-use behavior.
"""
import os
import traceback
import json
import time
import requests
from typing import Any, Optional

import streamlit as st
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware.types import wrap_model_call
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict

try:
    from langchain_anthropic import ChatAnthropic, ChatAnthropicVertex
    HAS_ANTHROPIC = True
    HAS_ANTHROPIC_VERTEX = True
except ImportError:
    try:
        from langchain_anthropic import ChatAnthropic
        HAS_ANTHROPIC = True
        HAS_ANTHROPIC_VERTEX = False
    except ImportError:
        HAS_ANTHROPIC = False
        HAS_ANTHROPIC_VERTEX = False

try:
    from langchain_google_vertexai import ChatVertexAI
    HAS_GOOGLE_VERTEX = True
except ImportError:
    HAS_GOOGLE_VERTEX = False

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False

from mcp_client import LinuxMCPClient, MCPClientError
from claude_vertex_wrapper import ClaudeVertexChat

load_dotenv()

# -----------------------------------------------------------------------------
# Config (see .env.example)
# -----------------------------------------------------------------------------
MODEL_ENDPOINT = os.getenv("MODEL_ENDPOINT", "http://localhost:8080").rstrip("/")
OPENAI_API_PATH = (os.getenv("OPENAI_API_PATH", "").strip().rstrip("/") or "")
MODEL_NAME = os.getenv("MODEL_NAME", "")
OPENAI_API_HOST = (os.getenv("OPENAI_API_HOST", "").strip() or None)
MCP_COMMAND = os.getenv("MCP_COMMAND", "linux-mcp-server")
LINUX_MCP_USER = (os.getenv("LINUX_MCP_USER", "").strip() or None)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip() or None
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip() or None
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "").strip() or None
GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "us-central1").strip()
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "120"))
MODEL_CONTEXT_TOKENS = int(os.getenv("MODEL_CONTEXT_TOKENS", "4096"))
MAX_TOOL_OUTPUT_CHARS = int(os.getenv("MAX_TOOL_OUTPUT_CHARS", "2400"))
# Tool choice sent to the API: "none" (vLLM without --enable-auto-tool-choice), "auto", or "required"
TOOL_CHOICE = (os.getenv("TOOL_CHOICE", "none").strip().lower() or "none")

# Cap tool output so the prompt fits in context
_SAFE_CHARS = min(MAX_TOOL_OUTPUT_CHARS, int(MODEL_CONTEXT_TOKENS * 0.12 * 4))


# -----------------------------------------------------------------------------
# Server detection and model discovery
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=60)
def detect_server_type(endpoint: str) -> str:
    """Detect if the endpoint is Ollama or another OpenAI-compatible server."""
    try:
        # Try Ollama API
        response = requests.get(f"{endpoint}/api/tags", timeout=5)
        if response.status_code == 200:
            return "Ollama"
    except:
        pass

    try:
        # Try OpenAI-compatible API
        response = requests.get(f"{endpoint}/v1/models", timeout=5)
        if response.status_code == 200:
            return "OpenAI-compatible"
    except:
        pass

    return "Unknown"


@st.cache_data(show_spinner=False, ttl=60)
def get_ollama_models(endpoint: str) -> list:
    """Get available models from Ollama server."""
    try:
        response = requests.get(f"{endpoint}/api/tags", timeout=5)
        if response.status_code == 200:
            data = json.loads(response.content)
            return [model["name"].split(":")[0] for model in data.get("models", [])]
    except:
        pass
    return []


def _truncate(text: str) -> str:
    if not text or len(text) <= _SAFE_CHARS:
        return text or ""
    return text[:_SAFE_CHARS] + "\n\n... (truncated)"


class _MCPToolArgs(BaseModel):
    """Schema for MCP tool args: optional host + any other params the tool accepts."""

    model_config = ConfigDict(extra="allow")

    host: Optional[str] = None
    Host: Optional[str] = None  # some models send capital H


def _make_tool(name: str, description: str, mcp: LinuxMCPClient):
    """Build a LangChain tool that calls the MCP server (tool-calling: LLM sends a dict of args)."""

    def run(**kwargs: Any) -> str:
        args = {k: v for k, v in kwargs.items() if v is not None and v != ""}
        if "Host" in args and "host" not in args:
            args["host"] = args.pop("Host")
        try:
            out = mcp.call_tool(name, args)
            return _truncate(out or "(No output)")
        except MCPClientError as e:
            return f"Error: {e}"

    return StructuredTool.from_function(
        name=name,
        description=description or f"Call Linux MCP tool: {name}",
        func=run,
        args_schema=_MCPToolArgs,
    )


def _build_tools(mcp: LinuxMCPClient) -> list:
    try:
        raw = mcp.list_tools()
    except Exception:
        raw = []
    if not raw:
        # Fallback list from Linux MCP Server usage docs
        fallback = [
            ("get_system_information", "Basic system info (OS, kernel, hostname, uptime)."),
            ("get_cpu_information", "CPU info, cores, load."),
            ("get_memory_information", "RAM and swap usage."),
            ("get_disk_usage", "Filesystem usage and mount points."),
            ("get_hardware_information", "Hardware (CPU arch, PCI, USB)."),
            ("list_services", "All systemd services and status."),
            ("get_service_status", "Status of a systemd service. Args: service_name."),
            ("get_service_logs", "Recent logs for a service. Args: service_name, lines (optional)."),
            ("list_processes", "Running processes by CPU usage."),
            ("get_process_info", "Details for a process. Args: pid."),
            ("get_journal_logs", "Systemd journal. Args: unit, priority, since, lines (optional)."),
            ("get_audit_logs", "Audit logs. Args: lines (optional)."),
            ("read_log_file", "Read a log file. Args: log_path, lines (optional)."),
            ("get_network_interfaces", "Network interfaces and IPs."),
            ("get_network_connections", "Active network connections."),
            ("get_listening_ports", "Listening ports."),
            ("list_block_devices", "Block devices and I/O."),
            ("list_directories", "List dirs under path. Args: path, order_by, sort, top_n (optional)."),
            ("list_files", "List files under path. Args: path, order_by, sort, top_n (optional)."),
            ("read_file", "Read a file. Args: path, lines (optional)."),
        ]
        return [_make_tool(n, d, mcp) for n, d in fallback]
    tools = []
    for t in raw:
        if isinstance(t, dict):
            n, d = t.get("name"), t.get("description") or ""
        else:
            n, d = getattr(t, "name", None) or str(t), ""
        if n:
            tools.append(_make_tool(n, d, mcp))
    return tools


SYSTEM_PROMPT = """You are a Linux system diagnostics assistant. Use the provided tools to answer the user. For a REMOTE Linux host, always pass "host" in the tool arguments (e.g. {"host": "demo.example.local"}). For the local machine, you may omit host or use {}. Summarize results clearly."""


@wrap_model_call
def _tool_choice_middleware(request, handler):
    """Override tool_choice so vLLM (and similar) accept the request when they don't support "auto"."""
    return handler(request.override(tool_choice=TOOL_CHOICE))


@st.cache_resource
def _get_graph(_key: tuple):
    """Build MCP client, tools, LLM, and LangChain agent (cached by config key)."""
    # Extract model name from the key tuple (last element)
    model_name = _key[3] if len(_key) > 3 else MODEL_NAME

    parts = MCP_COMMAND.strip().split()
    cmd, mcp_args = (parts[0], parts[1:]) if parts else (MCP_COMMAND, [])
    env = {}
    if LINUX_MCP_USER:
        env["LINUX_MCP_USER"] = LINUX_MCP_USER

    print(f"[DEBUG] Creating MCP client: {cmd}")
    mcp = LinuxMCPClient(cmd, args=mcp_args or None, env=env or None)

    print(f"[DEBUG] Building tools...")
    tools = _build_tools(mcp)
    print(f"[DEBUG] Built {len(tools)} tools")

    if not tools:
        raise RuntimeError("No MCP tools. Check MCP_COMMAND and linux-mcp-server.")

    # Detect which API to use
    is_anthropic_direct = "anthropic.com" in MODEL_ENDPOINT.lower() or (ANTHROPIC_API_KEY and not MODEL_ENDPOINT.startswith("http://localhost"))
    is_anthropic_vertex = ("vertex-ai-anthropic" in MODEL_ENDPOINT.lower() or "vertex-ai-claude" in MODEL_ENDPOINT.lower()) or (GOOGLE_PROJECT_ID and "claude" in model_name.lower())
    is_google_genai = "genai" in MODEL_ENDPOINT.lower() or "ai-studio" in MODEL_ENDPOINT.lower() or (GOOGLE_API_KEY and "gemini" in model_name.lower() and not GOOGLE_PROJECT_ID)
    is_google_vertex = "vertex" in MODEL_ENDPOINT.lower() and "gemini" in model_name.lower()

    if is_anthropic_vertex and GOOGLE_PROJECT_ID:
        print(f"[DEBUG] Using ClaudeVertexChat (Claude via Vertex AI - SAME AS CLAUDE CODE!): {model_name}")
        llm = ClaudeVertexChat(
            model=model_name,
            project_id=GOOGLE_PROJECT_ID,
            region=GOOGLE_LOCATION,
            temperature=0,
            timeout=REQUEST_TIMEOUT,
        )
    elif is_google_genai and HAS_GOOGLE_GENAI and GOOGLE_API_KEY:
        print(f"[DEBUG] Using ChatGoogleGenerativeAI (Gemini AI Studio) with model: {model_name}")
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=GOOGLE_API_KEY,
            temperature=0,
            timeout=REQUEST_TIMEOUT,
        )
    elif is_google_vertex and HAS_GOOGLE_VERTEX and GOOGLE_PROJECT_ID:
        print(f"[DEBUG] Using ChatVertexAI (Gemini via Vertex AI) with model: {model_name}")
        llm = ChatVertexAI(
            model=model_name,
            project=GOOGLE_PROJECT_ID,
            location=GOOGLE_LOCATION,
            temperature=0,
            timeout=REQUEST_TIMEOUT,
        )
    elif is_anthropic_direct and HAS_ANTHROPIC and ANTHROPIC_API_KEY:
        print(f"[DEBUG] Using ChatAnthropic with model: {model_name}")
        llm = ChatAnthropic(
            model=model_name,
            anthropic_api_key=ANTHROPIC_API_KEY,
            temperature=0,
            timeout=REQUEST_TIMEOUT,
        )
    else:
        print(f"[DEBUG] Using ChatOpenAI with model: {model_name}")
        base = MODEL_ENDPOINT + ("/" + OPENAI_API_PATH if OPENAI_API_PATH else "") + "/v1"
        llm_kw = dict(
            model=model_name,
            openai_api_key="not-needed",
            base_url=base,
            temperature=0,
            request_timeout=REQUEST_TIMEOUT,
        )
        if OPENAI_API_HOST:
            llm_kw["default_headers"] = {"Host": OPENAI_API_HOST}
        llm = ChatOpenAI(**llm_kw)

    print(f"[DEBUG] Creating agent with {len(tools)} tools")
    print(f"[DEBUG] Tool names: {[t.name for t in tools[:5]]}...")

    graph = create_agent(
        llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        middleware=[_tool_choice_middleware],
    )
    print(f"[DEBUG] Agent created successfully")
    return graph


def main():
    st.set_page_config(page_title="Linux MCP Chatbot", page_icon="🐧", layout="centered")
    st.title("🐧 Linux MCP Server Chatbot")
    st.caption("Run Linux diagnostics on any host (local or remote) via the Linux MCP Server.")

    # Detect server type and show model selection for Ollama
    with st.spinner("Detecting inference server..."):
        server_type = detect_server_type(MODEL_ENDPOINT)

    # Determine which model to use
    selected_model = MODEL_NAME

    if server_type == "Ollama":
        ollama_models = get_ollama_models(MODEL_ENDPOINT)
        if ollama_models:
            st.sidebar.markdown("### Model Selection")
            # If MODEL_NAME is set and in the list, use it as default, otherwise use first model
            default_idx = 0
            if MODEL_NAME and MODEL_NAME in ollama_models:
                default_idx = ollama_models.index(MODEL_NAME)
            selected_model = st.sidebar.radio(
                "Available models:",
                ollama_models,
                index=default_idx,
                key="model_selector"
            )
            st.sidebar.markdown("---")
        else:
            if not MODEL_NAME:
                st.error("Could not detect Ollama models. Set MODEL_NAME in .env manually.")
                st.stop()
    else:
        if not MODEL_NAME:
            st.error("Set MODEL_NAME in .env (e.g. gemma-3-270m, Mistral-Small-3.2-24B-Instruct-2506).")
            st.stop()

    st.sidebar.markdown(f"**Server Type:** `{server_type}`")
    st.sidebar.markdown(f"**Model:** `{selected_model}`")
    st.sidebar.markdown(f"**Endpoint:** `{MODEL_ENDPOINT}`")
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "Uses the [Linux MCP Server](https://rhel-lightspeed.github.io/linux-mcp-server/usage/). "
        "For remote hosts, set `LINUX_MCP_USER` in .env (e.g. `localuser` for demo.example.local)."
    )

    config_key = (MODEL_ENDPOINT, OPENAI_API_PATH or "", OPENAI_API_HOST or "", selected_model)
    try:
        graph = _get_graph(config_key)
    except Exception as e:
        st.error(f"Startup failed: {e}. Check MCP_COMMAND and MODEL_ENDPOINT.")
        st.stop()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).markdown(msg["content"])

    if prompt := st.chat_input("Ask about system info, services, logs, network, disk..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Running tools..."):
                try:
                    print(f"[DEBUG] Invoking agent with prompt: {prompt[:50]}...")
                    result = graph.invoke(
                        {"messages": [HumanMessage(content=prompt)]},
                        config={"configurable": {"thread_id": "default"}},
                    )
                    messages = result.get("messages") or []
                    print(f"[DEBUG] Got {len(messages)} messages in result")

                    # Debug: print all messages
                    for i, m in enumerate(messages):
                        msg_type = type(m).__name__
                        has_tool_calls = hasattr(m, 'tool_calls') and m.tool_calls
                        print(f"[DEBUG] Message {i+1}: {msg_type}, has_tool_calls={has_tool_calls}")
                        if has_tool_calls:
                            print(f"[DEBUG]   Tool calls: {[tc['name'] for tc in m.tool_calls]}")
                        if msg_type == "ToolMessage":
                            content_preview = str(m.content)[:200] if hasattr(m, 'content') else "No content"
                            print(f"[DEBUG]   ToolMessage content: {content_preview}...")

                    out = ""
                    for m in reversed(messages):
                        if isinstance(m, AIMessage) and m.content:
                            out = m.content if isinstance(m.content, str) else (m.content[0].get("text", "") if isinstance(m.content, list) and m.content else str(m.content))
                            break
                    if not out:
                        out = str(result)
                    print(f"[DEBUG] Final output length: {len(out)} chars")
                except Exception as e:
                    err_str = str(e)
                    out = f"**Error:** {err_str}"
                    if "chat template" in err_str.lower() and "tokenizer" in err_str.lower():
                        out = (
                            "**Error:** The inference server reported that this model has no chat template.\n\n"
                            "This is a **server-side** setting: start your server (e.g. vLLM) with an explicit "
                            "`--chat-template` for this model. Example for Gemma 3 with vLLM:\n\n"
                            "```\nvllm serve google/gemma-3-270m-it --chat-template /path/to/gemma3_chat.jinja\n```\n\n"
                            "See your server docs and [vLLM chat templates](https://docs.vllm.ai/en/latest/cli/chat.html)."
                        )
                    with st.expander("Traceback"):
                        st.code(traceback.format_exc())
            st.markdown(out)
        st.session_state.messages.append({"role": "assistant", "content": out})

    if st.sidebar.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()


if __name__ == "__main__":
    main()
