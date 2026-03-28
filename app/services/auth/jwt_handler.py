from datetime import datetime, timedelta
import jwt

SECRET_KEY = "cgms_secret_key"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 24


def create_access_token(data: dict):

    payload = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)

    payload.update({"exp": expire})

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return token