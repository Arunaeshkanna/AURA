from pathlib import Path

from aura.core.config import get_settings
from aura.schemas.models import Intent


TRAINING_EXAMPLES = [
    ("summarize this document", Intent.rag.value),
    ("answer from uploaded files", Intent.rag.value),
    ("what does the pdf say", Intent.rag.value),
    ("explain aura architecture", Intent.rag.value),
    ("describe the project workflow", Intent.rag.value),
    ("summarize the system pipeline", Intent.rag.value),
    ("search the latest AI news", Intent.research.value),
    ("research climate effects with sources", Intent.research.value),
    ("compare these current tools", Intent.research.value),
    ("analyze this csv", Intent.data.value),
    ("show dataframe trends", Intent.data.value),
    ("calculate metrics from excel", Intent.data.value),
    ("remember that I like short answers", Intent.memory.value),
    ("my preference is detailed reports", Intent.memory.value),
    ("what do you remember about me", Intent.memory.value),
    ("fix this python function", Intent.coding.value),
    ("debug this api code", Intent.coding.value),
    ("explain this error", Intent.coding.value),
    ("hello how are you", Intent.general.value),
    ("explain photosynthesis", Intent.general.value),
    ("what is el nino", Intent.general.value),
]


class FineTunedRouter:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_path = Path(self.settings.router_model_path)
        self._pipeline = None

    def train(self, examples: list[tuple[str, str]] | None = None) -> Path:
        from joblib import dump
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline

        rows = examples or TRAINING_EXAMPLES
        texts = [text for text, _ in rows]
        labels = [label for _, label in rows]
        pipeline = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), stop_words="english")),
                ("clf", LogisticRegression(max_iter=1000)),
            ]
        )
        pipeline.fit(texts, labels)
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        dump(pipeline, self.model_path)
        self._pipeline = pipeline
        return self.model_path

    def predict(self, query: str) -> Intent | None:
        pipeline = self._load()
        if pipeline is None:
            return None
        try:
            return Intent(str(pipeline.predict([query])[0]))
        except Exception:
            return None

    def _load(self):
        if self._pipeline is not None:
            return self._pipeline
        if not self.model_path.exists():
            return None
        try:
            from joblib import load

            self._pipeline = load(self.model_path)
            return self._pipeline
        except Exception:
            return None
