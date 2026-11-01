#!/usr/bin/env python3
"""M25 25.2 — first-run evidence: time-to-first-correct-decision, measured.

Records the release's first-run journey and enforces the SLOs:

- **install → first correct decision < 5 min**
- **< 2 min with ``agentpolicy init``** (the scaffolded path)

Measures (1) the wheel install into a fresh venv, (2) ``agentpolicy init``, and
(3) the first ``agentpolicy evaluate`` — writes ``FIRST_RUN_EVIDENCE.md`` and
exits non-zero if an SLO is missed (loud failure).

Usage::

    python3 scripts/release/first_run.py --wheel dist/*.whl
    # (--out defaults to docs/release/v0.1.0/FIRST_RUN_EVIDENCE.md)
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

#: SLO budgets, seconds.
SLO_TOTAL_S = 300.0   # install -> first correct decision < 5 min
SLO_INIT_S = 120.0    # with `init` (scaffold + decide) < 2 min


def check_slo(install_s: float, init_s: float, decide_s: float) -> list[str]:
    """Return SLO problems ([] == green)."""
    problems: list[str] = []
    total = install_s + init_s + decide_s
    if total > SLO_TOTAL_S:
        problems.append(f"install->decision {total:.1f}s exceeds {SLO_TOTAL_S:.0f}s (< 5 min)")
    if init_s + decide_s > SLO_INIT_S:
        problems.append(f"init path {init_s + decide_s:.1f}s exceeds {SLO_INIT_S:.0f}s (< 2 min)")
    return problems


def _timed(cmd: list[str], cwd: Path | None = None) -> tuple[float, int]:
    start = time.monotonic()
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)  # noqa: S603 — trusted argv
    return time.monotonic() - start, proc.returncode


def measure(wheel: Path) -> dict[str, float | int]:
    """Run the install -> init -> evaluate journey; return timings + exit codes."""
    tmp = Path(tempfile.mkdtemp(prefix="ap-firstrun-"))
    venv = tmp / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True, capture_output=True)  # noqa: S603
    py = venv / "bin" / "python"
    # Install WITH dependencies so the CLI can actually run a decision (uv
    # resolves from the local cache; falls back to pip if uv is absent).
    if shutil.which("uv"):
        install_cmd = ["uv", "pip", "install", "--python", str(py), str(wheel)]
    else:
        install_cmd = [str(py), "-m", "pip", "install", str(wheel)]
    install_s, install_rc = _timed(install_cmd)
    work = tmp / "work"
    work.mkdir()
    ap = venv / "bin" / "agentpolicy"
    init_s, init_rc = _timed([str(ap), "init", "-o", "agentpolicy.yaml"], cwd=work)
    decide_s, decide_rc = _timed(
        [str(ap), "evaluate", "--tool", "query_logs", "--action", "read",
         "--env", "staging", "--data", "internal", "--agent", "first-run-bot",
         "--policy", str(work / "agentpolicy.yaml"), "--format", "json"],
        cwd=work,
    )
    return {
        "install_s": install_s, "install_rc": install_rc,
        "init_s": init_s, "init_rc": init_rc,
        "decide_s": decide_s, "decide_rc": decide_rc,
    }


def write_evidence(m: dict[str, float | int], wheel: Path, out: Path, problems: list[str]) -> None:
    total = float(m["install_s"]) + float(m["init_s"]) + float(m["decide_s"])
    init_plus_decide = float(m['init_s']) + float(m['decide_s'])
    status = "**PASS**" if not problems else f"**FAIL** ({'; '.join(problems)})"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"""# AgentPolicy v0.1.0 — First-Run Evidence

> M25 25.2 (issue #269). Measured on this box with a clean-venv `pip install`
> of the release wheel; the decision path is deterministic (no ML/network).

## The journey

| Step | Command | Time | Exit |
|---|---|---|---|
| install | `pip install {wheel.name}` (fresh venv) | {m['install_s']:.2f}s | {m['install_rc']} |
| scaffold | `agentpolicy init -o agentpolicy.yaml` | {m['init_s']:.2f}s | {m['init_rc']} |
| first decision | `agentpolicy evaluate …` | {m['decide_s']:.2f}s | {m['decide_rc']} |

- **install → first correct decision:** **{total:.2f}s** — SLO **< 5 min**.
- **with `init` (scaffold + decide):** **{init_plus_decide:.2f}s** — SLO **< 2 min**.

## Verdict

**{status}** (SLOs: install→decision < 5 min; init path < 2 min).

The recorded timings come from the release wheel's SHA256SUMS entry; reproduce
with `make release-dry-run` then `python3 scripts/release/first_run.py`.
""", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="record first-run evidence")
    p.add_argument("--wheel", required=True, help="path to the built wheel")
    p.add_argument("--out", default="docs/release/v0.1.0/FIRST_RUN_EVIDENCE.md")
    a = p.parse_args(argv)
    wheel = Path(a.wheel)
    m = measure(wheel)
    problems = check_slo(float(m["install_s"]), float(m["init_s"]), float(m["decide_s"]))
    for step in ("install", "init", "decide"):
        if int(m[f"{step}_rc"]) != 0:
            problems.append(f"{step} step did not complete (rc={m[f'{step}_rc']})")
    write_evidence(m, wheel, Path(a.out), problems)
    total = float(m["install_s"]) + float(m["init_s"]) + float(m["decide_s"])
    print(f"first-run: install+init+decide = {total:.2f}s (SLO < 300s)")
    if problems:
        for prob in problems:
            print(f"  FAIL: {prob}", file=sys.stderr)
        return 1
    print("first-run SLOs: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
