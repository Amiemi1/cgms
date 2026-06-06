# ==============================================================
# ADMIN GUARD DECORATOR
# ==============================================================

from functools import wraps
from app.db.session import SessionLocal
from app.services.security.role_service import is_admin


def admin_only(handler):

    @wraps(handler)
    async def wrapper(message, *args, **kwargs):

        session = SessionLocal()

        try:

            user_id = message.from_user.id

            print(f"[DEBUG] Governance | Admin check | user={user_id}")

            if not is_admin(session, user_id):

                print(f"[DEBUG] Governance | Access denied | user={user_id}")

                await message.answer("Admin privileges required.")
                return

            return await handler(message, *args, **kwargs)

        finally:
            session.close()

    return wrapper