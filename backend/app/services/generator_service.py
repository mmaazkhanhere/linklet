import secrets
import string

BASE62_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase


def generate_short_code(length: int = 7) -> str:
    return "".join(secrets.choice(BASE62_ALPHABET) for _ in range(length))
