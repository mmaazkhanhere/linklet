import pytest
from backend.app.models.link import Link
from httpx import AsyncClient


async def register_and_login(client: AsyncClient, email: str) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Link User", "email_address": email, "password": "Password123!"},
    )
    response = await client.post(
        "/api/v1/auth/token",
        json={"email_address": email, "password": "Password123!"},
    )
    return response.json()["access_token"]


async def create_link(client: AsyncClient, email: str, destination: str = "https://example.com/original"):
    token = await register_and_login(client, email)
    response = await client.post(
        "/api/v1/links",
        json={"destination_url": destination},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return token, response.json()


@pytest.mark.asyncio
async def test_list_links_returns_only_owned_links_and_raw_array(async_client: AsyncClient):
    token, first = await create_link(async_client, "list-owner@example.com")
    await async_client.post(
        "/api/v1/links",
        json={"destination_url": "https://example.com/second"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await create_link(async_client, "list-other@example.com")

    response = await async_client.get(
        "/api/v1/links", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2
    assert all(item["link_id"] != first["link_id"] or item["destination_url"] == first["destination_url"] for item in response.json())


@pytest.mark.asyncio
async def test_list_links_empty_returns_empty_array(async_client: AsyncClient):
    token = await register_and_login(async_client, "list-empty@example.com")
    response = await async_client.get(
        "/api/v1/links", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["get", "put", "delete"])
async def test_management_endpoints_require_authentication(async_client: AsyncClient, method: str):
    path = "/api/v1/links" if method == "get" else "/api/v1/links/not-a-real-link"
    response = await getattr(async_client, method)(path)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_regenerate_preserves_link_state_and_invalidates_old_code(async_client: AsyncClient, db):
    token, original = await create_link(async_client, "regenerate@example.com")
    link = await db.get(Link, original["link_id"])
    link.total_clicks = 7
    await db.commit()
    old_code = original["short_code"]

    response = await async_client.put(
        f"/api/v1/links/{original['link_id']}",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "regen-1"},
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["link_id"] == original["link_id"]
    assert updated["short_code"] != old_code
    assert updated["destination_url"] == original["destination_url"]
    assert updated["created_on"].rstrip("Z") == original["created_on"].rstrip("Z")
    assert updated["total_clicks"] == 7

    old_response = await async_client.get(f"/{old_code}", follow_redirects=False)
    new_response = await async_client.get(f"/{updated['short_code']}", follow_redirects=False)
    assert old_response.status_code == 404
    assert new_response.status_code == 307
    assert new_response.headers["location"] == original["destination_url"]


@pytest.mark.asyncio
async def test_regenerate_replays_idempotent_result(async_client: AsyncClient):
    token, link = await create_link(async_client, "regen-replay@example.com")
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "regen-replay-1"}
    first = await async_client.put(f"/api/v1/links/{link['link_id']}", headers=headers)
    second = await async_client.put(f"/api/v1/links/{link['link_id']}", headers=headers)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()


@pytest.mark.asyncio
async def test_regenerate_and_delete_hide_other_users_links(async_client: AsyncClient):
    owner_token, link = await create_link(async_client, "owner@example.com")
    other_token = await register_and_login(async_client, "other@example.com")
    headers = {"Authorization": f"Bearer {other_token}"}

    regenerate = await async_client.put(f"/api/v1/links/{link['link_id']}", headers=headers)
    delete = await async_client.delete(f"/api/v1/links/{link['link_id']}", headers=headers)
    assert regenerate.status_code == delete.status_code == 404

    listed = await async_client.get(
        "/api/v1/links", headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert listed.json()[0]["short_code"] == link["short_code"]


@pytest.mark.asyncio
async def test_delete_removes_link_and_replays_idempotent_result(async_client: AsyncClient):
    token, link = await create_link(async_client, "delete@example.com")
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "delete-1"}

    first = await async_client.delete(f"/api/v1/links/{link['link_id']}", headers=headers)
    second = await async_client.delete(f"/api/v1/links/{link['link_id']}", headers=headers)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json() == {"message": "Link successfully deleted."}

    redirect = await async_client.get(f"/{link['short_code']}", follow_redirects=False)
    assert redirect.status_code == 404


@pytest.mark.asyncio
async def test_mutation_idempotency_key_rejects_different_link(async_client: AsyncClient):
    token, first = await create_link(async_client, "idempotency-links@example.com")
    _, second = await create_link(async_client, "idempotency-second@example.com")
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "same-key"}
    first_response = await async_client.put(f"/api/v1/links/{first['link_id']}", headers=headers)
    mismatch = await async_client.put(f"/api/v1/links/{second['link_id']}", headers=headers)
    assert first_response.status_code == 200
    assert mismatch.status_code == 400
    assert mismatch.json()["error"]["code"] == "IDEMPOTENCY_KEY_MISUSE"


@pytest.mark.asyncio
async def test_regenerate_retries_short_code_collision(async_client: AsyncClient, monkeypatch):
    token, first = await create_link(async_client, "regen-collision@example.com")
    _, occupied = await create_link(async_client, "regen-occupied@example.com")
    candidates = iter([occupied["short_code"], "fresh01"])
    monkeypatch.setattr(
        "backend.app.services.link_service.generate_short_code", lambda: next(candidates)
    )

    response = await async_client.put(
        f"/api/v1/links/{first['link_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["short_code"] == "fresh01"


@pytest.mark.asyncio
async def test_regenerate_fails_after_five_collisions_without_mutation(
    async_client: AsyncClient, monkeypatch
):
    token, first = await create_link(async_client, "regen-collision-fail@example.com")
    _, occupied = await create_link(async_client, "regen-occupied-fail@example.com")
    monkeypatch.setattr(
        "backend.app.services.link_service.generate_short_code",
        lambda: occupied["short_code"],
    )

    response = await async_client.put(
        f"/api/v1/links/{first['link_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 500
    listed = await async_client.get(
        "/api/v1/links", headers={"Authorization": f"Bearer {token}"}
    )
    assert listed.json()[0]["short_code"] == first["short_code"]
