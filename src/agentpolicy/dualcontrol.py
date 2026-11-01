"""Dual-control (quorum) approvals (WBS M18 ``18.3``, CUJ-26 / R41).

The **irreversible / mandatory human-gate class** needs a quorum (default 2) of
**distinct** approvers: one human cannot release it, two distinct humans can.
A record is bound to the call's :func:`action_identity` (the one canonical
identity hash) so a quorum for X cannot release Y, and a TTL still applies —
quorum does not remove expiry.

* :meth:`DualControlGate.request` opens a pending record (audited ``request``).
* :meth:`DualControlGate.approve` adds a distinct approver; a repeat by the same
  principal is rejected; reaching the quorum marks the record **released**.
* :meth:`DualControlGate.resolve` is the engine-facing check: released +
  matching identity → ``allow``; anything else → ``deny`` with a distinct code.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from agentpolicy import reason_codes
from agentpolicy.engine.escalation import action_identity
from agentpolicy.types import NormalizedCall

#: Default quorum — two distinct approvers for the irreversible class.
DEFAULT_QUORUM = 2


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _parse_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


@dataclass(frozen=True)
class DualControlRecord:
    """One quorum-gated approval bound to a call's action identity."""

    dual_control_id: str
    action_identity: str
    quorum: int
    status: str
    tool: str
    action: str
    created_at: str
    expires_at: str
    approvers: tuple[str, ...] = ()
    escalation_id: str | None = None

    def is_expired(self, now: datetime | None = None) -> bool:
        """Whether the record has outlived its TTL (treated as deny)."""
        return (now or _utcnow()) > _parse_iso(self.expires_at)

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "dual_control_id": self.dual_control_id,
            "action_identity": self.action_identity,
            "quorum": self.quorum,
            "status": self.status,
            "tool": self.tool,
            "action": self.action,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "approvers": list(self.approvers),
            "escalation_id": self.escalation_id,
        }


@dataclass
class DualControlGate:
    """Track quorum-gated approvals and enforce distinct-approver quorum."""

    quorum: int = DEFAULT_QUORUM
    ttl_seconds: int = 300
    _records: dict[str, DualControlRecord] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.quorum < 1:
            raise ValueError("quorum must be at least 1")

    @property
    def records(self) -> dict[str, DualControlRecord]:
        """Read-only view of all records (id -> record)."""
        return dict(self._records)

    def request(
        self,
        call: NormalizedCall,
        *,
        escalation_id: str | None = None,
        quorum: int | None = None,
        now: datetime | None = None,
    ) -> DualControlRecord:
        """Open a pending quorum record for *call* (audited ``request``)."""
        moment = now or _utcnow()
        record = DualControlRecord(
            dual_control_id="dc_" + secrets.token_hex(8),
            action_identity=action_identity(call.tool, call.action, call.arguments),
            quorum=quorum if quorum is not None else self.quorum,
            status="pending",
            tool=call.tool,
            action=call.action,
            created_at=moment.isoformat(),
            expires_at=(moment + timedelta(seconds=self.ttl_seconds)).isoformat(),
            escalation_id=escalation_id,
        )
        self._records[record.dual_control_id] = record
        self.events.append(
            {"kind": "request", "dual_control_id": record.dual_control_id,
             "at": _utcnow().isoformat()}
        )
        return record

    def approve(
        self, dual_control_id: str, *, approver: str, now: datetime | None = None
    ) -> DualControlRecord:
        """Record a distinct approver; release when the quorum is reached.

        Raises:
            ValueError: unknown/already-released/expired record, a blank
                approver, or an approver who has already approved (quorum
                requires **distinct** approvers).
        """
        if not approver or not approver.strip():
            raise ValueError("approver must be a non-blank string")
        record = self._records.get(dual_control_id)
        if record is None:
            raise ValueError("unknown dual_control_id")
        if record.status != "pending":
            raise ValueError(f"dual-control already {record.status}")
        if record.is_expired(now):
            raise ValueError("dual-control expired")
        if approver in record.approvers:
            raise ValueError(
                "quorum requires distinct approvers; this approver already approved"
            )
        approvers = (*record.approvers, approver)
        released = len(approvers) >= record.quorum
        updated = replace(
            record, approvers=approvers, status="released" if released else "pending"
        )
        self._records[dual_control_id] = updated
        self.events.append(
            {"kind": "released" if released else "approved",
             "dual_control_id": dual_control_id, "approver": approver,
             "at": _utcnow().isoformat()}
        )
        return updated

    def released(self, dual_control_id: str) -> bool:
        """Whether the record has reached its quorum."""
        record = self._records.get(dual_control_id)
        return record is not None and record.status == "released"

    def resolve(
        self, dual_control_id: str, *, call: NormalizedCall, now: datetime | None = None
    ) -> dict[str, Any]:
        """Resolve a quorum record: released + matching identity → allow, else deny."""
        record = self._records.get(dual_control_id)
        if record is None:
            return _resolution(
                "deny", reason_codes.DENY_DUAL_CONTROL_UNKNOWN,
                f"unknown dual-control {dual_control_id!r}",
            )
        if record.is_expired(now):
            return _resolution(
                "deny", reason_codes.HUMAN_GATE_TIMEOUT,
                f"dual-control {dual_control_id} expired without a quorum (timeout = deny)",
            )
        if action_identity(call.tool, call.action, call.arguments) != record.action_identity:
            return _resolution(
                "deny", reason_codes.DENY_ACTION_IDENTITY_MISMATCH,
                f"dual-control {dual_control_id} was bound to a different action identity",
            )
        if record.status == "released":
            return _resolution(
                "allow", reason_codes.ALLOW_DUAL_CONTROL_APPROVED,
                f"dual-control {dual_control_id} released by {list(record.approvers)}",
            )
        return _resolution(
            "deny", reason_codes.DENY_DUAL_CONTROL_PENDING,
            f"dual-control {dual_control_id} requires {record.quorum} distinct "
            f"approvers; {len(record.approvers)} so far",
        )

    def save(self, path: str | Path) -> None:
        """Persist all records to *path* (atomic replace)."""
        import os

        target = Path(path).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "quorum": self.quorum,
            "ttl_seconds": self.ttl_seconds,
            "records": [r.to_dict() for r in self._records.values()],
            "events": self.events,
        }
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, target)

    @classmethod
    def load(cls, path: str | Path) -> DualControlGate:
        """Load a gate previously written by :meth:`save` (empty if absent)."""
        file = Path(path).expanduser()
        if not file.exists():
            return cls()
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        gate = cls(
            quorum=data.get("quorum", DEFAULT_QUORUM),
            ttl_seconds=data.get("ttl_seconds", 300),
        )
        for item in data.get("records", []):
            try:
                record = DualControlRecord(
                    dual_control_id=str(item["dual_control_id"]),
                    action_identity=str(item["action_identity"]),
                    quorum=int(item["quorum"]),
                    status=str(item["status"]),
                    tool=str(item["tool"]),
                    action=str(item["action"]),
                    created_at=str(item["created_at"]),
                    expires_at=str(item["expires_at"]),
                    approvers=tuple(item.get("approvers", ())),
                    escalation_id=item.get("escalation_id"),
                )
            except (KeyError, TypeError, ValueError):
                continue
            gate._records[record.dual_control_id] = record
        gate.events = list(data.get("events", []))
        return gate


def _resolution(status: str, reason_code: str, explanation: str) -> dict[str, Any]:
    return {"status": status, "reason_code": reason_code, "explanation": explanation}


__all__ = ["DEFAULT_QUORUM", "DualControlGate", "DualControlRecord"]
