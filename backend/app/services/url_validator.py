from urllib.parse import urlsplit


def validate_destination_url(value: str) -> str:
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError("invalid destination URL")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
    except ValueError as exc:
        raise ValueError("invalid destination URL") from exc
    if parsed.scheme.lower() not in {"http", "https"} or not hostname:
        raise ValueError("invalid destination URL")
    return value
