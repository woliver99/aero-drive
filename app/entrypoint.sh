#!/bin/sh
set -e

DATA_DIR="${DATA_DIR:-/var/lib/maple-drive}"
CONFIG_DIR="$DATA_DIR/config"
USERS_DIR="$DATA_DIR/users"

mkdir -p "$CONFIG_DIR" "$USERS_DIR"

# 1. Generate TLS certs if missing
if [ ! -f "$CONFIG_DIR/cert.pem" ] || [ ! -f "$CONFIG_DIR/key.pem" ]; then
  echo "[MapleDrive] Generating self-signed TLS certificates..."
  openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout "$CONFIG_DIR/key.pem" \
    -out "$CONFIG_DIR/cert.pem" \
    -subj "/CN=mapledrive.local" >/dev/null 2>&1
fi

# 2. Initialize database if missing
if [ ! -f "$CONFIG_DIR/users.json" ]; then
  echo '[MapleDrive] Initializing empty users.json...'
  echo '{"users": {}}' > "$CONFIG_DIR/users.json"
fi

# 3. Start Rclone Engine
echo "[MapleDrive] Server starting on port ${PORT:-8080}..."
BASE_URL_ARG=""
if [ -n "$BASE_URL" ]; then
  echo "[MapleDrive] Serving at Base URL path: $BASE_URL"
  BASE_URL_ARG="--baseurl $BASE_URL"
fi

exec rclone serve webdav \
  --addr ":${PORT:-8080}" \
  --cert "$CONFIG_DIR/cert.pem" \
  --key "$CONFIG_DIR/key.pem" \
  --auth-proxy "/app/auth.py" \
  $BASE_URL_ARG
