from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from .config import JWT_ALGORITHM, JWT_EXPIRATION_MINUTES, get_jwt_secret
from .store import get_user_password_hash


def create_jwt_token(username: str) -> str:
    jwt_secret = get_jwt_secret()
    expiration = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    payload = {"sub": username, "exp": expiration}
    return jwt.encode(payload, jwt_secret, algorithm=JWT_ALGORITHM)


def verify_password(password: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), stored_hash.encode())


def authenticate_user(username: str, password: str) -> bool:
    stored_hash = get_user_password_hash(username)
    if not stored_hash:
        return False
    return verify_password(password, stored_hash)


def decode_access_token(token: str) -> dict:
    jwt_secret = get_jwt_secret()
    return jwt.decode(token, jwt_secret, algorithms=[JWT_ALGORITHM])


__all__ = [
    "create_jwt_token",
    "verify_password",
    "authenticate_user",
    "decode_access_token",
    "JWTError",
]