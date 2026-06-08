from functools import lru_cache
from typing import List


@lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(
        "all-MiniLM-L6-v2"
    )


def generate_embedding(text: str) -> List[float]:
    if not text:
        return []

    model = get_embedding_model()

    embedding = model.encode(
        text
    )

    return embedding.tolist()