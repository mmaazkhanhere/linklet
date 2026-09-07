from datetime import timedelta
import pytest
import jwt
from backend.app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing_argon2():
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)
    
    assert hashed != password
    assert hashed.startswith("$argon2id$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_jwt_token_generation_and_decoding():
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = create_access_token(subject=user_id)
    
    assert isinstance(token, str)
    payload = decode_access_token(token)
    assert payload["sub"] == user_id
    assert "exp" in payload


def test_jwt_expired_token():
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = create_access_token(subject=user_id, expires_delta=timedelta(seconds=-10))
    
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(token)
