from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    # 🔥 FIX: truncate to 72 bytes for bcrypt
    safe_password = password[:72]
    return pwd_context.hash(safe_password)


def verify_password(plain: str, hashed: str) -> bool:
    safe_password = plain[:72]
    return pwd_context.verify(safe_password, hashed)