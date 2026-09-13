#!/usr/bin/env bash
# Start the operator console (port 5000 — what Replit's Preview shows) and the mock credit-union
# app it drives (port 5001). Ctrl+C, or stopping Replit's Run, stops both.
set -euo pipefail
cd "$(dirname "$0")/.."

# Fictional demo operator for the mock app. Real targets must supply these as secrets.
export CUA_USERNAME="${CUA_USERNAME:-teller1}"
export CUA_PASSWORD="${CUA_PASSWORD:-teller-demo-pass}"

uv sync --quiet
trap 'kill 0' EXIT
uv run --no-sync python -m mock_app --port 5001 &
uv run --no-sync python -m cua.console --port 5000 --target-url http://127.0.0.1:5001
