#!/usr/bin/env python3
"""Score behavioral-eval outputs against each case's oracle (pure grep, no LLM).

Reads harness/spec/runs/<case>/output.txt (produced by run-spec.sh) and applies
the case's oracle.json: every `must_contain` regex must match, every
`must_not_contain` regex must NOT match. Deterministic — same output, same
verdict.

Usage:
  python3 harness/spec/score_spec.py                 # score every case that has a run
  python3 harness/spec/score_spec.py dec-search      # score one case

Exit status is 1 if any scored case fails, 0 otherwise — but note the honesty
caveat in harness/spec/README.md: a single LLM run is one noisy sample, not a
verdict. Per this repo's own EXPERIMENT.md, treat N<10 as uncertain.
"""

import json
import re
import sys
from pathlib import Path

SPEC = Path(__file__).resolve().parent
CASES = SPEC / "cases"
RUNS = SPEC / "runs"

wanted = sys.argv[1:] or sorted(p.name for p in CASES.iterdir() if p.is_dir())

any_fail = False
scored = 0
print("=== saygoal command behavioral eval ===\n")

for case in wanted:
    out = RUNS / case / "output.txt"
    oracle_p = CASES / case / "oracle.json"
    if not oracle_p.exists():
        print(f"[skip] {case}: no oracle.json")
        continue
    if not out.exists():
        print(f"[skip] {case}: no run yet (run-spec.sh {case})")
        continue

    text = out.read_text(encoding="utf-8")
    oracle = json.loads(oracle_p.read_text(encoding="utf-8"))
    scored += 1

    lines = []
    case_ok = True
    for item in oracle.get("must_contain", []):
        hit = bool(re.search(item["regex"], text))
        case_ok &= hit
        lines.append(f"    [{'✓' if hit else '✗'}] contains  {item['signal']}")
    for item in oracle.get("must_not_contain", []):
        hit = bool(re.search(item["regex"], text))
        case_ok &= not hit
        lines.append(f"    [{'✓' if not hit else '✗'}] absent    {item['signal']}")

    any_fail |= not case_ok
    print(f"[{'PASS' if case_ok else 'FAIL'}] {case}")
    for ln in lines:
        print(ln)
    if oracle.get("notes"):
        print(f"    note: {oracle['notes']}")
    print()

if scored == 0:
    print("No runs to score. Run: harness/spec/run-spec.sh all")
    sys.exit(0)

print(f"{scored} case(s) scored.")
sys.exit(1 if any_fail else 0)
