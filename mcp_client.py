"""
MCP client for Linux MCP Server (stdio transport).
See: https://rhel-lightspeed.github.io/linux-mcp-server/clients/
"""
import json
import os
import subprocess
import threading
import queue
import itertools
from threading import Lock


class MCPClientError(Exception):
    """Raised when the MCP server returns an error or times out."""
    pass


class LinuxMCPClient:
    """Client for the Linux MCP Server over stdio (same pattern as Claude Code / Cursor)."""

    def __init__(self, command: str, args: list | None = None, env: dict | None = None):
        self.command = [command] + (args or [])
        self.env = os.environ.copy()
        if env:
            self.env.update(env)

        self._id_counter = itertools.count(1)
        self._initialized = False
        self._write_lock = Lock()  # Thread safety for stdin writes
        self._responses = {}  # Dict of {req_id: response} for parallel requests
        self._responses_lock = Lock()

        self.proc = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=self.env,
        )
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        """Read responses from stdout and store them by request ID."""
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                response = json.loads(line)
                if "id" in response:
                    with self._responses_lock:
                        self._responses[response["id"]] = response
            except json.JSONDecodeError:
                pass  # Ignore non-JSON lines (like debug output)

    def _initialize(self):
        """Send initialize then notifications/initialized (MCP spec)."""
        if self._initialized:
            return
        self._rpc(
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {"roots": {"listChanged": True}, "sampling": {}},
                "clientInfo": {"name": "linux-mcp-chatbot", "version": "1.0.0"},
            },
        )
        # Thread-safe write for notification
        with self._write_lock:
            self.proc.stdin.write(
                json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
            )
            self.proc.stdin.flush()
        self._initialized = True

    def _rpc(self, method: str, params: dict):
        req_id = next(self._id_counter)
        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }
        # Thread-safe write to stdin
        with self._write_lock:
            self.proc.stdin.write(json.dumps(request) + "\n")
            self.proc.stdin.flush()

        # Wait for response (poll the dict)
        import time
        timeout = 120
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self._responses_lock:
                if req_id in self._responses:
                    response = self._responses.pop(req_id)
                    if "error" in response:
                        raise MCPClientError(response["error"])
                    return response.get("result")
            time.sleep(0.01)  # Poll every 10ms

        raise MCPClientError("Timeout waiting for MCP response")

    def list_tools(self) -> list:
        """Return list of tools (each with name, description, etc.)."""
        self._initialize()
        try:
            result = self._rpc(method="tools/list", params={})
        except MCPClientError as e:
            if "method" in str(e).lower() or "not found" in str(e).lower():
                result = self._rpc(method="listTools", params={})
            else:
                raise
        if not result:
            return []
        tools = result.get("tools") if isinstance(result, dict) else result
        return tools if isinstance(tools, list) else []

    def call_tool(self, name: str, arguments: dict) -> str:
        """Call tool by name with arguments. Returns combined text from result content."""
        self._initialize()
        try:
            result = self._rpc(
                method="tools/call",
                params={"name": name, "arguments": arguments or {}},
            )
        except MCPClientError as e:
            if "method" in str(e).lower() or "not found" in str(e).lower():
                result = self._rpc(
                    method="callTool",
                    params={"tool": name, "args": arguments or {}},
                )
            else:
                raise
        if not result:
            return ""
        if isinstance(result, dict):
            content = result.get("content") or []
            texts = [
                c.get("text", "")
                for c in content
                if isinstance(c, dict) and c.get("type") == "text"
            ]
            return "\n".join(texts) if texts else str(result)
        return str(result)

    def close(self):
        try:
            self.proc.terminate()
        except Exception:
            pass
