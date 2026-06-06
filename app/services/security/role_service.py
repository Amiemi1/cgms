# ==============================================================
# ROLE SERVICE
# ==============================================================

from sqlalchemy import text
from app.services.security.audit_service import record_audit

VALID_ROLES = ["admin", "contributor", "reader"]


# --------------------------------------------------------------
# GET USER ROLE
# --------------------------------------------------------------

def get_user_role(session, user_id):

    result = session.execute(
        text("""
            SELECT role
            FROM user_role
            WHERE user_id = :user_id
        """),
        {"user_id": user_id}
    ).fetchone()

    if result:
        return result[0]

    return "reader"


# --------------------------------------------------------------
# ASSIGN ROLE
# --------------------------------------------------------------

def assign_role(session, user_id, role):

    # ----------------------------------------------------------
    # DEBUG
    # ----------------------------------------------------------
    print(f"[DEBUG] Governance | Attempt role assignment | user={user_id} role={role}")

    # ----------------------------------------------------------
    # ROLE VALIDATION
    # ----------------------------------------------------------
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role}")

    # ----------------------------------------------------------
    # PREVENT ADMIN SELF-DOWNGRADE
    # ----------------------------------------------------------
    current_role = get_user_role(session, user_id)

    if current_role == "admin" and role != "admin":
        raise ValueError("Admin cannot downgrade their own role.")

    # ----------------------------------------------------------
    # DATABASE UPDATE
    # ----------------------------------------------------------
    session.execute(
        text("""
            INSERT INTO user_role (user_id, role, created_at)
            VALUES (:user_id, :role, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET role = :role
        """),
        {
            "user_id": user_id,
            "role": role
        }
    )

    session.commit()

    record_audit(
        session,
        user_id,
        "role_change",
        f"Role updated to {role}"
    )

    print(f"[DEBUG] Governance | Role assigned | user={user_id} role={role}")

    print(f"[DEBUG] Governance | Role assigned | user={user_id} role={role}")
    print("[DEBUG] New role proctection logic active")


# --------------------------------------------------------------
# CHECK ADMIN
# --------------------------------------------------------------

def is_admin(session, user_id):

    role = get_user_role(session, user_id)

    return role == "admin"