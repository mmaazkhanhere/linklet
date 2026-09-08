import hashlib

from backend.app.services.idempotency_service import empty_request_hash, request_hash


def test_request_hash_is_canonical_and_sha256():
    payload = {"destination_url": "https://example.com", "nested": {"b": 2, "a": 1}}
    expected = hashlib.sha256(
        b'{"destination_url":"https://example.com","nested":{"a":1,"b":2}}'
    ).hexdigest()
    assert request_hash(payload) == expected
    assert request_hash({"nested": {"a": 1, "b": 2}, "destination_url": "https://example.com"}) == expected


def test_empty_request_hash_is_hash_of_empty_body():
    assert empty_request_hash() == hashlib.sha256(b"").hexdigest()
