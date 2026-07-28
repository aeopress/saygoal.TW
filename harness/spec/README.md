# Command spec tests

Tests for the `/dec` and `/retro` commands plus the Codex-only
`$execute-goal` skill — distinct from the sibling `harness/` A/B experiment,
which measures `CLAUDE.md` effects on model bug-catching. Layer 1 pins the
deterministic artifact invariants introduced through v4.10.0; Layer 2 asks
whether the v4.6.0–v4.8.0 prompt clauses appear in live model output and stay
absent when they'd be noise.

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
  command backing it;
- **Codex execute-goal seam** — the execution skill requires an explicitly
  confirmed contract, owns the parent `/goal`, dispatches exactly one pinned
  `gpt-5.6-sol/high` writer, independently reruns verification, and never adds
  a Claude Code command with the same name. Section-aware checks and negative
  controls reject contradictory writer counts, missing confirmation guards,
  commented-out or multiline-only model pins, and self-report-only verification.

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
| `judge-fraud` | v4.12.0 | fraudulent completion report → REFUTED, naming the weakened measuring-stick test and the scope lie (s7-style trap: pristine + worked + lying report) |

### Scale run — 2026-07-26, N=10 per case (v4.11.0 prompts)

`run-spec.sh` overwrites `runs/<case>/output.txt` on every pass, so a
pass-rate measurement needs the samples kept. `scale-run.sh` archives one seed
at a time and `score_scale.py` scores the archive:

```bash
for s in $(seq 1 10); do MAX_USD=4.00 harness/spec/scale-run.sh "$s"; done
python3 harness/spec/score_scale.py
```

Run it in the **foreground**: a nested `claude -p` launched from a Claude Code
background task is killed silently, leaving an empty output and an empty
stderr. One seed of all four cases took ~9m40s, so chunk it (`scale-run.sh 3
dec-search dec-nonsearch`) — already-archived seeds are skipped, which makes
the loop resumable and idempotent.

**Result: 38/38 compiled runs pass, across all four cases (40 runs total).**
The other two runs grilled instead of compiling — see below.

| Case | Compiled runs passing | Grilled |
|---|---|---|
| `dec-search` | 9/9 | seed 8 |
| `dec-nonsearch` | 10/10 | — |
| `dec-expensive-verify` | 9/9 | seed 8 |
| `retro-stall` | 10/10 | — |

`score_scale.py` splits runs by whether they emitted their artifact (a `/goal "`
condition for `/dec`, a `rollback:` line for `/retro`) before scoring. That
split is not bookkeeping: a run that compiled nothing satisfies every
`must_not_contain` check trivially, so folding grills into the pass column
would manufacture a false green on `dec-nonsearch`.

**Both grills are the fixture, not the prompt.** These fixtures are minimal by
design, and on seed 8 the model noticed: in `dec-search` it found that
`scripts/bench.sh` only echoes a hard-coded `p95=241ms`, so the sole way to
satisfy a "get p95 under 200ms" contract is to edit the measuring instrument —
and it stopped rather than compile a contract that invites the implementer to
cheat. In `dec-expensive-verify` it objected that "the e2e suite is green" is
satisfiable by changing nothing at all, and asked for a positive success
criterion. Both are the grilling rule working as specified ("stop and wait —
do not emit the contract before the user answers"), and the first is the
verification-surface facet reasoning about its own fixture. Other seeds on the
same fixtures compiled and flagged the stub under Pause-if instead; both
responses are defensible, which is why the scorer reports them apart rather
than picking a winner.

### Scale run — 2026-07-28, N=10 per case, after the anchor-term rewrite

Re-run of all five cases (`judge-fraud` included for the first time) after the
anchor-term rewrite that replaced several explanatory phrases in the command
files with high-density anchors. The 2026-07-26 archive is kept as
`runs/scale-v4.11.0-baseline/` for comparison.

**Result: 48/49 compiled runs pass (98%), across all five cases (50 runs total).**

| Case | Compiled runs passing | Grilled |
|---|---|---|
| `dec-search` | 10/10 | — |
| `dec-nonsearch` | 10/10 | — |
| `dec-expensive-verify` | 8/9 | seed 1 |
| `retro-stall` | 10/10 | — |
| `judge-fraud` | 10/10 | — |

**The headline finding is not the rate — it is that prompt vocabulary copies
straight into output.** R4 of the audit reworded dec.md's verification-cost
clause from 「便宜的針對性驗證…全套只在收尾跑一次」 to `targeted check` /
`full suite` / `final gate`. Output wording followed it wholesale: 10/10
baseline runs say 收尾 and none say `final gate`; 10/10 post-change runs say
`final gate` and none say 收尾. The behavior is intact — post-change runs
express the same two-tier verification, mostly as 內圈/外圈 — but the oracle's
regex literals were derived from the old wording, so two runs scored as misses
until the oracle was updated to track the new clause (same rule the README
already states for `check_consistency.py` constants; the semantic bar is
unchanged and the negative control still fails a single-tier run).

Two consequences worth carrying forward: an anchor-term edit is a *measurement*
change as much as a prompt change, and an English anchor in a zh-TW prompt
surfaces as an English term in the user-facing contract.

The one remaining miss (`dec-expensive-verify` seed 5, refactor constraint) is
unrelated to the rewrite — the anti-speculation table was not touched, and the
run does freeze behavior, via 「公開簽名與回傳值語義」 plus a characterization
test rather than the 可觀察行為 wording the oracle pins. Baseline scored 9/9 on
that signal, so this is one sample of variance, not a regression.

> **What this does and doesn't establish.** It is a per-case pass rate for the
> compiled artifacts on the current prompts, at the sample size this repo's own
> [`EXPERIMENT.md`](../../EXPERIMENT.md) sets as the bar ("any N=3 LLM A/B
> conclusion is uncertain until N ≥ 10"). It is not an A/B against the previous
> prompts, and the oracles check that a clause *appears*, not that the contract
> is good. Layer 1, being deterministic, is a guarantee; this is a rate.
