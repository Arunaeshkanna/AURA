from aura.rag.retriever import HybridRetriever
from aura.schemas.models import AgentRole, AgentTrace, Source


class RAGAgent:
    role = AgentRole.rag

    def __init__(self) -> None:
        self.retriever = HybridRetriever()

    def run(
        self,
        query: str,
        filters: dict | None = None,
        token_budget: int = 16_000,
        preserve_weak: bool = False,
    ) -> tuple[list[Source], str, AgentTrace, dict]:
        sources = self.retriever.retrieve(query, filters=filters)
        optimized, stats = self.retriever.budgeter.optimize(sources, token_budget, preserve_weak=preserve_weak)
        context = self.retriever.budgeter.compress(optimized, token_budget, preserve_weak=preserve_weak)
        output = (
            f"Retrieved {len(sources)} local chunks; kept {stats['kept_sources']} after context optimization."
        )
        return optimized, context, AgentTrace(agent=self.role, input=query, output=output, confidence=0.82 if optimized else 0.2), stats
