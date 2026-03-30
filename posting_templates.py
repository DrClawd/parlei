from __future__ import annotations

from datetime import datetime
from typing import Any


def _format_dt(dt: datetime) -> str:
    return dt.strftime("%a %b %-d, %-I:%M %p")


def make_movie_embed(movie: dict[str, Any]) -> dict[str, Any]:
    """Reusable clean embed card style for movie postings."""
    synopsis = (movie.get("synopsis") or "Synopsis not available.").strip()
    synopsis = synopsis[:900]
    embed: dict[str, Any] = {
        "title": (movie.get("title") or "Untitled")[:250],
        "url": movie.get("fandango_url", ""),
        "description": (
            f"🏟️ **Playing at:** {movie.get('theater', 'Unknown theater')}\n\n"
            f"{synopsis}\n\n"
            f"🎟️ [Buy tickets on Fandango](<{movie.get('fandango_url','')}>)"
        ),
    }
    if movie.get("poster"):
        embed["image"] = {"url": movie["poster"]}
    return embed


def make_event_embed(event: dict[str, Any]) -> dict[str, Any]:
    """Reusable event embed matching weekender formatting."""
    start_dt = event.get("start_dt")
    end_dt = event.get("end_dt")
    start_fmt = _format_dt(start_dt) if isinstance(start_dt, datetime) else "TBD"
    end_fmt = _format_dt(end_dt) if isinstance(end_dt, datetime) else "TBD"
    desc = (
        f"📍 **Location:** {event.get('location') or 'Location TBD'}\n"
        f"🕐 **When:** {start_fmt} – {end_fmt}\n"
        f"💵 **Cost:** {event.get('cost', 'Free')}\n\n"
        f"{event.get('description') or 'No description available.'}"
    )
    embed: dict[str, Any] = {
        "title": (event.get("title") or "Untitled Event")[:250],
        "url": event.get("url"),
        "description": desc[:3500],
    }
    if event.get("image"):
        embed["image"] = {"url": event["image"]}
    return {k: v for k, v in embed.items() if v}


__all__ = ["make_movie_embed", "make_event_embed"]
build_movie_embed = make_movie_embed
build_event_embed = make_event_embed
