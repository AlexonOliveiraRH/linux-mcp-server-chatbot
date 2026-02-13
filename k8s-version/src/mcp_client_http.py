"""
MCP client for Linux MCP Server (HTTP transport - streamable-http).
Connects to MCP server running with LINUX_MCP_TRANSPORT=streamable-http
See: https://rhel-lightspeed.github.io/linux-mcp-server/
"""
import json
import os
import requests
import itertools
from threading import Lock
from typing import Any, Dict, List, Optional


class MCPClientError(Exception):
    """Raised when the MCP server returns an error or times out."""
    pass


class LinuxMCPClientHTTP:
    """Client for the Linux MCP Server over HTTP (streamable-http transport)."""

    def __init__(self, base_url: str, timeout: int = 120):
        """
        Initialize HTTP MCP client.

        Args:
            base_url: Full URL of MCP server endpoint (e.g., http://linux-mcp-server:8000/mcp)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self._id_counter = itertools.count(1)
        self._initialized = False
        self._session = requests.Session()
        self._write_lock = Lock()

    def _initialize(self):
        """Send initialize request (MCP spec)."""
        if self._initialized:
            return

        response = self._rpc(
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {"roots": {"listChanged": True}, "sampling": {}},
                "clientInfo": {"name": "linux-mcp-chatbot", "version": "1.0.0"},
            },
        )
        self._initialized = True
        return response

    def _parse_sse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Server-Sent Events (SSE) response.

        SSE format:
        data: {"jsonrpc":"2.0","id":1,"result":{...}}

        Args:
            response_text: Raw SSE response text

        Returns:
            Parsed JSON data
        """
        # Parse SSE - look for lines starting with "data: "
        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith('data: '):
                json_str = line[6:]  # Remove "data: " prefix
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue

        # If no SSE format found, try parsing as direct JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            raise MCPClientError(f"Invalid response format: {e}")

    def _rpc(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send JSON-RPC request to MCP server via HTTP.

        Args:
            method: RPC method name
            params: Method parameters

        Returns:
            Response data

        Raises:
            MCPClientError: On error or timeout
        """
        req_id = next(self._id_counter)
        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }

        try:
            # Send POST request to MCP endpoint
            # streamable-http transport uses SSE (Server-Sent Events)
            with self._write_lock:
                response = self._session.post(
                    self.base_url,
                    json=request,
                    timeout=self.timeout,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream",
                    },
                    stream=True,  # Enable streaming for SSE
                )

            response.raise_for_status()

            # Read the complete response
            response_text = response.text

            # Parse SSE response
            data = self._parse_sse_response(response_text)

            if "error" in data:
                raise MCPClientError(f"MCP error: {data['error']}")

            return data.get("result", {})

        except requests.exceptions.Timeout:
            raise MCPClientError(f"Request timed out after {self.timeout}s")
        except requests.exceptions.RequestException as e:
            raise MCPClientError(f"HTTP error: {e}")
        except MCPClientError:
            raise
        except Exception as e:
            raise MCPClientError(f"Unexpected error: {e}")

    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        self._initialize()
        result = self._rpc(method="tools/list", params={})
        return result.get("tools", [])

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the MCP server.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result
        """
        self._initialize()
        result = self._rpc(
            method="tools/call",
            params={"name": name, "arguments": arguments},
        )

        # Extract content from MCP response
        content = result.get("content", [])
        if not content:
            return None

        # Return first text content
        for item in content:
            if item.get("type") == "text":
                return item.get("text", "")

        return str(content)

    def close(self):
        """Close the HTTP session."""
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
