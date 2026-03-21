from sentence_transformers import SentenceTransformer
from typing import List, Optional

# Load model once (important)
_model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate embedding vector for text.
    Returns None if text is empty.
    """
    if not text or not text.strip():
        return None

    vector = _model.encode(text)
    return vector.tolist()