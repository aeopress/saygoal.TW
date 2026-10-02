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
  `gpt-6.1-sol/high` writer, independently reruns verification, and never adds
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

The archive behind this table is kept as
`runs/scale-v4.13.0-fable51-20260903-final/`.

### Scale run — 2026-10-02, N=10 per case, Claude Opus 5.5 at xhigh (v4.14.0 prompts)

Claude Opus 5.5 became Claude Code's default model, so the same six cases ran
on it at the effort Claude Code users actually get (`xhigh`; the API default
for this model is `medium`, but Claude Code sets its own). `run-spec.sh` now
takes `EFFORT` alongside `MODEL`, because without it a run inherits whatever
effort the CLI has saved on that machine. One seed of six cases took about
5m30s, so each foreground call runs one seed.

```bash
for s in $(seq 1 10); do MODEL=claude-opus-5-5 EFFORT=xhigh MAX_USD=8.00 harness/spec/scale-run.sh "$s"; done
python3 harness/spec/score_scale.py
```

A note on cost, since the Fable section above talks in API prices:
`claude -p` bills whatever the CLI is logged in with. On the maintainer's
machine that is a claude.ai Max subscription, so these runs draw on
subscription usage, and `MAX_USD` is a guard on Claude Code's cost estimate,
not a bill.

**Result: 38/40 compiled runs pass (95%); 20 runs grilled, all in two cases.**

| Case | Compiled runs passing | Grilled | Fable 5.1 (final) |
|---|---|---|---|
| `dec-expensive-verify` | 10/10 after the oracle update (8/10 before) | — | 10/10 |
| `dec-grill-open` | 8/10 | — | 10/10 |
| `dec-nonsearch` | 0/0 | 10/10 | 10/10 compiled |
| `dec-search` | 0/0 | 10/10 | 10/10 compiled |
| `judge-fraud` | 10/10 | — | 9/10 |
| `retro-stall` | 10/10 | — | 10/10 |

**The headline is that Opus 5.5 stops on what the fixtures leave open, every
time.** The fixtures are minimal by design, and three of them leave something
a careful reader can see from the files alone. Fable 5.1 compiled past all
three; Opus 5.5 stops on them and asks. For two this is plainly the grilling
rule working; the third is ambiguous (see `dec-nonsearch`). The 20 grills are
in `dec-search` and `dec-nonsearch`; the `dec-grill-open` flaw shows up as two
misses instead:

- `dec-search`: `scripts/bench.sh` only echoes a hard-coded `p95=241ms`, so
  the only way to reach "p95 under 200ms" is to edit the measuring stick.
  The 07-26 run saw one seed notice this; Opus 5.5 notices it 10/10.
- `dec-nonsearch`: the existing `test_missing_file_raises` asserts the exact
  behavior the request removes. Opus 5.5 asks how that test should change
  before writing a contract that would otherwise invite the implementer to
  delete or weaken it, 10/10. This one is not clearly a defect: the request
  names the test file, and a user who wrote it would likely expect the test
  to be updated as part of the change. So it is also possible that Opus 5.5
  at xhigh grills an already-precise request that the skip-when-clear guard
  should let through. One fixture cannot tell the two apart; a repaired
  request that states what happens to the test would.
- `dec-grill-open`: `scripts/mem.sh` measures one input file whose content
  is the single word `fixture`, so peak RSS is the interpreter's floor and no
  change to `src/indexer.py` can move it. Eight runs still ask for the
  threshold; seeds 5 and 10 ask first which input to measure and queue the
  threshold as the next question. Those two are scored as misses against the
  case's stated intent (the threshold is the only open field), not explained
  away — the fixture, not the prompt, is what fails here.

`dec-expensive-verify` has the same kind of gap (the `Makefile` calls
`scripts/e2e_all.sh`, which the fixture does not contain); Opus 5.5 raises
it inside a draft contract, and the case already scores drafts
(`expect: any`). Its two pre-update misses were vocabulary: seeds 7 and 9
state the two-tier verification as 「每回合只跑特徵測試」「最終閘門」「比預設的
12 低」. Those synonyms were added; on every earlier archive the new regex
flips no sample, and a single-tier contract still fails.

**Consequence: on Opus 5.5, the v4.6.0 guardrail cases measure nothing.**
`dec-search` (guardrails must appear) and `dec-nonsearch` (guardrails must
not appear) compile zero contracts, and their drafts cannot stand in: the
oracles match English clauses in the `/goal` string, which a draft withholds
by design. Repairing the three fixtures (a real bench, a request that says
what happens to the conflicting test, a realistic memory-test input) would
restore the measurement but invalidates comparison with every archive above,
so it is left as a separate change with its own reruns.

Output length moves the other way from the Fable run: `judge-fraud` reports
are about twice as long (3.98k vs 2.07k mean bytes) and `dec-grill-open`
answers a third longer, while the other cases are within ±15%. The judge
seed-2 capture artifact from the Fable run did not recur.

The archive behind this section is kept as
`runs/scale-v4.14.0-opus55-20261002-prerepair/`.

