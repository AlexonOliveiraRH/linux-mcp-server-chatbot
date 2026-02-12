#!/usr/bin/env python3
"""Test if the agent has tools."""
import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict
from langchain_core.tools import StructuredTool
from typing import Any, Optional

from mcp_client import LinuxMCPClient

load_dotenv()

MODEL_ENDPOINT = os.getenv("MODEL_ENDPOINT", "http://localhost:8080").rstrip("/")
MODEL_NAME = os.getenv("MODEL_NAME", "")
MCP_COMMAND = os.getenv("MCP_COMMAND", "linux-mcp-server")
LINUX_MCP_USER = os.getenv("LINUX_MCP_USER", "").strip() or None

print("=" * 60)
print("Agent Tool Test")
print("=" * 60)
print()

# Create MCP client
print("Creating MCP client...")
parts = MCP_COMMAND.strip().split()
cmd, mcp_args = (parts[0], parts[1:]) if parts else (MCP_COMMAND, [])
env = {}
if LINUX_MCP_USER:
    env["LINUX_MCP_USER"] = LINUX_MCP_USER

mcp = LinuxMCPClient(cmd, args=mcp_args or None, env=env or None)
print("✓ MCP client created")
print()

# Get tools from MCP
print("Getting tools from MCP...")
raw_tools = mcp.list_tools()
print(f"✓ Got {len(raw_tools)} tools from MCP")
print()

# Create LangChain tools
print("Creating LangChain StructuredTools...")

class MCPToolArgs(BaseModel):
    model_config = ConfigDict(extra="allow")
    host: Optional[str] = None

tools = []
for t in raw_tools[:5]:  # Just first 5 for testing
    name = t.get("name")
    desc = t.get("description", "")

    def make_run_func(tool_name):
        def run(**kwargs: Any) -> str:
            try:
                result = mcp.call_tool(tool_name, kwargs)
                return result[:200] or "(No output)"
            except Exception as e:
                return f"Error: {e}"
        return run

    tool = StructuredTool.from_function(
        name=name,
        description=desc,
        func=make_run_func(name),
        args_schema=MCPToolArgs,
    )
    tools.append(tool)

print(f"✓ Created {len(tools)} LangChain tools")
print(f"   Tool names: {[t.name for t in tools]}")
print()

# Create LLM
print("Creating LLM...")
llm = ChatOpenAI(
    model=MODEL_NAME,
    openai_api_key="not-needed",
    base_url=f"{MODEL_ENDPOINT}/v1",
    temperature=0,
)
print(f"✓ LLM created for model: {MODEL_NAME}")
print()

# Create agent
print("Creating agent...")
try:
    agent = create_agent(
        llm,
        tools=tools,
        system_prompt="You are a helpful assistant with access to Linux diagnostic tools.",
    )
    print("✓ Agent created")
    print()
except Exception as e:
    print(f"✗ Agent creation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Check if agent has tools
print("Checking agent configuration...")
print(f"  Agent type: {type(agent)}")
print(f"  Agent nodes: {agent.nodes if hasattr(agent, 'nodes') else 'N/A'}")

# Try to invoke the agent
print()
print("Testing agent with a query...")
try:
    from langchain_core.messages import HumanMessage

    result = agent.invoke(
        {"messages": [HumanMessage(content="What tools do you have access to?")]},
        config={"configurable": {"thread_id": "test"}},
    )

    print("✓ Agent responded")
    print()
    print("Response:")
    messages = result.get("messages", [])
    for msg in messages:
        if hasattr(msg, 'content') and msg.content:
            print(f"  {msg.content[:300]}")
            break

except Exception as e:
    print(f"✗ Agent invocation failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("Test complete")
print("=" * 60)

mcp.close()
