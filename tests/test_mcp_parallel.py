#!/usr/bin/env python3
"""Test MCP parallel tool calls."""
import time
import threading
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

# Test parallel calls
tools_to_test = [
    ("get_system_information", {"host": "demo.example.local"}),
    ("get_cpu_information", {"host": "demo.example.local"}),
    ("get_memory_information", {"host": "demo.example.local"}),
    ("get_disk_usage", {"host": "demo.example.local"}),
    ("get_network_interfaces", {"host": "demo.example.local"}),
    ("list_services", {"host": "demo.example.local"}),
]

results = {}
def call_tool(tool_name, args):
    start = time.time()
    try:
        result = mcp.call_tool(tool_name, args)
        elapsed = time.time() - start
        results[tool_name] = (True, elapsed, len(result))
    except Exception as e:
        elapsed = time.time() - start
        results[tool_name] = (False, elapsed, str(e)[:50])

print("Testing PARALLEL tool calls...")
print("=" * 60)

start_total = time.time()
threads = []
for tool_name, args in tools_to_test:
    t = threading.Thread(target=call_tool, args=(tool_name, args))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

total_elapsed = time.time() - start_total

print()
for tool_name, (success, elapsed, info) in results.items():
    status = "✓" if success else "✗"
    if success:
        print(f"{status} {tool_name:30s} {elapsed:.2f}s ({info} chars)")
    else:
        print(f"{status} {tool_name:30s} {elapsed:.2f}s - {info}")

print("=" * 60)
print(f"Total time (parallel): {total_elapsed:.2f}s")
print(f"Speedup vs sequential (~1.73s): {1.73/total_elapsed:.1f}x")

mcp.close()
