#!/usr/bin/env python3
"""Leak gate over the committed field-test results (must).

Field-test runs are persisted in git, so results must contain no unmasked
secrets. This gate scans every file under the version-scoped results root for
secret material and exits non-zero on any hit — run it before committing results.

Usage::

    python3 scripts/fieldtest/scan_results.py [RESULTS_DIR] [--quiet]

Env: FT_VERSION (default v0.1.0), FT_RESULTS_ROOT.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RESULTS_ROOT = Path(
    os.environ.get("FT_RESULTS_ROOT")
    or (REPO / "field-test" / os.environ.get("FT_VERSION", "v0.1.0") / "results")
)

_PATTERNS = [
    ("openai-key", re.compile(r"sk-[A-Za-z0-9]{16,}")),
    ("bearer", re.compile(r"bearer\s+[A-Za-z0-9._-]{20,}", re.IGNORECASE)),
    ("github-token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("aws-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]

# Known-safe dummy keys the harness injects on purpose.
_ALLOW = re.compile(r"omlx-test|local-test|\[REDACTED\]|_agentpolicy_redacted_")

_SKIP_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".zip", ".gz", ".parquet", ".whl"}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    quiet = "--quiet" in args
    args = [a for a in args if a != "--quiet"]
    root = Path(args[0]) if args else RESULTS_ROOT

    if not root.exists():
        print(f"scan-results: no results at {root} (nothing to scan)")
        return 0

    hits: list[tuple[str, str, int]] = []
    scanned = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() in _SKIP_SUFFIX:
            continue
        scanned += 1
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if _ALLOW.search(line):
                line = _ALLOW.sub("", line)
            for name, pattern in _PATTERNS:
                if pattern.search(line):
                    hits.append((name, str(path.relative_to(root)), lineno))

    if hits:
        print(f"scan-results: {len(hits)} potential secret(s) in {root}:", file=sys.stderr)
        for name, rel, lineno in hits[:50]:
            print(f"  {name}: {rel}:{lineno}", file=sys.stderr)
        if len(hits) > 50:
            print(f"  ... and {len(hits) - 50} more", file=sys.stderr)
        print("\nRefusing to persist unsanitized results. Sanitize and retry.", file=sys.stderr)
        return 1

    if not quiet:
        print(f"scan-results: clean — {scanned} file(s) scanned under {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
