from aura.core.graph import AuraGraph
from aura.rag.ingest import Ingestor
from aura.schemas.models import QueryRequest


def test_graph_returns_answer_with_local_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("AURA_VECTOR_DIR", str(tmp_path / "vector"))
    monkeypatch.setenv("AURA_MEMORY_DIR", str(tmp_path / "memory"))
    Ingestor().ingest_text(
        "Test architecture",
        "AURA has a planner, RAG retrieval, fact verifier, critic, memory, and writer.",
        "test",
        {"collection": "documents"},
    )
    response = AuraGraph().run(QueryRequest(query="Explain AURA architecture", remember=False))
    assert response.answer
    assert response.intent.value in {"general", "rag", "research"}
    assert response.latency_ms >= 0
