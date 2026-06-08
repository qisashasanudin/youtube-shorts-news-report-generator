from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STATE_FILE = REPO / "editorial_state.json"


def _load() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"used_stories": [], "daily_uploads": {}}


def _save(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _normalize(text: str) -> str:
    return " ".join(text.lower().replace("-", " ").split())


def is_duplicate(title: str, url: str, state: dict) -> bool:
    nt = _normalize(title)
    for story in state.get("used_stories", []):
        if url and story.get("url") and story["url"] == url:
            return True
        if nt and _normalize(story.get("title", "")) == nt:
            return True
    return False


def daily_count(state: dict, date_str: str) -> int:
    return int(state.get("daily_uploads", {}).get(date_str, 0))


def increment_daily(state: dict, date_str: str) -> None:
    state.setdefault("daily_uploads", {})[date_str] = daily_count(state, date_str) + 1


def mark_used(state: dict, title: str, url: str, date_str: str) -> None:
    state.setdefault("used_stories", []).append({"title": title, "url": url or "", "date": date_str})


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python src/editorial_state.py <check|count|mark> [args]")
        return 1

    cmd = sys.argv[1]
    state = _load()
    today = datetime.now().strftime("%Y-%m-%d")

    if cmd == "check":
        title = sys.argv[2] if len(sys.argv) > 2 else ""
        url = sys.argv[3] if len(sys.argv) > 3 else ""
        print("true" if is_duplicate(title, url, state) else "false")
    elif cmd == "count":
        print(daily_count(state, today))
    elif cmd == "mark":
        title = sys.argv[2] if len(sys.argv) > 2 else ""
        url = sys.argv[3] if len(sys.argv) > 3 else ""
        mark_used(state, title, url, today)
        increment_daily(state, today)
        _save(state)
        print(daily_count(state, today))
    else:
        print(f"Unknown command: {cmd}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
