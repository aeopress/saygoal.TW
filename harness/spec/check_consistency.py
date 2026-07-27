#!/usr/bin/env python3
"""Deterministic consistency checks for the saygoal command artifacts.

No LLM, no tokens, no network — pure file invariants. This is the regression
net for a multi-file prompt repo: it catches the mechanical mistakes that a
behavioral eval is too expensive and too noisy to guard against — version
drift across manifests, the Claude command and Codex skill falling out of
sync, READMEs quoting a stale version of a compiled clause, dangling command
references, and a mistyped history-file path that would silently break the
/dec ↔ /retro handoff. It also pins the Codex-only execute-goal delegation
contract and its custom writer-agent template.

Usage:
  python3 harness/spec/check_consistency.py         # report + exit 1 on any fail
  python3 harness/spec/check_consistency.py -v      # also print passing checks

Grounding note: the anti-fixation / trace clauses are quoted verbatim in the
English and Chinese READMEs but *paraphrased* in the Japanese one, so the
literal-freshness check deliberately excludes README.ja.md.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERBOSE = "-v" in sys.argv[1:]

# Canonical literals — the invariants worth pinning. Chosen as the byte-identical
# substring shared across every file that carries the clause (dec.md uses
# "repeating", SKILL.md uses "repeat", so the shared core omits that word).
ANTI_FIXATION = "an approach whose verification output has already failed twice"
TRACE_MARKER = "one-line search log"
HISTORY_PATH = ".claude/saygoal.history.jsonl"
TRACE_FILE = ".claude/saygoal.trace.log"
INVARIANTS_FILE = ".claude/saygoal.invariants.md"
DEFAULT_CAP = "stop after 12 turns"
STALE_CAP = "stop after 20 turns"
STOPCHECK_FILE = ".claude/saygoal.stop-check.sh"

# READMEs that quote the English clause verbatim (ja paraphrases → excluded).
READMES_QUOTING = ["README.md", "README.zh-CN.md", "README.zh-TW.md"]
ALL_READMES = ["README.md", "README.zh-CN.md", "README.zh-TW.md", "README.ja.md"]

BILEVEL_HEADING = {
    "README.md": "## The bilevel upgrade",
    "README.zh-TW.md": "## Bilevel 升級",
    "README.zh-CN.md": "## Bilevel 升级",
    "README.ja.md": "## Bilevel アップグレード",
}

STALL_CLASSES = ["驗證斷裂", "門檻不可達", "邊界牆住正解", "固著", "範圍錯置"]

results = []  # (ok: bool, name: str, detail: str)


def check(name, ok, detail=""):
    results.append((bool(ok), name, detail))


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def markdown_section(text, heading):
    """Return one level-2 Markdown section without later peer sections."""
    marker = f"## {heading}"
    start = text.find(marker)
    if start == -1:
        return ""
    start += len(marker)
    next_heading = re.search(r"(?m)^## ", text[start:])
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end]


def active_toml_string(text, key):
    """Read one active, single-line TOML string assignment (never comments)."""
    outside_multiline = []
    multiline_delimiter = None
    for line in text.splitlines():
        if multiline_delimiter:
            if multiline_delimiter in line:
                multiline_delimiter = None
            continue
        delimiter = next((d for d in ('"""', "'''") if d in line), None)
        if delimiter:
            outside_multiline.append(line.split(delimiter, 1)[0])
            if line.count(delimiter) % 2:
                multiline_delimiter = delimiter
            continue
        outside_multiline.append(line)

    match = re.search(
        rf'(?m)^[ \t]*{re.escape(key)}[ \t]*=[ \t]*"([^"\r\n]+)"[ \t]*(?:#.*)?$',
        "\n".join(outside_multiline),
    )
    return match.group(1) if match else None


