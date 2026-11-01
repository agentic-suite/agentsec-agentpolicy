"""Break-glass elevation (WBS M18 ``18.1`` / ``18.2``, CUJ-25 / R40).

A **declared, time-boxed, fully audited** posture elevation for one agent over
one or more environments. Elevation **widens *scope ceilings* only** — it never
bypasses the mandatory human gate (the composition guard lives in the engine).

* :meth:`BreakGlassLedger.elevate` requires a **logged reason** (never silent)
  and mints a ``bg_``-prefixed id; the elevation is an audited ``elevate`` event.
* :meth:`BreakGlassLedger.revert` ends a window early; :meth:`sweep` auto-reverts
  every expired window **without a manual action**, logging a ``revert`` event.
* The engine stamps ``break_glass_id`` on **every** decision made while a window
  elevates the agent.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

#: Default elevation TTL (short by design — RK-17: break-glass must not become
#: the default path by habit).
DEFAULT_TTL_SECONDS = 900


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class BreakGlassWindow:
    """A time-boxed elevation for one agent over one or more environments."""

    break_glass_id: str
    agent_id: str
    environments: frozenset[str]
    starts_at: str
    ends_at: str
    reason: str

    def is_active(
        self,
        *,
        at: str | None = None,
        environment: str | None = None,
        agent_id: str | None = None,
    ) -> bool:
        """Whether the window elevates *agent_id* in *environment* at *at*."""
        when = at or _utc_now()
        if agent_id is not None and agent_id != self.agent_id:
            return False
        if environment is not None and environment not in self.environments:
            return False
        return self.starts_at <= when <= self.ends_at

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "break_glass_id": self.break_glass_id,
            "agent_id": self.agent_id,
            "environments": sorted(self.environments),
            "starts_at": self.starts_at,
            "ends_at": self.ends_at,
            "reason": self.reason,
        }


@dataclass
class BreakGlassLedger:
    """Track declared elevations and their audited on/off events."""

    _windows: dict[str, BreakGlassWindow] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    _reverted: set[str] = field(default_factory=set)

    @property
    def windows(self) -> dict[str, BreakGlassWindow]:
        """Read-only view of the declared windows."""
        return dict(self._windows)

    def elevate(
        self,
        *,
        agent_id: str,
        environments: list[str] | tuple[str, ...],
        ends_at: str | None = None,
        reason: str,
        starts_at: str | None = None,
        ttl_seconds: int | None = None,
    ) -> BreakGlassWindow:
        """Declare an elevation (an audited ``elevate`` event).

        A **logged reason is mandatory** — an elevation is never silent.
        """
        if not reason or not reason.strip():
            raise ValueError("break-glass elevation requires a non-blank reason")
        if not agent_id or not agent_id.strip():
            raise ValueError("break-glass elevation requires an agent_id")
        if not environments:
            raise ValueError("a break-glass elevation must cover at least one environment")
        start = starts_at or _utc_now()
        if ends_at is None:
            ttl = ttl_seconds if ttl_seconds is not None else DEFAULT_TTL_SECONDS
            end = (datetime.fromisoformat(start) + timedelta(seconds=ttl)).isoformat()
        else:
            end = ends_at
        window = BreakGlassWindow(
            break_glass_id="bg_" + secrets.token_hex(8),
            agent_id=agent_id,
            environments=frozenset(environments),
            starts_at=start,
            ends_at=end,
            reason=reason,
        )
        self._windows[window.break_glass_id] = window
        self.events.append(
            {"kind": "elevate", "break_glass_id": window.break_glass_id, "at": _utc_now(),
             "window": window.to_dict()}
        )
        return window

    def revert(self, break_glass_id: str, *, at: str | None = None) -> BreakGlassWindow | None:
        """End an elevation early (an audited ``revert`` event)."""
        existing = self._windows.get(break_glass_id)
        if existing is None:
            return None
        ended = BreakGlassWindow(
            break_glass_id=existing.break_glass_id,
            agent_id=existing.agent_id,
            environments=existing.environments,
            starts_at=existing.starts_at,
            ends_at=at or _utc_now(),
            reason=existing.reason,
        )
        self._windows[break_glass_id] = ended
        if break_glass_id not in self._reverted:
            self._reverted.add(break_glass_id)
            self.events.append(
                {"kind": "revert", "break_glass_id": break_glass_id, "at": _utc_now()}
            )
        return ended

    def sweep(self, *, at: str | None = None) -> list[str]:
        """Auto-revert every expired window (audited), returning the reverted ids."""
        when = at or _utc_now()
        reverted: list[str] = []
        for window in list(self._windows.values()):
            if window.break_glass_id in self._reverted:
                continue
            if when > window.ends_at:
                self.revert(window.break_glass_id, at=when)
                reverted.append(window.break_glass_id)
        return reverted

    def active_window(
        self, agent_id: str, environment: str, *, at: str | None = None
    ) -> BreakGlassWindow | None:
        """The elevation in force for *agent_id* in *environment*, or ``None``.

        Expired windows are auto-reverted (swept) before the lookup, so the
        revert is logged even if no operator acts.
        """
        self.sweep(at=at)
        for window in self._windows.values():
            if window.is_active(at=at, environment=environment, agent_id=agent_id):
                return window
        return None

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
    def load(cls, path: str | Path) -> BreakGlassLedger:
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
                window = BreakGlassWindow(
                    break_glass_id=str(item["break_glass_id"]),
                    agent_id=str(item["agent_id"]),
                    environments=frozenset(item["environments"]),
                    starts_at=str(item["starts_at"]),
                    ends_at=str(item["ends_at"]),
                    reason=str(item.get("reason", "")),
                )
            except (KeyError, TypeError):
                continue
            ledger._windows[window.break_glass_id] = window
        ledger.events = list(data.get("events", []))
        for event in ledger.events:
            if event.get("kind") == "revert":
                ledger._reverted.add(str(event.get("break_glass_id", "")))
        return ledger


__all__ = ["DEFAULT_TTL_SECONDS", "BreakGlassLedger", "BreakGlassWindow"]
