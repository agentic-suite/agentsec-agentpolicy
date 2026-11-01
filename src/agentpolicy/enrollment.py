"""Agent enrollment ledger & probation posture (WBS M16 ``16.1``, CUJ-22 / R35).

A **first-seen unknown agent** lands in **probation**: reads are allowed, writes
require human classification (``escalate`` with reason ``agent_probation``). A
human **classifies** the agent (enrolled / blocked) — a **logged event** — and
the classification feeds the fleet inventory. No shadow IdP: the ledger is the
source of truth.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

#: Actions gated while an agent is in probation (writes + effectful ops).
PROBATION_GATED_ACTIONS: frozenset[str] = frozenset(
    {"write", "deploy", "send", "transfer", "grant", "delete", "drop", "destroy",
     "force_push", "revoke", "purge", "publish", "upload"}
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


class EnrollmentStatus(Enum):
    """An agent's enrollment state."""

    PROBATION = "probation"
    ENROLLED = "enrolled"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class Enrollment:
    """One agent's enrollment record."""

    agent_id: str
    status: EnrollmentStatus
    agent_class: str | None = None
    first_seen: str = field(default_factory=_utc_now)
    classified_by: str | None = None
    classified_at: str | None = None
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "agent_class": self.agent_class,
            "first_seen": self.first_seen,
            "classified_by": self.classified_by,
            "classified_at": self.classified_at,
            "note": self.note,
        }


@dataclass
class EnrollmentLedger:
    """Track first-seen agents, their probation, and classification events."""

    _records: dict[str, Enrollment] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def records(self) -> dict[str, Enrollment]:
        """Read-only view of the enrollment records."""
        return dict(self._records)

    def observe(self, agent_id: str, *, agent_class: str | None = None) -> Enrollment:
        """Return the agent's record, creating a PROBATION record if first-seen."""
        existing = self._records.get(agent_id)
        if existing is not None:
            return existing
        record = Enrollment(agent_id=agent_id, status=EnrollmentStatus.PROBATION,
                            agent_class=agent_class)
        self._records[agent_id] = record
        self.events.append({"kind": "probation", "agent_id": agent_id,
                            "at": _utc_now(), "agent_class": agent_class})
        return record

    def classify(
        self, agent_id: str, status: EnrollmentStatus, *, by: str, note: str = ""
    ) -> Enrollment:
        """Classify a probationary agent (a logged classification event).

        Raises:
            ValueError: the agent is unknown, the status is PROBATION, or ``by``
                is blank.
        """
        if not by or not by.strip():
            raise ValueError("classifier must be a non-blank string")
        if status == EnrollmentStatus.PROBATION:
            raise ValueError("classification must be ENROLLED or BLOCKED, not PROBATION")
        existing = self._records.get(agent_id)
        if existing is None:
            raise ValueError(f"unknown agent {agent_id!r}")
        classified = replace(
            existing, status=status, classified_by=by, classified_at=_utc_now(), note=note
        )
        self._records[agent_id] = classified
        self.events.append({
            "kind": "classification", "agent_id": agent_id, "status": status.value,
            "at": classified.classified_at, "by": by,
        })
        return classified

    def get(self, agent_id: str) -> Enrollment | None:
        """Return the agent's record, or ``None``."""
        return self._records.get(agent_id)

    def is_probation(self, agent_id: str) -> bool:
        """Whether the agent is currently in probation."""
        record = self._records.get(agent_id)
        return record is not None and record.status == EnrollmentStatus.PROBATION

    def save(self, path: str | Path) -> None:
        """Persist the ledger to *path* (atomic replace)."""
        import os

        target = Path(path).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "records": [r.to_dict() for r in self._records.values()],
            "events": self.events,
        }
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, target)

    @classmethod
    def load(cls, path: str | Path) -> EnrollmentLedger:
        """Load a ledger previously written by :meth:`save` (empty if absent)."""
        file = Path(path).expanduser()
        ledger = cls()
        if not file.exists():
            return ledger
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return ledger
        for item in data.get("records", []):
            try:
                record = Enrollment(
                    agent_id=str(item["agent_id"]),
                    status=EnrollmentStatus(item["status"]),
                    agent_class=item.get("agent_class"),
                    first_seen=str(item.get("first_seen", _utc_now())),
                    classified_by=item.get("classified_by"),
                    classified_at=item.get("classified_at"),
                    note=str(item.get("note", "")),
                )
            except (KeyError, ValueError):
                continue
            ledger._records[record.agent_id] = record
        ledger.events = list(data.get("events", []))
        return ledger


__all__ = ["PROBATION_GATED_ACTIONS", "Enrollment", "EnrollmentLedger", "EnrollmentStatus"]
