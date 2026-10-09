#!/usr/bin/env bash
set -euo pipefail
uv sync --locked --no-dev
npm --prefix frontend ci --no-audit --no-fund
npm --prefix frontend run build
