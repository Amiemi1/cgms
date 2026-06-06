from sqlmodel import Session, select
from app.db.models.memory import Memory
from app.services.security.decision_integrity import generate_decision_hash


def verify_decision_record(session: Session, decision_text: str):

    statement = select(Memory).where(
        Memory.summary == decision_text,
        Memory.memory_type == "decision"
    )

    memory = session.exec(statement).first()

    if not memory:
        return "Decision not found."

    if not memory.decision_hash:
        return "Decision has no integrity record."

    computed_hash = generate_decision_hash(
        memory.summary,
        memory.created_at
    )

    if computed_hash == memory.decision_hash:
        return f"""
Decision verified ✓

Decision: {memory.summary}
Created: {memory.created_at}
Integrity: VALID
"""
    else:
        return f"""
⚠ Decision integrity failure

Decision: {memory.summary}
Stored hash mismatch.
Possible tampering detected.
"""