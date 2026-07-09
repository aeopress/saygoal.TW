# Command spec tests

Tests for the `/dec` and `/retro` command *behavior* — distinct from the
sibling `harness/` A/B experiment, which measures `CLAUDE.md` effects on model
bug-catching. This suite asks a narrower question: **do the v4.6.0–v4.8.0
prompt changes produce the contract clauses they promise, and skip them when
they'd be noise?**

Two layers, cheap-to-expensive.

## Layer 1 — consistency (deterministic, free, CI-able)

```bash
python3 harness/spec/check_consistency.py       # exit 1 on any failure
python3 harness/spec/check_consistency.py -v     # also list passing checks
```

Pure file invariants — no LLM, no tokens, no network. This is the regression
net for a multi-file prompt repo, guarding the mechanical mistakes a behavioral
eval is too expensive and noisy to catch:

- **version sync** across all four manifest version fields (a partial `sed`
  bump fails here);
- **Claude command ↔ Codex skill mirror** — the search guardrails and the
  verification-cost rule must live in both `plugin/commands/dec.md` and
  `plugins/saygoal/skills/dec/SKILL.md`;
- **retro completeness** — all five stall classes, the rollback line, the
  history-file append, and the "structural rewrite only" rule;
- **history-path handshake** — `/retro` (writer) and `/dec` (reader) must name
  `.claude/saygoal.history.jsonl` byte-for-byte, with no mistyped variant;
- **README freshness** — the English/Chinese READMEs must quote the *current*
  anti-fixation / trace clauses (the Japanese README paraphrases, so it's
  excluded from the literal check); every README's bilevel section must cite
  arXiv 2603.23420, and any README advertising `/saygoal:retro` must have the
  command backing it.

The checks have negative controls: breaking a version or a mirrored clause
flips the relevant check to FAIL and the script to exit 1.

> **Caveat on README freshness**: the canonical clause literals live as
> constants at the top of `check_consistency.py`. If you reword a clause, update
> the constant too — that's what makes the READMEs get re-checked against the
> new wording.

## Layer 2 — behavioral eval (LLM-in-the-loop, costs tokens)

```bash
harness/spec/run-spec.sh all                 # or: run-spec.sh dec-search retro-stall
python3 harness/spec/score_spec.py           # grep each output against its oracle
MODEL=claude-opus-4-8 MAX_USD=2.50 harness/spec/run-spec.sh dec-search
```

`run-spec.sh` expands a command file with a case's arguments the way a slash
command would (`$ARGUMENTS` substitution), runs it inside the case's fixture
repo (so `/dec` can verify its verification target instead of grilling for
missing files), and captures the emitted contract to `runs/<case>/output.txt`
(gitignored). `score_spec.py` greps that output against `cases/<case>/oracle.json`
— every `must_contain` regex must match, every `must_not_contain` must not.
Deterministic given a fixed output.

| Case | Tests | Expects |
|---|---|---|
| `dec-search` | v4.6.0 positive | trace + anti-fixation clauses present on a search-type task |
| `dec-nonsearch` | v4.6.0 negative | those clauses **absent** on a deterministic single fix |
| `dec-expensive-verify` | v4.8.0 | verification-cost-aware cap (cheap per-turn check, full suite as final gate) |
| `retro-stall` | v4.7.0 | stall diagnosis + redirect to the real bottleneck + a rollback line, not just a bigger cap |

### Smoke run — 2026-07-09, N=1 each

All four cases pass on a single live run (CLI default model, `--effort` default).
Highlights from the actual outputs: `dec-search` wove both guardrails into the
`until` / `without` segments; `dec-nonsearch` correctly omitted them; `retro-stall`
named the cache fixation, redirected the contract to the untouched
`tokenize.py`, and shipped a `rollback:` line; `dec-expensive-verify` offered two
capped strategies keyed to the 40-minute suite cost.

> **This is a smoke test, not a verdict.** N=1 is one noisy sample. By this
> repo's own [`EXPERIMENT.md`](../../EXPERIMENT.md) standard — "any N=3 LLM A/B
> conclusion is uncertain until N ≥ 10" — a real behavioral claim needs the
> loop below. Layer 1, being deterministic, *is* a guarantee; Layer 2 at N=1 is
> evidence the pipeline works and the clauses appear, not proof of a rate.

Scale to a real verdict (per-case pass-rate over seeds):

```bash
for s in $(seq 1 10); do harness/spec/run-spec.sh all; \
  python3 harness/spec/score_spec.py >> runs/scored-$s.txt; done
```

(The runner overwrites `runs/<case>/output.txt` each pass; redirect or move the
outputs between seeds if you want to keep every sample.)
