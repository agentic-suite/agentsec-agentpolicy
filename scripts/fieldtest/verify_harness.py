#!/usr/bin/env python3
"""Verify the verifier — the field harness's own gate must actually catch a
shallow ("plumbing-only") pass and must accept a grounded one.

Deep verification is only trustworthy if the gate itself is exercised against a
known-bad input. This script:

  1. checks the weak-assertion catalogue flags the plumbing shapes and clears the
     grounded ones (against ``check_grounding._weak_reasons`` — the authoritative
     re-derivation), and
  2. drives the grounded pytest driver ``run_pytest.py`` against a selection that
     matches **no** tests (must fail: "no tests ran") and one that matches (must
     pass) — a skip / no-run is a failure, never a green.

Usage::

    python3 scripts/fieldtest/verify_harness.py

Exit 0 == the verifier is trustworthy; non-zero == the gate is too weak.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def _load_check_grounding():
    spec = importlib.util.spec_from_file_location("_cg", HERE / "check_grounding.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# (command, should-be-weak?) — the gate must classify every one correctly.
_CASES: list[tuple[str, bool]] = [
    ("python3 -c \"import json\"", True),
    ("python3 -m agentpolicy", True),
    ("test -f out.json", True),
    ("cat x | python3 -m json.tool", True),
    ("grep -q done out.txt || true", True),
    ("", True),
    (":", True),
    ("pytest tests/", True),
    ("/usr/bin/python3 scripts/fieldtest/run_pytest.py tests/test_x.py", False),
    ("/repo/.venv/bin/agentpolicy self-attack check --pack packs/self-attack", False),
    ("grep -q 'outcome: blocked' /tmp/qs.txt", False),
    ("curl -sf http://127.0.0.1:8000/v1/models", False),
]


def main() -> int:
    cg = _load_check_grounding()
    failures: list[str] = []
    for cmd, expect_weak in _CASES:
        got_weak = bool(cg._weak_reasons(cmd))
        if got_weak != expect_weak:
            failures.append(f"catalogue: {cmd!r} -> weak={got_weak}, expected {expect_weak}")

    # run_pytest.py: a selection matching no tests must FAIL (never a green).
    empty = subprocess.run(
        [sys.executable, str(HERE / "run_pytest.py"), "tests/test_types.py",
         "-k", "__no_such_test__"],
        capture_output=True, text=True, cwd=REPO,
    )
    if empty.returncode == 0:
        failures.append("run_pytest: a no-match selection passed (should fail: no tests ran)")

    # run_pytest.py: a real selection must PASS.
    real = subprocess.run(
        [sys.executable, str(HERE / "run_pytest.py"), "tests/test_types.py", "-k", "as_dict_shape"],
        capture_output=True, text=True, cwd=REPO,
    )
    if real.returncode != 0:
        failures.append("run_pytest: a real passing selection failed")

    if failures:
        print("verify-harness: FAILED", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print(
        f"verify-harness: OK — {len(_CASES)} catalogue case(s) classified correctly; "
        "run_pytest fails a no-match selection and passes a real one."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
