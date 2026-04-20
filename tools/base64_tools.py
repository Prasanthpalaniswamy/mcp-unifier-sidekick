import base64
import binascii

def encode_credentials(login: str, password: str) -> str:
    credentials = f"{login}:{password}"
    return base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

def decode_credentials(encoded_data: str) -> dict:
    try:
        decoded_bytes = base64.b64decode(encoded_data, validate=True)
        decoded_string = decoded_bytes.decode("utf-8")
    except (binascii.Error, UnicodeDecodeError) as exc:
        raise ValueError(
            "Invalid Base64 input. Please provide a valid Base64-encoded 'login:password' string."
        ) from exc

    if ":" not in decoded_string:
        raise ValueError(
            "Invalid credential format. Decoded value must contain 'login:password'."
        )

    login, password = decoded_string.split(":", 1)

    return {
        "result": {
            "login": login,
            "password": password
        }
    }