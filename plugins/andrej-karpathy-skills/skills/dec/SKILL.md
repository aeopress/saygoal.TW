---
name: dec
description: Convert an imperative coding request into a declarative contract with success criteria, a verification command, non-goals, and a ready-to-use Codex /goal condition. Use before implementation; do not edit files.
---

# Dec Skill

`dec` is short for declarative. Convert the user's request into a declarative contract. Do not implement.

Use this skill when the user invokes `$dec`, selects the `dec` skill, or asks to turn a coding task into success criteria for Codex `/goal`.

Output four blocks:

1. **成功條件 (Success criteria)**: verifiable end state, such as tests passing, output matching, a performance threshold, lint clean, or a concrete manual check when no command exists.
2. **驗證指令 (Verification command)**: a specific runnable command or check, such as `bun test foo.spec.ts`, `npx playwright test login.spec.ts`, `scripts/bench.sh`, or `manual check: ...`.
3. **非目標 (Non-goals)**: explicit scope boundaries for what this task must not change.
4. **Ready-to-use Codex `/goal` condition**: combine #1 and #3 into one Codex `/goal` string. Join compound conditions with `AND`.

Example:

```text
/goal "npx playwright test login.spec.ts passes AND login component file remains unchanged from baseline"
```

After outputting the four blocks, wait for the user to confirm. Confirmation can mean implementing directly from the contract, or using the generated `/goal` condition in Codex.

If the task is subjective, such as UI taste, wording, naming, or visual polish, or if it is too small, such as a typo or one-line rename, reply:

```text
不適用，建議直接做
```

Do not force a declarative contract when the task has no meaningful verifiable end state.
