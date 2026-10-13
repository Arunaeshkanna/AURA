from aura.tools.mcp_registry import MCPToolRegistry

registry = MCPToolRegistry()

try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover - only used when mcp sdk is absent
    FastMCP = None


if FastMCP is None:  # pragma: no cover
    raise RuntimeError("Install the official MCP Python SDK with `pip install mcp`.")


mcp = FastMCP("AURA MCP Server")


@mcp.tool()
def web_search(query: str, k: int = 5) -> dict:
    """Search the web and return research snippets."""
    return registry.call_tool("web.search", {"query": query, "k": k})


@mcp.tool()
def knowledge_stats() -> dict:
    """Return indexed knowledge-base statistics."""
    return registry.call_tool("knowledge.stats", {})


@mcp.tool()
def knowledge_ingest_url(url: str, title: str | None = None) -> dict:
    """Fetch a URL and add it to the AURA knowledge base."""
    return registry.call_tool("knowledge.ingest_url", {"url": url, "title": title})


@mcp.tool()
def knowledge_clear_uploaded() -> dict:
    """Clear uploaded document and URL chunks."""
    return registry.call_tool("knowledge.clear_uploaded", {})


if __name__ == "__main__":
    mcp.run()
