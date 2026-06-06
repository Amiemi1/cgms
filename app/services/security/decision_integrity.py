import hashlib
from datetime import datetime


# ------------------------------------------------
# GENERATE DECISION HASH
# ------------------------------------------------

def generate_decision_hash(summary: str, created_at: datetime):

    data = f"{summary}|{created_at}"

    return hashlib.sha256(data.encode()).hexdigest()


# ------------------------------------------------
# VERIFY DECISION
# ------------------------------------------------

def verify_decision(summary, created_at, stored_hash):

    new_hash = generate_decision_hash(summary, created_at)

    return new_hash == stored_hash