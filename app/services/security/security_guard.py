from app.services.security.access_control import can_create_memory
from app.services.security.security_logger import log_security_event


def enforce_memory_creation_security(session, chat_id):

    allowed = can_create_memory(session, chat_id)

    if not allowed:

        log_security_event(
            session,
            chat_id,
            "unauthorized_memory_creation",
            "User attempted to create memory without permission"
        )

        return False

    return True