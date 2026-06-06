from fastapi import APIRouter
from pydantic import BaseModel

from app.services.memory.memory_pipeline import process_message


router = APIRouter(prefix="/ingest", tags=["Ingest"])


class MessagePayload(BaseModel):
    channel: str
    user_id: str
    text: str


@router.post("/message")
def ingest_message(payload: MessagePayload):

    result = process_message(
        channel=payload.channel,
        user_id=payload.user_id,
        text=payload.text
    )

    return {
        "status": "processed",
        "result": result
    }