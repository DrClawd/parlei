#!/usr/bin/env python3
"""
weekender.py — Weekly events + movies digest for Discord.

Posts:
  • Day-grouped events (now → upcoming Saturday 11:59 PM) to #local-events
  • Movies currently playing at local theaters to #movies-this-week

Sources:
  • ilovetheburg.com Tribe Events Calendar REST API
  • Eventbrite St. Petersburg & Gulfport pages
  • Fandango theater pages: CMX Tyrone 10, AMC Sundial 12, Regal Park Place

Schedule: Sunday 03:00 AM via cron
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup
from posting_templates import build_movie_embed, make_event_embed

# ─── Config ────────────────────────────────────────────────────────────────────

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise SystemExit("DISCORD_TOKEN environment variable is required")
EVENTS_CHANNEL = "1479396569101893632"
MOVIES_CHANNEL = "1479397156095004784"

INTERESTS = [
    "yoga", "hike", "hiking", "kayak", "kayaking",
    "music", "live music", "festival", "concert",
    "cocktail", "cocktails", "fine dining", "restaurant", "food",
    "football", "improv", "comedy", "art", "gallery", "museum",
    "wine", "bourbon", "whiskey", "beer", "craft beer",
    "outdoor", "nature", "sport", "adventure", "waterfront",
    "comedy", "mystery", "history", "documentary", "science",
]

FANDANGO_THEATERS = [
    {"name": "CMX Tyrone 10",     "slug": "cmx-tyrone-10-aaxus"},
    {"name": "AMC Sundial 12",    "slug": "amc-sundial-12-AAPCJ"},
    {"name": "Regal Park Place",  "slug": "regal-park-place-AAPIO"},
]

TRIBE_API_PATH = "/wp-json/tribe/events/v1/events"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


# ─── Helpers ───────────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def strip_html(html_str: str) -> str:
    """Strip HTML tags and normalise whitespace."""
    if not html_str:
        return ""
    soup = BeautifulSoup(html_str, "html.parser")
    text = soup.get_text(separator=" ")
    return " ".join(text.split())


def truncate(text: str, max_len: int = 200) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "…"


def is_interest_match(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in INTERESTS)


def saturday_eow() -> date:
    """Return the date of the upcoming Saturday (or today if today is Saturday)."""
    today = date.today()
    days_ahead = (5 - today.weekday()) % 7  # 5 = Saturday
    return today + timedelta(days=days_ahead if days_ahead > 0 else 7)


def window(window_hours: int | None = None) -> tuple[datetime, datetime]:
    """Return (now, end). Default end is upcoming Saturday 11:59:59.

    If window_hours is provided (>0), end = now + window_hours.
    """
    now = datetime.now()
    if window_hours and window_hours > 0:
        return now, now + timedelta(hours=window_hours)

    sat = saturday_eow()
    end = datetime(sat.year, sat.month, sat.day, 23, 59, 59)
    return now, end


WEEKDAY_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _parse_clock_time(val: str) -> tuple[int, int] | None:
    """Parse times like 9:30am / 10am / 5:00pm."""
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*([ap]m)", val.strip().lower())
    if not m:
        return None
    hour = int(m.group(1)) % 12
    minute = int(m.group(2) or 0)
    if m.group(3) == "pm":
        hour += 12
    return hour, minute


def _next_occurrence_for_skybeach(
    date_text: str,
    start: datetime,
    end: datetime,
) -> tuple[datetime, datetime] | None:
    """Resolve SkyBeach recurrence strings into the next concrete datetime window."""
    parts = [p.strip() for p in date_text.split("-") if p.strip()]
    if len(parts) < 2:
        return None

    mode = parts[0].lower()
    if mode not in {"daily", "weekly"}:
        return None

    idx = 1
    weekdays: list[int] = []
    if mode == "weekly":
        if len(parts) < 3:
            return None
        day_tokens = [d.strip().lower() for d in parts[1].split(",") if d.strip()]
        weekdays = [WEEKDAY_INDEX[d] for d in day_tokens if d in WEEKDAY_INDEX]
        if not weekdays:
            return None
        idx = 2

    start_time = _parse_clock_time(parts[idx])
    if not start_time:
        return None
    end_time = _parse_clock_time(parts[idx + 1]) if len(parts) > idx + 1 else None

    for offset_days in range(0, 14):
        day = (start + timedelta(days=offset_days)).date()
        if mode == "weekly" and day.weekday() not in weekdays:
            continue

        cand_start = datetime(day.year, day.month, day.day, start_time[0], start_time[1])
        if cand_start < start:
            continue

        if end_time:
            cand_end = datetime(day.year, day.month, day.day, end_time[0], end_time[1])
            if cand_end <= cand_start:
                cand_end += timedelta(days=1)
        else:
            cand_end = cand_start + timedelta(hours=2)

        if cand_end < start or cand_start > end:
            continue

        return cand_start, cand_end

    return None


def group_by_day(events: list[dict]) -> dict[date, list[dict]]:
    grouped: dict[date, list[dict]] = {}
    for ev in events:
        d = ev["start_dt"].date()
        grouped.setdefault(d, []).append(ev)
    for day_events in grouped.values():
        day_events.sort(key=lambda e: e["start_dt"])
    return dict(sorted(grouped.items()))


def load_event_sources() -> list[dict[str, Any]]:
    """Parse JSON source definitions from local_event_sources.md bullet lines."""
    path = Path(__file__).parent.parent / "local_event_sources.md"
    if not path.exists():
        return []
    sources: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line.startswith("- "):
            continue
        body = line[2:].strip()
        if not body.startswith("{"):
            continue
        try:
            obj = json.loads(body)
        except Exception:
            continue
        if not isinstance(obj, dict) or not obj.get("url"):
            continue
        obj.setdefault("kind", "unknown")
        obj["nested"] = int(obj.get("nested", 0) or 0)
        obj["favorites"] = int(obj.get("favorites", 0) or 0)
        sources.append(obj)
    return sources


# ─── Event Sources ─────────────────────────────────────────────────────────────

def fetch_tribe_events(source: dict[str, Any], start: datetime, end: datetime) -> list[dict]:
    """Pull events from a Tribe Events REST API source."""
    source_url = source.get("url", "")
    base = re.match(r"^https?://[^/]+", source_url)
    if not base:
        return []
    api_url = base.group(0) + TRIBE_API_PATH
    log(f"Fetching tribe events: {source_url}")
    events: list[dict] = []
    page = 1
    while True:
        params = {
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "per_page": 50,
            "page": page,
        }
        try:
            r = requests.get(api_url, params=params, headers=HEADERS, timeout=20)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            log(f"  Error fetching ilovetheburg page {page}: {exc}")
            break

        raw_events = data.get("events", [])
        if not raw_events:
            break

        for ev in raw_events:
            try:
                start_dt = datetime.strptime(ev["start_date"], "%Y-%m-%d %H:%M:%S")
                end_dt = datetime.strptime(ev["end_date"], "%Y-%m-%d %H:%M:%S")
            except (ValueError, KeyError):
                continue

            # Skip already-ended events
            if end_dt < start:
                continue

            # Skip events that start after our window
            if start_dt > end:
                continue

            venue = ev.get("venue") or {}
            if isinstance(venue, list):
                venue = venue[0] if venue else {}
            venue_name = venue.get("venue", "") if isinstance(venue, dict) else ""
            venue_city = venue.get("city", "") if isinstance(venue, dict) else ""
            location = ", ".join(filter(None, [venue_name, venue_city]))

            cost_raw = ev.get("cost", "") or ""
            cost = cost_raw.strip() if cost_raw.strip() else "$0"

            desc = truncate(strip_html(ev.get("description", "") or ""), 200)
            title = unescape((ev.get("title") or "Untitled").strip())

            image_url = ""
            image = ev.get("image") or {}
            if isinstance(image, dict):
                image_url = image.get("url") or image.get("full") or image.get("thumbnail") or ""

            favorites = int(source.get("favorites", 0) or 0)
            events.append({
                "title": title,
                "description": desc,
                "location": location,
                "start_dt": start_dt,
                "end_dt": end_dt,
                "cost": cost,
                "url": ev.get("url", ""),
                "image": image_url,
                "source": source_url,
                "interest_match": True if favorites == 1 else is_interest_match(title + " " + desc),
                "force_include": favorites == 1,
                "nested": int(source.get("nested", 0) or 0),
            })

        total_pages = data.get("total_pages", 1)
        if page >= total_pages:
            break
        page += 1
        time.sleep(0.5)

    log(f"  Got {len(events)} ilovetheburg events")
    return events


def _parse_iso_dt(val: str) -> datetime | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def fetch_vista_happenings(source: dict[str, Any], start: datetime, end: datetime) -> list[dict]:
    """Fetch Vista events; nested=1 follows each event page for details."""
    source_url = source.get("url", "")
    nested = int(source.get("nested", 0) or 0)
    favorites = int(source.get("favorites", 0) or 0)
    log(f"Fetching Vista happenings: {source_url}")

    out: list[dict] = []
    try:
        r = requests.get(source_url, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except Exception as exc:
        log(f"  Vista fetch error: {exc}")
        return out

    soup = BeautifulSoup(r.text, "html.parser")
    links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/event/" in href:
            if href.startswith("/"):
                base = re.match(r"^https?://[^/]+", source_url)
                if base:
                    href = base.group(0) + href
            if href not in links:
                links.append(href)

    for i, link in enumerate(links):
        title = "Untitled Vista Event"
        start_dt = None
        end_dt = None
        description = ""
        location = "Vista at the Top"
        image_url = ""

        if nested == 1:
            try:
                pr = requests.get(link, headers=HEADERS, timeout=20)
                pr.raise_for_status()
            except Exception:
                continue
            ps = BeautifulSoup(pr.text, "html.parser")

            for script in ps.find_all("script", type="application/ld+json"):
                raw = (script.string or script.get_text() or "").strip()
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                except Exception:
                    continue
                candidates = data if isinstance(data, list) else [data]
                for d in candidates:
                    if isinstance(d, dict) and d.get("@type") == "Event":
                        title = unescape((d.get("name") or title).strip())
                        description = truncate(strip_html(d.get("description") or ""), 200)
                        start_dt = _parse_iso_dt(d.get("startDate") or "")
                        end_dt = _parse_iso_dt(d.get("endDate") or "")
                        image = d.get("image")
                        if isinstance(image, list):
                            image_url = image[0] if image else ""
                        elif isinstance(image, str):
                            image_url = image
                        loc = d.get("location") or {}
                        if isinstance(loc, dict):
                            location = loc.get("name") or location
                        break
                if start_dt:
                    break

            if not description:
                description = truncate(strip_html((ps.select_one("meta[property='og:description']") or {}).get("content", "")), 200)
            if not image_url:
                og = ps.select_one("meta[property='og:image']")
                if og and og.get("content"):
                    image_url = og.get("content")

        if start_dt is None:
            start_dt = start + timedelta(minutes=i)
        if end_dt is None:
            end_dt = min(end, start_dt + timedelta(hours=2))

        if end_dt < start or start_dt > end:
            continue

        out.append({
            "title": title,
            "description": description or "Event details on source page.",
            "location": location,
            "start_dt": start_dt,
            "end_dt": end_dt,
            "cost": "$0",
            "url": link,
            "image": image_url,
            "source": source_url,
            "interest_match": True if favorites == 1 else is_interest_match(title + " " + description),
            "force_include": favorites == 1,
            "nested": nested,
        })

    log(f"  Got {len(out)} Vista events")
    return out


def fetch_skybeach_happenings(source: dict[str, Any], start: datetime, end: datetime) -> list[dict]:
    """Fetch SkyBeach happenings from endpoint derived from source origin."""
    source_url = source.get("url", "")
    favorites = int(source.get("favorites", 0) or 0)
    base = re.match(r"^https?://[^/]+", source_url)
    if not base:
        return []
    events_api = base.group(0) + "/ajax/functions.php?operation=getEvents&category=all&date=all"

    log(f"Fetching SkyBeach happenings: {source_url}")
    out: list[dict] = []
    try:
        r = requests.get(events_api, headers=HEADERS, timeout=20)
        r.raise_for_status()
        payload = r.json()
        html_blob = payload.get("html", "")
    except Exception as exc:
        log(f"  SkyBeach fetch error: {exc}")
        return out

    soup = BeautifulSoup(html_blob, "html.parser")
    cards = soup.select("div.event")
    for card in cards:
        title = unescape((card.select_one("h2") or {}).get_text(strip=True) if card.select_one("h2") else "SkyBeach Event")
        date_text = (card.select_one(".event__date") or {}).get_text(" ", strip=True) if card.select_one(".event__date") else ""
        desc_text = (card.select_one(".event__description") or card.select_one("p") or {}).get_text(" ", strip=True) if (card.select_one(".event__description") or card.select_one("p")) else ""
        img = card.select_one("img[src]")
        image_url = img.get("src", "") if img else ""

        resolved = _next_occurrence_for_skybeach(date_text, start, end)
        if not resolved:
            continue
        start_dt, end_dt = resolved

        out.append({
            "title": title,
            "description": truncate(desc_text or date_text or "Event details on source page.", 200),
            "location": "SkyBeach Resort, St. Petersburg",
            "start_dt": start_dt,
            "end_dt": end_dt,
            "cost": "$0",
            "url": source_url,
            "image": image_url,
            "source": source_url,
            "interest_match": True if favorites == 1 else is_interest_match(title + " " + desc_text),
            "force_include": favorites == 1,
            "nested": int(source.get("nested", 0) or 0),
        })

    log(f"  Got {len(out)} SkyBeach events")
    return out


def fetch_eventbrite(source: dict[str, Any], start: datetime, end: datetime) -> list[dict]:
    """Scrape Eventbrite city pages for embedded event data."""
    source_url = source.get("url", "")
    favorites = int(source.get("favorites", 0) or 0)
    url = source_url.replace(".rss/", "/").replace(".rss", "")
    log(f"Fetching Eventbrite events: {url}")

    events: list[dict] = []
    seen_ids: set[str] = set()

    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except Exception as exc:
        log(f"  Error fetching {url}: {exc}")
        return events

    data_match = re.search(r'window\.__SERVER_DATA__\s*=\s*({.+?});\s*\n', r.text, re.DOTALL)
    if not data_match:
        log(f"  No __SERVER_DATA__ found at {url}")
        return events

    try:
        server_data = json.loads(data_match.group(1))
    except json.JSONDecodeError as exc:
        log(f"  JSON parse error at {url}: {exc}")
        return events

    buckets = server_data.get("buckets", [])
    for bucket in buckets:
        for ev in bucket.get("events", []):
            eid = str(ev.get("id") or ev.get("eid") or "")
            if not eid or eid in seen_ids:
                continue
            seen_ids.add(eid)

            try:
                sd = ev.get("start_date", "")
                st = ev.get("start_time", "00:00")
                ed = ev.get("end_date", sd)
                et = ev.get("end_time", "23:59")
                start_dt = datetime.strptime(f"{sd} {st}", "%Y-%m-%d %H:%M")
                end_dt = datetime.strptime(f"{ed} {et}", "%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                continue

            if end_dt < start or start_dt > end:
                continue

            venue = ev.get("primary_venue") or {}
            if isinstance(venue, dict):
                vname = venue.get("name", "")
                vaddr = venue.get("address", {}) or {}
                vcity = vaddr.get("city", "") if isinstance(vaddr, dict) else ""
            else:
                vname = vcity = ""
            location = ", ".join(filter(None, [vname, vcity]))

            title = (ev.get("name") or "Untitled").strip()
            summary = truncate(ev.get("summary") or ev.get("full_description") or "", 200)

            logo = ev.get("logo") or {}
            image_url = ""
            if isinstance(logo, dict):
                image_url = (
                    logo.get("url")
                    or (logo.get("original") or {}).get("url")
                    or (logo.get("event_logo") or {}).get("url")
                    or ""
                )
                image_url = normalize_url(image_url, ev.get("url", "https://www.eventbrite.com"))

            events.append({
                "title": title,
                "description": summary,
                "location": location,
                "start_dt": start_dt,
                "end_dt": end_dt,
                "cost": "$0" if str(ev.get("is_free", "")).lower() == "true" else "See Eventbrite for pricing",
                "url": ev.get("url", ""),
                "image": image_url,
                "source": source_url,
                "interest_match": True if favorites == 1 else is_interest_match(title + " " + summary),
                "force_include": favorites == 1,
                "nested": int(source.get("nested", 0) or 0),
            })

    log(f"  Got {len(events)} Eventbrite events")
    return events


def deduplicate(events: list[dict]) -> list[dict]:
    """Remove duplicate events by normalised title + start date."""
    seen: set[str] = set()
    unique: list[dict] = []
    for ev in events:
        key = re.sub(r"[^a-z0-9]", "", ev["title"].lower()) + ev["start_dt"].strftime("%Y%m%d")
        if key not in seen:
            seen.add(key)
            unique.append(ev)
    return unique


# ─── Movie Sources ─────────────────────────────────────────────────────────────

def scrape_theater_movies(theater: dict) -> list[dict]:
    """Scrape a Fandango theater page for currently listed movies."""
    slug = theater["slug"]
    theater_name = theater["name"]
    url = f"https://www.fandango.com/{slug}/theater-page"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except Exception as exc:
        log(f"  Error scraping {theater_name}: {exc}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    movies = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/movie-overview" not in href:
            continue
        title = a.get_text(strip=True)
        if not title or title in seen:
            continue
        seen.add(title)
        full_url = f"https://www.fandango.com{href}" if href.startswith("/") else href
        movies.append({
            "title": title,
            "theater": theater_name,
            "fandango_url": full_url,
            "poster": "",
            "synopsis": "",
        })

    return movies


def enrich_movie(movie: dict) -> dict:
    """Fetch poster and synopsis from the Fandango movie overview page."""
    url = movie["fandango_url"]
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except Exception as exc:
        log(f"    Error enriching {movie['title']}: {exc}")
        return movie

    soup = BeautifulSoup(r.text, "html.parser")

    # Poster from JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                data = data[0]
            if data.get("@type") == "Movie":
                poster = data.get("image", "")
                if poster:
                    movie["poster"] = poster
                break
        except Exception:
            pass

    # If no poster from LD, try img tags
    if not movie["poster"]:
        for img in soup.select("img[src*='fandango']"):
            src = img.get("src", "")
            if "poster" in src.lower() or "mast" in src.lower():
                movie["poster"] = src
                break

    # Synopsis
    for sel in ["[class*='synopsis']", "[class*='overview']", ".movie-details-body", "p.lead"]:
        found = soup.select(sel)
        if found:
            text = found[0].get_text(strip=True)
            if len(text) > 50:
                movie["synopsis"] = truncate(text, 300)
                break

    return movie


def fetch_movies() -> list[dict]:
    """Gather movies from all three Fandango theater pages, deduplicated."""
    log("Fetching movies from Fandango...")
    all_movies: dict[str, dict] = {}  # title_norm -> movie

    for theater in FANDANGO_THEATERS:
        log(f"  Scraping {theater['name']}...")
        theater_movies = scrape_theater_movies(theater)
        for m in theater_movies:
            norm = re.sub(r"[^a-z0-9]", "", m["title"].lower())
            if norm in all_movies:
                # Add theater to existing entry
                existing = all_movies[norm]["theater"]
                if theater["name"] not in existing:
                    all_movies[norm]["theater"] += f" · {theater['name']}"
                    # Use same fandango_url (already set)
            else:
                all_movies[norm] = m
        time.sleep(1)

    movies = list(all_movies.values())
    log(f"  Found {len(movies)} unique movies — enriching...")
    enriched = []
    for m in movies:
        enriched.append(enrich_movie(m))
        time.sleep(0.8)

    log(f"  Done enriching {len(enriched)} movies")
    return enriched


# ─── Discord Posting ───────────────────────────────────────────────────────────

def _discord_request_with_retry(url: str, headers: dict[str, str], payload: dict[str, Any], retries: int = 6) -> bool:
    for attempt in range(retries):
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        if r.status_code in (200, 201, 204):
            return True
        if r.status_code == 429:
            try:
                retry_after = float(r.json().get("retry_after", 1.0))
            except Exception:
                retry_after = 1.0
            sleep_for = retry_after + 0.25
            log(f"  Discord rate limited; retrying in {sleep_for:.2f}s")
            time.sleep(sleep_for)
            continue

        log(f"  Discord post failed: {r.status_code} {r.text[:200]}")
        return False

    log("  Discord post failed after retries")
    return False


def discord_post(channel_id: str, content: str, dry_run: bool = False, post_delay: float = 0.8) -> bool:
    """Post plain text to Discord (chunked) with retry/backoff."""
    if dry_run:
        print(f"\n{'='*60}\n[DRY RUN → channel {channel_id} TEXT]\n{content}\n{'='*60}")
        return True

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json",
    }

    chunks = []
    while len(content) > 1900:
        split_at = content.rfind("\n", 0, 1900)
        if split_at == -1:
            split_at = 1900
        chunks.append(content[:split_at])
        content = content[split_at:].lstrip("\n")
    chunks.append(content)

    for chunk in chunks:
        ok = _discord_request_with_retry(url, headers, {"content": chunk})
        if not ok:
            return False
        time.sleep(max(0.2, post_delay))
    return True


def discord_post_embed(channel_id: str, embed: dict[str, Any], dry_run: bool = False, content: str | None = None, post_delay: float = 0.8) -> bool:
    """Post one embed so each image stays attached to its item."""
    if dry_run:
        print(
            f"\n{'='*60}\n[DRY RUN → channel {channel_id} EMBED]\n"
            f"content={content or ''}\n"
            f"title={embed.get('title','')}\n"
            f"url={embed.get('url','')}\n"
            f"image={embed.get('image',{}).get('url','')}\n"
            f"{'='*60}"
        )
        return True

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {"embeds": [embed]}
    if content:
        payload["content"] = content

    ok = _discord_request_with_retry(url, headers, payload)
    if not ok:
        return False
    time.sleep(max(0.2, post_delay))
    return True


def normalize_url(raw: str, base_url: str) -> str:
    if not raw:
        return ""
    raw = raw.strip()
    if raw.startswith("//"):
        return "https:" + raw
    if raw.startswith("/"):
        m = re.match(r"^https?://[^/]+", base_url)
        return (m.group(0) + raw) if m else raw
    return raw


def discover_image_from_url(url: str) -> str:
    """Best-effort OG/Twitter image discovery for event pages."""
    if not url:
        return ""
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
    except Exception:
        return ""

    soup = BeautifulSoup(r.text, "html.parser")
    for selector, attr, val in [
        ("meta[property='og:image']", "content", None),
        ("meta[name='twitter:image']", "content", None),
        ("meta[property='og:image:url']", "content", None),
    ]:
        node = soup.select_one(selector)
        if node and node.get(attr):
            return normalize_url(node.get(attr), url)

    # fallback first meaningful image in page body
    img = soup.select_one("img[src]")
    if img and img.get("src"):
        return normalize_url(img.get("src"), url)
    return ""


def enrich_event_images(events: list[dict], max_checks: int = 20) -> None:
    """Fill missing event image fields using page metadata lookup."""
    checked = 0
    for ev in events:
        if ev.get("image"):
            continue
        if checked >= max_checks:
            break
        found = discover_image_from_url(ev.get("url", ""))
        if found:
            ev["image"] = found
        checked += 1
        time.sleep(0.2)



# ─── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Weekly events + movies digest for Discord.")
    parser.add_argument("--dry-run", action="store_true", help="Print output instead of posting to Discord.")
    parser.add_argument("--events-only", action="store_true", help="Skip movies.")
    parser.add_argument("--movies-only", action="store_true", help="Skip events.")
    parser.add_argument("--max-events", type=int, default=18, help="Max number of event cards to post.")
    parser.add_argument("--max-movies", type=int, default=20, help="Max number of movie cards to post.")
    parser.add_argument("--post-delay", type=float, default=0.8, help="Base delay between Discord posts.")
    parser.add_argument("--window-hours", type=int, default=24, help="Rolling now->N hours event window (default: 24). Set 0 to use weekend window.")
    parser.add_argument("--events-channel", type=str, default=EVENTS_CHANNEL, help="Discord channel id for event posts.")
    args = parser.parse_args()

    win_start, win_end = window(args.window_hours if args.window_hours > 0 else None)
    log(f"Window: {win_start} → {win_end}")

    # ── Events ──
    if not args.movies_only:
        raw_events: list[dict] = []
        sources = load_event_sources()
        for src in sources:
            kind = str(src.get("kind", "")).lower().strip()
            try:
                if kind == "tribe":
                    raw_events.extend(fetch_tribe_events(src, win_start, win_end))
                elif kind == "eventbrite":
                    raw_events.extend(fetch_eventbrite(src, win_start, win_end))
                elif kind == "vista":
                    raw_events.extend(fetch_vista_happenings(src, win_start, win_end))
                elif kind == "skybeach":
                    raw_events.extend(fetch_skybeach_happenings(src, win_start, win_end))
                else:
                    continue
            except Exception as exc:
                log(f"Source error ({src.get('url','unknown')}): {exc}")

        events = deduplicate(raw_events)
        log(f"Total unique events: {len(events)}")

        # Queue/throttle protection: prioritize and cap total event cards.
        forced = [e for e in events if e.get("force_include")]
        others = [e for e in events if not e.get("force_include")]

        forced_sorted = sorted(forced, key=lambda e: e["start_dt"])
        others_sorted = sorted(
            others,
            key=lambda e: (
                0 if e.get("interest_match") else 1,
                e["start_dt"],
            ),
        )

        remaining_slots = max(0, max(1, args.max_events) - len(forced_sorted))
        selected_events = forced_sorted + others_sorted[:remaining_slots]
        selected_events = deduplicate(selected_events)

        # Try to backfill missing event images from source pages.
        enrich_event_images(selected_events, max_checks=min(len(selected_events), 18))
        grouped = group_by_day(selected_events)

        if grouped:
            ok = True
            if args.window_hours and args.window_hours > 0:
                header = (
                    f"📅 **Upcoming Events — Next {args.window_hours} Hours**\n"
                    f"Window: {win_start.strftime('%a %b %-d, %-I:%M %p')} → {win_end.strftime('%a %b %-d, %-I:%M %p')}\n"
                    f"Curated for St. Petersburg & Gulfport 🌊\n"
                    f"🧾 Showing top {len(selected_events)} events (throttled)."
                )
            else:
                header = (
                    f"📅 **Weekend Events — {win_start.strftime('%B %-d')} through {win_end.strftime('%B %-d, %Y')}**\n"
                    f"Curated for St. Petersburg & Gulfport 🌊\n"
                    f"🧾 Showing top {len(selected_events)} events (throttled)."
                )
            ok &= discord_post(
                args.events_channel,
                header,
                dry_run=args.dry_run,
                post_delay=args.post_delay,
            )
            for day, day_events in grouped.items():
                ok &= discord_post(
                    args.events_channel,
                    f"**── {day.strftime('%A, %B %-d')} ──**",
                    dry_run=args.dry_run,
                    post_delay=args.post_delay,
                )
                for ev in day_events:
                    prefix = "⭐ Interest Match" if ev.get("interest_match") else None
                    ok &= discord_post_embed(
                        args.events_channel,
                    make_event_embed(ev),
                        dry_run=args.dry_run,
                        content=prefix,
                        post_delay=args.post_delay,
                    )
            if not ok:
                log("One or more event posts failed.")
        else:
            empty_msg = (
                f"📅 No events found in the next {args.window_hours} hours."
                if args.window_hours and args.window_hours > 0
                else "📅 No events found for this weekend. Check back next Sunday!"
            )
            discord_post(
                args.events_channel,
                empty_msg,
                dry_run=args.dry_run,
                post_delay=args.post_delay,
            )

    # ── Movies ──
    if not args.events_only:
        movies = fetch_movies()
        log(f"Total unique movies: {len(movies)}")

        if movies:
            movies_selected = movies[: max(1, args.max_movies)]
            ok = True
            ok &= discord_post(
                MOVIES_CHANNEL,
                f"🎬 **Movies Playing This Week**\n*At AMC Sundial 12, CMX Tyrone 10, and Regal Park Place*\n🧾 Showing top {len(movies_selected)} movies (throttled).",
                dry_run=args.dry_run,
                post_delay=args.post_delay,
            )
            for m in movies_selected:
                ok &= discord_post_embed(
                    MOVIES_CHANNEL,
                    build_movie_embed(m),
                    dry_run=args.dry_run,
                    post_delay=args.post_delay,
                )
            if not ok:
                log("One or more movie posts failed.")
        else:
            discord_post(
                MOVIES_CHANNEL,
                "🎬 No movies found this week. Fandango may be down or theaters may be closed.",
                dry_run=args.dry_run,
            )

    log("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
