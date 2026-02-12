#!/usr/bin/env python3
"""Test MCP client direct tool calls."""
from mcp_client import LinuxMCPClient
import os
from dotenv import load_dotenv

load_dotenv()

MCP_COMMAND = os.getenv("MCP_COMMAND", "linux-mcp-server")
LINUX_MCP_USER = os.getenv("LINUX_MCP_USER", "").strip() or None

print("=" * 60)
print("Testing MCP Direct Tool Calls")
print("=" * 60)
print()

# Create MCP client
print(f"1. Creating MCP client: {MCP_COMMAND}")
env = {}
if LINUX_MCP_USER:
    env["LINUX_MCP_USER"] = LINUX_MCP_USER
    print(f"   Remote user: {LINUX_MCP_USER}")

mcp = LinuxMCPClient(MCP_COMMAND, env=env or None)
print("   ✓ MCP client created")
print()

# List tools
print("2. Listing tools...")
tools = mcp.list_tools()
print(f"   ✓ Found {len(tools)} tools")
print(f"   First 5: {[t['name'] for t in tools[:5]]}")
print()

# Test local tool call
print("3. Testing LOCAL tool call: get_system_information")
try:
    result = mcp.call_tool("get_system_information", {})
    print(f"   ✓ Success! Result length: {len(result)} chars")
    print(f"   First 200 chars: {result[:200]}...")
except Exception as e:
    print(f"   ✗ Error: {e}")
print()

# Test remote tool call
print("4. Testing REMOTE tool call: get_system_information on demo.example.local")
try:
    result = mcp.call_tool("get_system_information", {"host": "demo.example.local"})
    print(f"   ✓ Success! Result length: {len(result)} chars")
    print(f"   First 200 chars: {result[:200]}...")
except Exception as e:
    print(f"   ✗ Error: {e}")
print()

print("=" * 60)
print("Test complete!")
print("=" * 60)

mcp.close()
