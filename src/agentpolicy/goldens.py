"""Golden regression suite (WBS M11 ``11.1``, CUJ-7 / R22).

Replays golden decision fixtures and detects **drift**: a decision that changed
between the committed baseline and the current engine is a finding, and a
**deny→allow flip** (a previously-blocked case that now allows) is a build
breaker. Deterministic because the engine is deterministic.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from agentpolicy.engine.engine import Engine
from agentpolicy.policy.loader import load_policy
from agentpolicy.policy.models import default_policy

#: Decisions that stop or gate a call (a flip *from* one of these is a breaker).
BLOCKING: frozenset[str] = frozenset({"deny", "escalate"})


@dataclass(frozen=True)
class GoldenCase:
    """One golden decision fixture."""

    name: str
    tool: str
    action: str
    environment: str
    data_class: str
    agent_id: str
    expected_decision: str | None = None
    expected_reason_code: str | None = None


@dataclass(frozen=True)
class DriftFinding:
    """A decision that drifted from the committed baseline."""

    name: str
    baseline: str
    current: str
    kind: str  # "flip" (block -> allow) or "drift"

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "name": self.name,
            "baseline": self.baseline,
            "current": self.current,
            "kind": self.kind,
        }


@dataclass(frozen=True)
class GateResult:
    """The outcome of a golden gate run."""

    findings: tuple[DriftFinding, ...]

    @property
    def flips(self) -> tuple[DriftFinding, ...]:
        """The build-breaking deny→allow flips."""
        return tuple(f for f in self.findings if f.kind == "flip")

    @property
    def passed(self) -> bool:
        """Whether the gate passes (no flips)."""
        return not self.flips


def load_cases(path: str | Path) -> list[GoldenCase]:
    """Load golden cases from a fixture YAML file (``cells``/``scenarios``/``fixtures``)."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if isinstance(data, list):
        rows, default_agent = data, "test-agent"
    else:
        rows = data.get("cells") or data.get("scenarios") or data.get("fixtures") or []
        default_agent = str(data.get("agent_id", "test-agent"))
    cases: list[GoldenCase] = []
    for row in rows:
        tool = str(row.get("tool", ""))
        action = str(row.get("action", ""))
        cases.append(
            GoldenCase(
                name=str(
                    row.get("name")
                    or f"{tool}:{action}:{row.get('environment', '')}:{row.get('data_class', '')}"
                ),
                tool=tool,
                action=action,
                environment=str(row.get("environment", row.get("env", ""))),
                data_class=str(row.get("data_class", row.get("data", ""))),
                agent_id=str(row.get("agent_id") or row.get("agent") or default_agent),
                expected_decision=row.get("decision") or row.get("expected"),
                expected_reason_code=row.get("reason_code"),
            )
        )
    return cases


def _engine(policy_path: str | None = None) -> Engine:
    return Engine(load_policy(policy_path) if policy_path else default_policy("balanced"))


def capture(cases: list[GoldenCase], *, policy: str | None = None) -> dict[str, dict[str, str]]:
    """Record the current decision for each case (a candidate baseline)."""
    engine = _engine(policy)
    baseline: dict[str, dict[str, str]] = {}
    for case in cases:
        decision = engine.evaluate(
            tool_name=case.tool, action=case.action, environment=case.environment,
            data_class=case.data_class, agent_id=case.agent_id,
        )
        baseline[case.name] = {
            "decision": decision.decision,
            "reason_code": decision.reason_code,
        }
    return baseline


def detect_flips(
    baseline: dict[str, dict[str, str]], cases: list[GoldenCase], *, policy: str | None = None
) -> GateResult:
    """Compare current decisions to *baseline*; collect flips and drift."""
    engine = _engine(policy)
    findings: list[DriftFinding] = []
    for case in cases:
        before = baseline.get(case.name)
        if before is None:
            continue
        current = engine.evaluate(
            tool_name=case.tool, action=case.action, environment=case.environment,
            data_class=case.data_class, agent_id=case.agent_id,
        ).decision
        prior = before["decision"]
        if prior == current:
            continue
        kind = "flip" if prior in BLOCKING and current == "allow" else "drift"
        findings.append(DriftFinding(case.name, prior, current, kind))
    return GateResult(tuple(findings))


def dump_baseline(baseline: dict[str, dict[str, str]]) -> str:
    """Serialize a baseline to JSON (a committable golden file)."""
    return json.dumps(baseline, indent=2, sort_keys=True)


def load_baseline(path: str | Path) -> dict[str, dict[str, str]]:
    """Load a baseline previously written by :func:`dump_baseline`."""
    data: dict[str, dict[str, str]] = json.loads(Path(path).read_text(encoding="utf-8"))
    return data


__all__ = [
    "BLOCKING",
    "DriftFinding",
    "GateResult",
    "GoldenCase",
    "capture",
    "detect_flips",
    "dump_baseline",
    "load_baseline",
    "load_cases",
]
