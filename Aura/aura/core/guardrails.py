from dataclasses import dataclass


INJECTION_PATTERNS = [
    "ignore previous instructions",
    "developer message",
    "system prompt",
    "reveal your prompt",
    "bypass",
    "jailbreak",
]


@dataclass
class GuardrailResult:
    allowed: bool
    reasons: list[str]
    sanitized: str


class Guardrails:
    def check_input(self, text: str) -> GuardrailResult:
        lowered = text.lower()
        reasons = [p for p in INJECTION_PATTERNS if p in lowered]
        sanitized = text.strip()
        return GuardrailResult(allowed=not reasons, reasons=reasons, sanitized=sanitized)

    def clean_retrieved_text(self, text: str) -> str:
        lines = []
        for line in text.splitlines():
            lowered = line.lower()
            if any(pattern in lowered for pattern in INJECTION_PATTERNS):
                continue
            lines.append(line)
        return "\n".join(lines).strip()

    def check_output(self, answer: str, citations_count: int) -> GuardrailResult:
        reasons = []
        if "according to sources" in answer.lower() and citations_count == 0:
            reasons.append("answer claims sourced evidence but has no citations")
        return GuardrailResult(allowed=not reasons, reasons=reasons, sanitized=answer.strip())