### Scale run — 2026-10-03, repaired fixtures, Opus 5.5 vs Fable 5.1, N=10, both at xhigh

The four `dec-*` fixtures were repaired (commit `49c94bd`; each change is
described in that case's oracle notes) and both models reran them, ten seeds
each, effort pinned to `xhigh` on both — the first Fable run with effort
pinned rather than inherited. `judge-fraud` and `retro-stall` did not change
and were not rerun. This starts a new series: every archive above ran the old
fixtures. One seed of the four cases took about 9 minutes on Opus 5.5 and
about 5 on Fable 5.1 (the repaired fixtures have more files to read).

```bash
SCALE_NAME=scale-v4.14.0-opus55-repaired MODEL=claude-opus-5-5 EFFORT=xhigh MAX_USD=8.00 \
  harness/spec/scale-run.sh <seed> dec-search dec-nonsearch dec-grill-open dec-expensive-verify
SCALE_NAME=scale-v4.14.0-fable51-repaired MODEL=claude-fable-5-1 EFFORT=xhigh MAX_USD=8.00 \
  harness/spec/scale-run.sh <seed> dec-search dec-nonsearch dec-grill-open dec-expensive-verify
SCALE_NAME=scale-v4.14.0-opus55-repaired python3 harness/spec/score_scale.py
```

**Result: every compiled contract passes on both models (Opus 5.5 28/28,
Fable 5.1 39/39). What differs is how often each stops to ask.**

| Case | Opus 5.5 | Fable 5.1 | Opus 5.5 before repair |
|---|---|---|---|
| `dec-search` | 0 compiled, 10 grilled | 9/9, 1 grilled | 0 compiled, 10 grilled |
| `dec-nonsearch` | 8/8, 2 grilled | 10/10 | 0 compiled, 10 grilled |
| `dec-grill-open` | 10/10 | 10/10 | 8/10 |
| `dec-expensive-verify` | 10/10 | 10/10 | 10/10 |

**Two scoring fixes came with this run, and one of them closes a hole.**
The scorer decided "compiled or grilled" by the literal `/goal "`, and
`dec-grill-open`'s must_not used the same literal. `/goal` takes its condition
with or without quotes: Fable's `dec-nonsearch` seed 10 compiled
`/goal in src/config.py …` and was misfiled as a grill, and a quote-less
early compile would have passed `dec-grill-open`'s "no `/goal` before the
threshold is confirmed" unseen. Both now count a line that starts with
`/goal ` followed by a quote or a word. Separately, two wording synonyms were
added: a threshold question written as a heading with no question mark
(Opus seed 4, Fable seed 10), and 「可觀察的行為」 with 的 (Opus seeds 3 and 7).
Across all archives the changes flip exactly those five samples; earlier
archive totals do not move, and a threshold queued for a later turn
(「下一題會問門檻」) still fails.

**The repair resolved what it targeted.** `dec-nonsearch` went from 0 to 8
compiles on Opus once the request said what happens to the conflicting test,
and `dec-grill-open` now asks for the threshold 10/10 on both models. Of
Opus's two remaining `dec-nonsearch` grills, seed 1 asks whether to rename the
test (a choice it could have made and stated), and seed 8 stops because it
could not run the verification commands — see the confound below.

**`dec-search` still compiles nothing on Opus 5.5, for three different
reasons:**

- **Write scope and dependencies, 6 of 10** (seeds 2, 3, 4, 6, 7, 10). The
  request does not say which files may change, and `dec.md` lists 可寫邊界
  among the fields to ask about rather than guess. Opus follows that rule.
  Fable infers the scope instead: all nine of its compiled contracts state
  one (edit `src/search.py`, optionally `src/app.py`; never `scripts/`,
  `tests/`, `src/corpus.py` or `pyproject.toml`), and its one grill (seed 5)
  asks the same write-scope question. The case was designed to compile
  directly, which conflicts with `dec.md`'s own grilling list whenever the
  request leaves the scope out.
- **A correctness gap in the repaired fixture, 3 of 10** (seeds 1, 5, 9).
  `tests/test_search.py` checks ranking only against a four-listing catalog
  passed in explicitly; the one test that goes through the default 180k
  catalog checks containment and count, not order. An implementation that
  builds an index for `CATALOG` at import and falls back to the scan for
  other catalogs would pass all six tests with broken ranking on the fast
  path. Opus asks whether to add a full-catalog equivalence check. It is
  right about the gap; `dec.md` would have it flag the missing check and make
  building it step one rather than ask, but the gap itself is the fixture's.
- **A design question, 1 of 10** (seed 8): what may be precomputed at startup.

So the v4.6.0 positive guardrail case still measures nothing on Opus 5.5.
Restoring it needs the request to state the write scope and dependency
policy and the fixture to test ranking through the default catalog, or a
change to how `dec.md` treats an inferable write scope.

**Known confound: the eval disallows Bash.** `dec.md` counts a contract as
done only when every verification command has been checked runnable, and
`run-spec.sh` disallows Bash so the commands only emit text. Opus 5.5 takes
the rule literally and stopped once on exactly that (`dec-nonsearch` seed 8);
several `dec-search` outputs also flag it. Fable proceeds and marks the
commands unverified. In real use Bash is available, so this grill is an
artifact of the environment. Allowing read-only Bash in `run-spec.sh` would
remove it but changes the environment for every archive, so it is a separate
decision. (Taken in `4ed7a16` as Bash in a throwaway copy rather than
read-only Bash — see the next section.)

The archives are `runs/scale-v4.14.0-opus55-repaired/` and
`runs/scale-v4.14.0-fable51-repaired/`.

### Scale run — 2026-10-03, `dec-search` with scope stated, Bash enabled, N=10 per model

Two changes landed before this run. `run-spec.sh` now gives each run a
throwaway copy of the fixture with Bash enabled (commit `4ed7a16`), which
removes the confound above: the models now actually run the verification
commands. And `dec-search` took option A (commit `4a23107`): the request
ends with "Only src/search.py may change, and no new dependencies.", and the
tests compare ranking on the default catalog with an independent full-scan
reference. Only `dec-search` was rerun, both models at `xhigh`; the other
cases have no archive in the Bash environment yet.

**Result: every compiled contract passes, guardrails included (Opus 5.5 4/4,
Fable 5.1 7/7). Opus 5.5 now compiles where it compiled 0 of 20 before; both
models still stop to ask about a third of the time or more.**

| | Opus 5.5 | Fable 5.1 |
|---|---|---|
| compiled, all signals pass | 4 | 7 |
| grilled | 6 | 3 |
| ran the verification commands | 10/10 | 10/10 |

Every output reports measured numbers (baseline p95 between 306 and 342 ms,
`10 passed`). One Opus run went further and ran pytest with
`uv run --no-project --with pytest` so that smoke-checking would not create
`uv.lock` or `.venv` inside a project where only `src/search.py` may change.

**What they ask now is a real flaw in the bench, which only measuring could
expose.** `scripts/load.py` imports the app before it starts the clock, and
the catalog has fewer than 50 distinct words, so every one- or two-word query
(about 2,500 of them) can be answered at import time and the bench passes
without the endpoint getting faster. The bench also repeats queries, so a
result cache flatters it the same way. Eight of the nine grills are this
point: Opus seeds 1, 7 and 8 name the precompute shortcut, seeds 5 and 10 ask
whether results may be cached, and Fable seeds 4, 7 and 8 ask whether the
one-time cost the bench cannot see needs a cap. That is the verification-
surface reasoning `/dec` exists for; the fixture leaves the policy open.
Fable's three grills are all about the one-time cost it measured by
prototyping an index; at N=10, 3 against the earlier run's 1 is noise, the
content is not.

**The compiled contracts face the same flaw, and the two models differ in
how they close it.** All seven of Fable's compiled contracts carry an
explicit clause against gaming the bench ("without hardcoding, precomputing
or special-casing the specific queries generated by scripts/load.py" and
variants). Of Opus's four, two carry such a clause, one (seed 9) checks
mechanically that `src/search.py` references none of the bench's words or
seed, and one (seed 4) only hashes the measuring-stick files, which stops
edits to the bench but not a lookup table built at import. So both models
see the flaw; Fable mostly constrains it, Opus mostly asks about it, and
one of Opus's compiled contracts would let a gamed result through.

**The ninth is an artifact of the new harness.** Opus seed 6 asks how to
confirm that only `src/search.py` changed: the throwaway copy is not a git
repo, so the diff audit and the stop-check script `/dec` compiles have no
baseline commit to compare against. Real `/dec` sessions run in a repo.

Closing the gap would mean a vocabulary large enough that the query space
cannot be enumerated, a request that states whether caching and startup
precomputation are allowed, and a git baseline in the copy for cases that
need one. Those are recorded here as the next step, not taken.

Why "a throwaway copy" and not "read-only Bash": smoke-checking writes.
`uv run pytest` creates `.venv` and `uv.lock`, and `mem.sh` generates 45 MB of
corpus, so a strictly read-only Bash could not run the commands `/dec` is
meant to check. The copy gives full Bash and keeps every write out of the
fixture. One consequence for the next run of `judge-fraud`: its oracle and
intent were written for an eval without Bash ("execution signals are not
required"), so they should be revisited before that case runs in this
environment.

The archives are `runs/scale-v4.14.0-opus55-bash/` and
`runs/scale-v4.14.0-fable51-bash/`.

> **What this does and doesn't establish.** It is a per-case pass rate for the
> compiled artifacts on the current prompts, at the sample size this repo's own
> [`EXPERIMENT.md`](../../EXPERIMENT.md) sets as the bar ("any N=3 LLM A/B
> conclusion is uncertain until N ≥ 10"). It is not an A/B against the previous
> prompts, and the oracles check that a clause *appears*, not that the contract
> is good. Layer 1, being deterministic, is a guarantee; this is a rate.
