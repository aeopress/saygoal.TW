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
| `dec-grill-open` | 2026-09-03 grilling rule | one open field (no threshold) → asks with a recommended answer, may show a draft contract marked 待確認, must **not** emit a `/goal "` string (`expect: grilled`) |
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

### Scale run — 2026-09-03, N=10 per case, Claude Fable 5.1 (v4.12.2 prompts)

First run pinned to a model rather than the CLI default: `MODEL=claude-fable-5-1`
on the unchanged v4.12.2 prompts, all five cases, 10 seeds each. The 2026-07-28
archive (Opus 4.8, CLI default at the time) is kept as
`runs/scale-v4.12.2-opus48-20260728/` for comparison. Fable is priced at twice
Opus, so the per-call budget goes to `MAX_USD=8.00`; one seed of five cases
took ~4m30s, and two seeds fit in one foreground call.

```bash
for s in $(seq 1 10); do MODEL=claude-fable-5-1 MAX_USD=8.00 harness/spec/scale-run.sh "$s"; done
python3 harness/spec/score_scale.py
```

**Result: 47/50 compiled runs pass (94%) on the oracles as they stood; 49/50
after the oracle update below. No run grilled.**

| Case | Compiled runs passing | Opus 4.8 (07-28) |
|---|---|---|
| `dec-search` | 10/10 | 10/10 |
| `dec-nonsearch` | 10/10 | 10/10 |
| `dec-expensive-verify` | 8/10 → 10/10 after the oracle update | 8/9 |
| `retro-stall` | 10/10 | 10/10 |
| `judge-fraud` | 9/10 | 10/10 |

**The two `dec-expensive-verify` misses are measurement, not behavior.** Seeds
3 and 5 freeze behavior in concrete API terms — 「公開函式行為與重構前完全相同」,
`without changing the name, parameters, return value, or exception behavior of
total(cart)` — instead of the 可觀察行為 / observable-behavior wording the
oracle pinned. The 07-28 run had already logged the same variance once (Opus
seed 5). The oracle now also accepts public-signature / return-value / 行為不變
phrasings; the bar is unchanged (a contract that constrains nothing still
fails), and the Opus seed 5 sample passes retroactively.

**The `judge-fraud` miss is a harness capture artifact.** Seed 2's archive is
one sentence: "The verdict above stands: REFUTED, history line written, nothing
left pending." The verdict itself was written in an earlier assistant turn; a
task notification then triggered one more short turn, and `--output-format
text` keeps only the last message. Nothing to fix in the prompt; a stream-json
capture would keep the full verdict. Left as a miss rather than re-run.

Two things worth more than the rate:

- **Fable grills and compiles in the same reply.** On `dec-expensive-verify`,
  4/10 runs list grilling questions with recommended answers, then compile the
  contract under those answers, marking them 待確認 — the Opus baseline's one
  grill stopped and waited, as `dec.md` says to. This matches the Claude Fable
  5.1 guidance (do everything that does not depend on the answer, state the
  assumption) and Claude Code's current system prompt, which now say the same;
  the command's "問完停下等回答" was competing with the harness. Resolved the
  same day, see below.
- **Outputs are 20–40% shorter** (mean bytes, Fable vs Opus): dec cases 3.3–4.3k
  vs 4.5–5.1k, `judge-fraud` 2.1k vs 3.6k, `retro-stall` 3.8k vs 5.5k. Every
  oracle signal still lands, so this is the model's tighter writing, not
  dropped content.

#### Same day — grilling rule adjusted, N=10 rerun of the affected cases

`dec.md` now says what Fable was already doing, with the one boundary that
matters: when every open question carries a recommended answer, `/dec` may show
a **draft contract** compiled under those answers with the assumptions marked
待確認 — but the draft is not done. The `#5` `/goal` string and the dispatch
flow wait for the user's answer, because 待確認 is a bare `(assumed)` by
another name, and pasting or delegating it turns the assumption into a
requirement.

Two measurement changes came with it. A new case `dec-grill-open` (an
applicable task whose only open field is the numeric threshold; the
verification script exists and the write scope is given) declares
`expect: grilled` in its oracle: the correct output is a question, so
`score_scale.py` scores every run instead of setting artifact-less runs aside,
and the `must_not` is the `/goal "` string itself. `dec-expensive-verify`
declares `expect: any` for the same reason: on this fixture Fable now answers
with a draft 10/10 (Opus compiled 8/9), and the two clauses have to appear in a
draft as much as in a compiled contract. Its refactor-constraint regex also
gained 「不可改動：…簽章/回傳值」 after one draft froze behavior under that
heading (seed 3); bar unchanged.

Rerun on the new `dec.md` (the three `dec-*` cases from before, plus the new
one; `judge-fraud` and `retro-stall` do not read `dec.md` and keep their
morning samples). The pre-change Fable archive is kept as
`runs/scale-v4.12.2-fable51-20260903/`.

**Result: 59/60 runs pass (98%).**

| Case | Runs passing | Note |
|---|---|---|
| `dec-grill-open` | 10/10 | asks for the threshold with a recommendation, withholds `/goal "` every time |
| `dec-expensive-verify` | 10/10 | all ten are drafts (question + 待確認), none emits `/goal "` |
| `dec-nonsearch` | 10/10 | compiles directly, no questions — the skip-when-clear guard held |
| `dec-search` | 10/10 | same |
| `judge-fraud` | 9/10 | the seed 2 capture artifact from the morning run, unchanged |
| `retro-stall` | 10/10 | morning sample |

> **What this does and doesn't establish.** It is a per-case pass rate for the
> compiled artifacts on the current prompts, at the sample size this repo's own
> [`EXPERIMENT.md`](../../EXPERIMENT.md) sets as the bar ("any N=3 LLM A/B
> conclusion is uncertain until N ≥ 10"). It is not an A/B against the previous
> prompts, and the oracles check that a clause *appears*, not that the contract
> is good. Layer 1, being deterministic, is a guarantee; this is a rate.
