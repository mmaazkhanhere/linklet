import pytest
from httpx import AsyncClient

from backend.app.models.link import Link


async def register_and_login(client: AsyncClient, email: str = "creator@example.com") -> str:
    payload = {"name": "Creator", "email_address": email, "password": "Password123!"}
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post(
        "/api/v1/auth/token",
        json={"email_address": email, "password": "Password123!"},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_tc_create_01_and_02_valid_http_and_https(async_client: AsyncClient):
    token = await register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    response = await async_client.post(
        "/api/v1/links", json={"destination_url": "http://example.com/path"}, headers=headers
    )
    assert response.status_code == 201
    body = response.json()
    assert body["destination_url"] == "http://example.com/path"
    assert len(body["short_code"]) == 7
    assert body["total_clicks"] == 0
    assert "link_id" in body and "created_on" in body

    https_response = await async_client.post(
        "/api/v1/links", json={"destination_url": "https://example.com"}, headers=headers
    )
    assert https_response.status_code == 201


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ["ftp://example.com", "not_a_url", "javascript:alert(1)", "http:///missing-host", "https://example.com/" + "a" * 2040])
async def test_tc_create_03_and_04_reject_invalid_urls(async_client: AsyncClient, url: str):
    token = await register_and_login(async_client, "invalid-url@example.com")
    response = await async_client.post(
        "/api/v1/links",
        json={"destination_url": url},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_DESTINATION_URL"


@pytest.mark.asyncio
async def test_tc_create_05_requires_authentication(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/links", json={"destination_url": "https://example.com"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_tc_create_06_retries_database_collision(async_client: AsyncClient, db, monkeypatch):
    token = await register_and_login(async_client, "collision@example.com")
    from backend.app.repositories.user_repository import UserRepository

    user = await UserRepository().get_by_email(db, "collision@example.com")
    db.add(Link(user_id=user.id, destination_url="https://existing.example", short_code="aaaaaaa"))
    await db.commit()

    candidates = iter(["aaaaaaa", "bbbbbbb"])
    monkeypatch.setattr("backend.app.services.link_service.generate_short_code", lambda: next(candidates))
    response = await async_client.post(
        "/api/v1/links",
        json={"destination_url": "https://new.example"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["short_code"] == "bbbbbbb"


@pytest.mark.asyncio
async def test_tc_create_07_replays_idempotent_creation(async_client: AsyncClient):
    token = await register_and_login(async_client, "idempotent@example.com")
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "create-key-1"}
    payload = {"destination_url": "https://example.com/idempotent"}

    first = await async_client.post("/api/v1/links", json=payload, headers=headers)
    second = await async_client.post("/api/v1/links", json=payload, headers=headers)
    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()

    mismatch = await async_client.post(
        "/api/v1/links", json={"destination_url": "https://example.com/other"}, headers=headers
    )
    assert mismatch.status_code == 400
    assert mismatch.json()["error"]["code"] == "IDEMPOTENCY_KEY_MISUSE"
