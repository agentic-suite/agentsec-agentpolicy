"""Freeze windows (WBS M15 ``15.1``, CUJ-21 / R33).

A **declared, audited freeze** tightens the posture for its window: while a
window covers an environment, a write is escalated (`freeze_active`) and every
decision in that environment carries the ``freeze_id``. Declaring and expiring a
freeze are **audit events**, so the on/off trail is explicit.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

#: Actions a freeze tightens (the write/effectful set).
FREEZE_GATED_ACTIONS: frozenset[str] = frozenset(
    {"write", "deploy", "send", "transfer", "grant", "delete", "drop", "destroy",
     "force_push", "revoke", "purge"}
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class FreezeWindow:
    """A declared change-freeze over one or more environments."""

    freeze_id: str
    environments: frozenset[str]
    starts_at: str
    ends_at: str
    reason: str = ""

    def is_active(self, *, at: str | None = None, environment: str | None = None) -> bool:
        """Whether the window is active at *at* (default now) for *environment*."""
        when = at or _utc_now()
        if environment is not None and environment not in self.environments:
            return False
        return self.starts_at <= when <= self.ends_at

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "freeze_id": self.freeze_id,
            "environments": sorted(self.environments),
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "reason": self.reason,
        }


@dataclass
class FreezeLedger:
    """Track declared freezes and their audited on/off events."""

    _windows: dict[str, FreezeWindow] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def windows(self) -> dict[str, FreezeWindow]:
        """Read-only view of the declared windows."""
        return dict(self._windows)

    def declare(
        self,
        *,
        environments: list[str] | tuple[str, ...],
        starts_at: str | None = None,
        ends_at: str,
        reason: str = "",
    ) -> FreezeWindow:
        """Declare a freeze window (an audited ``declare`` event)."""
        if not environments:
            raise ValueError("a freeze must cover at least one environment")
        if not ends_at:
            raise ValueError("a freeze needs an ends_at")
        window = FreezeWindow(
            freeze_id="frz_" + secrets.token_hex(8),
            environments=frozenset(environments),
            starts_at=starts_at or _utc_now(),
            ends_at=ends_at,
            reason=reason,
        )
        self._windows[window.freeze_id] = window
        self.events.append({"kind": "declare", "freeze_id": window.freeze_id,
                            "at": _utc_now(), "window": window.to_dict()})
        return window

    def expire(self, freeze_id: str, *, at: str | None = None) -> FreezeWindow | None:
        """End a freeze early (an audited ``expire`` event)."""
        existing = self._windows.get(freeze_id)
        if existing is None:
            return None
        ended = FreezeWindow(
            freeze_id=existing.freeze_id, environments=existing.environments,
            starts_at=existing.starts_at, ends_at=at or _utc_now(),
            reason=existing.reason,
        )
        self._windows[freeze_id] = ended
        self.events.append({"kind": "expire", "freeze_id": freeze_id, "at": _utc_now()})
        return ended

    def active(self, environment: str, *, at: str | None = None) -> list[FreezeWindow]:
        """All windows active at *at* for *environment*."""
        return [
            w for w in self._windows.values()
            if w.is_active(at=at, environment=environment)
        ]

    def active_freeze(self, environment: str, *, at: str | None = None) -> FreezeWindow | None:
        """The governing freeze for *environment* (strictest wins), or ``None``.

        Strictest = the **narrowest** scope (fewest environments); ties break on
        the earlier ``starts_at``. Deterministic and documented.
        """
        candidates = self.active(environment, at=at)
        if not candidates:
            return None
        return min(candidates, key=lambda w: (len(w.environments), w.starts_at))

    def save(self, path: str | Path) -> None:
        """Persist the ledger to *path* (atomic replace)."""
        import os

        target = Path(path).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "windows": [w.to_dict() for w in self._windows.values()],
            "events": self.events,
        }
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, target)

    @classmethod
    def load(cls, path: str | Path) -> FreezeLedger:
        """Load a ledger previously written by :meth:`save` (empty if absent)."""
        file = Path(path).expanduser()
        ledger = cls()
        if not file.exists():
            return ledger
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return ledger
        for item in data.get("windows", []):
            try:
                window = FreezeWindow(
                    freeze_id=str(item["freeze_id"]),
                    environments=frozenset(item["environments"]),
                    starts_at=str(item["starts_at"]),
                    ends_at=str(item["ends_at"]),
                    reason=str(item.get("reason", "")),
                )
            except (KeyError, TypeError):
                continue
            ledger._windows[window.freeze_id] = window
        ledger.events = list(data.get("events", []))
        return ledger


__all__ = ["FREEZE_GATED_ACTIONS", "FreezeLedger", "FreezeWindow"]
