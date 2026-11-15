def chunk_text(text: str, size: int = 300, overlap: int = 50) -> list[str]:
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("overlap must be between 0 and size - 1")

    words = text.split()
    step = size - overlap
    chunks = []

    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break

    return chunks
