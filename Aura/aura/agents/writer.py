from aura.core.llm import LLMGateway
from aura.schemas.models import AgentRole, AgentTrace, Citation, Intent, Source


class WriterAgent:
    role = AgentRole.writer

    def __init__(self) -> None:
        self.llm = LLMGateway()

    def write(self, query: str, intent: Intent, context: str, sources: list[Source]) -> tuple[str, list[Citation], AgentTrace]:
        prompt = (
            "Write a direct, evidence-grounded answer. Include practical next steps when useful.\n"
            f"Question: {query}\n\nEvidence:\n{context}"
        )
        result = self.llm.complete(prompt, intent)
        citations = [
            Citation(
                source_id=source.id,
                title=source.title,
                url=source.url,
                snippet=" ".join(source.content.split()[:32]),
            )
            for source in sources[:6]
        ]
        answer = result.text
        if citations:
            answer += "\n\nSources:\n" + "\n".join(
                f"- [{idx}] {citation.title}{f' - {citation.url}' if citation.url else ''}"
                for idx, citation in enumerate(citations, start=1)
            )
        return answer, citations, AgentTrace(agent=self.role, input=query, output=f"Used {result.model}", confidence=0.82)
