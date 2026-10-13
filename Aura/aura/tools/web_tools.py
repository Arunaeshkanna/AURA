from aura.schemas.models import Source


class WebSearchTool:
    def search(self, query: str, k: int = 5) -> list[Source]:
        try:
            from duckduckgo_search import DDGS

            results = []
            with DDGS() as ddgs:
                for item in ddgs.text(query, max_results=k):
                    body = item.get("body") or ""
                    results.append(
                        Source(
                            title=item.get("title") or "Web result",
                            url=item.get("href"),
                            source_type="web",
                            content=body,
                            metadata={"collection": "web", "query": query},
                            score=0.5,
                        )
                    )
            return results
        except Exception:
            return []
