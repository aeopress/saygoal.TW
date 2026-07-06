---
name: dec
description: Convert an imperative coding request into a declarative Codex /goal contract — outcome, verification, constraints, boundaries, iteration policy, stop and pause conditions. Use before implementation; do not edit files.
---

<!-- platform: Codex (skill) · output: seven-field /goal template -->
<!-- Running in Claude Code? Use plugin/commands/dec.md instead, which outputs a single natural-language /goal condition. -->

# Dec Skill

`dec` is short for **declarative**. Convert the user's request into a Codex `/goal` contract. **Do not implement.**

Use this skill when the user invokes `$dec`, selects the `dec` skill, or asks to turn a coding task into a Codex `/goal`.

---

## Not applicable — check first

If the task is **subjective** (UI taste, copy, naming, visual polish), **too small** (typo, one-line rename), or has **no verifiable end state**, reply:

```text
不適用，建議直接做
```

Do not force a contract when there is no meaningful verifiable end state.

---

## Grill open fields first — after applicability, before compiling

A contract only converges when no question remains. Before compiling, find the fields you could otherwise only fill by guessing — the success threshold, whether the verification target exists, the writable boundaries, tentative scope — and **resolve them by asking**, not by papering over them with `(assumed)`.

- **Ask one question at a time**, each with your recommended answer. If a read-only check can answer it (does the test file exist, is the script in package.json), check instead of asking.
- **Translate taste-based constraints into context, never copy them**: when the user says "keep it simple", "don't overengineer", or "quick and dirty", ask for the underlying reason as a fixed-choice question, recommending one option: **experimental, likely short-lived** / **deadline pressure, working first** / **long-lived production feature** — and encode the answer in the optional `Context:` field. Constraints can only enumerate what not to do; context lets the implementer decide correctly in situations the constraints did not anticipate.
- After each question, stop and wait — do not emit the contract before the user answers.
- If everything is already clear, skip grilling and compile directly. Do not interrogate an already-precise request.

**Contract done**: no bare `(assumed)` remains and every `Verification:` target is confirmed runnable. Grill until no open question is left, then output.

---

## Output: seven-field Codex `/goal` template

Fill all seven fields. Omit a field only if genuinely not applicable, and say why — do not pad it.

`Context:` is an **optional eighth line**: include it only when grilling surfaced intent (experiment vs long-lived, expected lifespan, deadline) or the user supplied it; otherwise omit the line silently — never pad it with "N/A".

```text
/goal [Outcome — one sentence stating the observable end state, not an action].
Context: [optional — why this task exists / expected lifespan, e.g. "throwaway experiment, likely deleted in a month — don't build anything painful to throw away"].
Verification: [command / artifact / evidence that proves completion; runnable or inspectable by Codex].
Constraints: [what must not change — behavior, public APIs, test assertions].
Boundaries: [allowed write paths / forbidden paths; external systems read-only or draft-only].
Iteration policy: make one focused change, rerun verification after each change, log each attempt result before the next.
Stop when: [verification exits 0 / artifact exists / evidence proves the outcome].
Pause if: [blocked / needs human decision / destructive operation / N consecutive failures / conflicting docs].
```

The **Iteration policy** above is a sensible default — keep it verbatim unless the user gives a specific strategy (e.g. "try at most 3 approaches before pausing"). The user does not need to supply it.

---

## Contract quality rules

- **Verify the verification first**: before emitting the contract, confirm with read-only checks that the `Verification:` target actually runs (test file exists, script is defined in package.json, binary is on PATH). If it doesn't exist yet, flag `⚠ verification does not exist yet — create it first` and make creating it the first step; otherwise the `/goal` loop fails on turn one. When creating the verification target is itself the task's deliverable (e.g. "write a script"), apply the same flag and make creating it step one — that is not a contradiction.
- **Mark invented thresholds**: ask for any numeric threshold the user did not supply (see grilling above); only if they tell you to pick does it get `(assumed — confirm)`, so a guess is never mistaken for a requirement.
- **Multi-part specs end with a per-item deviation report**: when the Outcome covers multiple spec items, extend `Verification:` and `Stop when:` to require a pasted completion report listing each item as implemented / deviated (with the difference explained). Items are independently acceptable deliverables (separate files, features, or verification paths); multiple dimensions of one deliverable do not count. The report is inspectable evidence, and it closes the failure mode where the loop converges but silently deviated from the spec.
- **Self-contained**: the `/goal` block will be pasted into a fresh session — no references to conversation context ("as discussed", "the function above"). File names, paths, and thresholds are spelled out inside the block.

---

## Internal rule: anti-speculation auto-fill (apply silently, do not echo this table)

Merge the matching constraint into the `Constraints:` field based on task keywords. Respect context: if the target is a UI element, CSS class, or scratch object, do **not** trigger the data-layer constraint.

| Task keyword | Auto-add to Constraints |
|---|---|
| performance / optimize / latency / benchmark | without removing any existing feature or test coverage |
| refactor / migrate / restructure | without changing observable behavior; existing tests must still pass |
| test / CI | without skipping, commenting out, or weakening any existing assertion |
| coverage | without adding trivially-true assertions that inflate the number |
| API / webhook / email / send / deploy / publish | in read-only or draft mode; do not send, deploy, or publish without explicit confirmation |
| delete / drop / remove (data, persistence) | pause before any irreversible deletion and surface the target first |
| auth / token / permission | do not change the authentication flow or token validation logic |
| "later" / "future" / "v2" / "could consider" (tentative phrasing) | treat as a non-goal unless success criteria explicitly require it |
| "keep it simple" / "don't overengineer" / "quick and dirty" (taste-based constraint) | do not merge into Constraints — grill for the underlying context (experiment? lifespan? deadline?) and encode it in `Context:` |

---

## Pause-if examples

```text
Pause if: the relevant file or test cannot be found; a required credential is missing；
a step would delete or overwrite data not created by this session; documentation contradicts the
task; 3 consecutive verifications fail without a new approach.
```

---

After output, wait for the user to confirm. On confirmation, the user pastes the generated `/goal` block into Codex CLI.
