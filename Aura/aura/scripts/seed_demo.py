from pathlib import Path

from aura.core.config import get_settings
from aura.rag.ingest import Ingestor


DEMO_DOCS = {
    "agentic_rag.md": """# Agentic RAG
Agentic RAG improves basic retrieval augmented generation by adding planning,
query rewriting, multi-query retrieval, reranking, context compression,
verification, and iterative reflection. A useful system can retrieve again when
the verifier or critic finds weak evidence.
""",
    "aura_architecture.md": """# AURA Architecture
AURA routes user queries through guardrails, a model router, planner agent,
research agent, RAG agent, data agent, A2A communication, fact verification,
reflection, report writing, and citation generation.
""",
    "sample_metrics.csv": """run,latency_ms,cost_usd,confidence
1,820,0.012,0.81
2,950,0.014,0.86
3,760,0.011,0.78
""",
}


def main() -> None:
    settings = get_settings()
    settings.docs_dir.mkdir(parents=True, exist_ok=True)
    for name, content in DEMO_DOCS.items():
        (Path(settings.docs_dir) / name).write_text(content, encoding="utf-8")
    count = Ingestor().ingest_directory()
    print(f"Seeded demo documents and ingested {count} chunks.")


if __name__ == "__main__":
    main()
