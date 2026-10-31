"""agenthalt integration (WBS M12 ``12.4``).

When a session's **hard** capability ceiling is exhausted (a blast-radius
budget is over its cap), the engine does not merely throttle the one call — it
raises a **halt** event carrying the evidence (the budget state), so an operator
(and agentwatch/agenthalt) can freeze the session and review. The controller is
a pure observer: it never blocks the decision itself, it records the trigger.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class HaltEvent:
    """A session halt trigger with its evidence."""

    session_id: str
    reason: str
    evidence: dict[str, Any]
    at: str

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "kind": "session_halt",
            "session_id": self.session_id,
            "reason": self.reason,
            "evidence": dict(self.evidence),
            "at": self.at,
        }


@dataclass
class HaltController:
    """Fires a :class:`HaltEvent` when a session's budget is exhausted.

    Args:
        on_halt: Optional callback invoked with the event (e.g. to notify
            agentwatch/agenthalt). Failures in the callback are swallowed — a
            notification must never block a decision.
    """

    on_halt: Callable[[HaltEvent], None] | None = None
    events: list[HaltEvent] = field(default_factory=list)

    def maybe_halt(self, session_id: str, budget_state: dict[str, Any]) -> HaltEvent | None:
        """Emit a halt event when ``budget_state['over']`` is non-empty."""
        over = budget_state.get("over") or []
        if not over:
            return None
        event = HaltEvent(
            session_id=session_id,
            reason=f"blast-radius budget exhausted: {', '.join(map(str, over))}",
            evidence=budget_state,
            at=_utc_now(),
        )
        self.events.append(event)
        if self.on_halt is not None:
            try:
                self.on_halt(event)
            except Exception:
                return event
        return event


__all__ = ["HaltController", "HaltEvent"]
