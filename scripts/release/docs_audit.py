#!/usr/bin/env python3
"""M25 25.6 — docs audit: ADRs accepted + relative links resolve.

Walks the markdown tree, checks every ADR carries an **accepted** status (no
lingering *Proposed*), and resolves every **relative** markdown link (http(s),
mailto and pure anchors are skipped). Exits non-zero on any problem (loud
failure), and can write an audit report.

Usage::

    python3 scripts/release/docs_audit.py [--out docs/release/v0.1.0/DOCS_AUDIT.md]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_STATUS = re.compile(r"\*\*Status:\*\*\s*([A-Za-z]+)", re.IGNORECASE)
_SKIP_PREFIX = ("http://", "https://", "mailto:", "#")
_FENCE = re.compile(r"```.*?```", re.DOTALL)


def _strip_code_fences(text: str) -> str:
    """Remove fenced code blocks so code samples aren't parsed as links."""
    return _FENCE.sub("", text)


def _is_skippable(target: str) -> bool:
    t = target.strip()
    if not t or t.startswith(_SKIP_PREFIX):
        return True
    # globs, templates, placeholders, and anything with whitespace/newlines
    if any(ch in t for ch in "*{}<>") or re.search(r"\s", t):
        return True
    return t.startswith(("http", "/"))
_TARGET_ROOTS = ("docs",)


def doc_files() -> list[Path]:
    """All audited markdown files: docs/** plus the repo README + CHANGELOG."""
    files = sorted((REPO / "docs").rglob("*.md"))
    for extra in ("README.md", "CHANGELOG.md"):
        p = REPO / extra
        if p.is_file():
            files.append(p)
    return files


def _strip_anchor(target: str) -> str:
    return target.split("#", 1)[0].strip()


def _rel(f: Path) -> str:
    try:
        return str(f.relative_to(REPO))
    except ValueError:
        return str(f)


def check_links(files: list[Path]) -> list[str]:
    """Return a problem for every relative link whose target does not exist."""
    problems: list[str] = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except OSError as exc:
            problems.append(f"{_rel(f)}: unreadable ({exc})")
            continue
        text = _strip_code_fences(text)
        for raw in _MD_LINK.findall(text):
            target = raw.strip()
            if _is_skippable(target):
                continue
            path = _strip_anchor(target)
            if not path:
                continue
            resolved = (f.parent / path).resolve()
            if not resolved.exists():
                problems.append(f"{_rel(f)}: broken link -> {target}")
    return problems


def check_adrs(adr_dir: Path) -> list[str]:
    """Return a problem for every ADR that is not 'accepted'."""
    problems: list[str] = []
    if not adr_dir.is_dir():
        return [f"ADR directory missing: {adr_dir}"]
    for f in sorted(adr_dir.glob("[0-9]*.md")):
        text = f.read_text(encoding="utf-8")
        m = _STATUS.search(text)
        if not m:
            problems.append(f"{f.name}: no Status line")
            continue
        status = m.group(1).lower()
        if status != "accepted":
            problems.append(f"{f.name}: status is {status!r} (not accepted)")
    return problems


def run(out: Path | None = None) -> list[str]:
    files = doc_files()
    link_problems = check_links(files)
    adr_problems = check_adrs(REPO / "docs" / "adr")
    problems = link_problems + adr_problems
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        status = "**GREEN**" if not problems else f"**{len(problems)} problem(s)**"
        detail = "\n".join(f"- {p}" for p in problems) or "_None._"
        out.write_text(f"""# AgentPolicy v0.1.0 — Docs Audit

> M25 25.6 (issue #273). Automated over {len(files)} markdown files:
> relative links resolve; every ADR is **accepted**.

## Result

{status} — {len(link_problems)} broken link(s), {len(adr_problems)} ADR issue(s).

### Detail

{detail}

## Reproduction

```sh
python3 scripts/release/docs_audit.py
```
""", encoding="utf-8")
    return problems


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="docs audit: links + ADR status")
    p.add_argument("--out", default="docs/release/v0.1.0/DOCS_AUDIT.md")
    a = p.parse_args(argv)
    out = Path(a.out) if a.out else None
    problems = run(out)
    if problems:
        for prob in problems:
            print(f"  FAIL: {prob}", file=sys.stderr)
        print(f"docs audit FAILED: {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print("docs audit: links resolve, all ADRs accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
