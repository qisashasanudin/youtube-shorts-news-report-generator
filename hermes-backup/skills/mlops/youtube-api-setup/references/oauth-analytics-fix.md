# OAuth Analytics Fix Notes

Problem: `youtube_analytics.py` returned 403 insufficient scope even after reauth attempt.
- Current token had: `https://www.googleapis.com/auth/youtube.upload`.
- Token appeared `creds.valid == True` and short-circuited re-auth.
- Refresh attempt raised `google.auth.exceptions.RefreshError: ('invalid_scope: Bad Request', ...)`.
- Root cause: token was valid for upload but NOT for analytics scopes.
- Fix: check `need_scopes.issubset(have_scopes)` before exiting early, and skip refresh on `invalid_scope`, going straight to `run_console()`.

Windows/terminal path trap:
- `Path(__file__).resolve().parents[n]` can resolve differently in Git Bash/MSYS.
- Result: `client_secrets.json` looked up in wrong directory before absolute path fix.
- Rule: prefer explicit absolute paths when the script must find files relative to its own location.

Channel-specific rule references:
- editorial_state.json: mark uploads after each successful upload.
- youtube_upload.py: strip hashtags from title, move into description/tags.
