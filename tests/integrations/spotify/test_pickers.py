"""Tests for the Spotify search results picker (browse-and-open, read-only)."""

from smorg.integrations.spotify.pickers import search_picker
from smorg.integrations.spotify.source import Album, Playlist, SearchResults, Track


def track(name: str = "Mr. Brightside") -> Track:
    return Track(
        track=name,
        artists=("The Killers",),
        album="Hot Fuss",
        url=f"https://open.spotify.com/track/{name}",
    )


def album(name: str = "Hot Fuss") -> Album:
    return Album(name=name, artists=("The Killers",), url=f"https://open.spotify.com/album/{name}")


def playlist(name: str = "This Is The Killers") -> Playlist:
    return Playlist(name=name, owner="Spotify", url=f"https://open.spotify.com/playlist/{name}")


def test_picker_lists_a_flat_mix_without_section_headings():
    results = SearchResults(items=(track(), album(), playlist(), track("Take On Me")))

    picker = search_picker(results)
    text = "\n".join(picker.content_lines())

    assert picker._title == "search"
    assert "songs" not in text
    assert "albums" not in text
    assert "playlists" not in text
    assert "Mr. Brightside · The Killers · song" in text
    assert "Hot Fuss · The Killers · album" in text
    assert "This Is The Killers · Spotify · playlist" in text
    assert "Take On Me · The Killers · song" in text


def test_hint_offers_open_not_play_or_queue():
    picker = search_picker(SearchResults(items=(track(),)))

    assert "⏎ open · esc close" in "\n".join(picker.content_lines())


def test_confirm_returns_the_highlighted_hit():
    first = track()
    picker = search_picker(SearchResults(items=(first, album())))

    assert picker.selected_value() is first


def test_no_matches_is_an_empty_picker():
    picker = search_picker(SearchResults(items=()))

    assert picker.rows() == []
    assert picker.selected_value() is None
