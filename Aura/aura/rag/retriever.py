from aura.core.guardrails import Guardrails
from aura.rag.store import HybridStore
from aura.schemas.models import Source


class QueryRewriter:
    def rewrite(self, query: str) -> list[str]:
        base = query.strip()
        variants = [base]
        if "compare" in base.lower():
            variants.append(base.replace("compare", "differences between"))
        variants.append(f"evidence for {base}")
        return list(dict.fromkeys(variants))


class ContextBudgeter:
    def optimize(
        self,
        sources: list[Source],
        token_budget: int = 16_000,
        preserve_weak: bool = False,
    ) -> tuple[list[Source], dict]:
        seen_fingerprints: set[str] = set()
        kept: list[Source] = []
        duplicates = 0
        weak = 0
        for source in sorted(sources, key=lambda item: item.score, reverse=True):
            fingerprint = " ".join(source.content.lower().split()[:80])
            if fingerprint in seen_fingerprints:
                duplicates += 1
                continue
            seen_fingerprints.add(fingerprint)
            if not preserve_weak and source.score < 0.015 and len(sources) > 4:
                weak += 1
                continue
            kept.append(source)

        safe_budget = min(token_budget, 6_000)
        max_sources = max(3, min(10, safe_budget // 900))
        selected = kept[:max_sources]
        stats = {
            "available_tokens": token_budget,
            "input_sources": len(sources),
            "kept_sources": len(selected),
            "duplicates_removed": duplicates,
            "weak_removed": weak,
            "estimated_output_tokens": min(safe_budget, sum(len(source.content.split()) * 2 for source in selected)),
        }
        return selected, stats

    def compress(self, sources: list[Source], token_budget: int = 16_000, preserve_weak: bool = False) -> str:
        optimized, _ = self.optimize(sources, token_budget, preserve_weak=preserve_weak)
        safe_budget = min(token_budget, 6_000)
        budget_words = max(120, int(safe_budget * 0.42))
        blocks = []
        used = 0
        per_source_limit = max(90, min(260, budget_words // max(1, len(optimized))))
        for idx, source in enumerate(optimized, start=1):
            words = source.content.split()
            remaining = budget_words - used
            if remaining <= 0:
                break
            snippet = " ".join(words[: min(len(words), remaining, per_source_limit)])
            used += len(snippet.split())
            blocks.append(f"[Source {idx}: {source.title}] {snippet}")
        return "\n\n".join(blocks)


class HybridRetriever:
    def __init__(self) -> None:
        self.store = HybridStore()
        self.rewriter = QueryRewriter()
        self.guardrails = Guardrails()
        self.budgeter = ContextBudgeter()

    def retrieve(self, query: str, k: int = 8, filters: dict | None = None) -> list[Source]:
        merged: dict[str, Source] = {}
        for variant in self.rewriter.rewrite(query):
            for source in self.store.search(variant, k=k, filters=filters):
                source.content = self.guardrails.clean_retrieved_text(source.content)
                if source.id not in merged or source.score > merged[source.id].score:
                    merged[source.id] = source
        return sorted(merged.values(), key=lambda source: source.score, reverse=True)[:k]
