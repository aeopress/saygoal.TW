#!/usr/bin/env bash
# Behavioral eval runner for the saygoal commands.
#
# Expands a command file (dec.md / retro.md) with a case's arguments the way a
# slash command would, feeds it to `claude -p`, and captures the emitted
# contract. Scoring is done separately by score_spec.py (pure grep on output).
#
# Usage:
#   harness/spec/run-spec.sh <case_id> [more_case_ids...]
#   harness/spec/run-spec.sh all
#   MODEL=claude-opus-4-8 harness/spec/run-spec.sh dec-search
#   MODEL=claude-opus-5-5 EFFORT=xhigh harness/spec/run-spec.sh all
#
# Notes:
#   - Each run gets a throwaway copy of the case's fixture repo, and Bash is
#     enabled inside it so /dec can smoke-check its verification commands the
#     way it would in a real session. Edit/Write stay disabled: these commands
#     emit text, they don't implement. Whatever Bash writes (.venv, generated
#     data) lands in the copy, which is deleted after the run.
#   - Output goes to harness/spec/runs/<case_id>/output.txt (gitignored).
#   - Needs network + a working `claude` CLI; run outside the sandbox.

set -euo pipefail

SPEC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SPEC/../.." && pwd)"
CASES_DIR="$SPEC/cases"
RUNS_DIR="$SPEC/runs"

if [ "${1:-}" = "all" ]; then
  set -- $(cd "$CASES_DIR" && for d in */; do echo "${d%/}"; done)
fi

[ $# -ge 1 ] || { echo "usage: run-spec.sh <case_id> [...] | all" >&2; exit 2; }

for CASE in "$@"; do
  CASE_DIR="$CASES_DIR/$CASE"
  [ -d "$CASE_DIR" ] || { echo "[run-spec] no such case: $CASE" >&2; exit 2; }

  COMMAND=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['command'])" "$CASE_DIR/meta.json")
  CMD_FILE="$ROOT/plugin/commands/${COMMAND}.md"
  [ -f "$CMD_FILE" ] || { echo "[run-spec] missing command file: $CMD_FILE" >&2; exit 2; }

  RUN_DIR="$RUNS_DIR/$CASE"
  mkdir -p "$RUN_DIR"

  ARGS=$(cat "$CASE_DIR/prompt.txt")

  # Expand $ARGUMENTS the way the slash command would. Use python to avoid
  # sed metacharacter hazards in the argument text.
  PROMPT=$(python3 - "$CMD_FILE" <<PY
import sys
body = open(sys.argv[1], encoding="utf-8").read()
args = open("$CASE_DIR/prompt.txt", encoding="utf-8").read().strip()
print(body.replace("\$ARGUMENTS", args))
PY
)

  printf '%s' "$PROMPT" > "$RUN_DIR/expanded_prompt.md"

  # /dec verifies its verification target against the filesystem, so run inside
  # a fresh copy of the case's fixture repo. A copy, not the repo itself: with
  # Bash enabled the model may run `uv sync`, a bench, or a data generator, and
  # none of that may leak into the next run. Not a git repo, so `git` fails
  # cleanly instead of reading the saygoal checkout around the fixtures.
  WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/saygoal-spec-$CASE.XXXXXX")"
  if [ -d "$CASE_DIR/repo" ]; then
    rsync -a --exclude .venv --exclude __pycache__ --exclude .pytest_cache \
      --exclude data "$CASE_DIR/repo/" "$WORKDIR/"
  fi

  echo "[run-spec] $CASE  (command=/$COMMAND, model=${MODEL:-<cli default>}, effort=${EFFORT:-<cli default>}, cwd=<copy of cases/$CASE/repo>)"

  set +e
  MODEL_ARG=()
  [ -n "${MODEL:-}" ] && MODEL_ARG=(--model "$MODEL")
  # Without EFFORT the run inherits the CLI's saved default, which differs by
  # machine and model — pin it when a run is meant to be compared.
  EFFORT_ARG=()
  [ -n "${EFFORT:-}" ] && EFFORT_ARG=(--effort "$EFFORT")
  ( cd "$WORKDIR" && printf '%s' "$PROMPT" | claude -p \
    ${MODEL_ARG[@]+"${MODEL_ARG[@]}"} \
    ${EFFORT_ARG[@]+"${EFFORT_ARG[@]}"} \
    --max-budget-usd "${MAX_USD:-1.00}" \
    --output-format text \
    --disallowed-tools "WebSearch,WebFetch,Task,Skill,Edit,Write" \
    --permission-mode bypassPermissions \
    --no-session-persistence \
    > "$RUN_DIR/output.txt" 2> "$RUN_DIR/stderr.log" )
  EXIT=$?
  set -e
  rm -rf "$WORKDIR"

  echo "[run-spec] $CASE  exit=$EXIT  $(wc -c < "$RUN_DIR/output.txt" | tr -d ' ') bytes → $RUN_DIR/output.txt"
done
