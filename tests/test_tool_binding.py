#!/usr/bin/env python3
"""Test tool binding with ClaudeVertexChat."""
import os
from dotenv import load_dotenv
from claude_vertex_wrapper import ClaudeVertexChat
from mcp_client import LinuxMCPClient
from app import _build_tools

load_dotenv()

GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "us-east5")
MODEL_NAME = os.getenv("MODEL_NAME", "claude-sonnet-4-5@20250929")
MCP_COMMAND = os.getenv("MCP_COMMAND", "linux-mcp-server")

print("=" * 60)
print("Testing Tool Binding with ClaudeVertexChat")
print("=" * 60)
print()

# Create MCP client
print("1. Creating MCP client...")
mcp = LinuxMCPClient(MCP_COMMAND)
print(f"   ✓ MCP client created")

# Build tools
print("2. Building tools...")
tools = _build_tools(mcp)
print(f"   ✓ Built {len(tools)} tools")
print(f"   First 3 tools: {[t.name for t in tools[:3]]}")
print()

# Create LLM
print("3. Creating ClaudeVertexChat...")
llm = ClaudeVertexChat(
    project_id=GOOGLE_PROJECT_ID,
    region=GOOGLE_LOCATION,
    model=MODEL_NAME,
    temperature=0,
)
print(f"   ✓ LLM created")
print(f"   Tools before binding: {llm._tools}")
print()

# Bind tools
print("4. Binding tools to LLM...")
bound_llm = llm.bind_tools(tools)
print(f"   ✓ Tools bound")
print(f"   Tools after binding: {len(bound_llm._tools) if bound_llm._tools else 0}")
if bound_llm._tools:
    print(f"   First tool: {bound_llm._tools[0]['name']}")
    print(f"   Tool schema keys: {list(bound_llm._tools[0].keys())}")
print()

# Test invocation
print("5. Testing LLM invocation with simple query...")
print("-" * 60)
from langchain_core.messages import HumanMessage

result = bound_llm.invoke([HumanMessage(content="What is the hostname of the local system? Use the get_system_information tool.")])
print("-" * 60)
print()
print(f"Result type: {type(result)}")
print(f"Result content: {result.content[:200]}...")
if hasattr(result, 'tool_calls'):
    print(f"Tool calls: {result.tool_calls}")
print()
print("=" * 60)
print("Test complete!")
print("=" * 60)
