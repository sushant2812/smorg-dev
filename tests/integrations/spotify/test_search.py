"""Tests for Spotify search: one /v1/search GET mapped to a flat mix of typed hits.

No network: httpx.MockTransport routes the request to a recorded response.
"""

import json
from pathlib import Path

import httpx
import pytest

from smorg.auth.store import Credentials
from smorg.core.contract import IntegrationError, Unavailable
from smorg.integrations.spotify.source import Album, Playlist, Track, search

FIXTURES = Path(__file__).parent / "fixtures"
SEARCH = json.loads((FIXTURES / "spotify_search.json").read_text())

CREDENTIALS = Credentials(
    access_token="spotify-secret-token",
    refresh_token=None,
    expires_at=None,
    scope="",
)


def _client(payload: object, status: int = 200) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/search"
        return httpx.Response(status, json=payload)

    return httpx.Client(transport=httpx.MockTransport(handler))


def _capturing_client(payload: object) -> tuple[httpx.Client, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=payload)

    return httpx.Client(transport=httpx.MockTransport(handler)), seen


def test_search_returns_songs_albums_and_playlists_as_typed_hits():
    results = search(CREDENTIALS, _client(SEARCH), "brightside")

    kinds = {type(item) for item in results.items}
    assert kinds == {Track, Album, Playlist}
    track = next(item for item in results.items if isinstance(item, Track))
    assert track.track == "Mr. Brightside"
    assert track.artists == ("The Killers",)
    assert track.url == "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp"


def test_hits_are_interleaved_not_grouped_by_type():
    # First of each bucket leads, so the second row is not another track.
    results = search(CREDENTIALS, _client(SEARCH), "brightside")

    assert isinstance(results.items[0], Track)
    assert not isinstance(results.items[1], Track)


def test_null_playlist_padding_is_skipped():
    results = search(CREDENTIALS, _client(SEARCH), "brightside")

    playlists = [item for item in results.items if isinstance(item, Playlist)]
    assert len(playlists) == 1
    assert playlists[0].owner == "Spotify"


def test_a_playlist_owner_without_a_display_name_falls_back_to_the_id():
    # display_name is nullable on Spotify; one nameless owner must not fail the whole search.
    payload = {
        "playlists": {
            "items": [
                {
                    "name": "Deep Focus",
                    "owner": {"display_name": None, "id": "curator-42"},
                    "external_urls": {"spotify": "https://open.spotify.com/playlist/xyz"},
                }
            ]
        }
    }

    results = search(CREDENTIALS, _client(payload), "focus")

    (playlist,) = results.items
    assert isinstance(playlist, Playlist)
    assert playlist.owner == "curator-42"


def test_query_is_sent_with_all_three_types():
    client, seen = _capturing_client(SEARCH)

    search(CREDENTIALS, client, "  brightside  ")

    (request,) = seen
    assert request.url.params["q"] == "brightside"
    assert request.url.params["type"] == "track,album,playlist"


def test_empty_query_is_refused_without_a_request():
    client, seen = _capturing_client(SEARCH)

    with pytest.raises(IntegrationError):
        search(CREDENTIALS, client, "   ")
    assert seen == []


def test_missing_buckets_yield_no_hits():
    results = search(CREDENTIALS, _client({}), "brightside")

    assert results.items == ()


def test_a_non_200_is_unavailable():
    with pytest.raises(Unavailable):
        search(CREDENTIALS, _client(SEARCH, status=500), "brightside")
