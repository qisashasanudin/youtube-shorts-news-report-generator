#!/usr/bin/env python3
"""Re-auth helper to upgrade YouTube OAuth token with analytics scopes."""

from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

PROJECT_ROOT = Path(__file__).resolve().parent
CLIENT_SECRETS_FILE = PROJECT_ROOT / "client_secrets.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
]

def main() -> int:
    if not CLIENT_SECRETS_FILE.exists():
        print(f"Missing client_secrets.json at: {CLIENT_SECRETS_FILE}")
        return 1

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        refreshed = False
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                refreshed = True
            except Exception as exc:
                print(f"Refresh failed: {exc}")
                creds = None

        if not refreshed or not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
            creds = flow.run_local_server(open_browser=True)

    TOKEN_FILE.write_text(creds.to_json(), encoding='utf-8')
    print(f"Saved token with scopes: {creds.scopes}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

