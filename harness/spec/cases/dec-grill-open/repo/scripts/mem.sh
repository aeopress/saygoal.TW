#!/usr/bin/env bash
# Prints peak RSS of one indexer run.
set -euo pipefail
cd "$(dirname "$0")/.."
/usr/bin/time -l python -m src.indexer README.md 2>&1 >/dev/null | awk '/maximum resident set size/ {printf "peak_rss_mb=%d\n", $1/1048576}'
