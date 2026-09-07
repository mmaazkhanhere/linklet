from datetime import datetime, timedelta, timezone

import pytest
import jwt
from httpx import AsyncClient

from backend.app.config import settings
from backend.app.core.security import create_access_token


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_tc_auth_01_successful_registration(async_client: AsyncClient):
    payload = {
        "name": "Jane Doe",
        "email_address": "jane@example.com",
        "password": "SecurePassword123!",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "Jane Doe"
    assert data["email_address"] == "jane@example.com"
    assert "hashed_password" not in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_tc_auth_02_duplicate_email(async_client: AsyncClient):
    payload = {
        "name": "Jane Doe",
        "email_address": "duplicate@example.com",
        "password": "SecurePassword123!",
    }
    res1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Attempt registration with existing email
    res2 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    err = res2.json()["error"]
    assert err["code"] == "EMAIL_ALREADY_EXISTS"
    assert "already registered" in err["message"].lower()


@pytest.mark.asyncio
async def test_tc_auth_03_invalid_email_and_short_password(async_client: AsyncClient):
    # Invalid email syntax
    res1 = await async_client.post(
        "/api/v1/auth/register",
        json={"name": "Bad User", "email_address": "not-an-email", "password": "SecurePassword123!"},
    )
    assert res1.status_code == 422
    assert res1.json()["error"]["code"] == "VALIDATION_ERROR"

    # Password less than 8 chars
    res2 = await async_client.post(
        "/api/v1/auth/register",
        json={"name": "Short Pass", "email_address": "shortpass@example.com", "password": "short"},
    )
    assert res2.status_code == 422
    assert res2.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_registration_normalizes_name_and_email(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "name": "  Jane Doe  ",
            "email_address": "  JANE@EXAMPLE.COM  ",
            "password": "SecurePassword123!",
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Jane Doe"
    assert response.json()["email_address"] == "jane@example.com"

    login = await async_client.post(
        "/api/v1/auth/token",
        json={"email_address": "JANE@EXAMPLE.COM", "password": "SecurePassword123!"},
    )
    assert login.status_code == 200


@pytest.mark.asyncio
async def test_registration_rejects_empty_or_overlong_name(async_client: AsyncClient):
    empty_name = await async_client.post(
        "/api/v1/auth/register",
        json={"name": "", "email_address": "empty@example.com", "password": "Password123!"},
    )
    assert empty_name.status_code == 422

    overlong_name = await async_client.post(
        "/api/v1/auth/register",
        json={"name": "x" * 101, "email_address": "long@example.com", "password": "Password123!"},
    )
    assert overlong_name.status_code == 422


@pytest.mark.asyncio
async def test_tc_auth_04_successful_login(async_client: AsyncClient):
    # Register user first
    await async_client.post(
        "/api/v1/auth/register",
        json={"name": "John Doe", "email_address": "john@example.com", "password": "Password123!"},
    )

    # 1. Login using JSON payload
    json_login_res = await async_client.post(
        "/api/v1/auth/token",
        json={"email_address": "john@example.com", "password": "Password123!"},
    )
    assert json_login_res.status_code == 200
    token_data = json_login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["expires_in"] == 86400

    # 2. Login using Form Data (OAuth2PasswordRequestForm compatibility)
    form_login_res = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "john@example.com", "password": "Password123!"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert form_login_res.status_code == 200
    form_token_data = form_login_res.json()
    assert "access_token" in form_token_data
    assert form_token_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_tc_auth_05_wrong_password_login(async_client: AsyncClient):
    # Register user
    await async_client.post(
        "/api/v1/auth/register",
        json={"name": "Alice Smith", "email_address": "alice@example.com", "password": "CorrectPassword123!"},
    )

    # Login with wrong password
    res = await async_client.post(
        "/api/v1/auth/token",
        json={"email_address": "alice@example.com", "password": "WrongPassword123!"},
    )
    assert res.status_code == 401
    err = res.json()["error"]
    assert err["code"] == "INVALID_CREDENTIALS"
    assert "Invalid email address or password" in err["message"]


@pytest.mark.asyncio
async def test_login_rejects_unknown_user_and_malformed_payload(async_client: AsyncClient):
    unknown_user = await async_client.post(
        "/api/v1/auth/token",
        json={"email_address": "unknown@example.com", "password": "Password123!"},
    )
    assert unknown_user.status_code == 401
    assert unknown_user.json()["error"]["code"] == "INVALID_CREDENTIALS"

    missing_password = await async_client.post(
        "/api/v1/auth/token",
        json={"email_address": "unknown@example.com"},
    )
    assert missing_password.status_code == 422
    assert missing_password.json()["error"]["code"] == "VALIDATION_ERROR"

    missing_form_fields = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "unknown@example.com"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert missing_form_fields.status_code == 401
    assert missing_form_fields.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_tc_auth_06_expired_or_invalid_token_access(async_client: AsyncClient):
    # Access without token
    res1 = await async_client.get("/api/v1/auth/me")
    assert res1.status_code == 401
    assert res1.json()["error"]["code"] == "INVALID_TOKEN"

    # Access with invalid garbage token
    res2 = await async_client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_garbage_token"})
    assert res2.status_code == 401
    assert res2.json()["error"]["code"] == "INVALID_TOKEN"

    expired_token = create_access_token("expired-user", expires_delta=timedelta(seconds=-1))
    res3 = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert res3.status_code == 401
    assert res3.json()["error"]["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_auth_rejects_tampered_missing_subject_and_unknown_user_tokens(async_client: AsyncClient):
    registered = await async_client.post(
        "/api/v1/auth/register",
        json={"name": "Token User", "email_address": "token@example.com", "password": "Password123!"},
    )
    user_id = registered.json()["id"]
    valid_token = create_access_token(user_id)

    tampered_token = f"{valid_token[:-1]}{'a' if valid_token[-1] != 'a' else 'b'}"
    tampered = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered_token}"}
    )
    assert tampered.status_code == 401
    assert tampered.json()["error"]["code"] == "INVALID_TOKEN"

    missing_subject = jwt.encode(
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    no_subject = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {missing_subject}"}
    )
    assert no_subject.status_code == 401
    assert no_subject.json()["error"]["code"] == "INVALID_TOKEN"

    unknown_user_token = create_access_token("does-not-exist")
    unknown_user = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {unknown_user_token}"}
    )
    assert unknown_user.status_code == 401
    assert unknown_user.json()["error"]["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_tc_auth_07_valid_token_access(async_client: AsyncClient):
    # Register user
    await async_client.post(
        "/api/v1/auth/register",
        json={"name": "Bob Builder", "email_address": "bob@example.com", "password": "CanWeFixIt123!"},
    )

    # Get token
    login_res = await async_client.post(
        "/api/v1/auth/token",
        json={"email_address": "bob@example.com", "password": "CanWeFixIt123!"},
    )
    access_token = login_res.json()["access_token"]

    # Request /auth/me with valid Bearer token
    me_res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["name"] == "Bob Builder"
    assert user_data["email_address"] == "bob@example.com"
    assert "id" in user_data


@pytest.mark.asyncio
async def test_protected_links_require_bearer_auth(async_client: AsyncClient):
    response = await async_client.get("/api/v1/links")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"
