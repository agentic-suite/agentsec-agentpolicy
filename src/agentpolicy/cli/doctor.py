"""``agentpolicy doctor`` — self-observability: environment checks + a verdict.

WBS M1 ``1.5`` — *Self-observability*. Runs a small set of local checks
(Python version, policy load, an engine smoke decision, and audit-sink
writability), prints them, and returns a verdict. Exit code 0 = healthy,
1 = at least one check failed.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentpolicy import __version__
from agentpolicy.engine.engine import Engine
from agentpolicy.policy.loader import load_policy
from agentpolicy.policy.models import default_policy

_MIN_PYTHON = (3, 11)


@dataclass
class Check:
    """A single environment check result."""

    name: str
    ok: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


def add_parser(subparsers: Any) -> None:
    """Register the ``agentpolicy doctor`` subcommand parser."""
    parser = subparsers.add_parser(
        "doctor",
        help="check the local environment and print a verdict",
        description="Run environment/config checks (python, policy load, engine, audit sink).",
    )
    parser.add_argument(
        "--policy", default=None, help="Path to agentpolicy.yaml (default: balanced preset)"
    )
    parser.add_argument("--json", action="store_true", help="Output checks as JSON")
    parser.set_defaults(func=_run)


def _checks(policy_path: str | None) -> list[Check]:
    checks: list[Check] = []
    py_ok = sys.version_info[:2] >= _MIN_PYTHON
    checks.append(
        Check(
            "python",
            py_ok,
            f"{sys.version.split()[0]} (requires >= {_MIN_PYTHON[0]}.{_MIN_PYTHON[1]})",
        )
    )

    try:
        policy = load_policy(policy_path) if policy_path else default_policy("balanced")
        checks.append(Check("policy", True, policy_path or "balanced preset"))
    except Exception as exc:
        checks.append(Check("policy", False, str(exc)))
        return checks

    try:
        decision = Engine(policy).evaluate(
            tool_name="query_logs",
            action="read",
            environment="staging",
            data_class="internal",
            agent_id="doctor",
        )
        checks.append(Check("engine", True, f"smoke decision = {decision.decision}"))
    except Exception as exc:
        checks.append(Check("engine", False, str(exc)))

    audit_dir = Path.home() / ".agentpolicy"
    try:
        audit_dir.mkdir(parents=True, exist_ok=True)
        probe = audit_dir / ".doctor-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        checks.append(Check("audit_sink", True, str(audit_dir)))
    except OSError as exc:
        checks.append(Check("audit_sink", False, str(exc)))

    return checks


def _run(args: argparse.Namespace) -> int:
    """Run the checks and print the verdict. 0 = healthy, 1 = unhealthy."""
    checks = _checks(args.policy)
    healthy = all(c.ok for c in checks)

    if args.json:
        print(
            json.dumps(
                {"version": __version__, "ok": healthy, "checks": [c.to_dict() for c in checks]},
                indent=2,
            )
        )
    else:
        print(f"agentpolicy doctor — {__version__}")
        for check in checks:
            print(f"  [{'ok' if check.ok else 'FAIL'}] {check.name}: {check.detail}")
        print(f"  verdict: {'healthy' if healthy else 'unhealthy'}")

    return 0 if healthy else 1
