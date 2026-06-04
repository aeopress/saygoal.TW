# saygoal

> **say a goal, watch it get done** — a declarative `/dec` + `/goal` workflow for Claude Code & Codex, in the spirit of Karpathy's "give it success criteria and watch it go".

![/dec — Imperative to Declarative](./saygoal.TW.png)

English | [繁體中文（台灣）](./README.zh-TW.md) | [简体中文](./README.zh-CN.md) | [日本語](./README.ja.md)

> **Source of truth**: [`aeopress/saygoal.TW`](https://github.com/aeopress/saygoal.TW) (formerly maintained at [`yelban/andrej-karpathy-skills.TW`](https://github.com/yelban/andrej-karpathy-skills.TW), now archived)

## What it does

`saygoal` turns a vague, imperative request into a **verifiable contract**, then lets the agent loop until that contract is met:

- **`/dec <task>`** rewrites your task into success criteria + a verification command + boundaries, and emits a ready-to-paste **`/goal` condition**.
- Paste that into Claude Code's (or Codex's) built-in **`/goal`** — a small fast model checks the transcript after each turn and keeps the agent working until the condition holds.

**30-second example:**

```
/dec fix the login flicker on first load

→ /goal "run npx playwright test login-flicker.spec.ts until it paste-shows 0 failures
         without changing the auth flow or any file outside the login component
         or stop after 20 turns"
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

Returns success criteria (e.g. "Playwright screenshot diff < 2px across 10 runs"), a verification command worded so Claude must *run it and paste the output*, and on-demand boundaries (what must not change / writable paths / external-system limits) — plus a ready-to-use `/goal` condition in the natural-language `[work] until [end state] without [constraints] or stop after 20 turns` shape you can paste directly. If the task is too subjective or too small, it replies "not applicable — just do it" instead of forcing a conversion. Good for one-shot prompts where you want the declarative discipline without committing to autonomous looping (or when you're on Cursor / an older Claude Code without `/goal`).

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
          or stop after 20 turns"
   Haiku reads the pasted test output from the transcript and judges deterministically.
   The loop actually converges.
```

`/dec` enforces three things that `/goal` alone cannot:

1. **Machine-checkable success conditions** — "diff < 2px", "10 passed", "p95 < X ms" map cleanly to evaluator yes/no.
2. **A verification command embedded in the contract** — forces Claude to actually run the check, not statically reason "this should work now". (Patching-without-running was a real failure mode in our T4 declarative-loop test.)
3. **Structured boundaries (five facets, on demand)** — what must not change, writable paths, external-system limits, pause-if, and a turn cap. For Claude they compile into the condition (`"… without test files changed and no new files in src/legacy/, or stop after 20 turns"`); pause-if is listed separately and is better as a Stop hook, since the evaluator can't judge it.

### The full pipeline

```
1. /dec <vague request>            ← contract + a pre-compiled /goal condition
2. you review the contract         ← human confirms direction
3. paste the /goal line from #1    ← Haiku takes over as judge
4. Claude loops to convergence     ← Karpathy's "watch it go"
```

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

### Codex

From the cloned repo root:

```
codex plugin marketplace add .
codex plugin add saygoal@saygoal
```

Then use `$dec <task>` (or pick it from `/skills`), and paste the generated `/goal "..."` into Codex's built-in `/goal`.

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

## Why the rules file isn't the leverage — the receipts

`saygoal` also ships a three-line `CLAUDE.md` (derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876) on LLM coding pitfalls). It's optional — and an A/B test says the rules file barely moves the model.

On Opus 4.8, bug-catching jumped **33% → 90%**, yet the three `CLAUDE.md` variants (v1 / v2 / none) stayed **statistically flat**: the model has already internalized the discipline, so the only leverage left is user-side — that's `/dec`. Most of v1's rules were already verbatim in Claude Code's system prompt; the one genuinely new line ("every changed line traces to the request") is what v2 kept.

Full data, the v1→v2 verbatim mapping, and caveats live in [`EXPERIMENT.md`](./EXPERIMENT.md).

## Relationship to upstream

This repository is a Traditional Chinese (Taiwan) localization fork of [`forrestchang/andrej-karpathy-skills`](https://github.com/forrestchang/andrej-karpathy-skills), updated for the Claude Code Opus 4.7 → 4.8 era. The plugin and marketplace are named `saygoal`; the README is bilingual (English + 繁體中文).

## License

[MIT](./LICENSE) — Copyright © 2026 yelban.

See [Relationship to upstream](#relationship-to-upstream) for attribution.
