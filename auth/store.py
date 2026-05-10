import json
from pathlib import Path


USERS_FILE = Path(__file__).with_name("users.json")


def load_users() -> dict[str, str]:
    with USERS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("auth/users.json must contain a JSON object of username to password hash mappings")

    return data


def get_user_password_hash(username: str) -> str | None:
    users = load_users()
    return users.get(username)