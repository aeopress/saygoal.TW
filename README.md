# saygoal

> **say a goal, watch it get done** — a declarative `/dec` + `/goal` workflow for Claude Code & Codex, in the spirit of Karpathy's "give it success criteria and watch it go".

![/dec — Imperative to Declarative](./saygoal.TW.png)

English | [繁體中文（台灣）](./README.zh-TW.md) | [简体中文](./README.zh-CN.md) | [日本語](./README.ja.md)

> **Source of truth**: [`aeopress/saygoal.TW`](https://github.com/aeopress/saygoal.TW) (formerly maintained at [`yelban/andrej-karpathy-skills.TW`](https://github.com/yelban/andrej-karpathy-skills.TW), now archived)

## What it does

`saygoal` turns a vague, imperative request into a **verifiable contract**, then lets the agent loop until that contract is met:

- **`/dec <task>`** rewrites your task into success criteria + a verification command + boundaries, and emits a ready-to-paste **`/goal` condition**.
- Paste that into Claude Code's (or Codex's) built-in **`/goal`** — a small fast model checks the transcript after each turn and keeps the agent working until the condition holds.
- **`/saygoal:retro`** — when a `/goal` loop stalls, reads the transcript as a search trace, diagnoses why, and structurally rewrites the contract (revised condition + a rollback line).

**30-second example:**

```
/dec fix the login flicker on first load

→ /goal "run npx playwright test login-flicker.spec.ts until it paste-shows 0 failures
         without changing the auth flow or any file outside the login component
         or stop after 12 turns"
```

`/dec` writes the contract; `/goal` drives to green. Works on **Claude Code** (`/dec` command) and **OpenAI Codex** (`$dec` skill — seven-field format).