def execute_goal_invariants(execute, writer):
    """Public workflow invariants, grouped by the section that owns them."""
    preconditions = markdown_section(execute, "Preconditions")
    preflight = markdown_section(execute, "Preflight")
    activation = markdown_section(execute, "Activate the goal")
    delegation = markdown_section(execute, "Delegate implementation")
    verification = markdown_section(execute, "Verify independently")
    unsafe_directives = re.sub(
        r"(?i)(?:do not|never)\s+spawn\s+parallel\s+writers?",
        "",
        execute,
    )
    unsafe_extra_writer = re.search(
        r"(?i)spawn[^\n]*(?:second|two|another|parallel)[^\n]*writer",
        unsafe_directives,
    )

    return {
        "confirmed_contract": (
            "- the user has not explicitly confirmed the contract;" in preconditions
            and "Pause without editing" in preconditions
        ),
        "parent_goal": (
            "Call `get_goal` first." in activation
            and "call `create_goal`" in activation
            and "Call `update_goal`" in verification
        ),
        "single_pinned_writer": (
            "Spawn exactly one subagent using the custom agent type `saygoal_writer`."
            in delegation
            and "do not spawn parallel writers" in delegation.lower()
            and unsafe_extra_writer is None
        ),
        "no_unpinned_fallback": (
            "Do not fall back" in preconditions
            and "Pause without editing" in preconditions
        ),
        "independent_verification": (
            "Rerun the contract's declared verification in the parent thread."
            in verification
            and "Do not accept the writer's claim as evidence by itself."
            in verification
        ),
        "writer_model": (
            active_toml_string(writer, "model") == "gpt-5.6-sol"
            and active_toml_string(writer, "model_reasoning_effort") == "high"
        ),
        "writer_safety": (
            active_toml_string(writer, "sandbox_mode") == "workspace-write"
            and "Do not spawn subagents" in writer
        ),
        "effective_writer_identity": (
            'model = "gpt-5.6-sol"' in preflight
            and 'model_reasoning_effort = "high"' in preflight
            and 'sandbox_mode = "workspace-write"' in preflight
            and "exactly one matching definition" in preflight.lower()
            and "normalized full effective definition, including"
            in preflight.lower()
            and "byte-for-byte" in preflight.lower()
        ),
        "dirty_baseline": (
            "`git diff --binary`" in preflight
            and "`git diff --cached --binary`" in preflight
            and "content hashes for every untracked path" in preflight
            and "overlaps a pre-existing dirty path" in preflight
        ),
        "effective_workspace": (
            "current effective sandbox mode is exactly `workspace-write`"
            in preflight
        ),
    }


# ---------------------------------------------------------------- version sync
def collect_versions():
    """Every version field that must move together on a release."""
    mp = json.loads(read(".claude-plugin/marketplace.json"))
    plug = json.loads(read("plugin/.claude-plugin/plugin.json"))
    codex = json.loads(read("plugins/saygoal/.codex-plugin/plugin.json"))
    return {
        "marketplace.metadata.version": mp["metadata"]["version"],
        "marketplace.plugins[0].version": mp["plugins"][0]["version"],
        "plugin/.claude-plugin/plugin.json": plug["version"],
        "codex-plugin/plugin.json": codex["version"],
    }


try:
    versions = collect_versions()
    unique = set(versions.values())
    check(
        "version sync across all manifests",
        len(unique) == 1,
        f"all {next(iter(unique))}" if len(unique) == 1 else f"DRIFT: {versions}",
    )
except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
    check("manifests parse as JSON with expected shape", False, repr(e))


# --------------------------------------------------------------- command files
for cmd in ["dec.md", "retro.md", "repo-audit.md", "judge.md"]:
    p = ROOT / "plugin" / "commands" / cmd
    check(f"command file present & non-empty: {cmd}",
          p.exists() and p.stat().st_size > 0,
          "" if p.exists() else "missing")


# ------------------------------------------------ Claude command ↔ Codex skill
dec = read("plugin/commands/dec.md")
skill = read("plugins/saygoal/skills/dec/SKILL.md")

check("anti-fixation clause mirrored: dec.md ↔ SKILL.md",
      ANTI_FIXATION in dec and ANTI_FIXATION in skill,
      f"dec={ANTI_FIXATION in dec} skill={ANTI_FIXATION in skill}")
check("trace-log clause mirrored: dec.md ↔ SKILL.md",
      TRACE_MARKER in dec and TRACE_MARKER in skill,
      f"dec={TRACE_MARKER in dec} skill={TRACE_MARKER in skill}")
check("verification-cost rule mirrored: dec.md ↔ SKILL.md",
      "驗證成本" in dec and "verification cost" in skill.lower(),
      f"dec={'驗證成本' in dec} skill={'verification cost' in skill.lower()}")
check("Codex dec offers execute-goal only after confirmation",
      "$execute-goal" in skill and "do not invoke it automatically" in skill.lower())


# ---------------------------------------------------------- retro completeness
retro = read("plugin/commands/retro.md")
missing_classes = [c for c in STALL_CLASSES if c not in retro]
check("retro.md names all five stall classes", not missing_classes,
      f"missing: {missing_classes}" if missing_classes else "all present")
