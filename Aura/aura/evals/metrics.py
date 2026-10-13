from aura.schemas.models import EvalResult, QueryResponse


def citation_coverage(response: QueryResponse) -> float:
    return 1.0 if response.citations else 0.0


def faithfulness_proxy(response: QueryResponse) -> float:
    if not response.citations:
        return 0.2
    answer_terms = set(response.answer.lower().split())
    citation_terms = set(" ".join(c.snippet for c in response.citations).lower().split())
    return min(1.0, len(answer_terms & citation_terms) / max(1, len(answer_terms)) + 0.25)


def answer_relevance(query: str, response: QueryResponse) -> float:
    query_terms = set(query.lower().split())
    answer_terms = set(response.answer.lower().split())
    return min(1.0, len(query_terms & answer_terms) / max(1, len(query_terms)) + 0.35)


def evaluate_response(query: str, response: QueryResponse) -> EvalResult:
    return EvalResult(
        retrieval_recall=1.0 if response.citations else 0.0,
        citation_coverage=citation_coverage(response),
        faithfulness_proxy=faithfulness_proxy(response),
        answer_relevance=answer_relevance(query, response),
        latency_ms=response.latency_ms,
        iterations=response.iterations,
    )
