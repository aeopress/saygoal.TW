---
name: execute-goal
description: Execute an explicitly confirmed saygoal /goal contract by activating the parent goal, delegating implementation to exactly one pinned saygoal_writer agent, and independently verifying the result. Use after $dec has produced a complete contract and the user has approved it; do not use to draft, revise, or guess a contract.
---

# Execute Goal

Execute a confirmed contract. Keep contract compilation in `$dec`; keep implementation in the pinned writer.

## Preconditions

Require either the full self-contained seven-field `/goal` contract in the request or an unambiguous reference to the most recent contract that the user explicitly confirmed.

Pause without editing when any of these is true:

- the user has not explicitly confirmed the contract;
- an open question, bare `(assumed)`, or unverified `Verification:` target remains;
- another active goal has a different outcome;
- the custom `saygoal_writer` agent is unavailable;
- selecting a custom agent type is unsupported in the current surface.

Do not fall back to the built-in `worker`, a default agent, or a prompt-only model request. Exact model pinning is part of this workflow.

## Preflight

1. Read the confirmed contract and the applicable `AGENTS.md` files.
2. Confirm the declared verification target still exists and is runnable with read-only checks.
3. Require that the current effective sandbox mode is exactly `workspace-write`. Parent live runtime overrides are reapplied to children, so pause if it is read-only or danger-full-access; do not change the permission mode automatically.
4. Capture a content-complete dirty baseline: `git status --short`, `git diff --binary`, `git diff --cached --binary`, and content hashes for every untracked path. If the contract's write scope overlaps a pre-existing dirty path, pause for the user's decision before delegation. After implementation, compare the protected dirty paths byte-for-byte against this baseline.
5. Confirm the effective custom-agent identity, not its name alone. Require exactly one matching definition for `name = "saygoal_writer"` and verify these active values against the bundled template: `model = "gpt-5.6-sol"`, `model_reasoning_effort = "high"`, and `sandbox_mode = "workspace-write"`. Compare the normalized full effective definition, including `developer_instructions`, byte-for-byte with the bundled template; pause on any difference. Use the runtime's effective agent catalog when available; otherwise inspect project `.codex/agents/*.toml` and personal `~/.codex/agents/*.toml`, pausing on duplicates or precedence ambiguity. Also confirm that the exact model is available in the current account.
6. If the agent is missing or differs from the template, read [references/saygoal-writer.toml](references/saygoal-writer.toml), offer to install or repair that exact template at either `.codex/agents/saygoal-writer.toml` or `~/.codex/agents/saygoal-writer.toml`, and pause. Never overwrite an existing definition without showing the difference and receiving approval. Installing to the personal path requires approval. Tell the user to start a new thread after installation so Codex discovers the agent.

## Activate the goal

Call `get_goal` first.

- With no active goal, call `create_goal` using the full confirmed contract as the objective.
- With a matching active goal, continue it without replacing it.
- With a different active goal, pause for the user to resolve it.

Do not create a goal before the pinned writer and verification target pass preflight.

## Delegate implementation

Spawn exactly one subagent using the custom agent type `saygoal_writer`. Include in its task:

- the full confirmed contract;
- the working directory;
- the content-complete dirty baseline and protected dirty paths;
- the requirement to implement, run the declared verification, and return a per-item implemented/deviated report when the contract has multiple deliverables.

Do not edit in the parent thread while the writer is active. Wait for its result. If verification later fails and the contract permits another attempt, send one focused follow-up to the same writer; do not spawn parallel writers.

## Verify independently

After the writer returns:

1. Inspect `git status --short` and the complete diff. Compare every protected dirty path byte-for-byte with the preflight baseline, preserve every pre-existing user change, and reject writes outside `Boundaries:`.
2. Rerun the contract's declared verification in the parent thread. Do not accept the writer's claim as evidence by itself.
3. Run any final full-suite gate named by the contract after targeted checks pass.
4. Check every `Constraints:`, `Stop when:`, and `Pause if:` clause and require the deviation report when applicable.

Call `update_goal` with `complete` only after all inspectable evidence proves the outcome. Use `blocked` only when the goal tool's repeated-blocker threshold is actually satisfied. Otherwise keep the goal active and report the concrete next attempt or pause condition.

End with the verification output, files changed by this workflow, and any deviations. Never claim the pinned model was used unless the spawned agent was actually `saygoal_writer`.
