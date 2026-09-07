import asyncio

import pytest
from backend.app.models.link import Link
from httpx import AsyncClient


async def create_link(client: AsyncClient, db, email: str = "redirect@example.com") -> Link:
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Redirect User", "email_address": email, "password": "Password123!"},
    )
    token_response = await client.post(
        "/api/v1/auth/token",
        json={"email_address": email, "password": "Password123!"},
    )
    response = await client.post(
        "/api/v1/links",
        json={"destination_url": "https://example.com/redirect-target"},
        headers={"Authorization": f"Bearer {token_response.json()['access_token']}"},
    )
    assert response.status_code == 201
    link_id = response.json()["link_id"]
    return await db.get(Link, link_id)


@pytest.mark.asyncio
async def test_redirect_resolves_publicly_and_increments_clicks(async_client: AsyncClient, db):
    link = await create_link(async_client, db)

    response = await async_client.get(f"/{link.short_code}", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == link.destination_url
    await db.refresh(link)
    assert link.total_clicks == 1


@pytest.mark.asyncio
async def test_redirect_returns_standard_not_found_error(async_client: AsyncClient):
    response = await async_client.get("/nonexistent", follow_redirects=False)

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "LINK_NOT_FOUND",
            "message": "The requested short link does not exist or has been removed.",
            "details": None,
        }
    }


@pytest.mark.asyncio
async def test_health_route_is_not_captured_by_redirect(async_client: AsyncClient):
    response = await async_client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path, expected_status",
    [("/docs", 200), ("/redoc", 200), ("/openapi.json", 200), ("/api/v1/links", 401)],
)
async def test_reserved_routes_are_not_captured_by_redirect(
    async_client: AsyncClient, path: str, expected_status: int
):
    response = await async_client.get(path, follow_redirects=False)
    assert response.status_code == expected_status


@pytest.mark.asyncio
async def test_malformed_short_code_does_not_resolve(async_client: AsyncClient):
    response = await async_client.get("/too-short", follow_redirects=False)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_concurrent_redirects_do_not_lose_clicks(async_client: AsyncClient, db):
    link = await create_link(async_client, db, "concurrent-redirect@example.com")

    responses = await asyncio.gather(
        *(
            async_client.get(f"/{link.short_code}", follow_redirects=False)
            for _ in range(20)
        )
    )

    assert all(response.status_code == 307 for response in responses)
    await db.refresh(link)
    assert link.total_clicks == 20
