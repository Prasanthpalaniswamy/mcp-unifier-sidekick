import argparse
import getpass
import json
from pathlib import Path

import bcrypt


USERS_FILE = Path(__file__).with_name("users.json")


def generate_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def load_users() -> dict[str, str]:
    if not USERS_FILE.exists():
        return {}

    with USERS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("auth/users.json must contain a JSON object of username to password hash mappings")

    return data


def save_users(users: dict[str, str]) -> None:
    with USERS_FILE.open("w", encoding="utf-8") as file:
        json.dump(users, file, indent=2)
        file.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a bcrypt password hash for a user")
    parser.add_argument("username", help="Username to create or update")
    parser.add_argument("--password", help="Plain text password. If omitted, you will be prompted securely")
    parser.add_argument("--print-only", action="store_true", help="Only print the generated hash without updating auth/users.json")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Enter password: ")
    confirm_password = getpass.getpass("Confirm password: ") if not args.password else args.password

    if password != confirm_password:
        raise ValueError("Passwords do not match")

    password_hash = generate_password_hash(password)

    if args.print_only:
        print(password_hash)
        return

    users = load_users()
    users[args.username] = password_hash
    save_users(users)

    print(f"Updated {USERS_FILE} with bcrypt hash for user '{args.username}'")
    print(f"Hash: {password_hash}")


if __name__ == "__main__":
    main()