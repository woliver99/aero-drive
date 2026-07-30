#!/usr/bin/env bash
set -e

IMAGE_NAME="aerodrive:latest"
CONTAINER_NAME="aerodrive"
PORT="${PORT:-8080}"

echo "[AeroDrive] Building container image..."
sudo podman build -t "$IMAGE_NAME" .

echo "[AeroDrive] Cleaning up any existing container named '$CONTAINER_NAME'..."
sudo podman rm -f "$CONTAINER_NAME" 2>/dev/null || true

echo "[AeroDrive] Starting container on port $PORT..."
mkdir -p aerodrive_data
sudo podman run --rm -d \
  --name "$CONTAINER_NAME" \
  -p "${PORT}:8080" \
  -e BASE_URL="${BASE_URL:-}" \
  -v ./aerodrive_data:/var/lib/aerodrive \
  "$IMAGE_NAME"

echo ""
echo "========================================================="
echo " AeroDrive server started successfully!"
echo " WebDAV Endpoint: https://localhost:${PORT}"
echo ""
echo " Manage users and passwords via container exec:"
echo "   sudo podman exec -it $CONTAINER_NAME aerodrive user add <username>"
echo "   sudo podman exec -it $CONTAINER_NAME aerodrive password add <username> <password> [note]"
echo "========================================================="
