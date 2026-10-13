from aura.schemas.models import AgentRole, AgentTrace, Source


class CriticAgent:
    role = AgentRole.critic

    def reflect(self, answer: str, sources: list[Source], confidence: float) -> tuple[bool, AgentTrace]:
        issues = []
        if confidence < 0.62:
            issues.append("low evidence confidence")
        if len(answer.split()) < 30:
            issues.append("answer may be too thin")
        if not sources:
            issues.append("missing citations")
        passed = not issues
        output = "PASS" if passed else f"FAIL: {', '.join(issues)}"
        return passed, AgentTrace(agent=self.role, input=answer[:500], output=output, confidence=confidence)
