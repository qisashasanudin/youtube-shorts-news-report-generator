#!/usr/bin/env python3
"""TikTok Content Posting API upload — OAuth + video upload + publish.

Usage (first run opens browser for auth):
    python src/scripts/tiktok_upload.py video.mp4 --title "Caption #gaming" --privacy public

Subsequent runs use saved token.json (auto-refreshes).
"""

from __future__ import annotations

import json
import sys
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread
from urllib.parse import urlencode, urlparse, parse_qs

import requests

REPO = Path(__file__).resolve().parents[2]
CLIENT_SECRETS = REPO / "tiktok_client_secrets.json"
TOKEN_FILE = REPO / "tiktok_token.json"

# TikTok API endpoints
AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
UPLOAD_CREATE_URL = "https://open.tiktokapis.com/v2/video/upload/"
UPLOAD_PUBLISH_URL = "https://open.tiktokapis.com/v2/video/publish/"
USER_INFO_URL = "https://open.tiktokapis.com/v2/user/info/"

# Required scopes for Content Posting API
SCOPES = [
    "user.info.basic",
    "video.upload",
    "video.publish",
]

# Redirect URI for local callback server
REDIRECT_URI = "http://localhost:8080/callback"
CALLBACK_PORT = 8080


class CallbackHandler(BaseHTTPRequestHandler):
    """Handles TikTok OAuth redirect and captures the auth code."""

    auth_code: str | None = None
    state: str | None = None
    error: str | None = None

    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)

        if "code" in query:
            CallbackHandler.auth_code = query["code"][0]
            CallbackHandler.state = query.get("state", [""])[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<h1>Success! You can close this window.</h1>")
        elif "error" in query:
            CallbackHandler.error = query["error"][0]
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"<h1>Error: {CallbackHandler.error}</h1>".encode())
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing code parameter")

    def log_message(self, format, *args):
        pass  # Suppress default logging


def _load_client_secrets() -> dict:
    if not CLIENT_SECRETS.exists():
        raise FileNotFoundError(
            f"{CLIENT_SECRETS} not found. Create it with your TikTok app's client_key and client_secret:\n"
            '{"client_key": "...", "client_secret": "..."}'
        )
    return json.loads(CLIENT_SECRETS.read_text(encoding="utf-8"))


def _save_token(token_data: dict) -> None:
    TOKEN_FILE.write_text(json.dumps(token_data, indent=2), encoding="utf-8")


def _load_token() -> dict | None:
    if TOKEN_FILE.exists():
        return json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    return None


