import subprocess
from contextlib import AsyncExitStack
from typing import Any


class AuraMCPClient:
    """Small real MCP client helper for local stdio MCP servers."""

    def __init__(self, command: str = "python", args: list[str] | None = None) -> None:
        self.command = command
        self.args = args or ["-m", "aura.mcp_real_server"]

    async def list_tools(self) -> list[Any]:
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except Exception:
            return []

        server_params = StdioServerParameters(command=self.command, args=self.args)
        async with AsyncExitStack() as stack:
            read, write = await stack.enter_async_context(stdio_client(server_params))
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            result = await session.list_tools()
            return list(result.tools)

    def smoke_check(self) -> dict:
        return {
            "command": self.command,
            "args": self.args,
            "example": f"{self.command} {' '.join(self.args)}",
            "transport": "stdio",
        }
