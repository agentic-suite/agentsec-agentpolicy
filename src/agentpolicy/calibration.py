"""Shadow calibration (WBS M10 ``10.3``, CUJ-4 / R30).

Turns the audit trail into **calibration rates**: of the decisions observed in
shadow mode, how many *would have been blocked* while sitting near the allow
boundary (potential **false blocks**), and how many *allows* sit near the block
boundary (potential **false misses**) — plus the counterfactual-threshold
distribution. See ``docs/reference/shadow-calibration-canary.md``.

The heuristic is explicit and deterministic: a blocked decision is a
false-block candidate when its counterfactual boundary is at or below
``false_block_boundary``; an allowed decision is a false-miss candidate when its
counterfactual boundary is at or above ``false_miss_boundary``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agentpolicy.audit.models import AuditEntry

#: Decisions that stop the call.
_BLOCKED = frozenset({"deny", "escalate"})
#: Decisions that let the call through.
_ALLOWED = frozenset({"allow", "audit", "allow_with_obligation"})


@dataclass(frozen=True)
class CalibrationReport:
    """Shadow-mode calibration rates + the counterfactual-threshold table."""

    total: int
    shadow: int
    would_block: int
    false_block: int
    false_block_rate: float
    allowed: int
    false_miss: int
    false_miss_rate: float
    threshold_table: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "total": self.total,
            "shadow": self.shadow,
            "would_block": self.would_block,
            "false_block": self.false_block,
            "false_block_rate": self.false_block_rate,
            "allowed": self.allowed,
            "false_miss": self.false_miss,
            "false_miss_rate": self.false_miss_rate,
            "threshold_table": dict(self.threshold_table),
        }


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def calibrate(
    entries: list[AuditEntry],
    *,
    false_block_boundary: float = 0.5,
    false_miss_boundary: float = 0.75,
) -> CalibrationReport:
    """Compute shadow-calibration rates from audit entries.

    Args:
        entries: The audit entries (typically a shadow snapshot).
        false_block_boundary: A blocked decision at or below this counterfactual
            boundary is a false-block candidate.
        false_miss_boundary: An allowed decision at or above this boundary is a
            false-miss candidate.

    Returns:
        A :class:`CalibrationReport`.
    """
    shadow = [e for e in entries if e.dry_run]
    would_block = [e for e in shadow if e.decision in _BLOCKED]
    allowed = [e for e in shadow if e.decision in _ALLOWED]

    false_block = [
        e for e in would_block
        if e.counterfactual is not None and e.counterfactual <= false_block_boundary
    ]
    false_miss = [
        e for e in allowed
        if e.counterfactual is not None and e.counterfactual >= false_miss_boundary
    ]

    table: dict[str, int] = {}
    for entry in shadow:
        if entry.counterfactual is not None:
            key = str(entry.counterfactual)
            table[key] = table.get(key, 0) + 1

    return CalibrationReport(
        total=len(entries),
        shadow=len(shadow),
        would_block=len(would_block),
        false_block=len(false_block),
        false_block_rate=_rate(len(false_block), len(would_block)),
        allowed=len(allowed),
        false_miss=len(false_miss),
        false_miss_rate=_rate(len(false_miss), len(allowed)),
        threshold_table=table,
    )


__all__ = ["CalibrationReport", "calibrate"]
