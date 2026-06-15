from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CLIENT_SECRETS = REPO / "client_secrets.json"
TOKEN_FILE = REPO / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
]


def _load_client_secrets() -> dict:
    if not CLIENT_SECRETS.exists():
        raise FileNotFoundError(CLIENT_SECRETS)
    return json.loads(CLIENT_SECRETS.read_text(encoding="utf-8"))


def _build_flow():
    from google_auth_oauthlib.flow import InstalledAppFlow

    return InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)


def _refresh_if_needed(creds):
    from google.auth.transport.requests import Request

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())


def get_credentials():
    creds = None
    if TOKEN_FILE.exists():
        from google.oauth2.credentials import Credentials

        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired:
        _refresh_if_needed(creds)
        if creds.valid:
            TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
            return creds

    flow = _build_flow()
    creds = flow.run_local_server(port=0)
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return creds


def _get_channel_id(service) -> str:
    resp = service.channels().list(part="id", mine=True).execute()
    items = resp.get("items") or []
    if not items:
        raise RuntimeError("No channel found for authenticated user")
    return items[0]["id"]


def fetch_analytics(channel_id: str, start: str, end: str, metrics: str, dimensions: str | None = None, filters: str | None = None):
    from googleapiclient.discovery import build

    creds = get_credentials()
    service = build("youtubeAnalytics", "v2", credentials=creds)

    body = {
        "ids": f"channel=={channel_id}",
        "startDate": start,
        "endDate": end,
        "metrics": metrics,
    }
    if dimensions:
        body["dimensions"] = dimensions
    if filters:
        body["filters"] = filters

    return service.reports().query(**body).execute()


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch YouTube Analytics for MashButtonGaming")
    ap.add_argument("--days", type=int, default=7, help="Lookback window in days")
    ap.add_argument("--start", help="Explicit start date YYYY-MM-DD")
    ap.add_argument("--end", help="Explicit end date YYYY-MM-DD")
    ap.add_argument("--metrics", default="views,estimatedMinutesWatched,averageViewDuration,comments,likes,dislikes,shares,subscribersGained,subscribersLost", help="Comma-separated analytics metrics")
    ap.add_argument("--dimensions", default=None)
    ap.add_argument("--filters", default=None)
    args = ap.parse_args()

    end = args.end or datetime.utcnow().strftime("%Y-%m-%d")
    start = args.start or (datetime.utcnow() - timedelta(days=args.days)).strftime("%Y-%m-%d")

    try:
        creds = get_credentials()
        from googleapiclient.discovery import build

        service = build("youtube", "v3", credentials=creds)
        channel_id = _get_channel_id(service)
        report = fetch_analytics(
            channel_id=channel_id,
            start=start,
            end=end,
            metrics=args.metrics,
            dimensions=args.dimensions,
            filters=args.filters,
        )
    except Exception as exc:
        print(f"[ERROR] analytics fetch failed: {exc}")
        return 2

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
