#!/usr/bin/env python3
"""Test if the agent can actually call tools."""
import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict
from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage
from typing import Any, Optional

from mcp_client import LinuxMCPClient

load_dotenv()

MODEL_ENDPOINT = os.getenv("MODEL_ENDPOINT", "http://localhost:8080").rstrip("/")
MODEL_NAME = os.getenv("MODEL_NAME", "")
MCP_COMMAND = os.getenv("MCP_COMMAND", "linux-mcp-server")
LINUX_MCP_USER = os.getenv("LINUX_MCP_USER", "").strip() or None

print("Testing tool calling with a real query...")
print()

# Create MCP client
parts = MCP_COMMAND.strip().split()
cmd, mcp_args = (parts[0], parts[1:]) if parts else (MCP_COMMAND, [])
env = {}
if LINUX_MCP_USER:
    env["LINUX_MCP_USER"] = LINUX_MCP_USER

mcp = LinuxMCPClient(cmd, args=mcp_args or None, env=env or None)

# Get all tools
raw_tools = mcp.list_tools()
print(f"Available tools: {len(raw_tools)}")

class MCPToolArgs(BaseModel):
    model_config = ConfigDict(extra="allow")
    host: Optional[str] = None

tools = []
for t in raw_tools:
    name = t.get("name")
    desc = t.get("description", f"Call Linux MCP tool: {name}")

    def make_run_func(tool_name):
        def run(**kwargs: Any) -> str:
            print(f"    → Calling tool: {tool_name} with args: {kwargs}")
            try:
                result = mcp.call_tool(tool_name, kwargs)
                print(f"    ← Tool returned {len(result)} characters")
                return result[:500] or "(No output)"
            except Exception as e:
                print(f"    ← Tool error: {e}")
                return f"Error: {e}"
        return run

    tool = StructuredTool.from_function(
        name=name,
        description=desc,
        func=make_run_func(name),
        args_schema=MCPToolArgs,
    )
    tools.append(tool)

print(f"Created {len(tools)} LangChain tools")
print()

# Create LLM with verbose
llm = ChatOpenAI(
    model=MODEL_NAME,
    openai_api_key="not-needed",
    base_url=f"{MODEL_ENDPOINT}/v1",
    temperature=0,
    verbose=True,
)

# Create agent with clearer system prompt
system_prompt = """You are a Linux diagnostics assistant. You have access to diagnostic tools.

When asked about system information, use the get_system_information tool.
When asked about CPU, use get_cpu_information.
When asked about memory, use get_memory_information.

Always use the available tools to answer questions about Linux systems."""

agent = create_agent(
    llm,
    tools=tools,
    system_prompt=system_prompt,
)

print("Agent created. Testing with query...")
print()

# Test query
query = "What is the system hostname and OS version?"
print(f"Query: {query}")
print()

try:
    result = agent.invoke(
        {"messages": [HumanMessage(content=query)]},
        config={"configurable": {"thread_id": "test"}},
    )

    print()
    print("=" * 60)
    print("RESULT:")
    print("=" * 60)
    messages = result.get("messages", [])
    for i, msg in enumerate(messages):
        print(f"\nMessage {i+1} ({type(msg).__name__}):")
        if hasattr(msg, 'content'):
            print(msg.content if isinstance(msg.content, str) else str(msg.content)[:500])

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

mcp.close()
