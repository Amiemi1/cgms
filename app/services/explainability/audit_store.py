from datetime import datetime


AUDIT_RECORDS = []


def store_audit_record(record: dict):

    enriched_record = {
        **record,
        "storedAt": datetime.utcnow().isoformat()
    }

    AUDIT_RECORDS.insert(
        0,
        enriched_record
    )

    # keep only latest 100 records
    del AUDIT_RECORDS[100:]

    print(
        "📜 AUDIT RECORD STORED",
        enriched_record
    )

    return enriched_record


def get_audit_records(limit: int = 50):

    return AUDIT_RECORDS[:limit]