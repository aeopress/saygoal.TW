# CLAUDE.md

Notes that complement Claude Code's built-in guidance. Apply to code work; for non-code tasks (writing, docs, design), use judgment.

## Stop when confused

If a request is ambiguous, name what is unclear and ask. Do not pick an interpretation silently. This applies *before* writing code, not after the fact.

## Every changed line should trace to the request

Before reporting done, re-read your own diff. If a line does not directly serve the user's stated goal, remove it. This is the working definition of "surgical changes."

## Prompt authoring: bilingual anchors

The Chinese prompts anchor key concepts bilingually —「弱化檢查(test tampering)」「量尺路徑(verification surface)」. Keep both halves when editing: the English anchor is what makes decompression reliable across models and corpora; the payoff is decompression stability, not brevity. Never compress checklists, literal constraint strings, or anything embedded in a `/goal` condition (the Haiku evaluator only pattern-matches — keep those fully explicit).

Rewording an anchor also moves the measuring stick: output vocabulary tracks prompt vocabulary almost exactly (see the 2026-07-28 scale run in `harness/spec/README.md`), so any check pinned to the old wording — `check_consistency.py` constants, case oracles — must be updated in the same change. Extend it with synonyms for the new wording and keep the semantic bar where it was; never loosen a check to make a run go green.

## Loop on declarative goals

When the user gives a verifiable end state (tests pass, output matches, lint clean, benchmark below X), drive toward it autonomously. When they give imperative steps, follow them.

If the request is imperative but an obvious success criterion exists, propose the declarative version first ("I can verify this by Y — okay to drive toward that?") rather than guessing.
