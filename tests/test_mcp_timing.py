#!/usr/bin/env python3
"""Test MCP tool call timing."""
import time
from mcp_client import LinuxMCPClient
import os
from dotenv import load_dotenv

load_dotenv()

MCP_COMMAND = os.getenv("MCP_COMMAND")
LINUX_MCP_USER = os.getenv("LINUX_MCP_USER", "").strip() or None

env = {}
if LINUX_MCP_USER:
    env["LINUX_MCP_USER"] = LINUX_MCP_USER

mcp = LinuxMCPClient(MCP_COMMAND, env=env or None)

# Test each tool that was called
tools_to_test = [
    ("get_system_information", {"host": "demo.example.local"}),
    ("get_cpu_information", {"host": "demo.example.local"}),
    ("get_memory_information", {"host": "demo.example.local"}),
    ("get_disk_usage", {"host": "demo.example.local"}),
    ("get_network_interfaces", {"host": "demo.example.local"}),
    ("list_services", {"host": "demo.example.local"}),
    ("list_processes", {"host": "demo.example.local"}),
]

print("Testing tool call timing (sequential)...")
print("=" * 60)

total_time = 0
for tool_name, args in tools_to_test:
    start = time.time()
    try:
        result = mcp.call_tool(tool_name, args)
        elapsed = time.time() - start
        total_time += elapsed
        status = f"✓ {elapsed:.2f}s"
        result_len = len(result)
    except Exception as e:
        elapsed = time.time() - start
        total_time += elapsed
        status = f"✗ {elapsed:.2f}s - {str(e)[:50]}"
        result_len = 0

    print(f"{tool_name:30s} {status:20s} ({result_len} chars)")

print("=" * 60)
print(f"Total time: {total_time:.2f}s")
print(f"Average per tool: {total_time/len(tools_to_test):.2f}s")

mcp.close()
