"""Standards claims linter (WBS M23 ``23.6``, R32).

The published coverage **claims** must be honest: each claim references a
framework control in the computed coverage matrix (:mod:`agentpolicy.compliance`)
and must **not** assert coverage of a control no shipped pack covers. This is
the guardrail that keeps the standards story from drifting from the code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentpolicy import compliance


@dataclass(frozen=True)
class Claim:
    """One published coverage claim, tied to a framework control."""

    text: str
    framework: str
    control_id: str

    def to_dict(self) -> dict[str, str]:
        """JSON-friendly representation."""
        return {"text": self.text, "framework": self.framework, "control_id": self.control_id}


#: The shipped claims (each must map to a covered control).
CLAIMS: tuple[Claim, ...] = (
    Claim(
        "Destructive tool calls in production are blocked before they run.",
        "OWASP-ASI", "ASI02",
    ),
    Claim(
        "Sensitive data flowing to an external tool is blocked (exfil-sink).",
        "OWASP-LLM", "LLM02",
    ),
    Claim(
        "Sensitive data to an external sink is blocked (exfiltration via tool).",
        "ATLAS", "AML.T0012",
    ),
)


def _index(matrix: dict[str, Any]) -> tuple[set[str], set[str]]:
    known: set[str] = set()
    covered: set[str] = set()
    for framework in matrix.get("frameworks", {}).values():
        for control in framework.get("controls", []):
            known.add(str(control["id"]))
            if control.get("covered"):
                covered.add(str(control["id"]))
    return known, covered


def lint_claims(
    claims: tuple[Claim, ...] | list[Claim] | None = None,
    *,
    matrix: dict[str, Any] | None = None,
) -> list[str]:
    """Lint claims against the coverage matrix; return findings (empty == clean)."""
    resolved = matrix if matrix is not None else compliance.coverage_matrix()
    known, covered = _index(resolved)
    source = claims if claims is not None else CLAIMS
    findings: list[str] = []
    for claim in source:
        if claim.control_id not in known:
            findings.append(
                f"claim {claim.control_id!r} references an unknown control"
            )
        elif claim.control_id not in covered:
            findings.append(
                f"claim asserts coverage of uncovered control {claim.control_id}"
            )
    return findings


__all__ = ["CLAIMS", "Claim", "lint_claims"]
