#!/usr/bin/env bash
# Archive one seed of the Layer 2 behavioral eval.
#
# run-spec.sh overwrites runs/<case>/output.txt on every pass, so a multi-seed
# pass-rate measurement needs the outputs kept. This wrapper runs the cases for
# one seed and copies each output to runs/scale/<case>/seed<N>.txt, where
# score_scale.py can score them all without re-spending tokens.
#
# Usage:
#   harness/spec/scale-run.sh <seed> [case_id ...]     # defaults to all cases
#   MAX_USD=4.00 harness/spec/scale-run.sh 3 dec-search
#
# Run in the FOREGROUND: a nested `claude -p` launched from a Claude Code
# background task is killed silently (empty output, empty stderr).

set -euo pipefail

SPEC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEED="${1:-}"
[ -n "$SEED" ] || { echo "usage: scale-run.sh <seed> [case_id ...]" >&2; exit 2; }
shift

if [ $# -eq 0 ]; then
  set -- $(cd "$SPEC/cases" && for d in */; do echo "${d%/}"; done)
fi

export MAX_USD="${MAX_USD:-4.00}"

for CASE in "$@"; do
  DEST="$SPEC/runs/scale/$CASE"
  mkdir -p "$DEST"
  if [ -s "$DEST/seed$SEED.txt" ]; then
    echo "[scale] $CASE seed$SEED already archived — skipping"
    continue
  fi
  "$SPEC/run-spec.sh" "$CASE"
  SRC="$SPEC/runs/$CASE/output.txt"
  if [ -s "$SRC" ]; then
    cp "$SRC" "$DEST/seed$SEED.txt"
    echo "[scale] archived $CASE seed$SEED ($(wc -c < "$SRC" | tr -d ' ') bytes)"
  else
    # An empty output means the run itself failed (budget, network, nesting).
    # Record it as such rather than scoring a blank file as a content failure.
    echo "EMPTY_RUN" > "$DEST/seed$SEED.txt"
    echo "[scale] WARNING: $CASE seed$SEED produced no output — marked EMPTY_RUN" >&2
  fi
done
