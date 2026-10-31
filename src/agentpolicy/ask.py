"""The ask-gate broker (WBS M7 ``7.1``).

The Cedar ``ask`` outcome means "a human must decide". This broker is the single
source of truth for that round-trip, bound to an **action identity** and a TTL:

* :meth:`AskBroker.create` records a pending ask for a call that resolved to
  ``ask`` and mints an ``ask_``-prefixed, unguessable id.
* :meth:`AskBroker.approve` / :meth:`AskBroker.deny` record the human decision.
* :meth:`AskBroker.resolve` is the engine-facing re-submission check: **approved
  → allow, denied/expired/unknown/pending → deny**. An approval is bound to the
  exact ``(tool, action, arguments)`` identity, so an approval for X cannot
  release Y.

**Timeout = deny:** an ask whose TTL has elapsed resolves to a deny with reason
code ``human_gate_timeout`` — an unanswered gate never silently allows.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from agentpolicy import reason_codes
from agentpolicy.cedar.models import Decision
from agentpolicy.engine.escalation import (
    _canonical_args,  # noqa: F401 - re-exported for tests/parity
    action_identity,
)
from agentpolicy.types import NormalizedCall


class AskStatus(Enum):
    """Lifecycle of an ask record."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


@dataclass(frozen=True)
class Ask:
    """One recorded ask request (the human gate for a Cedar ``ask`` decision)."""

    ask_id: str
    status: AskStatus
    tool: str
    action: str
    agent_id: str
    environment: str
    data_class: str
    action_identity: str
    reason: str
    created_at: str
    expires_at: str
    arguments: dict[str, Any] | None = None
    approver: str | None = None
    denied_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation for the CLI."""
        return {
            "ask_id": self.ask_id,
            "status": self.status.value,
            "tool": self.tool,
            "action": self.action,
            "agent_id": self.agent_id,
            "environment": self.environment,
            "data_class": self.data_class,
            "action_identity": self.action_identity,
            "reason": self.reason,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "expired": self.is_expired(),
            "approver": self.approver,
            "denied_reason": self.denied_reason,
        }

    def is_expired(self, now: datetime | None = None) -> bool:
        """Whether the ask has outlived its TTL (treated as deny)."""
        return (now or _utcnow()) > _parse_iso(self.expires_at)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _parse_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


class AskBroker:
    """Track ask records and enforce approve/deny/expire + replay safety.

    Args:
        ttl_seconds: Default ask TTL in seconds (default 300 = 5 min).
    """

    def __init__(self, ttl_seconds: int = 300) -> None:
        self.ttl = timedelta(seconds=ttl_seconds)
        self._records: dict[str, Ask] = {}
        self._identity_index: dict[str, str] = {}

    @property
    def records(self) -> dict[str, Ask]:
        """Read-only view of all ask records (id -> record)."""
        return dict(self._records)

    def pending(self, now: datetime | None = None) -> list[Ask]:
        """Return unresolved asks in creation order."""
        return [r for r in self._records.values() if r.status == AskStatus.PENDING]

    def create(self, call: NormalizedCall, *, reason: str = "",
               now: datetime | None = None) -> Ask:
        """Create a pending ask for a call that resolved to ``ask``."""
        now = now or _utcnow()
        ask = Ask(
            ask_id="ask_" + secrets.token_hex(8),
            status=AskStatus.PENDING,
            tool=call.tool,
            action=call.action,
            agent_id=call.agent_id,
            environment=call.environment,
            data_class=call.data_class,
            action_identity=action_identity(call.tool, call.action, call.arguments),
            reason=reason,
            arguments=call.arguments,
            created_at=now.isoformat(),
            expires_at=(now + self.ttl).isoformat(),
        )
        self._records[ask.ask_id] = ask
        return ask

    def approve(self, ask_id: str, *, approver: str,
                now: datetime | None = None) -> Ask:
        """Approve a pending ask (the call may execute)."""
        record = self._require_pending(ask_id, now)
        if not approver or not approver.strip():
            raise ValueError("approver must be a non-blank string")
        approved = replace(record, status=AskStatus.APPROVED, approver=approver)
        self._records[ask_id] = approved
        self._identity_index[approved.action_identity] = ask_id
        return approved

    def deny(self, ask_id: str, *, approver: str, reason: str = "",
             now: datetime | None = None) -> Ask:
        """Deny a pending ask (the call must not execute)."""
        record = self._require_pending(ask_id, now)
        if not approver or not approver.strip():
            raise ValueError("approver must be a non-blank string")
        denied = replace(
            record, status=AskStatus.DENIED, approver=approver,
            denied_reason=reason or None,
        )
        self._records[ask_id] = denied
        return denied

    def resolve(self, ask_id: str, *, call: NormalizedCall,
                now: datetime | None = None) -> dict[str, Any]:
        """Resolve an ask for a call: approved → allow, else deny."""
        record = self._records.get(ask_id)
        if record is None:
            return _resolution(
                "deny", reason_codes.DENY_ASK_UNKNOWN,
                f"unknown ask {ask_id!r}",
            )
        if record.is_expired(now):
            self._records[ask_id] = replace(record, status=AskStatus.EXPIRED)
            return _resolution(
                "deny", reason_codes.HUMAN_GATE_TIMEOUT,
                f"ask {ask_id} expired without a decision (timeout = deny)",
            )
        if action_identity(call.tool, call.action, call.arguments) != record.action_identity:
            return _resolution(
                "deny", reason_codes.DENY_ACTION_IDENTITY_MISMATCH,
                f"ask {ask_id} was resolved for a different tool/action/argument set",
            )
        if record.status == AskStatus.APPROVED:
            return _resolution(
                "allow", reason_codes.ALLOW_ASK_APPROVED,
                f"ask {ask_id} approved by {record.approver}",
            )
        if record.status == AskStatus.DENIED:
            return _resolution(
                "deny", reason_codes.DENY_ASK_DENIED,
                record.denied_reason or "ask denied",
            )
        return _resolution(
            "deny", reason_codes.DENY_ASK_PENDING,
            f"ask {ask_id} is still pending and was not approved",
        )

    def find_by_action_identity(self, identity: str) -> str | None:
        """Return the approved ask id bound to an action identity."""
        return self._identity_index.get(identity)

    def save(self, path: str | Path) -> None:
        """Persist all records to *path* as JSON (atomic replace)."""
        import os

        target = Path(path).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "ttl_seconds": int(self.ttl.total_seconds()),
            "records": [r.to_dict() for r in self._records.values()],
        }
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, target)

    @classmethod
    def load(cls, path: str | Path) -> AskBroker:
        """Load a broker previously written by :meth:`save`.

        A missing/unreadable file yields an empty broker (no approvals assumed).
        """
        file = Path(path).expanduser()
        if not file.exists():
            return cls()
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        broker = cls(ttl_seconds=data.get("ttl_seconds", 300))
        for item in data.get("records", []):
            try:
                status = AskStatus(item["status"])
                record = Ask(
                    ask_id=item["ask_id"],
                    status=status,
                    tool=item["tool"],
                    action=item["action"],
                    agent_id=item["agent_id"],
                    environment=item["environment"],
                    data_class=item["data_class"],
                    action_identity=item["action_identity"],
                    reason=item.get("reason", ""),
                    created_at=item["created_at"],
                    expires_at=item["expires_at"],
                    arguments=item.get("arguments"),
                    approver=item.get("approver"),
                    denied_reason=item.get("denied_reason"),
                )
            except (KeyError, ValueError):
                continue
            broker._records[record.ask_id] = record
            if record.status == AskStatus.APPROVED:
                broker._identity_index[record.action_identity] = record.ask_id
        return broker

    def _require_pending(self, ask_id: str, now: datetime | None) -> Ask:
        record = self._records.get(ask_id)
        if record is None:
            raise ValueError("unknown ask_id")
        if record.status != AskStatus.PENDING:
            raise ValueError(f"ask already resolved as {record.status.value}")
        if record.is_expired(now):
            self._records[ask_id] = replace(record, status=AskStatus.EXPIRED)
            raise ValueError("ask expired")
        return record


def _resolution(status: str, reason_code: str, explanation: str) -> dict[str, Any]:
    return {"status": status, "reason_code": reason_code, "explanation": explanation}


def gate(
    decision: Decision, call: NormalizedCall, broker: AskBroker
) -> tuple[Decision, Ask | None]:
    """Wire a Cedar ``ask`` decision into the broker: create + stamp an ask.

    A decision that is not ``ask`` is returned untouched with ``None``.

    Args:
        decision: The Cedar decision.
        call: The canonical call.
        broker: The ask broker to record into.

    Returns:
        ``(decision_with_ask_id, ask)``; ``ask`` is ``None`` for a non-ask decision.
    """
    if decision.decision != "ask":
        return decision, None
    ask = broker.create(call, reason=decision.explanation)
    return replace(decision, ask_id=ask.ask_id), ask


__all__ = ["Ask", "AskBroker", "AskStatus", "action_identity", "gate"]
