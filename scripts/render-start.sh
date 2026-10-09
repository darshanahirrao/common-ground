#!/usr/bin/env bash
set -euo pipefail
exec .venv/bin/uvicorn common_ground.api:app --host 0.0.0.0 --port "${PORT:-10000}" --workers 1 --no-access-log
