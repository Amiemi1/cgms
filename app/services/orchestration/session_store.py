from datetime import datetime


SESSION_LOG = []


def store_session_event(
    event_name: str,
    payload: dict
):

    SESSION_LOG.insert(
        0,
        {
            "event": event_name,
            "payload": payload,
            "time": datetime.utcnow().isoformat()
        }
    )

    del SESSION_LOG[300:]

    print(
        "🎞 SESSION EVENT STORED",
        event_name
    )


def get_session_history(
    limit: int = 100
):

    return SESSION_LOG[:limit]