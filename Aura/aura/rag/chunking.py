from aura.schemas.models import Source


def chunk_text(title: str, text: str, source: str, metadata: dict, chunk_size: int = 900, overlap: int = 120) -> list[Source]:
    words = text.split()
    chunks: list[Source] = []
    start = 0
    index = 0
    while start < len(words):
        end = min(len(words), start + chunk_size)
        content = " ".join(words[start:end])
        chunks.append(
            Source(
                title=f"{title} chunk {index + 1}",
                url=metadata.get("url"),
                source_type=source,
                content=content,
                metadata={**metadata, "chunk": index, "document": title},
            )
        )
        if end == len(words):
            break
        start = max(0, end - overlap)
        index += 1
    return chunks
