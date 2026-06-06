from sentence_transformers import SentenceTransformer
from typing import List

# ------------------------------------------------
# LOAD EMBEDDING MODEL
# ------------------------------------------------

model = SentenceTransformer("all-MiniLM-L6-v2")


# ------------------------------------------------
# GENERATE EMBEDDING
# ------------------------------------------------

def generate_embedding(text: str) -> List[float]:

    if not text:
        return []

    vector = model.encode(text)

    return vector.tolist()