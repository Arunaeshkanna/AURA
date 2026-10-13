from aura.schemas.models import AgentRole, AgentTrace, Source
from aura.tools.web_tools import WebSearchTool


class ResearchAgent:
    role = AgentRole.research

    def __init__(self) -> None:
        self.web = WebSearchTool()

    def run(self, query: str, use_web: bool) -> tuple[list[Source], AgentTrace]:
        sources = self.web.search(query) if use_web else []
        output = f"Found {len(sources)} external sources." if sources else "External web search skipped or unavailable."
        return sources, AgentTrace(agent=self.role, input=query, output=output, confidence=0.7 if sources else 0.35)
