import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60


def validate_auth_config() -> None:
    if not os.getenv("JWT_SECRET"):
        raise RuntimeError("JWT_SECRET environment variable is required for authentication")


def get_jwt_secret() -> str:
    validate_auth_config()
    return os.getenv("JWT_SECRET")


__all__ = [
    "JWT_ALGORITHM",
    "JWT_EXPIRATION_MINUTES",
    "validate_auth_config",
    "get_jwt_secret",
]