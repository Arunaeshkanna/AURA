from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from aura.core.config import get_settings
from aura.schemas.models import Source


class HybridStore:
    """ChromaDB-backed store with a JSONL compatibility mirror."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.path = Path(self.settings.vector_dir) / "sources.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._collection = self._connect_chroma()

    def _connect_chroma(self):
        if not self.settings.use_chroma:
            return None
        try:
            import chromadb

            if self.settings.chroma_host:
                client = chromadb.HttpClient(host=self.settings.chroma_host, port=self.settings.chroma_port)
            else:
                client = chromadb.PersistentClient(path=str(self.settings.vector_dir / "chroma"))
            return client.get_or_create_collection(name="aura_sources")
        except Exception:
            return None

    def add(self, sources: list[Source]) -> int:
        with self.path.open("a", encoding="utf-8") as handle:
            for source in sources:
                handle.write(source.model_dump_json() + "\n")
        if self._collection is not None and sources:
            try:
                self._collection.upsert(
                    ids=[source.id for source in sources],
                    documents=[source.content for source in sources],
                    metadatas=[self._clean_metadata(source) for source in sources],
                )
            except Exception:
                pass
        return len(sources)

    def all_sources(self) -> list[Source]:
        if not self.path.exists():
            return []
        sources = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    sources.append(Source.model_validate_json(line))
        return sources

    def search(self, query: str, k: int = 8, filters: dict | None = None) -> list[Source]:
        if self._collection is not None:
            results = self._search_chroma(query, k, filters)
            if results:
                return results
        return self._search_jsonl(query, k, filters)

    def _search_chroma(self, query: str, k: int, filters: dict | None) -> list[Source]:
        try:
            raw = self._collection.query(query_texts=[query], n_results=k, where=self._chroma_where(filters))
            ids = raw.get("ids", [[]])[0]
            docs = raw.get("documents", [[]])[0]
            metadatas = raw.get("metadatas", [[]])[0]
            distances = raw.get("distances", [[]])[0] if raw.get("distances") else [0.0 for _ in ids]
            sources = []
            for source_id, content, metadata, distance in zip(ids, docs, metadatas, distances):
                score = max(0.0, 1.0 - float(distance))
                sources.append(
                    Source(
                        id=source_id,
                        title=str(metadata.get("title", "Chroma source")),
                        url=metadata.get("url") or None,
                        source_type=str(metadata.get("source_type", "chroma")),
                        content=content,
                        metadata={key: value for key, value in metadata.items() if key not in {"title", "url", "source_type"}},
                        score=score,
                    )
                )
            return sources
        except Exception:
            return []

    def _search_jsonl(self, query: str, k: int, filters: dict | None) -> list[Source]:
        sources = self.all_sources()
        if filters:
            sources = self._filter_sources(sources, filters)
        if not sources:
            return []
        corpus = [source.content for source in sources]
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(corpus + [query])
        scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
        ranked = sorted(zip(sources, scores), key=lambda item: item[1], reverse=True)[:k]
        results = []
        for source, score in ranked:
            source.score = float(score)
            results.append(source)
        return results

    def stats(self) -> dict:
        sources = self.all_sources()
        collections: dict[str, int] = {}
        uploaded_documents = 0
        uploaded_links = 0
        for source in sources:
            collection = source.metadata.get("collection", source.source_type)
            collections[collection] = collections.get(collection, 0) + 1
            if source.metadata.get("uploaded_kind") == "document":
                uploaded_documents += 1
            if source.metadata.get("uploaded_kind") == "url":
                uploaded_links += 1
        return {
            "documents": len(sources),
            "collections": collections,
            "uploaded_documents": uploaded_documents,
            "uploaded_links": uploaded_links,
            "chroma_enabled": self._collection is not None,
        }

    def clear_uploaded(self) -> int:
        sources = self.all_sources()
        removed_sources = [source for source in sources if source.metadata.get("uploaded_kind") in {"document", "url"}]
        kept = [source for source in sources if source.metadata.get("uploaded_kind") not in {"document", "url"}]
        removed = len(removed_sources)
        with self.path.open("w", encoding="utf-8") as handle:
            for source in kept:
                handle.write(source.model_dump_json() + "\n")
        if self._collection is not None and removed_sources:
            try:
                self._collection.delete(ids=[source.id for source in removed_sources])
            except Exception:
                pass
        return removed

    def _filter_sources(self, sources: list[Source], filters: dict) -> list[Source]:
        filtered = []
        for source in sources:
            keep = True
            for key, value in filters.items():
                actual = str(source.metadata.get(key, "")).lower()
                if isinstance(value, (list, tuple, set)):
                    expected = {str(item).lower() for item in value}
                    keep = actual in expected
                else:
                    keep = actual == str(value).lower()
                if not keep:
                    break
            if keep:
                filtered.append(source)
        return filtered

    def _chroma_where(self, filters: dict | None) -> dict | None:
        if not filters:
            return None
        clauses = []
        for key, value in filters.items():
            if isinstance(value, (list, tuple, set)):
                clauses.append({key: {"$in": list(value)}})
            else:
                clauses.append({key: str(value)})
        return clauses[0] if len(clauses) == 1 else {"$and": clauses}

    def _clean_metadata(self, source: Source) -> dict:
        metadata = {
            **source.metadata,
            "title": source.title,
            "url": source.url or "",
            "source_type": source.source_type,
        }
        return {
            key: str(value) if value is not None else ""
            for key, value in metadata.items()
            if isinstance(value, (str, int, float, bool)) or value is None
        }
