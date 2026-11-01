"""Parity / absorption ledger (WBS M23 ``23.5``, PRD 10).

Every predecessor capability is recorded with a status of **delivered**,
**delegated**, or **waived** (with a reason). :func:`parity_gate` returns the
capabilities that are *neither* delivered/delegated *nor* explicitly waived —
**green == no silent drops**. This is the closure of the M0 porting map.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

#: Valid capability statuses.
STATUSES: frozenset[str] = frozenset({"delivered", "delegated", "waived"})


@dataclass(frozen=True)
class ParityEntry:
    """One predecessor capability and where it landed."""

    capability: str
    status: str
    where: str
    reason: str = ""

    def to_dict(self) -> dict[str, str]:
        """JSON-friendly representation."""
        return {
            "capability": self.capability, "status": self.status,
            "where": self.where, "reason": self.reason,
        }


#: The absorption ledger (the WBS porting map, closed).
PARITY_LEDGER: tuple[ParityEntry, ...] = (
    ParityEntry("Decision engine (allow/audit/escalate/deny + risk dimensions)",
                "delivered", "cedar/ (five outcomes), engine/"),
    ParityEntry("Action taxonomy (13 domains)", "delivered", "taxonomy/, canonical.py"),
    ParityEntry("Explainability + reason codes + criticality",
                "delivered", "explain.py, reason_codes.py"),
    ParityEntry("Audit log (JSONL/SQLite/Postgres) + policy version",
                "delivered", "audit/, cedar/policy.policy_hash"),
    ParityEntry("Escalation round-trip", "delivered", "engine/escalation.py, ask.py"),
    ParityEntry("Delivery surfaces (library/MCP/HTTP/CLI) + adapters",
                "delivered", "api.py, adapters/, server/, cli/"),
    ParityEntry(
        "Posture presets + init scaffold + diff", "delivered",
        "policy/, cli/init.py, cli/diff.py",
    ),
    ParityEntry("Shadow mode + score calibration", "delivered", "calibration.py, canary.py"),
    ParityEntry("Session state (budgets, rate limits)", "delivered", "session_store.py, engine/"),
    ParityEntry("Argument validation + output inspection",
                "delivered", "engine/argument_policy.py, output_inspector.py, redaction.py"),
    ParityEntry("Adversarial normalization (tool names, dispatcher)",
                "delivered", "engine/normalize.py, dispatcher.py"),
    ParityEntry("OWASP mapping + security baseline",
                "delivered", "compliance.py, SECURITY_BASELINE.md"),
    ParityEntry("OPA/Rego peer backend", "delivered", "policy/opa.py"),
    ParityEntry(
        "Legacy policy YAML schema + loader", "delivered",
        "policy/{schema,loader,models}.py",
    ),
)


def parity_gate() -> list[str]:
    """Capabilities neither delivered/delegated nor explicitly waived (empty == green)."""
    drops: list[str] = []
    for entry in PARITY_LEDGER:
        if entry.status in ("delivered", "delegated"):
            continue
        if entry.status == "waived" and entry.reason:
            continue
        drops.append(entry.capability)
    return drops


def parity_report() -> dict[str, Any]:
    """A JSON-friendly summary of the ledger."""
    by_status: dict[str, int] = {}
    for entry in PARITY_LEDGER:
        by_status[entry.status] = by_status.get(entry.status, 0) + 1
    return {
        "total": len(PARITY_LEDGER),
        "by_status": by_status,
        "entries": [entry.to_dict() for entry in PARITY_LEDGER],
    }


__all__ = ["PARITY_LEDGER", "STATUSES", "ParityEntry", "parity_gate", "parity_report"]
