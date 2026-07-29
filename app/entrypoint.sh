#!/bin/sh
set -e

DATA_DIR="${AERODRIVE_DATA_DIR:-/var/lib/aerodrive}"
CONFIG_DIR="$DATA_DIR/config"
USERS_DIR="$DATA_DIR/users"

mkdir -p "$CONFIG_DIR" "$USERS_DIR"

# 1. Generate TLS certs if missing
if [ ! -f "$CONFIG_DIR/cert.pem" ] || [ ! -f "$CONFIG_DIR/key.pem" ]; then
  echo "[AeroDrive] Generating self-signed TLS certificates..."
  openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout "$CONFIG_DIR/key.pem" \
    -out "$CONFIG_DIR/cert.pem" \
    -subj "/CN=aerodrive.local" >/dev/null 2>&1
fi

# 2. Initialize database if missing
if [ ! -f "$CONFIG_DIR/users.json" ]; then
  echo '[AeroDrive] Initializing empty users.json...'
  echo '{"users": {}}' > "$CONFIG_DIR/users.json"
fi

# 3. Start Rclone Engine
echo "[AeroDrive] Server starting on port ${PORT:-8080}..."
exec rclone serve webdav \
  --addr ":${PORT:-8080}" \
  --cert "$CONFIG_DIR/cert.pem" \
  --key "$CONFIG_DIR/key.pem" \
  --auth-proxy "/app/auth.py"
