"""Approval analytics (WBS M16 ``16.3``, CUJ-23 / R36).

Turns the human-gate stores (escalations + asks) into an approval report:
**approval rate**, **latency** (mean seconds to resolve), the **shadow→enforce
delta**, and the **rubber-stamp gates** — a gate that is (almost) always
approved is surfaced, not celebrated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

#: Status values that count as an approval / a denial.
_APPROVED = "approved"
_DENIED = "denied"
_EXPIRED = "expired"
_PENDING = "pending"


def _status_of(record: Any) -> str:
    status = getattr(record, "status", None)
    return getattr(status, "value", str(status))


def _seconds_between(start: str | None, end: str | None) -> float | None:
    if not start or not end:
        return None
    try:
        a = datetime.fromisoformat(start.replace("Z", "+00:00"))
        b = datetime.fromisoformat(end.replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0.0, (b - a).total_seconds())


@dataclass(frozen=True)
class ApprovalAnalytics:
    """A human-gate approval report."""

    total: int
    approved: int
    denied: int
    expired: int
    pending: int
    approval_rate: float
    mean_latency_seconds: float | None
    shadow_delta: float | None
    rubber_stamp_gates: tuple[str, ...] = ()
    by_gate: dict[str, dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "total": self.total,
            "approved": self.approved,
            "denied": self.denied,
            "expired": self.expired,
            "pending": self.pending,
            "approval_rate": self.approval_rate,
            "mean_latency_seconds": self.mean_latency_seconds,
            "shadow_delta": self.shadow_delta,
            "rubber_stamp_gates": list(self.rubber_stamp_gates),
            "by_gate": {k: dict(v) for k, v in self.by_gate.items()},
        }


def _blocked(entry: Any) -> bool:
    return getattr(entry, "decision", "") in ("deny", "escalate")


def _shadow_delta(audit_entries: tuple[Any, ...]) -> float | None:
    """Shadow blocked-rate minus enforced blocked-rate (``None`` if no data)."""
    shadow = [e for e in audit_entries if getattr(e, "dry_run", False)]
    enforced = [e for e in audit_entries if not getattr(e, "dry_run", False)]
    if not shadow or not enforced:
        return None
    shadow_rate = sum(1 for e in shadow if _blocked(e)) / len(shadow)
    enforced_rate = sum(1 for e in enforced if _blocked(e)) / len(enforced)
    return shadow_rate - enforced_rate


def analyze_approvals(
    escalations: tuple[Any, ...] | list[Any] = (),
    asks: tuple[Any, ...] | list[Any] = (),
    *,
    audit_entries: tuple[Any, ...] | list[Any] = (),
    rubber_stamp_threshold: float = 0.99,
    min_approvals: int = 3,
) -> ApprovalAnalytics:
    """Compute the approval report from the gate records.

    Args:
        escalations: ``Escalation`` records (M3 gate).
        asks: ``Ask`` records (M7 gate).
        audit_entries: Audit entries (for the shadow→enforce delta).
        rubber_stamp_threshold: A gate at or above this approval rate (with at
            least ``min_approvals``) is a rubber-stamp candidate.
        min_approvals: Minimum approvals before a gate can be flagged.

    Returns:
        An :class:`ApprovalAnalytics`.
    """
    records = [*escalations, *asks]
    approved = denied = expired = pending = 0
    latencies: list[float] = []
    by_gate: dict[str, dict[str, int]] = {}
    for record in records:
        status = _status_of(record)
        bucket = by_gate.setdefault(
            str(getattr(record, "tool", "unknown")),
            {"approved": 0, "denied": 0, "expired": 0, "pending": 0},
        )
        if status == _APPROVED:
            approved += 1
            bucket["approved"] += 1
        elif status == _DENIED:
            denied += 1
            bucket["denied"] += 1
        elif status == _EXPIRED:
            expired += 1
            bucket["expired"] += 1
        else:
            pending += 1
            bucket["pending"] += 1
        latency = _seconds_between(
            getattr(record, "created_at", None), getattr(record, "resolved_at", None)
        )
        if latency is not None:
            latencies.append(latency)

    decided = approved + denied
    approval_rate = approved / decided if decided else 0.0
    mean_latency = sum(latencies) / len(latencies) if latencies else None

    rubber_stamp: list[str] = []
    for gate, counts in sorted(by_gate.items()):
        gate_decided = counts["approved"] + counts["denied"]
        if gate_decided >= min_approvals and counts["approved"] / gate_decided >= (
            rubber_stamp_threshold
        ):
            rubber_stamp.append(gate)

    return ApprovalAnalytics(
        total=len(records),
        approved=approved,
        denied=denied,
        expired=expired,
        pending=pending,
        approval_rate=approval_rate,
        mean_latency_seconds=mean_latency,
        shadow_delta=_shadow_delta(tuple(audit_entries)),
        rubber_stamp_gates=tuple(rubber_stamp),
        by_gate=by_gate,
    )


__all__ = ["ApprovalAnalytics", "analyze_approvals"]
