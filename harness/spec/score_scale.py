#!/usr/bin/env python3
"""Per-case pass rate across archived seeds of the Layer 2 behavioral eval.

score_spec.py verdicts one run; this scores every seed archived by
scale-run.sh (runs/scale/<case>/seed<N>.txt) and reports a rate, plus a
per-signal breakdown so a flaky clause is visible rather than averaged away.

Runs are split into two populations first:

  * **compiled** — the run emitted its artifact (a `/goal "` condition for
    /dec, a `rollback:` line for /retro) and is scored against the oracle;
  * **grilled** — the run stopped to ask the user instead. That is legitimate
    /dec behavior (a contract only converges once no question remains), so it
    is reported separately rather than counted as a content failure.

Splitting them is also what keeps a `must_not_contain` case honest: a run that
compiled nothing trivially satisfies every absence check, so scoring it as a
pass would manufacture a false green.

Scoring is identical to score_spec.py (same oracle, same regexes) and reads
only archived files, so re-scoring after an oracle change costs nothing.

Usage:
  python3 harness/spec/score_scale.py               # every case with archives
  python3 harness/spec/score_scale.py dec-search    # one case
"""

import json
import re
import sys
from pathlib import Path

SPEC = Path(__file__).resolve().parent
CASES = SPEC / "cases"
SCALE = SPEC / "runs" / "scale"

# An emitted artifact: /dec compiles a `/goal "…"` condition, /retro ships a
# revised condition carrying the original on a `rollback:` line, /judge
# delivers a verdict from its fixed taxonomy.
ARTIFACT = re.compile(r'/goal "|rollback:|VERIFIED|REFUTED')

wanted = sys.argv[1:] or sorted(p.name for p in CASES.iterdir() if p.is_dir())


def seed_key(path):
    match = re.search(r"seed(\d+)\.txt$", path.name)
    return int(match.group(1)) if match else 0


print("=== saygoal Layer 2 — pass rate over seeds ===\n")

overall = []
for case in wanted:
    oracle_p = CASES / case / "oracle.json"
    case_dir = SCALE / case
    if not oracle_p.exists() or not case_dir.is_dir():
        continue
    oracle = json.loads(oracle_p.read_text(encoding="utf-8"))
    seeds = sorted(case_dir.glob("seed*.txt"), key=seed_key)
    if not seeds:
        continue

    signals = [(i["signal"], i["regex"], True) for i in oracle.get("must_contain", [])]
    signals += [(i["signal"], i["regex"], False) for i in oracle.get("must_not_contain", [])]

    misses = {sig: [] for sig, _, _ in signals}
    passed, grilled, empty = 0, [], []
    for path in seeds:
        text = path.read_text(encoding="utf-8")
        n = seed_key(path)
        if text.strip() == "EMPTY_RUN":
            empty.append(n)
            continue
        if not ARTIFACT.search(text):
            grilled.append(n)
            continue
        ok = True
        for sig, rx, want in signals:
            hit = bool(re.search(rx, text))
            if hit != want:
                misses[sig].append(n)
                ok = False
        passed += ok

    compiled = len(seeds) - len(empty) - len(grilled)
    rate = f"{passed}/{compiled}" if compiled else "0/0"
    pct = f"{100 * passed / compiled:.0f}%" if compiled else "n/a"
    print(f"[{case}]  {rate} compiled runs pass  ({pct})   "
          f"[{len(seeds)} run(s): {compiled} compiled, {len(grilled)} grilled, "
          f"{len(empty)} failed]")
    for sig, _, want in signals:
        bad = misses[sig]
        verb = "missing in" if want else "wrongly present in"
        if bad:
            print(f"    ✗ {sig}: {verb} seed(s) {', '.join(map(str, bad))}")
        else:
            print(f"    ✓ {sig}")
    if grilled:
        print(f"    ~ grilled instead of compiling on seed(s) "
              f"{', '.join(map(str, grilled))} — read those before judging: "
              f"stopping to ask is correct when the fixture leaves a field unanswerable")
    if empty:
        print(f"    ! run failed (no output) on seed(s) {', '.join(map(str, empty))}")
    if oracle.get("notes"):
        print(f"    note: {oracle['notes']}")
    print()
    overall.append((case, passed, compiled, len(grilled), len(empty)))

if not overall:
    print("No archived seeds. Run: harness/spec/scale-run.sh <seed>")
    sys.exit(0)

total_pass = sum(p for _, p, _, _, _ in overall)
total_compiled = sum(c for _, _, c, _, _ in overall)
total_grilled = sum(g for _, _, _, g, _ in overall)
total_failed = sum(f for _, _, _, _, f in overall)
runs = total_compiled + total_grilled + total_failed
print(f"{len(overall)} case(s), {runs} run(s): {total_pass}/{total_compiled} "
      f"compiled runs pass ({100 * total_pass / total_compiled:.0f}%)"
      if total_compiled else "nothing scored")
if total_grilled or total_failed:
    print(f"plus {total_grilled} grilled and {total_failed} failed run(s), "
          f"excluded from the rate above and listed per case.")
