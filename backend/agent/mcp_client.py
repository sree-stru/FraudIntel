"""MCP Client for connecting to the MongoDB MCP Server.

Routes all FraudIntel database operations through the official MongoDB
MCP Server, satisfying the hackathon Partner track requirement for
meaningful MCP integration.
"""

import asyncio
import logging
from typing import Any, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import CallToolResult, Tool
from agent.config import settings

logger = logging.getLogger(__name__)


class FraudIntelMCPClient:
    """A client to communicate with the FraudIntel MongoDB MCP server."""

    def __init__(self):
        logger.info("Initializing MongoDB MCP Server client...")

        # Use the official MongoDB MCP server as required by the hackathon
        mongodb_uri = settings.mongodb_uri
        self.server_params = StdioServerParameters(
            command="npx",
            args=[
                "-y", "mongodb-mcp-server",
                "--connectionString", mongodb_uri,
            ],
        )
        self._client_ctx = None
        self._session: Optional[ClientSession] = None
        self._tools: dict[str, Tool] = {}
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    async def connect(self):
        """Establish the stdio connection and initialize the session."""
        logger.info("Starting MCP Client → connecting to MongoDB MCP Server...")
        self._client_ctx = stdio_client(self.server_params)
        read, write = await self._client_ctx.__aenter__()

        self._session = ClientSession(read, write)
        await self._session.__aenter__()

        await self._session.initialize()
        self.loop = asyncio.get_running_loop()

        # Discover and cache available tools
        tools = await self.get_tools()
        self._tools = {t.name: t for t in tools}
        logger.info(
            "✅ MCP Client connected. Available tools: %s",
            sorted(self._tools.keys()),
        )

    async def disconnect(self):
        """Close the session and connection."""
        if self._session:
            await self._session.__aexit__(None, None, None)
            self._session = None
        if self._client_ctx:
            await self._client_ctx.__aexit__(None, None, None)
            self._client_ctx = None
        self._tools = {}
        logger.info("MCP Client disconnected.")

    async def get_tools(self) -> List[Tool]:
        """Retrieve the list of available tools from the MCP server."""
        if not self._session:
            raise RuntimeError("Not connected to MCP server.")

        response = await self._session.list_tools()
        return response.tools

    @property
    def is_connected(self) -> bool:
        """Check if the MCP client is connected and ready."""
        return self._session is not None

    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Call a specific tool on the MCP server.

        Args:
            name: MCP tool name (e.g. ``"find"``, ``"aggregate"``).
            arguments: Tool-specific arguments dict.

        Returns:
            The text content of the first result item, or ``None``.

        Raises:
            RuntimeError: If not connected or the tool returns an error.
        """
        if not self._session:
            raise RuntimeError("Not connected to MCP server.")

        logger.info("MCP → %s(%s)", name,
                     str(arguments)[:200])
        result: CallToolResult = await self._session.call_tool(
            name, arguments,
        )

        if result.isError:
            error_msg = str(result.content)
            logger.error("MCP tool %s error: %s", name, error_msg)
            raise RuntimeError(f"MCP tool error: {error_msg}")

        # Extract content from the result
        if not result.content:
            return None

        return result.content[0].text


# Singleton instance to be managed by FastAPI lifecycle
mcp_client = FraudIntelMCPClient()
