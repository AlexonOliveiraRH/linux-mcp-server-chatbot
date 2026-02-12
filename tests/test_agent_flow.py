#!/usr/bin/env python3
"""Test full agent flow with Claude Vertex."""
import os
from dotenv import load_dotenv
from claude_vertex_wrapper import ClaudeVertexChat
from mcp_client import LinuxMCPClient
from app import _build_tools
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

load_dotenv()

GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "us-east5")
MODEL_NAME = os.getenv("MODEL_NAME", "claude-sonnet-4-5@20250929")
MCP_COMMAND = os.getenv("MCP_COMMAND", "linux-mcp-server")
LINUX_MCP_USER = os.getenv("LINUX_MCP_USER", "").strip() or None

SYSTEM_PROMPT = """You are a Linux system diagnostics assistant. Use the provided tools to answer the user. For a REMOTE Linux host, always pass "host" in the tool arguments (e.g. {"host": "demo.example.local"}). For the local machine, you may omit host or use {}. Summarize results clearly."""

print("=" * 60)
print("Testing Full Agent Flow")
print("=" * 60)
print()

# Create MCP client
print("1. Creating MCP client...")
env = {}
if LINUX_MCP_USER:
    env["LINUX_MCP_USER"] = LINUX_MCP_USER
mcp = LinuxMCPClient(MCP_COMMAND, env=env or None)
tools = _build_tools(mcp)
print(f"   ✓ Built {len(tools)} tools")
print()

# Create LLM
print("2. Creating Claude Vertex LLM...")
llm = ClaudeVertexChat(
    project_id=GOOGLE_PROJECT_ID,
    region=GOOGLE_LOCATION,
    model=MODEL_NAME,
    temperature=0,
)
print("   ✓ LLM created")
print()

# Create agent
print("3. Creating agent...")
agent = create_agent(
    llm,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
)
print("   ✓ Agent created")
print()

# Test query
print("4. Running test query: 'What is the hostname of demo.example.local?'")
print("-" * 60)
result = agent.invoke(
    {"messages": [HumanMessage(content="What is the hostname of demo.example.local? Use get_system_information tool with host parameter.")]},
    config={"configurable": {"thread_id": "test"}},
)
print("-" * 60)
print()

print("5. Results:")
messages = result.get("messages", [])
print(f"   Total messages: {len(messages)}")
for i, msg in enumerate(messages):
    msg_type = type(msg).__name__
    content_preview = str(msg.content)[:100] if hasattr(msg, 'content') else "No content"
    print(f"   Message {i+1} ({msg_type}): {content_preview}...")
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        print(f"      Tool calls: {[tc['name'] for tc in msg.tool_calls]}")

print()
print("=" * 60)
print("Test complete!")
print("=" * 60)

mcp.close()
