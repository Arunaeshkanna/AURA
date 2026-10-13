from aura.schemas.models import AgentRole, AgentTrace, Source


class FactVerifier:
    role = AgentRole.verifier

    def verify(self, answer: str, sources: list[Source]) -> tuple[float, AgentTrace]:
        if not sources:
            confidence = 0.25
        else:
            answer_terms = set(answer.lower().split())
            source_terms = set(" ".join(source.content for source in sources).lower().split())
            overlap = len(answer_terms & source_terms) / max(1, len(answer_terms))
            confidence = min(0.95, 0.45 + overlap)
        output = f"Evidence support confidence: {confidence:.2f}"
        return confidence, AgentTrace(agent=self.role, input=answer[:500], output=output, confidence=confidence)

    def verify_citations(self, sources: list[Source]) -> tuple[float, str]:
        if not sources:
            return 0.0, "No citations available to verify."
        verified = 0
        for source in sources:
            if len(source.content.split()) >= 12 and not source.content.lower().startswith(("pdf extraction failed", "word extraction failed")):
                verified += 1
        score = verified / max(1, len(sources))
        return score, f"Citation verification: {verified}/{len(sources)} sources contain extractable supporting text."
