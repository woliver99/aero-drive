#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "[MapleDrive] Starting container via compose..."
mkdir -p mapledrive_data

podman compose up --build -d

echo ""
echo "========================================================="
echo " MapleDrive server started successfully!"
echo " WebDAV Endpoint: https://127.0.0.1:8080"
echo "========================================================="
