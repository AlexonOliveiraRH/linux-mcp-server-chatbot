#!/usr/bin/env python3
"""Debug script to test MCP client and tool loading."""
import os
import sys
from dotenv import load_dotenv
from mcp_client import LinuxMCPClient, MCPClientError

load_dotenv()

MCP_COMMAND = os.getenv("MCP_COMMAND", "linux-mcp-server")
LINUX_MCP_USER = os.getenv("LINUX_MCP_USER", "").strip() or None

print("=" * 60)
print("MCP Client Debug")
print("=" * 60)
print()

print(f"MCP_COMMAND: {MCP_COMMAND}")
print(f"LINUX_MCP_USER: {LINUX_MCP_USER}")
print()

# Parse command
parts = MCP_COMMAND.strip().split()
cmd, mcp_args = (parts[0], parts[1:]) if parts else (MCP_COMMAND, [])
print(f"Command: {cmd}")
print(f"Args: {mcp_args}")
print()

# Setup environment
env = {}
if LINUX_MCP_USER:
    env["LINUX_MCP_USER"] = LINUX_MCP_USER
print(f"Environment: {env}")
print()

# Create MCP client
print("Creating MCP client...")
try:
    mcp = LinuxMCPClient(cmd, args=mcp_args or None, env=env or None)
    print("✓ MCP client created")
except Exception as e:
    print(f"✗ Failed to create MCP client: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# List tools
print("Listing tools...")
try:
    tools = mcp.list_tools()
    print(f"✓ Got {len(tools)} tools")
    print()

    if tools:
        print("Available tools:")
        for i, tool in enumerate(tools, 1):
            if isinstance(tool, dict):
                name = tool.get("name", "Unknown")
                desc = tool.get("description", "No description")
                print(f"  {i}. {name}")
                print(f"     {desc[:80]}...")
            else:
                print(f"  {i}. {tool}")
    else:
        print("⚠️  No tools returned!")
        print("Will use fallback tool list")

except Exception as e:
    print(f"✗ Failed to list tools: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test a tool
if tools:
    print("Testing get_system_information tool...")
    try:
        result = mcp.call_tool("get_system_information", {})
        print("✓ Tool call successful")
        print()
        print("Result:")
        print(result[:500])
        if len(result) > 500:
            print(f"\n... ({len(result) - 500} more characters)")
    except Exception as e:
        print(f"✗ Tool call failed: {e}")
        import traceback
        traceback.print_exc()

print()
print("=" * 60)
print("Debug complete")
print("=" * 60)

# Clean up
mcp.close()
