#!/usr/bin/env python3
"""Deterministic consistency checks for the saygoal command artifacts.

No LLM, no tokens, no network — pure file invariants. This is the regression
net for a multi-file prompt repo: it catches the mechanical mistakes that a
behavioral eval is too expensive and too noisy to guard against — version
drift across manifests, the Claude command and Codex skill falling out of
sync, READMEs quoting a stale version of a compiled clause, dangling command
references, and a mistyped history-file path that would silently break the
/dec ↔ /retro handoff.

Usage:
  python3 harness/spec/check_consistency.py         # report + exit 1 on any fail
  python3 harness/spec/check_consistency.py -v      # also print passing checks

Grounding note: the anti-fixation / trace clauses are quoted verbatim in the
English and Chinese READMEs but *paraphrased* in the Japanese one, so the
literal-freshness check deliberately excludes README.ja.md.
"""

import json
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
for cmd in ["dec.md", "retro.md", "repo-audit.md"]:
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
for rel in ["plugin/commands/dec.md", "plugin/commands/retro.md", *ALL_READMES]:
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
