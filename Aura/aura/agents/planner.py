from aura.schemas.models import AgentRole, AgentTrace, Intent


class PlannerAgent:
    role = AgentRole.planner

    def plan(self, query: str, intent: Intent) -> tuple[list[str], AgentTrace]:
        tasks = ["understand user goal", "retrieve relevant evidence", "verify support", "write cited answer"]
        if intent == Intent.research:
            tasks.insert(1, "search external sources if enabled")
        if intent == Intent.data:
            tasks.insert(1, "inspect structured data files")
        if intent == Intent.memory:
            tasks.insert(1, "recall and update memory")
        output = " -> ".join(tasks)
        return tasks, AgentTrace(agent=self.role, input=query, output=output, confidence=0.86)
