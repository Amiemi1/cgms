# =====================================================
# EMBEDDING SERVICE
# =====================================================

from sentence_transformers import SentenceTransformer

# Load once globally (fast reuse)
model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_embedding(text: str):
    """
    Generate a 384-dimension embedding vector
    for semantic search.
    """

    vector = model.encode(text)

    return vector.tolist()