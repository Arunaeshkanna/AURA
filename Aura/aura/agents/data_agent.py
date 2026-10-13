from aura.core.config import get_settings
from aura.schemas.models import AgentRole, AgentTrace, Source
from aura.tools.data_tools import DataTool


class DataAgent:
    role = AgentRole.data

    def __init__(self) -> None:
        self.settings = get_settings()
        self.tool = DataTool()

    def run(self, query: str) -> tuple[list[Source], AgentTrace]:
        summary = self.tool.summarize_csvs(self.settings.docs_dir)
        source = Source(title="Structured data summary", source_type="data", content=summary, metadata={"collection": "data"})
        return [source], AgentTrace(agent=self.role, input=query, output=summary, confidence=0.75)