→ [Install](#install) · [How it works](#dec--goal--the-pipeline) · [Why the rules file isn't the leverage](#why-the-rules-file-isnt-the-leverage--the-receipts)

## `/dec` + `/goal` — the pipeline

Karpathy's strongest observation is **a user-side discipline**, not something the assistant self-enforces:

> "LLMs are exceptionally good at looping until they meet specific goals... Don't tell it what to do, give it success criteria and watch it go."

Two slash commands map onto Karpathy's two verbs — "give it success criteria" and "watch it go":

| | `/dec` (this repo) | `/goal` (built into Claude Code v2.1.139+) |
|---|---|---|
| Phase | **Before action**: rewrites a vague request into a contract | **During action**: keeps Claude turning until the contract is met |
| Action | Rewrites your input; **does not implement yet** | After each turn a small fast model evaluates whether the contract holds; if not, Claude starts another turn automatically |
| Persistence | One-shot transformation; you confirm before execution | Session-scoped until `/goal clear` |
| Evaluator | **You** (review the contract before execution) | **Haiku** (yes/no judge reading the transcript) |
| Karpathy verb | "give it success criteria" | "watch it go" |

### When declarative beats imperative

| Imperative (weak leverage) | Declarative (strong leverage) |
|---|---|
| "Add input validation" | "Write failing tests for these invalid inputs, then make them pass" |
| "Fix the bug" | "Write a test that reproduces the bug, then make it pass — other tests must still pass" |
| "Make it faster" | "Reduce p95 latency under this load to <X ms; benchmark with `scripts/bench.sh`" |
| "Refactor X" | "Refactor X without changing observable behavior; existing tests must still pass" |

- **Declarative** works for: features with observable outcomes, bug fixes, performance work, refactors with test coverage.
- **Imperative** (skip `/dec`): exploratory edits, UI tweaks, prose, anything where "done" is subjective.

Together with the goal, hand the agent its verification tool: a test command, a benchmark script, a lint command, a browser MCP for visual checks. Then leave it to iterate.

### `/dec` alone

`dec` is short for **declarative**. The command reframes a command-style request into a contract; you confirm before anything is implemented.

```
/dec fix the login flicker on first load
```

Returns success criteria (e.g. "Playwright screenshot diff < 2px across 10 runs"), a verification command worded so Claude must *run it and paste the output*, and on-demand boundaries (what must not change / writable paths / external-system limits) — plus a ready-to-use `/goal` condition in the natural-language `[work] until [end state] without [constraints] or stop after 12 turns` shape you can paste directly. If the task is too subjective or too small, it replies "not applicable — just do it" instead of forcing a conversion. Good for one-shot prompts where you want the declarative discipline without committing to autonomous looping (or when you're on Cursor / an older Claude Code without `/goal`).

**Grill first, then compile**: a contract only converges when no question remains — so on a vague request, `/dec` grills before compiling, asking one question at a time, each with a recommended answer, to resolve the fields it could otherwise only guess (threshold, whether the verification target exists, writable boundaries) instead of silently marking them `(assumed)`. Three behaviors: **vague** → one question at a time until it converges; **too subjective / too small** → "not applicable — just do it"; **clear and substantial** → compiles straight to a contract, no interrogation. The skip-when-clear guard means it probes only when genuinely needed, never badgering an already-precise request (verified end-to-end on the Codex CLI). This is exactly the Fable 5 workflow Thariq of the Claude Code team describes — "I'd ask Claude to interview me about the implementation before writing the final spec file" ([source video](https://x.com/trq212/status/2073100352921215386)).

**Context, not just constraints**: the sharpest idea in Thariq's video — instead of "keep it simple, don't overengineer", say "this feature is an experiment, there's a real chance we delete it in a month, so don't build anything painful to throw away". Constraints can only enumerate what not to do; context lets the agent decide correctly in situations the constraints didn't anticipate. So when `/dec` meets a taste-based constraint it doesn't copy it into the contract — it grills for the underlying reason (experiment? lifespan? deadline? — a fixed-range question, so the Claude command asks it as a single-select AskUserQuestion) and encodes the answer in an optional **Context** facet: a one-clause prefix in the Claude `/goal` condition (the evaluator only judges the until / without parts; context is for the implementing agent), or an optional `Context:` line in the Codex seven-field template.

**Multi-part specs → per-item deviation report**: when the spec lists several items, the contract extends verification to "paste a per-item completion report: each item marked implemented / deviated, with the difference explained" — matching Thariq's "prepare a report on what was implemented and if anything differed". The report is evidence the evaluator can pattern-match, and it closes the stealthiest failure mode: the loop converged, but built something other than what you asked for. The report defaults to self-reporting by the implementer; on multi-part specs the Claude command asks one more grilling question, letting you upgrade to **workflow verification** — one independent verifier agent per item, judging outcome against the spec without reading the implementation process — exactly Thariq's "use a workflow to verify each part of the plan". Independent verification is more trustworthy (self-reporting is grading your own homework) but costs more tokens, hence an option, defaulting to self-report.

**Search-type tasks → convergence guardrails**: when a task only converges through repeated try→verify cycles (performance tuning, flaky-test debugging, chasing a benchmark number), the classic stall is the loop re-proposing the same change until the turn budget runs out — given the same state, the LLM falls back to its priors. This is exactly the failure mode [Bilevel Autoresearch](https://arxiv.org/abs/2603.23420) documents on Karpathy's own pretraining benchmark, and its fix — break the inner loop's deterministic search pattern — carries over to `/dec` with the contract as the mechanism carrier: the compiled condition gains a **trace clause** in the until segment (`pasting every 5 turns a one-line search log: approaches tried → result → ruled out`), keeping the transcript legible as a search trace, and an **anti-fixation clause** in the without segment (`without repeating an approach whose verification output has already failed twice`) — the prompt-carrier equivalent of the paper's Tabu Search mechanism. Non-search tasks get neither: there the clauses are noise.

### Two ways to consume a contract — spec mode vs loop mode

The same contract has two consumption modes; pick per task, not per habit:

- **Spec mode** — hand the contract (fields #1–#4, no `/goal` prefix) to a single implementation pass — your own session or a delegated model — and accept against the Verification field. Claude 5-era models show first-shot correctness on well-specified problems, and the contract is exactly that spec; a one-shot run also skips the loop's per-turn cost (context re-read plus verification rerun every turn). On deterministic tasks, try this first.
- **Loop mode** — paste the compiled `/goal` condition when the task genuinely needs supervised iteration: search-type tasks (performance tuning, flaky tests, benchmark chasing), delegation you want harness-checked, or unattended runs. On current models the loop's value is the convergence guarantee and evidence honesty — an evaluator that can't be talked past — not "keeping the model working".

Either way the acceptance criteria are identical: the contract doesn't change, only who drives.

### `/dec` as the boundary-setter for `/goal`

`/goal` is only as good as the condition string you feed it. Vague conditions never converge:

```
❌ /goal "make the login page not flicker"
   How does Haiku verify "no flicker"? Watch screenshots? Read console?
   The evaluator answers always-yes or always-no — the loop never converges.

✅ /dec fix the login flicker on first load
   →  Success:    Playwright screenshot diff < 2px across 10 runs
      Verify:     run `npx playwright test login-flicker.spec.ts` and paste output showing 0 failures
      Boundaries: writes limited to the login component; don't change the auth flow

✅ /goal "run npx playwright test login-flicker.spec.ts until it paste-shows 0 failures
          without changing the auth flow or any file outside the login component
          or stop after 12 turns"
   Haiku reads the pasted test output from the transcript and judges deterministically.
   The loop actually converges.
```

`/dec` enforces three things that `/goal` alone cannot:

1. **Machine-checkable success conditions** — "diff < 2px", "10 passed", "p95 < X ms" map cleanly to evaluator yes/no.
2. **A verification command embedded in the contract** — forces Claude to actually run the check, not statically reason "this should work now". (Patching-without-running was a real failure mode in our T4 declarative-loop test.)
3. **Structured boundaries (five facets, on demand)** — what must not change (including the **verification surface**: the exact files the check itself depends on — test files, bench scripts, CI config — listed as paths, because moving the measuring instrument is how a loop fakes green), writable paths, external-system limits, pause-if, and a turn cap. For Claude they compile into the condition (`"… without test files changed and no new files in src/legacy/, or stop after 12 turns"`); pause-if is listed separately and is better as a Stop hook, since the evaluator can't judge it. The turn cap is verification-cost-aware: a loop reruns its check every turn, so an expensive check (full e2e suite, long benchmark) lowers the cap — or the contract compiles a cheap targeted check per turn and saves the full suite for the end.

### The full pipeline

```
1. /dec <vague request>            ← contract + a pre-compiled /goal condition
2. you review the contract         ← human confirms direction
3. paste the /goal line from #1    ← Haiku takes over as judge
4. Claude loops to convergence     ← Karpathy's "watch it go"
5. loop stalled? /saygoal:retro    ← reads the trace, rewrites the contract (the outer loop)
```

### When the loop stalls — `/saygoal:retro`, the outer loop

A `/goal` loop can stall: it hits `or stop after 12 turns` still re-proposing variations of the same failed fix. Re-pasting the same condition harder is the one move that reliably does nothing — in [Bilevel Autoresearch](https://arxiv.org/abs/2603.23420)'s ablation, parameter-level adjustment showed no reliable gain, while mechanism-level rewriting carried the entire 5× effect. `/saygoal:retro` is that outer loop for this pipeline: it reads the stalled session's transcript as a search trace, classifies the stall — broken verification, unreachable threshold, a boundary walling off the solution (auto-added constraints are the prime suspect), fixation, or a mis-scoped task — and structurally rewrites the contract. Output: a revised ready-to-paste condition plus a `rollback:` line carrying the original verbatim, so a bad rewrite never costs more than one paste. Each retro also appends one line to `.claude/saygoal.history.jsonl`, which future `/dec` grilling reads first — past stall reasons become the next contract's pre-checks.

### The contract is also a delegation prompt — pairing with Codex delegation tools

`/dec` output isn't only food for `/goal`. A good delegation prompt needs five things — context, explicit goals, constraints, output format, and a completion criterion — which is exactly what the contract's fields are. So the same contract (minus the `/goal` prefix) drops straight into a delegation prompt:

- **[openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc)** (`/codex:rescue`): compile the vague request into a contract with `/dec` first, then hand it off with `/codex:rescue --background <full contract>`. When harvesting (`/codex:result`), accept against the contract's Verification field; the per-item deviation report means you can judge the final output alone, without replaying the process.
- **[codex-orchestrator](https://github.com/yelban/codex-orchestrator)** (`codex-agent` CLI): when fanning out tasks in parallel, each `codex-agent start "<contract>"` carries its own verification and boundaries; after `await-turn`, accept against Verification.
- **`codex exec`** (the bare codex CLI — the most universal channel, no plugin required): dispatch `codex exec -C <repo> --sandbox workspace-write --json "<contract>"` as a background task. The task id, the `--json` event stream, the completion notification, and TaskStop give you run-status tracking — the same PID + exit-code + JSONL that codex-orchestrator wraps, provided natively by Claude's background tasks. This is the lowest-common-denominator fallback for environments where neither plugin is available (needs network — allow it if Claude runs sandboxed).

The Claude command automates this: after emitting the contract, `/dec` detects these channels (the session's skills list, `command -v codex-agent`, `command -v codex`) and, if any is present, asks for the execution channel via AskUserQuestion — loop yourself with `/goal`, or delegate. Your choice is remembered in the project's `.claude/saygoal.local.json` and surfaces as the first option next time, but it **still asks every time** (every delegation spends quota; the per-task veto stays in your hands). Pick delegation and it dispatches in the background on the spot; harvest against the contract's Verification field. With none installed, delegation is never mentioned — behavior is unchanged.

**What delegation adds to the contract.** A delegated run has no shared transcript and a model you steer less directly, so `/dec` compiles three more mechanisms when you pick a channel:

- **A compiled stop-check** — before dispatch, the contract becomes `.claude/saygoal.stop-check.sh`: it reruns the verification itself instead of trusting output pasted earlier, fails when the verification surface moved against the dispatch-time commit, and prints evidence per check. The gate the whole run rests on is the one gate the implementing model must not adjudicate — and Claude and the delegated model now share a single measuring stick, so "done" stops having two readings.
- **A trace file** — a background process leaves no transcript to read, so search-type contracts append one line per attempt to `.claude/saygoal.trace.log` (time, executor, tried → result → ruled out). `/saygoal:retro` reads that file instead of reconstructing a transcript it never had, and the executor column is what later tells you whether delegated turns converged faster.
- **A three-input harvest** — acceptance reads the contract text, the diff, and the stop-check's output and exit code. Nothing else: a non-zero exit is an outright reject, and the implementation process is never replayed into your context.

The division of labor is upstream/downstream: `/dec` owns "is the contract convergent", the delegation tool owns "who executes and how parallel". Same contract — paste it into `/goal` to loop yourself, or hand it to a delegation tool to outsource to another model. The acceptance criteria don't change.

### Works for Codex `/goal` too

OpenAI's Codex CLI shipped its own `/goal` in [v0.128.0 on 2026-04-30](https://developers.openai.com/codex/cli/slash-commands) — eleven days before Claude Code's v2.1.139. Codex's [official goal-writing guidance](https://developers.openai.com/codex/use-cases/follow-goals) lists four things a good goal should specify:

> "what Codex should achieve, what it shouldn't change, how it should validate progress, and when it should stop"

— and asserts **"Codex should know what 'done' means before it starts."** This is exactly the contract `/dec` writes:

| Codex docs requirement | `/dec` output (Codex seven-field) |
|---|---|
| what Codex should achieve | **Outcome** |
| what it shouldn't change | **Constraints + Boundaries** |
| how it should validate progress | **Verification** |
| when it should stop | **Stop when + Pause if** |

Three confirmed values of running `dec` before opening a Codex `/goal`:

1. **You don't have to remember Codex's checklist** — `/dec`'s template fills all seven Codex fields (outcome, verification, constraints, boundaries, iteration policy, stop, pause) every time.
2. **`/dec` requires each field to be measurable** — [`plugin/commands/dec.md`](./plugin/commands/dec.md) demands "a verifiable end state the `/goal` evaluator can find in the transcript: exit codes, output match, a quantified threshold". Codex docs say goals should be testable but don't ship a template that enforces this on the user side.
3. **`/dec`'s "not applicable — just do it" short-circuit for subjective tasks** (UI tweaks, prose, single-line renames) has no documented equivalent in Codex's `/goal`. Opening `/goal` on a subjective task is exactly what Codex docs warn against: **"Avoid using a goal for a loose list of unrelated work."**

**Using `dec` with Codex**: this repo also ships a Codex `dec` skill (packaged as a Codex plugin at [`plugins/saygoal`](./plugins/saygoal)) that outputs Codex's seven-field `/goal` template (the Claude command outputs a single natural-language condition instead — each side emits its host's native format). In Codex CLI, invoke it as `$dec <request>` or select it through `/skills`; the generated `/goal` block is ready to paste into Codex `/goal "..."`. This does not change Claude Code's `/dec`: the original command remains at [`plugin/commands/dec.md`](./plugin/commands/dec.md), still using Claude's `$ARGUMENTS` template.

> **Caveat — design claim, not empirical.** We have **not** run a controlled benchmark of `/dec` + Codex `/goal`. The mapping above is derived by reading `/dec`'s prompt template against Codex's [published goal-writing guidance](https://developers.openai.com/codex/use-cases/follow-goals). The N=40 A/B test in [`EXPERIMENT.md`](./EXPERIMENT.md) measured CLAUDE.md effects on Opus 4.7, not `/dec` itself.

> **Note on invocation:** when installed via the plugin (Option A below), Claude Code namespaces the command to `/saygoal:dec`. For the short `/dec` form, install the command file manually (Option C). The built-in `/goal` is always available regardless of install method.

> **Note on the `/goal` evaluator:** `/goal` sends each turn's transcript to Claude Code's built-in "small fast model" slot, which [defaults to Haiku](https://code.claude.com/docs/en/goal.md). There is no `/goal`-specific model override; the only way to swap it is to redirect the slot globally with the `ANTHROPIC_DEFAULT_HAIKU_MODEL` environment variable ([model config docs](https://code.claude.com/docs/en/model-config.md)), which changes the `haiku` alias everywhere — most setups never need to touch this.

## Install

### Claude Code

```
/plugin marketplace add aeopress/saygoal.TW
/plugin install saygoal@saygoal
```

Then use `/saygoal:dec <task>`. The built-in `/goal` is always available — no install needed.

> **Upgrading from the old version?** This project was formerly `andrej-karpathy-skills.TW` (marketplace name `karpathy-skills`, old repo now archived). If you installed it before the rename, remove the old marketplace first — otherwise you won't get updates. `marketplace remove` also uninstalls the old plugin:
>
> ```
> /plugin marketplace remove karpathy-skills
> /plugin marketplace add aeopress/saygoal.TW
> /plugin install saygoal@saygoal
> /reload-plugins
> ```

### Codex

Install straight from GitHub (mirrors the Claude Code marketplace command):

```
codex plugin marketplace add aeopress/saygoal.TW
codex plugin add saygoal@saygoal
```

Or from a cloned repo root, swap the first line for `codex plugin marketplace add .`.

Then use `$dec <task>` (or pick it from `/skills`), and paste the generated `/goal "..."` into Codex's built-in `/goal`.

For optional pinned execution, explicitly confirm that contract and invoke `$execute-goal`. On first use it detects whether the bundled `saygoal_writer` custom-agent template is installed and offers project-scoped (`.codex/agents/`) or personal (`~/.codex/agents/`) setup; start a new thread after setup, then invoke it again. It activates the parent `/goal`, delegates to exactly one `gpt-5.6-sol` writer at `high` reasoning, and independently reruns verification.

`$execute-goal` never silently substitutes an unpinned model. If that exact model or custom-agent selection is unavailable, it pauses before editing. This is Codex-only; the Claude Code `/saygoal:dec` command is unchanged.

- **Update**: `codex plugin marketplace upgrade saygoal`, then re-run `codex plugin add saygoal@saygoal`.
- **Remove**: `codex plugin remove saygoal@saygoal`, then `codex plugin marketplace remove saygoal`.

<details>
<summary><b>Advanced</b> — short <code>/dec</code>, the optional <code>CLAUDE.md</code> rules, auto-update, Cursor</summary>

**Short `/dec` (no namespace).** The plugin namespaces the command to `/saygoal:dec`. For the bare `/dec`, drop the command file in globally:

```bash
mkdir -p ~/.claude/commands
curl -o ~/.claude/commands/dec.md \
  https://raw.githubusercontent.com/aeopress/saygoal.TW/main/plugin/commands/dec.md
```

**The three `CLAUDE.md` reminders (optional).** Our [A/B test](./EXPERIMENT.md) found no measurable effect on Opus 4.7/4.8 — install only if you want them:

```bash
curl -o CLAUDE.md https://raw.githubusercontent.com/aeopress/saygoal.TW/main/CLAUDE.md
# or append just the rules to an existing CLAUDE.md:
# curl -s https://raw.githubusercontent.com/aeopress/saygoal.TW/main/CLAUDE.md | sed -n '/^## Stop when confused/,$p' >> CLAUDE.md
```

**Auto-updating short `/dec`.** Clone once and symlink, so `git pull` keeps it current:

```bash
mkdir -p ~/.claude/external ~/.claude/commands
git clone https://github.com/aeopress/saygoal.TW ~/.claude/external/saygoal.TW
ln -sf ~/.claude/external/saygoal.TW/plugin/commands/dec.md ~/.claude/commands/dec.md
# update later: cd ~/.claude/external/saygoal.TW && git pull
```

**Cursor.** The repo includes [`.cursor/rules/karpathy-guidelines.mdc`](.cursor/rules/karpathy-guidelines.mdc) (`alwaysApply: true`); see [`CURSOR.md`](./CURSOR.md).

</details>

## Bonus command: `/saygoal:repo-audit`

The plugin also ships `/saygoal:repo-audit` — a principal-level, read-only repo audit (adapted from [OmerFarukOruc's `/repo-audit` gist](https://gist.github.com/OmerFarukOruc/753f95b1ac278b683be83ed26b3bcc1f), tuned for the saygoal pipeline). It maps the repo, fans out parallel subagents per audit dimension, mines git history for churn × complexity hotspots, adversarially verifies every Critical/High finding before reporting it, and writes a single `AUDIT.md` — whose task plan ends **each task with a ready-to-paste `/goal` condition**, so the audit feeds straight into the same declarative loop: audit → task → `/goal`.

It complements `/dec` rather than overlapping it — same pipeline, different trigger and granularity:

| | `/repo-audit` | `/dec` | `/goal` |
|---|---|---|---|
| Role | batch **finder** | single-task **contractor** | **executor** |
| Triggered by | the codebase itself (you don't know the problems yet) | a need already in your head | a condition in hand |
| Output | `AUDIT.md` — a whole task queue | one contract + one condition | loops until green |

Audit tasks already embed `/dec`'s evaluator rules, so they paste straight into `/goal` without another `/dec` pass; `/dec` remains the tool for day-to-day single tasks.

```
/saygoal:repo-audit                  # full audit → AUDIT.md
/saygoal:repo-audit security         # optional focus: a dimension or a path
/saygoal:repo-audit use a workflow   # opt into multi-agent orchestration on big repos
```

Run it in normal mode (not plan mode) and let it run end to end — it's read-only; the only file it creates is `AUDIT.md`.

## The bilevel upgrade — what arXiv 2603.23420 changed here

[Bilevel Autoresearch: Meta-Autoresearching Itself](https://arxiv.org/abs/2603.23420) puts an outer loop on top of Karpathy's autoresearch loop: read the inner loop's trace, find where its search is stuck, rewrite the search mechanism itself, validate, revert on failure. The paper's own framing (§5.3) says Python code is just one carrier of a "mechanism" — skills, prompts, and workflows are equivalent carriers. That maps one-to-one onto this pipeline: **`/goal` is the inner loop, the contract is its search mechanism, and `/dec` was already the human-gated mechanism designer**. Releases v4.6.0–v4.8.0 filled in what the mapping showed was missing:

| Paper mechanism | Already in saygoal | Added (v4.6.0–v4.8.0) |
|---|---|---|
| Inner loop: propose → evaluate → keep/discard | `/goal` (built into Claude Code / Codex) | — |
| Mechanism carrier designed before the run | the contract; `/dec` compiles it | — |
| Evaluator that can't be gamed | "run CMD **and paste the output**" wording; verify-the-verification pre-check | — |
| Structured search trace | — | **trace clause** (v4.6.0): a one-line search log every 5 turns, on search-type tasks |
| Tabu Search — its top generated mechanism | — | **anti-fixation clause** (v4.6.0): never repeat an approach that already failed verification twice |
| Level 2 outer loop: read trace → diagnose → rewrite mechanism | — | **`/saygoal:retro`** (v4.7.0): five stall classes → structural contract rewrite |
| Validate-and-revert on every injection | — | **`rollback:` line** (v4.7.0): every rewrite ships with the original condition verbatim |
| Persistent cross-run memory (the EvoScientist lineage) | — | **`.claude/saygoal.history.jsonl`** (v4.7.0): retro appends, `/dec` grilling reads first |
| Level 1.5 negative result: parameter tweaks gain nothing | — | retro's hard rule (v4.7.0): structural rewrites only — a bigger turn cap alone is forbidden |
| Group B lesson: a frozen parameter walled off the solution | the anti-speculation table auto-adds constraints | retro treats auto-added constraints as the **prime suspect** behind a stall (v4.7.0) |
| Loop cost (from the companion loop-engineering write-up, not the paper) | turn cap | **verification-cost-aware cap** (v4.8.0): expensive checks lower the cap, or per-turn checks go targeted with the full suite last |

> **Same honesty rule as everything else here**: the paper's 5× headline is n = 3 per group with a standard deviation at 67% of the mean, on a single benchmark, and at least one reader reported a failed replication. By this repo's own [`EXPERIMENT.md`](./EXPERIMENT.md) standard ("any N = 3 LLM A/B conclusion is uncertain until N ≥ 10"), treat the number as unverified. What we adopted are the **architecture patterns** — trace, tabu, outer-loop rewrite, validate-and-revert — which are cheap and fail-safe: every clause compiles away on non-search tasks, and every rewrite carries its own rollback.

## Why the rules file isn't the leverage — the receipts

`saygoal` also ships a three-line `CLAUDE.md` (derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876) on LLM coding pitfalls). It's optional — and an A/B test says the rules file barely moves the model.

On Opus 4.8, bug-catching jumped **33% → 90%**, yet the three `CLAUDE.md` variants (v1 / v2 / none) stayed **statistically flat**: the model has already internalized the discipline, so the only leverage left is user-side — that's `/dec`. Most of v1's rules were already verbatim in Claude Code's system prompt; the one genuinely new line ("every changed line traces to the request") is what v2 kept.

Full data, the v1→v2 verbatim mapping, and caveats live in [`EXPERIMENT.md`](./EXPERIMENT.md).

## Relationship to upstream

This repository is a Traditional Chinese (Taiwan) localization fork of [`forrestchang/andrej-karpathy-skills`](https://github.com/forrestchang/andrej-karpathy-skills), updated for the Claude Code Opus 4.7 → 4.8 era. The plugin and marketplace are named `saygoal`; the README is bilingual (English + 繁體中文).

## License

[MIT](./LICENSE) — Copyright © 2026 yelban.

See [Relationship to upstream](#relationship-to-upstream) for attribution.
