from aura.memory.store import MemoryStore
from aura.schemas.models import AgentRole, AgentTrace


class MemoryAgent:
    role = AgentRole.memory

    def __init__(self) -> None:
        self.store = MemoryStore()

    def recall(self) -> tuple[str, AgentTrace]:
        memories = self.store.recall()
        text = "\n".join(f"- {item['kind']}: {item['content']}" for item in memories)
        return text, AgentTrace(agent=self.role, input="recall", output=f"Recalled {len(memories)} memories.", confidence=0.7)

    def remember_interaction(self, query: str, answer: str) -> AgentTrace:
        semantic = self._extract_semantic_memory(query)
        if semantic:
            self.store.remember("semantic", semantic, {"source": "user_query"})
        self.store.remember("episodic", f"Q: {query}\nA: {answer[:500]}")
        output = "Stored episodic memory."
        if semantic:
            output += " Learned semantic preference/fact."
        return AgentTrace(agent=self.role, input=query, output=output, confidence=0.82 if semantic else 0.75)

    def _extract_semantic_memory(self, query: str) -> str | None:
        lowered = query.lower()
        triggers = ["remember that", "remember my", "my preference", "i prefer", "always answer", "call me"]
        if not any(trigger in lowered for trigger in triggers):
            return None
        cleaned = query.strip()
        for trigger in triggers:
            index = lowered.find(trigger)
            if index >= 0:
                cleaned = query[index:].strip()
                break
        return cleaned[:500]
