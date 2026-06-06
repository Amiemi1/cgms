from aiogram import F
from aiogram.types import Message

from app.db.session import SessionLocal
from app.db.models.memory import Memory

from app.services.security.admin_manager import add_admin, remove_admin, is_admin
from app.services.security.memory_access_control import grant_access, revoke_access


def register_security_handlers(dp):

    # ------------------------------------------------
    # ADD ADMIN
    # ------------------------------------------------
    @dp.message(F.text.startswith("/admin add"))
    async def admin_add_handler(message: Message):

        session = SessionLocal()

        try:

            parts = message.text.split()

            if len(parts) < 3:
                await message.answer("Usage: /admin add <telegram_id>")
                return

            target_user_id = int(parts[2])

            if not is_admin(session, message.from_user.id):
                await message.answer("Only admins can assign admin roles.")
                return

            success = add_admin(session, target_user_id)

            if success:
                await message.answer(
                    f"Admin privileges granted to {target_user_id}"
                )
            else:
                await message.answer(
                    "User is already an admin."
                )

        finally:
            session.close()


    # ------------------------------------------------
    # REMOVE ADMIN
    # ------------------------------------------------
    @dp.message(F.text.startswith("/admin remove"))
    async def admin_remove_handler(message: Message):

        session = SessionLocal()

        try:

            parts = message.text.split()

            if len(parts) < 3:
                await message.answer("Usage: /admin remove <telegram_id>")
                return

            target_user_id = int(parts[2])

            if not is_admin(session, message.from_user.id):
                await message.answer("Only admins can remove admin roles.")
                return

            success = remove_admin(session, target_user_id)

            if success:
                await message.answer(
                    f"Admin privileges removed from {target_user_id}"
                )
            else:
                await message.answer(
                    "User is not an admin."
                )

        finally:
            session.close()


    # ------------------------------------------------
    # LOCK MEMORY
    # ------------------------------------------------
    @dp.message(F.text.startswith("/lock"))
    async def lock_memory_handler(message: Message):

        session = SessionLocal()

        try:

            parts = message.text.split(" ")

            if len(parts) < 2:
                await message.answer("Usage: /lock <memory_id>")
                return

            memory_id = int(parts[1])

            memory = session.get(Memory, memory_id)

            if not memory:
                await message.answer("Memory not found.")
                return

            # -----------------------------------
            # LOCK PROTECTION
            # -----------------------------------

            if memory.is_locked:
                await message.answer("Memory is already locked.")
                return

            memory.is_locked = True

            session.add(memory)
            session.commit()

            await message.answer(f"Memory {memory_id} locked.")

        finally:
            session.close()

    # ------------------------------------------------
    # UNLOCK MEMORY
    # ------------------------------------------------
    @dp.message(F.text.startswith("/unlock"))
    async def unlock_memory_handler(message: Message):

        session = SessionLocal()

        try:

            parts = message.text.split(" ")

            if len(parts) < 2:
                await message.answer("Usage: /unlock <memory_id>")
                return

            memory_id = int(parts[1])

            memory = session.get(Memory, memory_id)

            if not memory:
                await message.answer("Memory not found.")
                return

            # -----------------------------------
            # LOCK CHECK
            # -----------------------------------

            if not memory.is_locked:
                await message.answer("Memory is not locked.")
                return

            memory.is_locked = False

            session.add(memory)
            session.commit()

            await message.answer(f"Memory {memory_id} unlocked.")

        finally:
            session.close()


    # ------------------------------------------------
    # GRANT MEMORY ACCESS
    # ------------------------------------------------
    @dp.message(F.text.startswith("/grant"))
    async def grant_memory_access_handler(message: Message):

        session = SessionLocal()

        try:

            parts = message.text.split()

            if len(parts) < 4:
                await message.answer(
                    "Usage: /grant <memory_id> <user_id> <permission>"
                )
                return

            memory_id = int(parts[1])
            user_id = int(parts[2])
            permission = parts[3]

            grant_access(
                session,
                memory_id,
                user_id,
                permission
            )

            await message.answer("Access granted.")

        finally:
            session.close()


    # ------------------------------------------------
    # REVOKE MEMORY ACCESS
    # ------------------------------------------------
    @dp.message(F.text.startswith("/revoke"))
    async def revoke_memory_access_handler(message: Message):

        session = SessionLocal()

        try:

            parts = message.text.split()

            if len(parts) < 3:
                await message.answer(
                    "Usage: /revoke <memory_id> <user_id>"
                )
                return

            memory_id = int(parts[1])
            user_id = int(parts[2])

            revoke_access(
                session,
                memory_id,
                user_id
            )

            await message.answer("Access revoked.")

        finally:
            session.close()