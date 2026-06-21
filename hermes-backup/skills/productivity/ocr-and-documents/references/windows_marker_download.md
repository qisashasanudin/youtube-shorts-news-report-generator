# Windows marker-pdf model download behavior

## Cache location on Windows
`marker` / `datalab` caches models under:
`C:\Users\<user>\AppData\Local\datalab\datalab\Cache\models\layout\<date_tag>\`

## First-run model size
First extraction can download a ~1.35GB `model.safetensors` file plus layout assets. Low-speed connections or CPU-only Windows hosts can make this exceed typical single-run timeouts.

## Practical options for large downloads
- Run extraction in background with `notify_on_complete=true` instead of blocking.
- Pre-warm once by running a small extract; then later runs reuse cached models.
- If connectivity is very slow, consider uploading to a URL and using `web_extract` first-choice behavior for online-capable environments.
