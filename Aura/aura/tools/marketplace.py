from dataclasses import dataclass


@dataclass
class ToolCard:
    name: str
    category: str
    status: str
    description: str


class ToolMarketplace:
    def list_tools(self) -> list[ToolCard]:
        return [
            ToolCard("Web Search", "research", "enabled", "Searches the internet when document-only mode is off."),
            ToolCard("File Ingest", "knowledge", "enabled", "Indexes PDF, PowerPoint, Word, Excel, text, CSV, HTML, and JSON files."),
            ToolCard("URL Ingest", "knowledge", "enabled", "Adds webpages and links as a URL-only source."),
            ToolCard("Context Optimizer", "rag", "enabled", "Filters, reranks, deduplicates, and compresses evidence."),
            ToolCard("Citation Verifier", "safety", "enabled", "Checks whether citations contain extractable supporting text."),
            ToolCard("Prompt Injection Guard", "safety", "enabled", "Detects suspicious input and retrieved-document instructions."),
            ToolCard("GitHub MCP", "external", "available", "Placeholder for future GitHub MCP connection."),
            ToolCard("Arxiv MCP", "external", "available", "Placeholder for future Arxiv MCP connection."),
            ToolCard("Filesystem MCP", "external", "available", "Placeholder for future filesystem MCP connection."),
        ]
