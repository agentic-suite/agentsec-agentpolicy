#!/usr/bin/env python3
"""Run a pytest selection as a *grounded* field-test assertion.

Deep verification: a field-test pass must not rest on "pytest exited 0" when the
tests were actually skipped or none ran. This driver fails (exit 1) if:

  * pytest exits non-zero, or
  * any test was **skipped** (agentpolicy's field policy: a skip is a failure), or
  * no test ran at all.

On success it prints the pass/skip/fail counts and ``ok: ...``.

Usage::

    python3 run_pytest.py tests/test_m12_budgets.py [MORE ...] \\
        [--marker omlx] [--allow-skip] [-k EXPR]
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(argv: list[str]) -> int:
    files: list[str] = []
    marker: str | None = None
    allow_skip = False
    extra: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--marker":
            marker = argv[i + 1]
            i += 2
            continue
        if a == "--allow-skip":
            allow_skip = True
            i += 1
            continue
        if a == "-k":
            extra += ["-k", argv[i + 1]]
            i += 2
            continue
        files.append(a)
        i += 1

    if not files:
        print("run_pytest: no test files given", file=sys.stderr)
        return 2

    cmd = [sys.executable, "-m", "pytest", *files, "-q", "-rs",
           "-p", "no:cacheprovider", "--no-header"]
    if marker:
        cmd += ["-m", marker]
    cmd += extra

    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    out = proc.stdout + proc.stderr
    sys.stdout.write(out)

    if proc.returncode != 0:
        print(f"fail: pytest exited {proc.returncode}", file=sys.stderr)
        return 1

    def _count(kind: str) -> int:
        m = re.search(rf"(\d+) {kind}", out)
        return int(m.group(1)) if m else 0

    passed = _count("passed")
    skipped = _count("skipped")
    failed = _count("failed")
    errors = _count("error")
    if failed or errors:
        print(f"fail: {failed} failed, {errors} error", file=sys.stderr)
        return 1
    if passed == 0:
        print("fail: no tests ran", file=sys.stderr)
        return 1
    if skipped and not allow_skip:
        print(f"fail: {skipped} test(s) skipped (a skip is a failure)", file=sys.stderr)
        return 1

    print(f"ok: {passed} passed, {skipped} skipped (marker={marker or '-'}), 0 failed")
    return 0


if __name__ == "__main__":  # pragma: no cover - process entry point
    raise SystemExit(main(sys.argv[1:]))