check("retro.md ships a rollback: line", "rollback:" in retro)
check("retro.md forbids parameter-only rewrites (Level 1.5 negative result)",
      "結構性重寫" in retro and "無效" in retro)
check("retro.md appends the history file", HISTORY_PATH in retro)


# ------------------------------------------------------- history-path handshake
# dec (reader) and retro (writer) must agree on the exact path, byte for byte.
check("history path agrees: retro writes it, dec reads it",
      HISTORY_PATH in retro and HISTORY_PATH in dec,
      f"retro={HISTORY_PATH in retro} dec={HISTORY_PATH in dec}")
# No near-miss variant anywhere (e.g. a dash or wrong dir would break silently).
variant_files = []
for rel in ["plugin/commands/dec.md", "plugin/commands/retro.md",
            "plugin/commands/judge.md", *ALL_READMES]:
    txt = read(rel)
    if "saygoal.history" in txt and HISTORY_PATH not in txt:
        variant_files.append(rel)
check("no mistyped history-path variant", not variant_files,
      f"variants in: {variant_files}" if variant_files else "clean")


# ------------------------------------------------ delegation channels (v4.9.0)
# The bare `codex exec` channel must be wired end to end: detected in dec.md,
# present in the preference enum, and documented in every README.
check("dec.md detects the codex exec channel", "`command -v codex`" in dec,
      "" if "`command -v codex`" in dec else "missing `command -v codex`")
check("dec.md preference enum includes codex-exec", '"codex-exec"' in dec)
missing_deleg = [r for r in ALL_READMES if "codex exec" not in read(r)]
check("every README documents the codex exec delegation channel",
      not missing_deleg, f"missing in: {missing_deleg}" if missing_deleg else "all four")


# ------------------- P1: verification surface, delegated trace, invariants (2026-07-26)
# The verification-surface facet must exist on both platforms; the delegated
# trace file must be named byte-identically by its writer clause (dec) and its
# reader (retro); dec must read the project invariants file; repo-audit must
# not suppress findings at the finder — the gate is the mechanical file:line
# check plus the refuter.
audit = read("plugin/commands/repo-audit.md")

check("verification-surface facet mirrored: dec.md ↔ SKILL.md",
      "量尺路徑" in dec and "verification surface" in skill.lower(),
      f"dec={'量尺路徑' in dec} skill={'verification surface' in skill.lower()}")
check("harvest audits the verification surface before semantic review",
      "收割三件套" in dec and "拒收" in dec)
check("trace-file handshake: dec (writer clause) ↔ retro (reader)",
      TRACE_FILE in dec and TRACE_FILE in retro,
      f"dec={TRACE_FILE in dec} retro={TRACE_FILE in retro}")
trace_variants = [rel for rel in ["plugin/commands/dec.md", "plugin/commands/retro.md",
                                  "plugin/commands/judge.md"]
                  if "saygoal.trace" in read(rel) and TRACE_FILE not in read(rel)]
check("no mistyped trace-file variant", not trace_variants,
      f"variants in: {trace_variants}" if trace_variants else "clean")
check("dec.md reads the project invariants file", INVARIANTS_FILE in dec)
check("repo-audit finders report everything; the gate is downstream",
      "全報" in audit and "寧要 15 個高信心" not in audit)
check("repo-audit mechanically verifies cited file:line before the refuter",
      "行號" in audit and "file:line" in audit)


# --------------------------------------- P2: default turn cap (2026-07-26)
# The default cap moved 20 → 12 for the Claude 5 generation (a turn now does
# far more work; the cap is a stop-loss, not an allowance). The default must
# agree between dec.md (rule + example) and repo-audit.md (per-task /goal
# conditions), and no file may still quote the retired 20-turn default.
check("default turn cap agrees: dec.md ↔ repo-audit.md",
      DEFAULT_CAP in dec and DEFAULT_CAP in audit,
      f"dec={DEFAULT_CAP in dec} audit={DEFAULT_CAP in audit}")
stale_cap = [rel for rel in
             ["plugin/commands/dec.md", "plugin/commands/repo-audit.md", *ALL_READMES]
             if STALE_CAP in read(rel)]
check("no file still quotes the retired 20-turn default", not stale_cap,
      f"stale in: {stale_cap}" if stale_cap else "clean")


