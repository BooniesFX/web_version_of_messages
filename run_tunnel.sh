#!/usr/bin/env bash
set -euo pipefail

APP_HOST="127.0.0.1"
APP_PORT="5000"

# Load .env overrides if present
if [[ -f ".env" ]]; then
  # shellcheck disable=SC1091
  set -a
  source ".env"
  set +a
fi

APP_HOST="${APP_IP:-$APP_HOST}"
APP_PORT="${APP_PORT:-$APP_PORT}"
APP_URL="http://${APP_HOST}:${APP_PORT}"

# Start Flask app in background
uv run app.py > app.log 2>&1 &
APP_PID=$!

cleanup() {
  echo "Stopping app (pid $APP_PID)..."
  kill "$APP_PID" 2>/dev/null || true
}
trap cleanup EXIT

# Wait for app to become ready
for i in {1..60}; do
  if curl -fsS "$APP_URL" >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "$APP_PID" 2>/dev/null; then
    echo "App failed to start. Check app.log"
    exit 1
  fi
  sleep 0.5
done

# Start Cloudflare tunnel in foreground (force http2 to avoid QUIC issues)
cloudflared tunnel --protocol http2 --url "$APP_URL"
