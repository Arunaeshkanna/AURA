import json
from datetime import datetime
from pathlib import Path
from statistics import mean

from aura.core.config import get_settings
from aura.schemas.models import QueryRequest, QueryResponse


class MetricsStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.path = Path(settings.metrics_dir) / "runs.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, request: QueryRequest, response: QueryResponse, model: str | None = None) -> None:
        words = response.answer.split()
        context_tokens = int(response.context_stats.get("estimated_output_tokens", 0))
        output_tokens = int(len(words) / 0.75) if words else 0
        total_tokens = context_tokens + output_tokens
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": request.query[:240],
            "intent": response.intent.value,
            "source_scope": request.source_scope,
            "confidence": response.confidence,
            "latency_ms": response.latency_ms,
            "iterations": response.iterations,
            "citations": len(response.citations),
            "context_tokens_est": context_tokens,
            "output_tokens_est": output_tokens,
            "total_tokens_est": total_tokens,
            "cost_estimate_usd": response.cost_estimate_usd,
            "model": model or self._model_from_trace(response),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

    def list_runs(self, limit: int = 100) -> list[dict]:
        if not self.path.exists():
            return []
        rows = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return rows[-limit:]

    def summary(self) -> dict:
        rows = self.list_runs(1000)
        if not rows:
            return {
                "runs": 0,
                "avg_latency_ms": 0,
                "avg_confidence": 0,
                "total_tokens_est": 0,
                "total_cost_estimate_usd": 0.0,
                "avg_iterations": 0,
                "citation_rate": 0,
            }
        return {
            "runs": len(rows),
            "avg_latency_ms": round(mean(row["latency_ms"] for row in rows), 2),
            "avg_confidence": round(mean(row["confidence"] for row in rows), 3),
            "total_tokens_est": sum(row["total_tokens_est"] for row in rows),
            "total_cost_estimate_usd": round(sum(row["cost_estimate_usd"] for row in rows), 6),
            "avg_iterations": round(mean(row["iterations"] for row in rows), 2),
            "citation_rate": round(mean(1 if row["citations"] else 0 for row in rows), 3),
        }

    def _model_from_trace(self, response: QueryResponse) -> str:
        for trace in response.traces:
            if trace.agent.value == "writer" and trace.output.startswith("Used "):
                return trace.output.replace("Used ", "", 1)
        return "unknown"
