#!/usr/bin/env bash
# Load test for GET /search; prints the p95 line the loop greps for.
# About a minute at current latency.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHONPATH=. python3 scripts/load.py
