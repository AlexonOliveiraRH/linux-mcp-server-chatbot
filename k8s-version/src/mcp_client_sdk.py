"""
MCP client using official Python SDK for streamable-http transport.
Connects to MCP server running with LINUX_MCP_TRANSPORT=streamable-http
"""
import asyncio
import threading
from typing import Any, Dict, List, Optional
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


class MCPClientError(Exception):
    """Raised when the MCP server returns an error or times out."""
    pass


class LinuxMCPClientSDK:
    """Client for Linux MCP Server using official SDK with persistent session."""

    def __init__(self, base_url: str, timeout: int = 120):
        """
        Initialize MCP client with official SDK.

        Args:
            base_url: Full URL of MCP server (e.g., http://linux-mcp-server:8000/mcp)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._session: Optional[ClientSession] = None
        self._read = None
        self._write = None
        self._lock = threading.Lock()
        self._initialize()

    def _initialize(self):
        """Initialize async event loop in separate thread."""
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()

        # Wait for loop to be ready
        while self._loop is None:
            pass

    async def _connect(self):
        """Connect to MCP server."""
        transport = streamable_http_client(self.base_url)
        self._read, self._write = await transport.__aenter__()
        self._session = ClientSession(self._read, self._write)
        await self._session.__aenter__()
        await self._session.initialize()

    def _run_async(self, coro):
        """Run async coroutine in the event loop thread."""
        if self._loop is None:
            raise MCPClientError("Event loop not initialized")

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        try:
            return future.result(timeout=self.timeout)
        except Exception as e:
            raise MCPClientError(f"Async operation failed: {e}")

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from MCP server.

        Returns:
            List of tool definitions
        """
        async def _list_tools():
            with self._lock:
                if self._session is None:
                    await self._connect()

                response = await self._session.list_tools()
                return [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema,
                    }
                    for tool in response.tools
                ]

        try:
            return self._run_async(_list_tools())
        except Exception as e:
            raise MCPClientError(f"Failed to list tools: {e}")

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the MCP server.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result
        """
        async def _call_tool():
            with self._lock:
                if self._session is None:
                    await self._connect()

                response = await self._session.call_tool(name, arguments)

                # Extract text content
                for content in response.content:
                    if hasattr(content, 'text'):
                        return content.text

                return str(response.content)

        try:
            return self._run_async(_call_tool())
        except Exception as e:
            raise MCPClientError(f"Failed to call tool {name}: {e}")

    def close(self):
        """Close the client session."""
        async def _close():
            if self._session:
                await self._session.__aexit__(None, None, None)
            if self._read and self._write:
                # Close transport
                pass

        if self._loop and self._session:
            self._run_async(_close())
            self._session = None

        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
            if self._thread:
                self._thread.join(timeout=5)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
