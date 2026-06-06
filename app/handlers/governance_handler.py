from aiogram import F
from aiogram.types import Message

from sqlmodel import select

from app.db.session import SessionLocal
from app.db.models.memory import Memory
from app.db.models.decision_lineage import DecisionLineage

from app.services.security.role_service import assign_role
from app.services.security.admin_guard import admin_only
from app.services.security.decision_integrity import verify_decision
from app.services.security.audit_service import get_recent_audit


def register_governance_handlers(dp):

    # ------------------------------------------------
    # ROLE ASSIGNMENT
    # ------------------------------------------------
    @dp.message(F.text.startswith("/role"))
    @admin_only
    async def role_handler(message: Message):

        session = SessionLocal()

        try:

            parts = message.text.split()

            if len(parts) != 3:
                await message.answer(
                    "Usage: /role <user_id> <admin|contributor|reader>"
                )
                return

            user_id = int(parts[1])
            role = parts[2]

            try:
                assign_role(session, user_id, role)
            except ValueError as e:
                await message.answer(str(e))
                return

            await message.answer(
                f"Role updated.\nUser: {user_id}\nRole: {role}"
            )

        finally:
            session.close()


    # ------------------------------------------------
    # GOVERNANCE AUDIT
    # ------------------------------------------------
    @dp.message(F.text.startswith("/audit"))
    @admin_only
    async def audit_handler(message: Message):

        session = SessionLocal()

        try:

            logs = get_recent_audit(session)

            if not logs:
                await message.answer("No audit records found.")
                return

            response = "Governance Audit Log\n\n"

            for log in logs:

                user_id, action, details, created_at = log

                response += (
                    f"User: {user_id}\n"
                    f"Action: {action}\n"
                    f"Details: {details}\n"
                    f"Time: {created_at}\n\n"
                )

            await message.answer(response)

        finally:
            session.close()


    # ------------------------------------------------
    # VERIFY DECISION
    # ------------------------------------------------
    @dp.message(F.text.startswith("/verify"))
    async def verify_decision_handler(message: Message):

        session = SessionLocal()

        try:

            parts = message.text.split(maxsplit=1)

            if len(parts) < 2:
                await message.answer("Usage: /verify <decision text>")
                return

            query = parts[1]

            decision = session.exec(
                select(Memory)
                .where(
                    Memory.memory_type == "decision",
                    Memory.summary.ilike(f"%{query}%")
                )
                .order_by(Memory.id.desc())
            ).first()

            if not decision:
                await message.answer("Decision not found.")
                return

            valid = verify_decision(
                decision.summary,
                decision.created_at,
                decision.decision_hash
            )

            if valid:
                response = (
                    "Decision verified.\n\n"
                    f"Decision: {decision.summary}\n"
                    f"Hash: {decision.decision_hash}\n"
                    "Integrity: VALID"
                )
            else:
                response = (
                    "WARNING: Decision integrity compromised.\n\n"
                    f"Decision: {decision.summary}"
                )

            await message.answer(response)

        finally:
            session.close()
# ------------------------------------------------
    # DECISION LINEAGE
    # ------------------------------------------------
    @dp.message(F.text.startswith("/lineage"))
    async def lineage_handler(message: Message):

        session = SessionLocal()

        try:

            parts = message.text.split(maxsplit=1)

            if len(parts) < 2:
                await message.answer("Usage: /lineage <decision text>")
                return

            query = parts[1]

            decision = session.exec(
                select(Memory)
                .where(
                    Memory.memory_type == "decision",
                    Memory.summary.ilike(f"%{query}%")
                )
                .order_by(Memory.id.desc())
            ).first()

            if not decision:
                await message.answer("No matching decision found.")
                return

            lineage = session.exec(
                select(DecisionLineage).where(
                    DecisionLineage.decision_id == decision.id
                )
            ).first()

            if not lineage:
                await message.answer("Decision found but no lineage recorded.")
                return

            response = (
                f"Decision Lineage\n\n"
                f"Decision: {decision.summary}\n"
                f"Reasoning Engine: {lineage.reasoning_engine}\n"
                f"Triggered by user: {lineage.triggered_by_user}\n"
                f"Created: {lineage.created_at}"
            )

            await message.answer(response)

        finally:
            session.close()