# ------------------------------------ P3: compiled stop-check (2026-07-26)
# The gate the whole loop rests on must not be adjudicated by the implementing
# model: dispatch compiles the contract into an executable stop-check whose
# exit code decides acceptance, and harvest runs that script first. The path
# must appear both at the compile rule and at the harvest step.
check("dec.md compiles the stop-check at dispatch and runs it at harvest",
      dec.count(STOPCHECK_FILE) >= 2,
      f"occurrences={dec.count(STOPCHECK_FILE)}")
stopcheck_variants = [rel for rel in ["plugin/commands/dec.md", "plugin/commands/retro.md",
                                      "plugin/commands/judge.md"]
                      if "saygoal.stop-check" in read(rel) and STOPCHECK_FILE not in read(rel)]
check("no mistyped stop-check variant", not stopcheck_variants,
      f"variants in: {stopcheck_variants}" if stopcheck_variants else "clean")

# The delegated-run mechanisms are user-visible: every README must name the
# two artifacts a delegated contract lands, in every language.
missing_stopcheck = [r for r in ALL_READMES if STOPCHECK_FILE not in read(r)]
check("every README documents the compiled stop-check", not missing_stopcheck,
      f"missing in: {missing_stopcheck}" if missing_stopcheck else "all four")
missing_trace = [r for r in ALL_READMES if TRACE_FILE not in read(r)]
check("every README documents the delegated trace file", not missing_trace,
      f"missing in: {missing_trace}" if missing_trace else "all four")


# -------------------------------- judge acceptance gate (v4.12.0, 2026-07-27)
# /saygoal:judge is the pipeline's acceptance gate (adapted from fable-judge in
# Sahir619/fable-method, MIT, re-anchored on the contract). Pinned: the full
# verdict taxonomy, the claims-not-evidence stance, re-run + UNVERIFIABLE
# labeling, the authority order, read-and-run-only, the contract anchors
# (surface + stop-check), and the shared-history handshake with /dec.
judge = read("plugin/commands/judge.md")

check("judge verdict taxonomy is complete",
      all(v in judge for v in ["VERIFIED", "VERIFIED WITH CAVEATS", "REFUTED"]))
check("judge treats reports as claims, not evidence",
      "主張的集合,不是證據" in judge)
check("judge re-runs claimed verifications and labels the un-runnable",
      "UNVERIFIABLE" in judge and "重跑" in judge)
check("judge pins the authority order",
      "使用者明示 > 規格 > 測試 > 現行程式碼行為" in judge)
check("judge never fixes — read-and-run only",
      "不修任何東西" in judge)
check("judge audits the verification surface and runs the stop-check",
      "量尺" in judge and STOPCHECK_FILE in judge)
check("judge appends the shared history file with verdict outcomes",
      HISTORY_PATH in judge and '"verified"' in judge and '"refuted"' in judge)
check("dec reads judge verdicts from the history file",
      "saygoal:judge" in dec and HISTORY_PATH in dec)
check("dec harvest names the judge as its invocable form",
      "收割程序的可叫用形式是 `/saygoal:judge`" in dec)
check("judge declares the conflict-of-interest rule (fresh-context verifier)",
      "利益衝突" in judge)
missing_judge_docs = [r for r in ALL_READMES if "saygoal:judge" not in read(r)]
check("every README documents /saygoal:judge and the command exists",
      not missing_judge_docs and (ROOT / "plugin/commands/judge.md").exists(),
      f"missing in: {missing_judge_docs}" if missing_judge_docs else "all four")


# ----------------------------------------- Codex execute-goal seam (v4.10.0)
execute_path = ROOT / "plugins/saygoal/skills/execute-goal/SKILL.md"
writer_path = execute_path.parent / "references/saygoal-writer.toml"
check("Codex execute-goal skill is present & non-empty",
      execute_path.exists() and execute_path.stat().st_size > 0,
      "" if execute_path.exists() else "missing")
check("pinned saygoal writer template is present & non-empty",
      writer_path.exists() and writer_path.stat().st_size > 0,
      "" if writer_path.exists() else "missing")

