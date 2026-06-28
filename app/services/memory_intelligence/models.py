from pydantic import BaseModel
from typing import Dict


class MemoryScore(BaseModel):
    importance: int
    confidence: int
    freshness: int
    priority: int
    composite: int
    factors: Dict[str, int]