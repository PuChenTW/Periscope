"""Integration tests for user flow."""

import pytest


# Integration Tests
@pytest.mark.asyncio
async def test_full_user_flow(async_client, clear_async_db_cache):
    """Test complete user flow: register → login → use authenticated endpoints."""
    # Step 1: Register
    register_response = await async_client.post(
        "/auth/register",
        json={
            "email": "flowtest@example.com",
            "password": "flowpassword123",
            "timezone": "UTC",
        },
    )
    assert register_response.status_code == 201

    # Step 2: Login
    login_response = await async_client.post(
        "/auth/login",
        json={
            "email": "flowtest@example.com",
            "password": "flowpassword123",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Step 3: Get profile
    profile_response = await async_client.get("/users/me", headers=headers)
    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == "flowtest@example.com"

    # Step 4: Update timezone
    update_response = await async_client.put("/users/me", json={"timezone": "Europe/Paris"}, headers=headers)
    assert update_response.status_code == 200
    assert update_response.json()["timezone"] == "Europe/Paris"

    # Step 5: Get config (should exist from registration)
    config_response = await async_client.get("/users/config", headers=headers)
    assert config_response.status_code == 200
    config_data = config_response.json()
    assert config_data["delivery_time"] == "07:00:00"
    assert config_data["summary_style"] == "brief"

    # Step 6: Add a content source
    source_response = await async_client.post(
        "/users/sources",
        json={
            "source_type": "rss",
            "source_url": "https://example.com/feed.xml",
            "source_name": "Test Feed",
        },
        headers=headers,
    )
    assert source_response.status_code == 201
    source_id = source_response.json()["id"]

    # Step 7: Update interest profile
    interest_response = await async_client.put(
        "/users/interest-profile",
        json={"keywords": "technology, programming"},
        headers=headers,
    )
    assert interest_response.status_code == 200

    # Step 8: Verify config includes new source and interests
    final_config = await async_client.get("/users/config", headers=headers)
    assert final_config.status_code == 200
    final_data = final_config.json()
    assert len(final_data["sources"]) == 1
    assert final_data["sources"][0]["source_name"] == "Test Feed"
    assert "technology" in final_data["interest_profile"]["keywords"]

    # Step 9: Delete the source
    delete_response = await async_client.delete(f"/users/sources/{source_id}", headers=headers)
    assert delete_response.status_code == 200
