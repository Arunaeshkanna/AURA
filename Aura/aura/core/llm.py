from dataclasses import dataclass

from aura.core.config import get_settings
from aura.core.router_training import FineTunedRouter
from aura.schemas.models import Intent


@dataclass
class LLMResponse:
    text: str
    model: str
    cost_estimate_usd: float = 0.0


class ModelRouter:
    def __init__(self) -> None:
        self.fine_tuned_router = FineTunedRouter()

    def classify(self, query: str) -> Intent:
        q = query.lower()
        if any(term in q for term in ["csv", "table", "dataframe", "plot", "metric", "dataset"]):
            return Intent.data
        if any(term in q for term in ["remember", "preference", "memory"]):
            return Intent.memory
        if any(term in q for term in ["architecture", "workflow", "pipeline", "uploaded", "document", "knowledge base", "rag"]):
            return Intent.rag
        trained_intent = self.fine_tuned_router.predict(query)
        if trained_intent is not None:
            return trained_intent
        if any(term in q for term in ["research", "latest", "sources", "cite", "compare"]):
            return Intent.research
        if any(term in q for term in ["code", "bug", "function", "api", "python"]):
            return Intent.coding
        return Intent.general

    def select_model(self, intent: Intent, complexity: int) -> str:
        settings = get_settings()
        if complexity > 55:
            return settings.fast_model
        if intent in {Intent.research, Intent.coding} or complexity > 12:
            return settings.powerful_model
        if intent in {Intent.data, Intent.rag, Intent.memory}:
            return settings.fast_model
        return settings.small_model


class LLMGateway:
    def __init__(self) -> None:
        self.router = ModelRouter()
        self.settings = get_settings()

    def complete(self, prompt: str, intent: Intent = Intent.general) -> LLMResponse:
        prompt = self._fit_prompt(prompt, self.settings.max_prompt_tokens)
        complexity = len(prompt.split()) // 80
        model = self.router.select_model(intent, complexity)
        if self.settings.groq_api_key:
            try:
                from groq import Groq

                client = Groq(api_key=self.settings.groq_api_key)
                result = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                )
                return LLMResponse(text=result.choices[0].message.content or "", model=model)
            except Exception as exc:  # pragma: no cover - network/provider fallback
                if self._is_token_limit_error(exc):
                    smaller_prompt = self._fit_prompt(prompt, max(1800, self.settings.max_prompt_tokens // 2))
                    try:
                        result = client.chat.completions.create(
                            model=self.settings.fast_model,
                            messages=[{"role": "user", "content": smaller_prompt}],
                            temperature=0.2,
                        )
                        return LLMResponse(text=result.choices[0].message.content or "", model=f"{self.settings.fast_model}-retry")
                    except Exception as retry_exc:
                        return LLMResponse(text=self._local_response(smaller_prompt, retry_exc), model="groq-fallback")
                return LLMResponse(text=self._local_response(prompt, exc), model="groq-fallback")
        return LLMResponse(text=self._local_response(prompt), model="local-deterministic")

    def _fit_prompt(self, prompt: str, max_tokens: int) -> str:
        max_words = max(400, int(max_tokens * 0.62))
        words = prompt.split()
        if len(words) <= max_words:
            return prompt
        head = words[:220]
        tail_budget = max_words - len(head) - 28
        tail = words[-tail_budget:] if tail_budget > 0 else []
        return " ".join(
            head
            + [
                "\n\n[Context compressed by AURA because the model token limit would be exceeded. "
                "Some middle evidence was removed; rely on the included citations and evidence.]\n\n"
            ]
            + tail
        )

    def _is_token_limit_error(self, exc: Exception) -> bool:
        text = str(exc).lower()
        return any(term in text for term in ["request too large", "tokens per minute", "rate_limit_exceeded", "tpm"])

    def _local_response(self, prompt: str, exc: Exception | None = None) -> str:
        prefix = "Local fallback response"
        if exc:
            if self._is_token_limit_error(exc):
                prefix += " after Groq token-limit response"
            else:
                prefix += " after provider error"
        lines = [line.strip() for line in prompt.splitlines() if line.strip()]
        evidence = [line for line in lines if line.startswith("[Source")]
        if evidence:
            joined = " ".join(evidence[:4])
            return f"{prefix}. Based on the available evidence, the strongest answer is: {joined[:900]}"
        return f"{prefix}. I decomposed the request and produced a concise answer from available local context."
