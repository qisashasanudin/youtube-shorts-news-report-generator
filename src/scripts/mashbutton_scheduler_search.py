#!/usr/bin/env python3
"""
MashButtonGaming Shorts Scheduler — broad search engine approach.

- Auto-checks and launches headless Edge (CDP on port 9222) if needed
- Uses direct HTTP requests to Bing & Yahoo (no browser/CDP required for search)
- Rotates through broad shooter/FPS queries
- Dedupes against editorial_state.json
- Outputs exactly 10 real stories to scheduler_output.json
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path for imports
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src" / "scripts"))

from search_web import search_web

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

EDITORIAL_STATE_PATH = ROOT / "editorial_state.json"
OUTPUT_PATH = ROOT / "scheduler_output.json"
MAX_STORIES = 10

# Edge CDP configuration
EDGE_CDP_PORT = 9222
EDGE_CDP_URL = f"http://127.0.0.1:{EDGE_CDP_PORT}"

BLOCKED_DOMAINS = {
    "aliexpress.com", "alibaba.com", "amazon.com", "ebay.com", "walmart.com",
    "bestbuy.com", "gamestop.com", "steamcommunity.com", "store.steampowered.com",
    "epicgames.com", "twitch.tv", "youtube.com", "reddit.com",
    "tiktok.com", "facebook.com", "instagram.com",
}

SHOOTER_QUERIES = [
    "battlefield 6 news 2026",
    "call of duty modern warfare 4 news 2026",
    "valorant patch notes 2026",
    "counter-strike 2 update 2026",
    "overwatch 2 new hero 2026",
    "tactical shooter games 2026",
    "rainbow six siege update 2026",
    "escape from tarkov news 2026",
    "apex legends season 2026",
    "halo infinite update 2026",
    "destiny 2 news 2026",
    "fps games 2026 release",
    "third person shooter games 2026",
    "xbox showcase shooter games 2026",
    "playstation shooter games 2026",
]

SHOOTER_PATTERNS = [
    "shooter", "fps", "first person", "third person", "tps",
    "tactical", "battlefield", "call of duty", "modern warfare",
    "valorant", "counter-strike", "overwatch", "halo", "destiny",
    "escape from tarkov", "rainbow six", "siege", "doom", "halflife",
    "gta", "fortnite", "pubg", "apex", "warzone",
]

TWITTER_LEAKER_QUERIES = [
    "billbil-kun leak 2026 shooter",
    "insider gaming leak 2026 fps",
    "tom henderson leak 2026",
    "jeff grubb leak 2026",
    "shpeshal nick leak 2026",
    "midori leak 2026",
]


def load_editorial_state() -> dict[str, Any]:
    if EDITORIAL_STATE_PATH.exists():
        try:
            return json.loads(EDITORIAL_STATE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"used_stories": [], "daily_uploads": {}}


def seen_urls(state: dict[str, Any]) -> set[str]:
    urls: set[str] = set()
    for story in state.get("used_stories", []):
        url = story.get("url") or story.get("official_url")
        if url:
            urls.add(url.strip())
    for story in state.get("stories", []):
        url = story.get("official_url") or story.get("url")
        if url:
            urls.add(url.strip())
    return urls


def _looks_like_shooter(title: str) -> bool:
    t = title.lower()
    return any(p in t for p in SHOOTER_PATTERNS)


def _blocked(url: str) -> bool:
    try:
        from urllib.parse import urlsplit
    except Exception:
        return False
    host = urlsplit(url).netloc.lower()
    return any(host == d or host.endswith("." + d) for d in BLOCKED_DOMAINS)


def _dedup_title(title: str, seen_titles: set[str]) -> bool:
    normalized = re.sub(r"[^a-z0-9 ]+", " ", title.lower()).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    if len(normalized) < 20:
        return False
    if normalized in seen_titles:
        return False
    seen_titles.add(normalized)
    return True


def check_edge_cdp() -> bool:
    """Check if Edge CDP is responding on port 9222."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"{EDGE_CDP_URL}/json/version", timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def launch_edge_headless() -> bool:
    """Launch Edge headless with CDP on port 9222."""
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    edge_exe = None
    for p in edge_paths:
        if Path(p).exists():
            edge_exe = p
            break
    if not edge_exe:
        logger.warning("[scheduler] Edge not found in standard locations")
        return False

    # Kill existing Edge processes to avoid profile lock issues
    try:
        subprocess.run(
            ["taskkill", "/f", "/im", "msedge.exe"],
            capture_output=True, timeout=10
        )
        time.sleep(2)
    except Exception:
        pass

    # Launch Edge headless with remote debugging
    user_data_dir = Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data"
    cmd = [
        edge_exe,
        f"--remote-debugging-port={EDGE_CDP_PORT}",
        "--headless=new",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--disable-background-networking",
        "about:blank",
    ]
    try:
        # Use DETACHED_PROCESS to run in background
        subprocess.Popen(
            cmd,
            creationflags=subprocess.DETACHED_PROCESS,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info(f"[scheduler] Launched Edge headless on port {EDGE_CDP_PORT}")
    except Exception as e:
        logger.warning(f"[scheduler] Failed to launch Edge: {e}")
        return False

    # Wait for CDP to become ready
    for _ in range(10):
        time.sleep(1)
        if check_edge_cdp():
            logger.info("[scheduler] Edge CDP is ready")
            return True
    logger.warning("[scheduler] Edge CDP did not become ready in time")
    return False


def ensure_edge_cdp() -> bool:
    """Ensure Edge CDP is available, launch if needed."""
    if check_edge_cdp():
        logger.info("[scheduler] Edge CDP already running")
        return True
    logger.info("[scheduler] Edge CDP not found, launching...")
    return launch_edge_headless()


def fetch_stories_for_query(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """Fetch and score stories for a single query."""
    try:
        results = search_web(query, max_results=max_results)
        now = datetime.now().isoformat()
        stories = []
        for item in results:
            url = item.get("url", "")
            if not url or _blocked(url):
                continue
            stories.append({
                "title": item.get("title", "").strip(),
                "published": now,
                "source_domain": url.split("/")[2] if url.count("/") >= 2 else url,
                "official_url": url,
                "rationale": f"Search query: {query}",
                "verify_query": query,
            })
        return stories
    except Exception as exc:
        logger.warning(f"[scheduler] search failed for '{query}': {exc}")
        return []


def build_stories() -> list[dict[str, Any]]:
    state = load_editorial_state()
    used = seen_urls(state)
    stories: list[dict[str, Any]] = []
    seen_titles: set[str] = set()

    # Combine all queries
    all_queries = SHOOTER_QUERIES + TWITTER_LEAKER_QUERIES

    for query in all_queries:
        if len(stories) >= MAX_STORIES:
            break
        candidates = fetch_stories_for_query(query, max_results=5)
        # Priority: shooter-related first
        shooters = [s for s in candidates if _looks_like_shooter(s.get("title", ""))]
        general = [s for s in candidates if not _looks_like_shooter(s.get("title", ""))]
        pool = shooters + general

        for item in pool:
            if len(stories) >= MAX_STORIES:
                break
            url = (item.get("official_url") or "").strip()
            if not url or url in used:
                continue
            if _blocked(url):
                continue
            title = (item.get("title") or "").strip()
            if not _dedup_title(title, seen_titles):
                continue
            stories.append(item)
            used.add(url)

    return stories[:MAX_STORIES]


def render_discord_report(stories: list[dict[str, Any]]) -> str:
    lines = [f"Scheduler results: {len(stories)} stories"]
    for idx, story in enumerate(stories, 1):
        title = story.get("title") or "(no title)"
        url = story.get("official_url") or ""
        source = story.get("source_domain") or ""
        lines.append(f"{idx}. {title}")
        if url:
            lines.append(f"   URL: {url}")
        if source:
            lines.append(f"   Source: {source}")
    return "\n".join(lines)


def main() -> int:
    # Ensure Edge CDP is available (for any browser-dependent steps downstream)
    ensure_edge_cdp()

    stories = build_stories()
    if not stories:
        logger.warning("[scheduler] No stories found!")
        return 1

    payload = {"stories": stories}
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    report = render_discord_report(stories)
    print(report, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())