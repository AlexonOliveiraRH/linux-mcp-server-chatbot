"""
Linux MCP Server Chatbot - OpenShift Version
Connects to MCP server via HTTP (streamable-http transport)
"""
import os
import sys
import streamlit as st
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool

# Import Claude Vertex wrapper
from claude_vertex_wrapper import ClaudeVertexChat

# Import MCP clients
from mcp_client_stdio import LinuxMCPClient as LinuxMCPClientStdio, MCPClientError
from mcp_client_http import LinuxMCPClientHTTP, MCPClientError


# Configuration from environment variables
# Stdio transport (integrated mode - MCP server as subprocess)
MCP_COMMAND = os.getenv("MCP_COMMAND")  # e.g., "podman" or "uvx"
MCP_ARGS = os.getenv("MCP_ARGS", "")     # e.g., "run,--rm,quay.io/..."

# HTTP transport (separate server mode)
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://linux-mcp-server:8000/mcp")
MCP_TIMEOUT = int(os.getenv("MCP_TIMEOUT", "300"))

MODEL_ENDPOINT = os.getenv("MODEL_ENDPOINT", "https://vertex-ai-anthropic")
MODEL_NAME = os.getenv("MODEL_NAME", "claude-sonnet-4-5@20250929")
GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "us-east5")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "300"))
TOOL_CHOICE = os.getenv("TOOL_CHOICE", "none")

# Advanced configuration
MODEL_CONTEXT_TOKENS = int(os.getenv("MODEL_CONTEXT_TOKENS", "200000"))
MAX_TOOL_OUTPUT_CHARS = int(os.getenv("MAX_TOOL_OUTPUT_CHARS", "8000"))


# ==================== MCP Client Setup ====================

@st.cache_resource
def get_mcp_client():
    """Initialize and cache the MCP client (stdio or HTTP transport)."""
    if MCP_COMMAND:
        # Stdio transport - run MCP server as subprocess
        print(f"[DEBUG] Starting MCP server via stdio: {MCP_COMMAND}")
        print(f"[DEBUG] MCP_ARGS: {MCP_ARGS}")
        try:
            args = MCP_ARGS.split(",") if MCP_ARGS else []

            # Pass environment variables to subprocess
            env = {
                "LINUX_MCP_USER": os.getenv("LINUX_MCP_USER", "root"),
            }

            # Add SSH key paths if they exist
            ssh_key_path = os.getenv("SSH_KEY_PATH")
            if ssh_key_path and os.path.exists(ssh_key_path):
                env["SSH_KEY_PATH"] = ssh_key_path
                print(f"[DEBUG] Using SSH key: {ssh_key_path}")

            ssh_config_path = os.getenv("SSH_CONFIG_PATH")
            if ssh_config_path and os.path.exists(ssh_config_path):
                env["SSH_CONFIG_PATH"] = ssh_config_path
                print(f"[DEBUG] Using SSH config: {ssh_config_path}")

            print(f"[DEBUG] Creating MCP client with env: {env}")
            client = LinuxMCPClientStdio(command=MCP_COMMAND, args=args, env=env)

            # Give subprocess time to start
            import time
            time.sleep(1)

            # Check if process is alive
            poll_result = client.proc.poll()
            if poll_result is not None:
                print(f"[ERROR] MCP subprocess exited with code {poll_result}")
                # Try to read any stderr output
                stderr_output = client.proc.stderr.read() if client.proc.stderr else ""
                print(f"[ERROR] Subprocess stderr: {stderr_output}")
                raise Exception(f"MCP subprocess exited immediately with code {poll_result}")

            print(f"[DEBUG] MCP subprocess is running (PID: {client.proc.pid})")
            print(f"[DEBUG] MCP client created, listing tools...")
            # Test connection
            tools = client.list_tools()
            print(f"[DEBUG] Connected to MCP server via stdio. Available tools: {len(tools)}")
            return client
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[ERROR] Failed to start MCP server: {e}")
            print(f"[ERROR] Traceback:\n{error_details}")
            st.error(f"Cannot start MCP server with command '{MCP_COMMAND}': {e}")
            st.error(f"Details: {error_details}")
            sys.exit(1)
    else:
        # HTTP transport - connect to existing server
        print(f"[DEBUG] Connecting to MCP server at {MCP_SERVER_URL}")
        try:
            client = LinuxMCPClientHTTP(base_url=MCP_SERVER_URL, timeout=MCP_TIMEOUT)
            # Test connection
            tools = client.list_tools()
            print(f"[DEBUG] Connected to MCP server via HTTP. Available tools: {len(tools)}")
            return client
        except Exception as e:
            print(f"[ERROR] Failed to connect to MCP server: {e}")
            st.error(f"Cannot connect to MCP server at {MCP_SERVER_URL}: {e}")
            sys.exit(1)


