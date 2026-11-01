#!/usr/bin/env python3
"""Deep-verification gate: every PASS must be *really* a pass.

A surface pass ("the command ran") is not enough. For every case verdict under
``field-test/<FT_VERSION>/results/`` this gate re-checks, from the evidence on
disk, that a PASS rests on **>=1 grounded assertion** (not an import/existence/
json.tool/cannot-fail/bare-driver shape) and that an LLM-required case captured
its request/response pairs. It prints a table + a grounding census and exits
non-zero when any PASS fails the deep check.

Usage::

    python3 scripts/fieldtest/check_grounding.py [RESULTS_DIR] [--strict]

Env: FT_VERSION (default v0.1.0), FT_RESULTS_ROOT.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RESULTS_ROOT = Path(
    os.environ.get("FT_RESULTS_ROOT")
    or (REPO / "field-test" / os.environ.get("FT_VERSION", "v0.1.0") / "results")
)
REGISTRY = Path(__file__).resolve().parent / "cases" / "registry.json"

_WEAK_RES = [
    (re.compile(r"^\s*(:|true)\s*$"), "bare-true"),
    (re.compile(r"python3?\s+-c\s+['\"]import "), "import-only"),
    (re.compile(r"python3?\s+-m\s+[A-Za-z_.]+\s*$"), "module-import-only"),
    (re.compile(r"\|\|\s*true"), "cannot-fail"),
    (re.compile(r"json\.tool"), "json.tool"),
    (re.compile(r"\btest\s+-[fsn]\b"), "existence-only"),
    (re.compile(r"python3\s+/ft/scripts/[\w.-]+\.py"), "driver-only"),
    (re.compile(r"(^|\s)pytest\s"), "bare-pytest"),
]
_SECRET_RE = re.compile(r"sk-[A-Za-z0-9]{16,}|bearer\s+[A-Za-z0-9._-]{20,}", re.IGNORECASE)


def _weak_reasons(cmd: str) -> list[str]:
    out: list[str] = []
    if not cmd.strip():
        return ["empty-command"]
    for pattern, reason in _WEAK_RES:
        if not pattern.search(cmd):
            continue
        # existence/driver shapes are only weak when they stand alone.
        if reason in ("existence-only", "driver-only") and ("grep" in cmd or "&&" in cmd):
            continue
        # a pytest selection is grounded only through the run_pytest.py driver.
        if reason == "bare-pytest" and "run_pytest.py" in cmd:
            continue
        out.append(reason)
    return sorted(set(out))


def _load_verdicts(results: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for vp in sorted(results.glob("*/cases/*/verdict.json")):
        try:
            v = json.loads(vp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        v["_case_dir"] = str(vp.parent)
        out[str(v.get("id", vp.parent.name))] = v
    return out


def _scan_secrets(llm_dir: Path) -> bool:
    if not llm_dir.exists():
        return False
    for f in llm_dir.glob("*.json"):
        try:
            if _SECRET_RE.search(f.read_text(encoding="utf-8", errors="replace")):
                return True
        except OSError:
            continue
    return False


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    strict = "--strict" in args
    args = [a for a in args if a != "--strict"]
    results = Path(args[0]) if args else RESULTS_ROOT

    try:
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        registry = []
    verdicts = _load_verdicts(results)

    rows: list[tuple[str, str, str, str]] = []
    census = {"grounded": 0, "over-claimed": 0, "unverified": 0, "pass": 0, "fail": 0}

    for case in registry:
        cid = case["id"]
        v = verdicts.get(cid)
        if v is None:
            rows.append((cid, "not run", "—", "no verdict"))
            continue
        status = str(v.get("status", "fail"))
        if status == "declared":
            rows.append((cid, "declared", "—", v.get("limitation", "")))
            continue
        if status != "pass":
            census["fail"] += 1
            rows.append((cid, "FAIL", "—", "case failed"))
            continue
        census["pass"] += 1

        assertions: list[dict] = []
        ap = Path(v.get("_case_dir", "")) / "assertions.ndjson"
        if ap.exists():
            for line in ap.read_text(encoding="utf-8").splitlines():
                try:
                    assertions.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        grounded = 0
        for a in assertions:
            cmd = str(a.get("cmd", ""))
            weak = _weak_reasons(cmd)
            if a.get("ok") and a.get("grounded") and not weak:
                grounded += 1

        llm_required = str(case.get("llm", "no")).lower() in ("yes", "true", "1")
        llm_dir = Path(v.get("_case_dir", "")) / "artifacts" / "llm"
        llm_pairs = len(list(llm_dir.glob("*-request.json"))) if llm_dir.exists() else 0
        llm_clean = not _scan_secrets(llm_dir)

        problems: list[str] = []
        if grounded < 1:
            problems.append("no grounded assertion")
        if int(v.get("assertions_total", 0) or 0) < 1:
            problems.append("verdict records no assertions")
        if bool(v.get("grounded")) and grounded < 1:
            problems.append("verdict claims grounded but re-derivation found none")
        if llm_required and llm_pairs < 1:
            problems.append("no LLM capture")
        if llm_required and not llm_clean:
            problems.append("unmasked secret in LLM capture")

        if not problems:
            census["grounded"] += 1
            rows.append((cid, "PASS", "grounded", f"{grounded} grounded check(s)"))
        else:
            census["over-claimed"] += 1
            rows.append((cid, "PASS", "OVER-CLAIMED", "; ".join(problems)))

    print(f"== deep-verification gate ({results}) ==")
    print(f"{'CASE':<22} {'VERDICT':<14} {'GROUNDING':<13} NOTE")
    for cid, verdict, grounding, note in rows:
        print(f"{cid:<22} {verdict:<14} {grounding:<13} {note}")
    print()
    print(
        f"census: {census['pass']} PASS ({census['grounded']} grounded, "
        f"{census['over-claimed']} over-claimed) · {census['fail']} FAIL"
    )

    bad = census["over-claimed"]
    if bad:
        print(
            f"\ndeep-verification FAILED: {bad} PASS(es) are not deeply verified.",
            file=sys.stderr,
        )
        return 1
    if strict and census["pass"] == 0:
        print("\ndeep-verification: no passes recorded (nothing to verify).", file=sys.stderr)
        return 1
    print("\ndeep-verification: every PASS is grounded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
