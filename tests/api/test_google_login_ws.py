import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message, expected_response",
    [
        (
            {"action": "get_oauth_url"},
            {"action": "oauth_url", "auth_url": "https://mock.auth.url"},
        ),
        ({"action": "auth", "code": ""}, {"error": "No code in auth"}),
        (
            {"action": "auth", "code": "test_code"},
            {
                "action": "auth_success",
                "access_token": "mock_access_token",
                "refresh_token": "mock_refresh_token",
                "is_new_user": True,
                "token_type": "bearer",
            },
        ),
        ({"action": "auth", "code": "invalid_code"}, {"error": "Invalid OAuth code"}),
        ({"action": "invalid_action"}, {"error": "Invalid action: invalid_action"}),
    ],
)
async def test_ws_google_login(mock_websocket_client, message, expected_response):
    await mock_websocket_client.send_json(message)
    response = await mock_websocket_client.receive_json()

    for key, value in expected_response.items():
        assert response.get(key) == value
