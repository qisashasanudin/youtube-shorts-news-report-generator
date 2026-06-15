from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

REPO = Path(__file__).resolve().parents[2]
LOG_FILE = REPO / "analytics_log.json"


def _load_log() -> dict:
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text(encoding="utf-8"))
    return {"videos": {}}


def _save_log(log: dict) -> None:
    LOG_FILE.write_text(json.dumps(log, indent=2), encoding="utf-8")


def _int(value: str | int | None) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _get_credentials():
    scopes = [
        "https://www.googleapis.com/auth/youtube.readonly",
    ]
    creds = None
    token_file = REPO / "token.json"
    secrets_file = REPO / "client_secrets.json"
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if not creds or not creds.valid:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(str(secrets_file), scopes)
            creds = flow.run_local_server()
        token_file.write_text(creds.to_json(), encoding="utf-8")
    return creds


def log_metrics(video_id: str) -> dict[str, Any]:
    creds = _get_credentials()
    service = build("youtube", "v3", credentials=creds)
    resp = service.videos().list(part="snippet,statistics", id=video_id).execute()
    items = resp.get("items") or []
    if not items:
        raise RuntimeError(f"Video not found: {video_id}")

    item = items[0]
    snippet = item.get("snippet", {})
    statistics = item.get("statistics", {})

    now = datetime.now(timezone.utc).isoformat()
    record = {
        "video_id": video_id,
        "title": snippet.get("title"),
        "channel_id": snippet.get("channelId"),
        "published_at": snippet.get("publishedAt"),
        "last_checked": now,
        "metrics": {
            "views": _int(statistics.get("viewCount")),
            "likes": _int(statistics.get("likeCount")),
            "dislikes": _int(statistics.get("dislikeCount")),
            "comments": _int(statistics.get("commentCount")),
            "favorites": _int(statistics.get("favoriteCount")),
        },
    }

    log = _load_log()
    log["videos"][video_id] = record
    _save_log(log)
    return record


def main() -> int:
    ap = argparse.ArgumentParser(description="Log YouTube per-video metrics into analytics_log.json")
    ap.add_argument("video_id", help="YouTube video ID")
    args = ap.parse_args()

    record = log_metrics(args.video_id)
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
