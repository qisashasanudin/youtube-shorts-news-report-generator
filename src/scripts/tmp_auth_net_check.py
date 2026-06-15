from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parents[1]
CLIENT_SECRETS = REPO / "client_secrets.json"
TOKEN_FILE = REPO / "token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def load_client_secrets() -> dict:
    return json.loads(CLIENT_SECRETS.read_text(encoding="utf-8"))


def build_auth_flow():
    from google_auth_oauthlib.flow import InstalledAppFlow

    return InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)


def refresh_credentials(creds) -> None:
    from google.auth.transport.requests import Request

    creds.refresh(Request())


def resolve_credentials():
    creds = None
    if TOKEN_FILE.exists():
        from google.oauth2.credentials import Credentials

        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        refresh_credentials(creds)
        if creds.valid:
            TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
            return creds

    flow = build_auth_flow()
    creds = flow.run_local_server(port=0)
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return creds


def test_network() -> None:
    print("[NETWORK] start")
    resp = requests.get("https://www.google.com/generate_204", timeout=20)
    print("[NETWORK] status=", resp.status_code, sep="")
    print("[NETWORK] end")


def test_youtube_channel() -> None:
    print("[YT] start")
    creds = resolve_credentials()
    from googleapiclient.discovery import build

    service = build("youtube", "v3", credentials=creds)
    response = service.channels().list(part="id,snippet", mine=True).execute()
    print("[YT] response_items=", len(response.get("items", [])), sep="")
    if response.get("items"):
        print("[YT] channel_id=", response["items"][0]["id"], sep="")
    print("[YT] end")


def main() -> int:
    test_network()
    test_youtube_channel()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
