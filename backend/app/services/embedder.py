import functools

from fastembed import TextEmbedding

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@functools.lru_cache
def get_model() -> TextEmbedding:
    return TextEmbedding(MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    return [vector.tolist() for vector in get_model().embed(texts)]
