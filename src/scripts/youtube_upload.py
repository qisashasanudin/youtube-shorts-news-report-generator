from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CLIENT_SECRETS = REPO / "client_secrets.json"
TOKEN_FILE = REPO / "token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


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


def upload(
    video_path: Path,
    title: str,
    description: str,
    tags: list[str] | None = None,
    privacy: str = "private",
):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    if not video_path.exists():
        raise FileNotFoundError(video_path)

    creds = get_credentials()
    service = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": "24",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
    )

    request = service.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )

    response: dict | None = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[YT_UPLOAD] progress: {int(status.progress() * 100)}%")

    return response


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: python src/scripts/youtube_upload.py <video_path> [--title <title>] [--privacy private|public|unlisted] [--description <text>] [--tags a,b,c]")
        return 1

    video_path = Path(args[0])
    title = video_path.stem
    privacy = "private"
    description = title
    tags: list[str] = []

    it = iter(args[1:])
    for arg in it:
        if arg == "--title" and args:
            title = next(it)
        elif arg == "--privacy" and args:
            privacy = next(it)
        elif arg == "--description" and args:
            description = next(it)
        elif arg == "--tags" and args:
            tags = next(it).split(",")

    result = upload(video_path=video_path, title=title, description=description, tags=tags, privacy=privacy)
    print(json.dumps(result, indent=2)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
