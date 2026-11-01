"""Deferred-optional registry (WBS M23 ``23.7``, R13 / R14 / R31).

An item is either **implemented** or **explicitly waived with a written reason**
— "may be waived" never means "silently dropped". :func:`deferred_gate` fails any
item that has neither an implementation nor a waiver reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DeferredItem:
    """One deferred-optional item and its disposition."""

    req: str
    title: str
    status: str
    reason: str = ""

    def to_dict(self) -> dict[str, str]:
        """JSON-friendly representation."""
        return {
            "req": self.req, "title": self.title, "status": self.status,
            "reason": self.reason,
        }


#: The deferred-optional items (v0.1.0 disposition).
DEFERRED: tuple[DeferredItem, ...] = (
    DeferredItem(
        "R13", "OPA → Cedar migration assistant", "waived",
        "The assistant is a v0.2 authoring surface; v0.1.0 already evaluates the "
        "OPA/Rego peer backend via policy/opa.py, so the migration path is documented, "
        "not automated.",
    ),
    DeferredItem(
        "R14", "Rule-pack marketplace", "waived",
        "A distribution surface, not a control; v0.1.0 ships the pack format + repo "
        "so packs are installable from source, and the marketplace waits for v0.3.",
    ),
    DeferredItem(
        "R31", "Fleet sync", "waived",
        "agentpolicy decides; agentwatch/agentcomply own the fleet. Shipping a second "
        "inventory source would duplicate the single source of truth (ADR-0007).",
    ),
)


def deferred_gate() -> list[str]:
    """Items with neither an implementation nor a waiver reason (empty == ok)."""
    bad: list[str] = []
    for item in DEFERRED:
        if item.status == "implemented":
            continue
        if item.status == "waived" and item.reason:
            continue
        bad.append(item.req)
    return bad


def deferred_report() -> dict[str, Any]:
    """A JSON-friendly summary of the deferred-optional disposition."""
    return {
        "reqs": [item.req for item in DEFERRED],
        "by_status": {
            status: sum(1 for item in DEFERRED if item.status == status)
            for status in sorted({item.status for item in DEFERRED})
        },
        "items": [item.to_dict() for item in DEFERRED],
    }


__all__ = ["DEFERRED", "DeferredItem", "deferred_gate", "deferred_report"]