if execute_path.exists() and writer_path.exists():
    execute = execute_path.read_text(encoding="utf-8")
    writer = writer_path.read_text(encoding="utf-8")
    invariants = execute_goal_invariants(execute, writer)

    check("execute-goal requires an explicitly confirmed contract",
          invariants["confirmed_contract"])
    check("execute-goal owns the parent /goal lifecycle",
          invariants["parent_goal"])
    check("execute-goal dispatches exactly one pinned writer",
          invariants["single_pinned_writer"])
    check("execute-goal refuses an unpinned worker fallback",
          invariants["no_unpinned_fallback"])
    check("execute-goal independently verifies writer output",
          invariants["independent_verification"])
    check("writer pins gpt-5.6-sol at high reasoning", invariants["writer_model"])
    check("writer is workspace-write and cannot delegate further",
          invariants["writer_safety"])
    check("execute-goal verifies the effective writer identity",
          invariants["effective_writer_identity"])
    check("execute-goal preserves a content-complete dirty baseline",
          invariants["dirty_baseline"])
    check("execute-goal requires effective workspace-write",
          invariants["effective_workspace"])

    contradictory_execute = execute.replace(
        "do not spawn parallel writers.", "spawn a second writer."
    )
    commented_model = writer.replace(
        'model = "gpt-5.6-sol"', '# model = "gpt-5.6-sol"'
    )
    self_report_only = execute.replace(
        "Rerun the contract's declared verification in the parent thread.",
        "Accept the writer's verification report.",
    )
    confirmation_guard_removed = execute.replace(
        "- the user has not explicitly confirmed the contract;", ""
    )
    model_only_in_instructions = commented_model.replace(
        'developer_instructions = """',
        'developer_instructions = """\nmodel = "gpt-5.6-sol"',
    )
    check("execute-goal negative control rejects a second writer",
          not execute_goal_invariants(contradictory_execute, writer)["single_pinned_writer"])
    check("execute-goal negative control rejects a commented model pin",
          not execute_goal_invariants(execute, commented_model)["writer_model"])
    check("execute-goal negative control rejects self-report-only verification",
          not execute_goal_invariants(self_report_only, writer)["independent_verification"])
    check("execute-goal negative control rejects a missing confirmation guard",
          not execute_goal_invariants(confirmation_guard_removed, writer)["confirmed_contract"])
    check("execute-goal negative control ignores model text inside instructions",
          not execute_goal_invariants(execute, model_only_in_instructions)["writer_model"])

check("Claude plugin has no execute-goal command",
      not (ROOT / "plugin/commands/execute-goal.md").exists())
missing_execute_docs = [r for r in ALL_READMES if "$execute-goal" not in read(r)]
check("every README documents the Codex-only execute-goal skill",
      not missing_execute_docs,
      f"missing in: {missing_execute_docs}" if missing_execute_docs else "all four")


# --------------------------------------------------- README literal freshness
# The READMEs that quote the compiled clause must quote the *current* clause.
stale = [r for r in READMES_QUOTING if ANTI_FIXATION not in read(r)]
check("English/Chinese READMEs quote the current anti-fixation clause",
      not stale, f"stale/paraphrased: {stale}" if stale else "fresh")
stale_trace = [r for r in READMES_QUOTING if TRACE_MARKER not in read(r)]
check("English/Chinese READMEs quote the current trace clause",
      not stale_trace, f"stale: {stale_trace}" if stale_trace else "fresh")


# ------------------------------------------------------------- README parity
for rel, heading in BILEVEL_HEADING.items():
    check(f"bilevel section present: {rel}", heading in read(rel),
          "" if heading in read(rel) else f"missing heading {heading!r}")

# Every README that advertises /saygoal:retro must have the command backing it.
retro_exists = (ROOT / "plugin" / "commands" / "retro.md").exists()
for rel in ALL_READMES:
    if "saygoal:retro" in read(rel):
        check(f"{rel} references /saygoal:retro and the command exists",
              retro_exists)


# ------------------------------------------------------------- arXiv citation
# The bilevel work is attributed; a broken/absent id would mislead readers.
ARXIV = "2603.23420"
for rel in ALL_READMES:
    if BILEVEL_HEADING[rel] in read(rel):
        check(f"{rel} cites arXiv {ARXIV} in the bilevel section",
              ARXIV in read(rel))


# --------------------------------------------------------------------- report
fails = [r for r in results if not r[0]]
width = max(len(name) for _, name, _ in results)
print(f"=== saygoal command consistency: {len(results)} checks, "
      f"{len(results) - len(fails)} passed, {len(fails)} failed ===\n")
for ok, name, detail in results:
    if ok and not VERBOSE:
        continue
    mark = "PASS" if ok else "FAIL"
    line = f"[{mark}] {name.ljust(width)}"
    if detail:
        line += f"  — {detail}"
    print(line)

if fails:
    print(f"\n{len(fails)} check(s) failed.")
    sys.exit(1)
print(f"\nAll {len(results)} checks passed.")