@st.cache_resource
def get_langchain_tools():
    """Convert MCP tools to LangChain StructuredTools."""
    from pydantic import BaseModel, create_model, Field
    from typing import Optional

    mcp_client = get_mcp_client()

    try:
        mcp_tools = mcp_client.list_tools()
        print(f"[DEBUG] Retrieved {len(mcp_tools)} tools from MCP server")
    except MCPClientError as e:
        st.error(f"Error listing MCP tools: {e}")
        return []

    langchain_tools = []
    for t in mcp_tools:
        tool_name = t["name"]
        tool_description = t.get("description", "No description")
        input_schema = t.get("inputSchema", {})

        # Extract properties from the schema
        properties = input_schema.get("properties", {})
        required_fields = input_schema.get("required", [])

        # Build pydantic model fields dynamically
        fields = {}
        for prop_name, prop_info in properties.items():
            prop_type = str  # Default to string
            prop_description = prop_info.get("description", "")
            default_value = prop_info.get("default", ...)

            # Handle optional fields (anyOf with null)
            if "anyOf" in prop_info:
                prop_type = Optional[str]
                if default_value == ...:
                    default_value = None

            # If not required and no default, make it optional
            if prop_name not in required_fields and default_value == ...:
                prop_type = Optional[str]
                default_value = None

            fields[prop_name] = (prop_type, Field(default=default_value, description=prop_description))

        # Create Pydantic model for this tool's arguments
        if fields:
            ArgsModel = create_model(f"{tool_name}_args", **fields)
        else:
            ArgsModel = None

        # Create a closure to capture tool_name
        def make_tool_func(name):
            def tool_func(**kwargs) -> str:
                """Execute MCP tool."""
                print(f"[DEBUG] Calling MCP tool: {name} with args: {kwargs}")
                try:
                    result = mcp_client.call_tool(name, kwargs)
                    # Truncate output if too long
                    result_str = str(result)
                    if len(result_str) > MAX_TOOL_OUTPUT_CHARS:
                        result_str = result_str[:MAX_TOOL_OUTPUT_CHARS] + f"\n... (truncated {len(result_str) - MAX_TOOL_OUTPUT_CHARS} chars)"
                    return result_str
                except MCPClientError as e:
                    return f"Error calling tool {name}: {e}"

            return tool_func

        langchain_tools.append(
            StructuredTool(
                name=tool_name,
                description=tool_description,
                func=make_tool_func(tool_name),
                args_schema=ArgsModel,
            )
        )

    print(f"[DEBUG] Created {len(langchain_tools)} LangChain StructuredTools")
    print(f"[DEBUG] Tool names: {[t.name for t in langchain_tools]}")
    return langchain_tools


# ==================== LLM Setup ====================

@st.cache_resource
def get_llm():
    """Initialize the LLM (Claude via Vertex AI)."""
    print(f"[DEBUG] Initializing LLM: {MODEL_NAME} at {MODEL_ENDPOINT}")

    if "vertex-ai-anthropic" in MODEL_ENDPOINT.lower():
        # Claude via Vertex AI
        if not GOOGLE_PROJECT_ID:
            st.error("GOOGLE_PROJECT_ID environment variable not set")
            sys.exit(1)

        llm = ClaudeVertexChat(
            model=MODEL_NAME,
            project_id=GOOGLE_PROJECT_ID,
            region=GOOGLE_LOCATION,
            max_tokens=8192,
            temperature=0.0,
            timeout=REQUEST_TIMEOUT,
        )
        print(f"[DEBUG] Using ClaudeVertexChat with project {GOOGLE_PROJECT_ID}")

    elif "api.openai.com" in MODEL_ENDPOINT.lower():
        # OpenAI
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=MODEL_NAME,
            temperature=0.0,
            timeout=REQUEST_TIMEOUT,
        )
        print(f"[DEBUG] Using ChatOpenAI")

    else:
        # Generic OpenAI-compatible endpoint
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            base_url=MODEL_ENDPOINT,
            model=MODEL_NAME,
            temperature=0.0,
            timeout=REQUEST_TIMEOUT,
        )
        print(f"[DEBUG] Using ChatOpenAI with custom endpoint: {MODEL_ENDPOINT}")

    return llm


@st.cache_resource
def get_agent():
    """Create the LangChain agent with MCP tools."""
    llm = get_llm()
    tools = get_langchain_tools()

    if not tools:
        st.error("No MCP tools available. Check MCP server connection.")
        sys.exit(1)

    # System prompt
    system_prompt = """You are a helpful Linux system administrator assistant.

You have access to tools that can run commands on Linux systems via SSH.

When a user asks about system information, use the appropriate tools to gather the data.

IMPORTANT:
- You can call MULTIPLE tools in PARALLEL for efficiency
- When tools are independent, call them all at once in a single response
- Format your final answers clearly and concisely
- For remote systems, always pass the 'host' parameter to the tools
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # Bind tools to LLM
    if TOOL_CHOICE == "auto":
        llm_with_tools = llm.bind_tools(tools)
    else:
        # For models without native tool calling, use TOOL_CHOICE=none
        llm_with_tools = llm

    print(f"[DEBUG] Creating agent with {len(tools)} tools")
    print(f"[DEBUG] Tool choice: {TOOL_CHOICE}")

    agent = create_tool_calling_agent(llm_with_tools, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True,
    )

    print(f"[DEBUG] Agent created successfully")
    return agent_executor


# ==================== Streamlit UI ====================

def main():
    st.set_page_config(
        page_title="Linux MCP Chatbot",
        page_icon="🐧",
        layout="wide",
    )

    st.title("🐧 Linux MCP Server Chatbot")
    st.markdown("Ask questions about your Linux systems. The AI agent will use MCP tools to gather information.")

    # Sidebar with configuration
    with st.sidebar:
        st.header("Configuration")
        if MCP_COMMAND:
            st.text(f"MCP Server: stdio ({MCP_COMMAND})")
        else:
            st.text(f"MCP Server: {MCP_SERVER_URL}")
        st.text(f"Model: {MODEL_NAME}")
        st.text(f"Endpoint: {MODEL_ENDPOINT}")

        # Display connected tools
        try:
            tools = get_langchain_tools()
            st.success(f"✅ Connected ({len(tools)} tools)")
            with st.expander("Available Tools"):
                for tool in tools:
                    st.text(f"• {tool.name}")
        except Exception as e:
            st.error(f"❌ MCP connection error: {e}")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about your Linux systems..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    agent = get_agent()
                    response = agent.invoke({"input": prompt})
                    answer = response.get("output", "No response")

                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

    # Clear chat button
    if st.sidebar.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()


if __name__ == "__main__":
    main()
