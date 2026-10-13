from typing import Any

from aura.rag.ingest import Ingestor
from aura.rag.store import HybridStore
from aura.tools.web_tools import WebSearchTool


class MCPToolRegistry:
    def __init__(self) -> None:
        self.store = HybridStore()
        self.ingestor = Ingestor()
        self.web = WebSearchTool()

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "web.search",
                "description": "Search the web and return research snippets.",
                "input_schema": {"query": "str", "k": "int"},
            },
            {
                "name": "knowledge.stats",
                "description": "Return indexed knowledge-base statistics.",
                "input_schema": {},
            },
            {
                "name": "knowledge.ingest_url",
                "description": "Fetch a URL and add it to the knowledge base.",
                "input_schema": {"url": "str", "title": "str | None"},
            },
            {
                "name": "knowledge.clear_uploaded",
                "description": "Clear uploaded document and URL chunks.",
                "input_schema": {},
            },
        ]

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        args = arguments or {}
        if name == "web.search":
            results = self.web.search(str(args.get("query", "")), int(args.get("k", 5)))
            return {"results": [source.model_dump() for source in results]}
        if name == "knowledge.stats":
            return self.store.stats()
        if name == "knowledge.ingest_url":
            count = self.ingestor.ingest_url(str(args["url"]), args.get("title"))
            return {"ingested_chunks": count, "url": args["url"]}
        if name == "knowledge.clear_uploaded":
            return {"removed_chunks": self.store.clear_uploaded()}
        raise ValueError(f"Unknown MCP tool: {name}")
