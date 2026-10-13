from aura.core.graph import AuraGraph
from aura.evals.metrics import evaluate_response
from aura.rag.ingest import Ingestor
from aura.schemas.models import QueryRequest


def main() -> None:
    ingestor = Ingestor()
    ingestor.ingest_text(
        "AURA architecture",
        (
            "AURA uses a planner, hybrid retrieval, specialist agents, fact verification, "
            "reflection, memory, and a writer. The retrieval system combines keyword search, "
            "metadata, context compression, and citation generation."
        ),
        "eval",
        {"collection": "research"},
    )
    graph = AuraGraph()
    query = "Explain the AURA agent architecture with citations"
    response = graph.run(QueryRequest(query=query, source_scope="web", use_web=False, remember=False))
    result = evaluate_response(query, response)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
