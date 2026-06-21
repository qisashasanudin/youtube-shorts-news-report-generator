#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF' >&2
Usage: ./run_short_builder.sh --url "<youtube-url>" --title "<TITLE>" --subtitle "<50-150 word narration>"

This wrapper ensures the script runs with python3 and maps --url to the shorts builder's --youtube option.
EOF
  exit 1
}

URL=""
TITLE=""
SUBTITLE=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --youtube=*) URL="${1#*=}" ;;
    --youtube)
      shift
      URL="${1:-}"
      ;;
    --url=*) URL="${1#*=}" ;;
    --url)
      shift
      URL="${1:-}"
      ;;
    --title=*) TITLE="${1#*=}" ;;
    --title)
      shift
      TITLE="${1:-}"
      ;;
    --subtitle=*) SUBTITLE="${1#*=}" ;;
    --subtitle)
      shift
      SUBTITLE="${1:-}"
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      ;;
  esac
  shift
done

if [ -z "$URL" ] || [ -z "$TITLE" ] || [ -z "$SUBTITLE" ]; then
  echo "Error: --url, --title, and --subtitle are required." >&2
  usage
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is not installed or not on PATH." >&2
  exit 1
fi

exec python3 src/shorts_builder.py --youtube "$URL" --title "$TITLE" --subtitle "$SUBTITLE"
