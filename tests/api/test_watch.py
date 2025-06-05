# tests/api/test_watch.py
import pytest

from app.api.v1.endpoints.watch import get_available_watch_games
from app.schemas.watch import WatchGame, WatchGameUser


class DummyResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP error: {self.status_code}")

    def json(self):
        return self._data


class DummyClient:
    def __init__(self, data, status_code=200):
        self._response = DummyResponse(data, status_code)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, timeout):
        return self._response


@pytest.mark.asyncio
async def test_get_available_watch_games_success(monkeypatch):
    raw_games = [
        {
            "game_id": 42,
            "start_time": "2025-05-28T16:00:00Z",
            "users": [
                {"uid": "user1", "nickname": "Alice"},
                {"uid": "user2", "nickname": "Bob"},
            ],
        },
        {
            "game_id": 99,
            "start_time": "2025-05-28T17:00:00Z",
            "users": [],
        },
    ]
    monkeypatch.setattr(
        "app.api.v1.endpoints.watch.AsyncClient",
        lambda *args, **kwargs: DummyClient(raw_games, status_code=200),
    )
    result = await get_available_watch_games()
    assert isinstance(result, list)
    assert result == [
        WatchGame(
            game_id=42,
            start_time="2025-05-28T16:00:00Z",
            users=[
                WatchGameUser(uid="user1", nickname="Alice"),
                WatchGameUser(uid="user2", nickname="Bob"),
            ],
        ),
        WatchGame(
            game_id=99,
            start_time="2025-05-28T17:00:00Z",
            users=[],
        ),
    ]


@pytest.mark.asyncio
async def test_get_available_watch_games_http_error(monkeypatch):
    monkeypatch.setattr(
        "app.api.v1.endpoints.watch.AsyncClient",
        lambda *args, **kwargs: DummyClient([], status_code=500),
    )
    with pytest.raises(RuntimeError) as excinfo:
        await get_available_watch_games()
    assert "HTTP error: 500" in str(excinfo.value)
