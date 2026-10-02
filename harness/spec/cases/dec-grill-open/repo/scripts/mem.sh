#!/usr/bin/env bash
# Prints peak RSS of one indexer run over the reference corpus.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/make_corpus.py data/corpus
/usr/bin/time -l python3 -m src.indexer data/corpus/*.txt 2>&1 >/dev/null | awk '/maximum resident set size/ {printf "peak_rss_mb=%d\n", $1/1048576}'
