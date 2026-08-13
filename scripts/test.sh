#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "========================================================="
echo " Running MapleDrive Integration Test Suite"
echo "========================================================="

python3 -m unittest discover -s tests -v "$@"