def _refresh_access_token(client_key: str, client_secret: str, refresh_token: str) -> dict:
    """Refresh expired access token using refresh token."""
    data = {
        "client_key": client_key,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    resp = requests.post(TOKEN_URL, data=data, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _exchange_code_for_tokens(client_key: str, client_secret: str, auth_code: str) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    data = {
        "client_key": client_key,
        "client_secret": client_secret,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }
    resp = requests.post(TOKEN_URL, data=data, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _run_local_callback_server(state: str) -> str:
    """Start local server, open browser for auth, return auth code."""
    server = HTTPServer(("localhost", CALLBACK_PORT), CallbackHandler)
    CallbackHandler.auth_code = None
    CallbackHandler.error = None

    # Build auth URL
    secrets = _load_client_secrets()
    auth_params = {
        "client_key": secrets["client_key"],
        "scope": ",".join(SCOPES),
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "state": state,
    }
    auth_url = f"{AUTH_URL}?{urlencode(auth_params)}"

    print(f"🌐 Opening browser for TikTok authorization...")
    print(f"   If browser doesn't open, go to: {auth_url}")
    webbrowser.open(auth_url)

    # Wait for callback
    while CallbackHandler.auth_code is None and CallbackHandler.error is None:
        server.handle_request()

    server.server_close()

    if CallbackHandler.error:
        raise RuntimeError(f"TikTok auth error: {CallbackHandler.error}")

    if not CallbackHandler.auth_code:
        raise RuntimeError("No auth code received")

    print(f"✅ Got authorization code")
    return CallbackHandler.auth_code


def get_credentials() -> dict:
    """Get valid access token, refreshing or running OAuth flow as needed."""
    secrets = _load_client_secrets()
    client_key = secrets["client_key"]
    client_secret = secrets["client_secret"]

    token_data = _load_token()

    # Token exists and is valid
    if token_data and "access_token" in token_data:
        expires_at = token_data.get("expires_at", 0)
        if time.time() < expires_at - 60:  # 60s buffer
            return token_data

    # Token expired but we have refresh token
    if token_data and "refresh_token" in token_data:
        print("🔄 Refreshing access token...")
        new_tokens = _refresh_access_token(client_key, client_secret, token_data["refresh_token"])
        token_data.update(new_tokens)
        token_data["expires_at"] = time.time() + new_tokens.get("expires_in", 7200)
        _save_token(token_data)
        return token_data

    # No valid token — run full OAuth flow
    print("🔐 No valid token found. Starting OAuth flow...")
    import secrets as pysecrets
    state = pysecrets.token_urlsafe(16)
    auth_code = _run_local_callback_server(state)
    new_tokens = _exchange_code_for_tokens(client_key, client_secret, auth_code)
    new_tokens["expires_at"] = time.time() + new_tokens.get("expires_in", 7200)
    _save_token(new_tokens)
    return new_tokens


def _create_upload_session(access_token: str, video_size: int, chunk_size: int | None = None) -> dict:
    """Step 1: Create upload session, returns upload_url and video_id."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    # TikTok recommends chunk_size for large files; for Shorts (<500MB) single chunk is fine
    if chunk_size is None:
        chunk_size = video_size

    payload = {
        "media_type": "VIDEO",
        "media_source_info": {"source": "FILE_UPLOAD"},
        "video_size": video_size,
        "chunk_size": chunk_size,
    }
    resp = requests.post(UPLOAD_CREATE_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["data"]


def _upload_video_chunks(upload_url: str, video_path: Path, chunk_size: int) -> None:
    """Step 2: Upload video file in chunks to the upload_url."""
    file_size = video_path.stat().st_size
    uploaded = 0

    with video_path.open("rb") as f:
        while uploaded < file_size:
            chunk = f.read(chunk_size)
            if not chunk:
                break

            headers = {
                "Content-Range": f"bytes {uploaded}-{uploaded + len(chunk) - 1}/{file_size}",
                "Content-Type": "video/mp4",
            }
            resp = requests.put(upload_url, headers=headers, data=chunk, timeout=120)
            resp.raise_for_status()

            uploaded += len(chunk)
            print(f"[TIKTOK_UPLOAD] progress: {int(uploaded / file_size * 100)}%")


def _publish_video(access_token: str, video_id: str, title: str, privacy: str) -> dict:
    """Step 3: Publish the uploaded video."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }

    # Privacy mapping: PUBLIC, SELF_ONLY, FRIENDS, MUTUAL_FOLLOW_FRIENDS
    privacy_map = {
        "public": "PUBLIC",
        "private": "SELF_ONLY",
        "unlisted": "MUTUAL_FOLLOW_FRIENDS",  # closest equivalent
    }
    privacy_level = privacy_map.get(privacy.lower(), "PUBLIC")

    payload = {
        "post_info": {
            "title": title,
            "privacy_level": privacy_level,
            "disable_duet": False,
            "disable_stitch": False,
            "disable_comment": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_id": video_id,
        },
    }
    resp = requests.post(UPLOAD_PUBLISH_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["data"]


def upload(
    video_path: Path,
    title: str,
    description: str = "",
    privacy: str = "private",
) -> dict:
    """Upload video to TikTok via Content Posting API.

    Args:
        video_path: Path to MP4 file
        title: Caption/title (will be used as TikTok post text)
        description: Not used by TikTok API (kept for API compatibility)
        privacy: "public", "private", or "unlisted"

    Returns:
        Dict with publish_id and other response data
    """
    if not video_path.exists():
        raise FileNotFoundError(video_path)

    # Validate video size (TikTok limit: 500MB for Shorts)
    file_size = video_path.stat().st_size
    max_size = 500 * 1024 * 1024  # 500MB
    if file_size > max_size:
        raise ValueError(f"Video too large: {file_size / 1024 / 1024:.1f}MB > 500MB limit")

    # Get valid access token
    creds = get_credentials()
    access_token = creds["access_token"]

    print(f"📤 Uploading {video_path.name} ({file_size / 1024 / 1024:.1f}MB)...")

    # Step 1: Create upload session
    print("  [1/3] Creating upload session...")
    session = _create_upload_session(access_token, file_size)
    upload_url = session["upload_url"]
    video_id = session["video_id"]
    print(f"       video_id: {video_id}")

    # Step 2: Upload video chunks
    print("  [2/3] Uploading video...")
    chunk_size = session.get("chunk_size", file_size)
    _upload_video_chunks(upload_url, video_path, chunk_size)

    # Step 3: Publish
    print("  [3/3] Publishing...")
    result = _publish_video(access_token, video_id, title, privacy)
    publish_id = result.get("publish_id")
    print(f"✅ Published! publish_id: {publish_id}")

    return result


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(
            "Usage: python src/scripts/tiktok_upload.py <video_path> "
            "[--title <caption>] [--privacy public|private|unlisted] [--description <text>]"
        )
        return 1

    video_path = Path(args[0])
    title = video_path.stem
    privacy = "private"
    description = ""

    it = iter(args[1:])
    for arg in it:
        if arg == "--title":
            try:
                title = next(it)
            except StopIteration:
                print("Error: --title requires a value")
                return 1
        elif arg == "--privacy":
            try:
                privacy = next(it)
            except StopIteration:
                print("Error: --privacy requires a value")
                return 1
        elif arg == "--description":
            try:
                description = next(it)
            except StopIteration:
                print("Error: --description requires a value")
                return 1

    try:
        result = upload(video_path=video_path, title=title, description=description, privacy=privacy)
        print(json.dumps(result, indent=2)[:4000])
        return 0
    except Exception as e:
        print(f"❌ Upload failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())