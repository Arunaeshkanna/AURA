import json
from datetime import datetime
from pathlib import Path

from aura.core.config import get_settings


class MemoryStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.path = Path(self.settings.memory_dir) / "memory.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def remember(self, kind: str, content: str, metadata: dict | None = None) -> None:
        record = {
            "kind": kind,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

    def recall(self, limit: int = 10) -> list[dict]:
        if not self.path.exists():
            return []
        rows = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return rows[-limit:]
