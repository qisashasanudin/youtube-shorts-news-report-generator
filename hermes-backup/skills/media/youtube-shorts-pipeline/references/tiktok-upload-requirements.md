# TikTok Upload Module Requirements

Documenting the requirements and design for a future `src/scripts/tiktok_upload.py` module, mirroring the existing `youtube_upload.py` pattern.

## Current Status (2026-06-09)

- **TikTok app**: "mashbuttongaming-uploader" created on developer.tiktok.com
- **Environment**: Sandbox (Production pending review)
- **Credentials**: Client Key + Client Secret available
- **Products needed**: Content Posting API
- **Scopes needed**: `video.upload`, `video.publish`, `user.info.basic`
- **Redirect URI**: `http://localhost:8080/callback` (dev) + production HTTPS domain
- **App Review**: Requires demo video showing full OAuth → upload → publish flow in Sandbox

## OAuth Flow (TikTok)

```
# 1. User authorization (browser)
https://www.tiktok.com/v2/auth/authorize/
  ?client_key={CLIENT_KEY}
  &scope=user.info.basic,video.upload,video.publish
  &response_type=code
  &redirect_uri=http://localhost:8080/callback
  &state={RANDOM_STATE}

# 2. Token exchange
POST https://open.tiktokapis.com/v2/oauth/token/
client_key={CLIENT_KEY}&client_secret={CLIENT_SECRET}&code={AUTH_CODE}&grant_type=authorization_code&redirect_uri={REDIRECT_URI}

# Response: access_token (2h), refresh_token (1yr), open_id
```

## Video Upload Flow (2-step)

```python
# Step 1: Create upload session
POST https://open.tiktokapis.com/v2/video/upload/
Authorization: Bearer {access_token}
{
  "media_type": "VIDEO",
  "media_source_info": {"source": "FILE_UPLOAD"},
  "video_size": 12345678,
  "chunk_size": 12345678  # or smaller for chunked upload
}

# Response: upload_url, video_id

# Step 2: Upload video chunks
PUT {upload_url}
Content-Range: bytes 0-12345677/12345678
Content-Type: video/mp4
<binary video data>

# Step 3: Publish
POST https://open.tiktokapis.com/v2/video/publish/
Authorization: Bearer {access_token}
{
  "post_info": {
    "title": "Caption #gaming #shorts",
    "privacy_level": "PUBLIC",
    "disable_duet": false,
    "disable_stitch": false,
    "disable_comment": false
  },
  "source_info": {"source": "FILE_UPLOAD", "video_id": "{VIDEO_ID}"}
}
```

## Token Storage Design

Mirror `youtube_upload.py` pattern:
- `tiktok_token.json` in project root: `{client_key, client_secret, access_token, refresh_token, expires_at, open_id, scopes}`
- Auto-refresh when `expires_at < now + 60s`
- Refresh endpoint: `POST /v2/oauth/token/` with `grant_type=refresh_token`

## CLI Interface (matching youtube_upload.py)

```bash
python src/scripts/tiktok_upload.py video.mp4 --title "Caption #gaming #shorts" --privacy public
```

Args:
- `video_path` (positional)
- `--title` — caption text (hashtags extracted for tags)
- `--privacy` — `PUBLIC` | `SELF_ONLY` | `FRIENDS` | `MUTUAL_FOLLOW_FRIENDS`
- `--description` — optional, appended to title
- `--tags` — comma-separated, merged with title hashtags

## Constraints & Limits

| Limit | Value |
|-------|-------|
| Video size | ≤ 500 MB |
| Duration | 3s – 10min (Shorts: ≤ 60s) |
| Resolution | 720p+ recommended |
| Format | MP4, MOV |
| Rate limit (sandbox) | ~100 req/day/user |
| Rate limit (prod) | Higher, undocumented |
| Access token TTL | 2 hours |
| Refresh token TTL | 1 year |

## Demo Video Requirements (App Review)

Must record screen capture showing:
1. App UI initiating TikTok OAuth login
2. User granting permissions (scopes above)
3. App uploading video via Content Posting API
4. Video appearing on TikTok profile
- Must use **Sandbox** environment
- Format: MP4/MOV, ≤ 50MB, max 5 files
- Domain in video must match redirect URI domain

## Next Steps

1. Add Content Posting API + scopes in TikTok Developer Portal
2. Fill all required Basic Information fields (icon, description, ToS, Privacy Policy, category)
3. Build minimal OAuth + upload test in Sandbox
4. Record demo video
5. Submit for review
6. After approval → build `src/scripts/tiktok_upload.py`

## References

- TikTok Content Posting API docs: https://developers.tiktok.com/doc/content-posting-api
- OAuth 2.0 guide: https://developers.tiktok.com/doc/login-kit-web
- App Review guidelines: https://developers.tiktok.com/doc/app-review-guidelines