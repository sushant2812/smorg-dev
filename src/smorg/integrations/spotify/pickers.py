"""Picker over Spotify search hits: one flat mix of songs, albums, and playlists to open."""

from __future__ import annotations

from rich.text import Text
from textual.binding import Binding

from smorg.integrations.spotify.source import Album, SearchItem, SearchResults, Track
from smorg.shell.picker import Picker, Row, Section

_DIM = "dim"
_OPEN_HINT = "⏎ open · esc close"


class SearchPicker(Picker):
    BINDINGS = [
        Binding("up", "cursor_up", "select", show=False),
        Binding("down", "cursor_down", "select", show=False),
        Binding("enter", "confirm", "choose", show=False),
        Binding("escape", "close", "close", show=False),
    ]


def _hit_row(item: SearchItem) -> Text:
    if isinstance(item, Track):
        row = Text(item.track)
        row.append(f" · {', '.join(item.artists)}", style=_DIM)
        row.append(" · song", style=_DIM)
        return row
    if isinstance(item, Album):
        row = Text(item.name)
        row.append(f" · {', '.join(item.artists)}", style=_DIM)
        row.append(" · album", style=_DIM)
        return row
    row = Text(item.name)
    row.append(f" · {item.owner}", style=_DIM)
    row.append(" · playlist", style=_DIM)
    return row


def search_picker(results: SearchResults) -> SearchPicker:
    """One ungrouped list of hits; confirming a row opens it in Spotify."""
    rows: list[Row] = [(_hit_row(item), item) for item in results.items]
    sections: list[Section] = [("", rows)]
    return SearchPicker("search", sections, _OPEN_HINT, 0)
