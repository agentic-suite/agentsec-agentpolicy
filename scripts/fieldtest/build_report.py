#!/usr/bin/env python3
"""Fill ``docs/field-test/<FT_VERSION>/FIELD_TEST_REPORT.generated.md`` from the results.

The **canonical** report (``FIELD_TEST_REPORT.md``) is **hand-maintained** — this
script never overwrites it. It writes a ``.generated.md`` draft (for reference /
diffing) and refuses to touch a file carrying the ``HAND-MAINTAINED`` marker
unless ``--force``. Update the canonical report **by hand**.

Reads the newest run's ``summary.json`` + per-case ``verdict.json`` under
``field-test/<FT_VERSION>/results/`` and writes the report sections required by
the field-test plan §13 (BLUF + gate verdict, master table, CUJ coverage, the
declared register). The report is assembled **from** the results, never the
reverse.

Usage::

    python3 scripts/fieldtest/build_report.py [RUN_DIR] [-o OUT.md]

Env: FT_VERSION (default v0.1.0), FT_RESULTS_ROOT.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FT_VERSION = os.environ.get("FT_VERSION", "v0.1.0")
RESULTS_ROOT = Path(
    os.environ.get("FT_RESULTS_ROOT") or (REPO / "field-test" / FT_VERSION / "results")
)
# The canonical report is HAND-MAINTAINED. This script must NEVER overwrite it:
# it defaults to a `.generated.md` sibling, and refuses a file carrying the
# HAND-MAINTAINED marker unless --force is passed.
REPORT = REPO / "docs" / "field-test" / FT_VERSION / "FIELD_TEST_REPORT.md"
GENERATED = REPO / "docs" / "field-test" / FT_VERSION / "FIELD_TEST_REPORT.generated.md"
_HAND_MARKER = "HAND-MAINTAINED"
REGISTRY = HERE / "cases" / "registry.json"


def _newest_run_dir() -> Path | None:
    if not RESULTS_ROOT.exists():
        return None
    runs = sorted(p for p in RESULTS_ROOT.iterdir() if p.is_dir())
    return runs[-1] if runs else None


def _load_verdicts(run_dir: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for vp in sorted(run_dir.glob("cases/*/verdict.json")):
        try:
            v = json.loads(vp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        out[str(v.get("id", vp.parent.name))] = v
    return out


def _registry() -> list[dict]:
    try:
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def _status(v: dict | None) -> str:
    if v is None:
        return "not-run"
    return str(v.get("status", "fail"))


def build(run_dir: Path) -> str:
    verdicts = _load_verdicts(run_dir)
    reg = _registry()
    totals = {"pass": 0, "fail": 0, "declared": 0, "not-run": 0}
    for case in reg:
        st = _status(verdicts.get(case["id"]))
        if st not in totals:
            st = "fail"
        totals[st] += 1

    now = datetime.now(UTC).isoformat()
    gate = "GREEN" if totals["fail"] == 0 and totals["pass"] > 0 else "NOT GREEN"
    lines = [
        f"# Field-Test Report — agentpolicy {FT_VERSION}",
        "",
        f"**Run:** `{run_dir.name}` · **Generated:** {now}",
        "**Plan:** [FIELD_TEST_PLAN.md](FIELD_TEST_PLAN.md)",
        "",
        "## 1. BLUF + release-gate verdict",
        "",
        f"**{totals['pass']} pass · {totals['fail']} fail · {totals['declared']} declared · "
        f"{totals['not-run']} not-run → {gate}.**",
        "",
        "A case passes only on grounded assertions (see `check_grounding.py`); a `declared`",
        "case names its limitation; a case that could not run is a failure.",
        "",
        "## 2. Scenario results (master table)",
        "",
        "| Case | Suite | Class | Status | Grounded |",
        "|---|---|---|---|---|",
    ]
    for case in sorted(reg, key=lambda c: c["id"]):
        v = verdicts.get(case["id"])
        st = _status(v)
        grounded = "—" if v is None else ("yes" if v.get("grounded") else "no")
        lines.append(
            f"| {case['id']} | {case.get('suite', '')} | {case.get('class', 'P/F')} | "
            f"{st} | {grounded} |"
        )

    declared = [c for c in reg if _status(verdicts.get(c["id"])) == "declared"]
    lines += ["", "## 3. Declared register", ""]
    if declared:
        lines += ["| Case | Limitation | Release gate |", "|---|---|---|"]
        for c in declared:
            v = verdicts.get(c["id"]) or {}
            lines.append(
                f"| {c['id']} | {v.get('limitation', '')} | {v.get('release_gate_item', '')} |"
            )
    else:
        lines.append("_None declared._")

    lines += ["", "## 4. Evidence & reproduce", "",
              "```", "bash scripts/fieldtest/run-all.sh        # regenerate results",
              "python3 scripts/fieldtest/collect-results.py",
              "python3 scripts/fieldtest/check_grounding.py --strict",
              "python3 scripts/fieldtest/scan_results.py",
              "python3 scripts/fieldtest/build_report.py   # regenerate this report",
              "```", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    force = "--force" in args
    args = [a for a in args if a != "--force"]
    out = GENERATED
    if "-o" in args:
        out = Path(args[args.index("-o") + 1])
        args = args[: args.index("-o")]
    # Never clobber the hand-maintained report. Compare *resolved* paths so a
    # relative -o (e.g. docs/field-test/…/FIELD_TEST_REPORT.md) is caught too.
    def _is_canonical(path: Path) -> bool:
        try:
            return path.resolve() == REPORT.resolve()
        except OSError:
            return False

    if _is_canonical(out) and REPORT.exists() and _HAND_MARKER in REPORT.read_text(
        encoding="utf-8"
    ):
        if not force:
            print(
                f"build-report: REFUSING to overwrite the hand-maintained {REPORT.name} "
                f"(marker {_HAND_MARKER!r}). Writing the generated draft to "
                f"{GENERATED.name} instead.\n"
                "  Update the canonical report by hand; use --force only to intentionally "
                "replace it.",
                file=sys.stderr,
            )
            out = GENERATED
    run_dir = Path(args[0]) if args else _newest_run_dir()
    if run_dir is None or not run_dir.exists():
        print("build-report: no run directory found", file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(run_dir), encoding="utf-8")
    print(f"build-report: wrote {out} from {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
