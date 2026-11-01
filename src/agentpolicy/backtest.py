"""Policy backtest & PR decision-diff (WBS M20 ``20.1``-``20.3``, CUJ-29 / R43).

Replay a window of recorded agentwatch history against a **candidate** policy
versus the **baseline** in force, and emit the exact **flip set** — newly-denied
/ newly-asked / newly-allowed / unchanged.

* **Read-only:** the backtest re-executes nothing in the live path and emits **no
  fleet events**; it evaluates reconstructed calls through a throwaway engine.
* **Advisory:** every report is watermarked ``backtest`` and excluded from live
  analytics and the golden gate; a flip is a review signal, never a build failure.
* **Exact & reproducible:** the classification is a pure function of the two
  decisions, replayed in a stable order.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentpolicy.canonical import canonicalize
from agentpolicy.engine.engine import Engine
from agentpolicy.policy.models import Policy, default_policy
from agentpolicy.types import NormalizedCall

#: The report watermark — a backtest decision is not a live decision.
WATERMARK = "backtest"

#: The transition labels (the four quadrants).
UNCHANGED = "unchanged"
NEWLY_DENIED = "newly_denied"
NEWLY_ASKED = "newly_asked"
NEWLY_ALLOWED = "newly_allowed"


def _classify(decision: str) -> str:
    """Collapse an engine outcome to one of ``allow`` / ``ask`` / ``deny``."""
    if decision == "deny":
        return "deny"
    if decision == "escalate":
        return "ask"
    return "allow"


def classify_transition(before: str, after: str) -> str:
    """Classify a ``(before, after)`` outcome pair into the four-quadrant label.

    ``before`` / ``after`` are the collapsed outcomes (``allow`` / ``ask`` /
    ``deny``). The mapping is total and deterministic: the *after* outcome decides
    a non-unchanged transition (``deny`` is stricter than ``ask``).
    """
    if before == after:
        return UNCHANGED
    if after == "deny":
        return NEWLY_DENIED
    if after == "ask":
        return NEWLY_ASKED
    return NEWLY_ALLOWED


@dataclass(frozen=True)
class Flip:
    """One transitioned call in the backtest diff."""

    event_id: str
    tool: str
    action: str
    environment: str
    data_class: str
    agent_id: str
    before: str
    after: str
    reason_code: str

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "event_id": self.event_id, "tool": self.tool, "action": self.action,
            "environment": self.environment, "data_class": self.data_class,
            "agent_id": self.agent_id, "before": self.before, "after": self.after,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class BacktestReport:
    """The advisory decision-diff for a replayed history window."""

    total: int
    unchanged: int
    newly_denied: tuple[Flip, ...] = ()
    newly_asked: tuple[Flip, ...] = ()
    newly_allowed: tuple[Flip, ...] = ()
    window_start: str | None = None
    window_end: str | None = None
    watermark: str = WATERMARK
    advisory: bool = True
    emits_events: bool = False
    excluded_from_golden_gate: bool = True
    coverage_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "watermark": self.watermark,
            "advisory": self.advisory,
            "emits_events": self.emits_events,
            "excluded_from_golden_gate": self.excluded_from_golden_gate,
            "total": self.total,
            "unchanged": self.unchanged,
            "newly_denied": [f.to_dict() for f in self.newly_denied],
            "newly_asked": [f.to_dict() for f in self.newly_asked],
            "newly_allowed": [f.to_dict() for f in self.newly_allowed],
            "window_start": self.window_start,
            "window_end": self.window_end,
            "coverage_note": self.coverage_note,
        }

    def summary(self) -> str:
        """A compact, PR-step-summary-friendly summary (advisory)."""
        return (
            f"backtest (advisory, read-only): {self.total} actions · "
            f"{len(self.newly_denied)} newly-denied · {len(self.newly_asked)} newly-asked · "
            f"{len(self.newly_allowed)} newly-allowed · {self.unchanged} unchanged\n"
            f"window: {self.window_start}..{self.window_end}\n{self.coverage_note}"
        )


def call_from_event(event: dict[str, Any]) -> NormalizedCall:
    """Reconstruct the canonical call from an agentwatch decision event."""
    principal = event.get("principal", {})
    action = event.get("action", {})
    resource = event.get("resource", {})
    return canonicalize(
        tool=str(action.get("tool", "")),
        action=str(action.get("verb", "read")),
        environment=str(resource.get("environment", "staging")),
        data_class=str(resource.get("data_class", "internal")),
        agent_id=str(principal.get("agent_id", "unknown")),
        agent_class=str(principal.get("agent_class", "general")),
    )


def load_history(path: str | Path) -> list[dict[str, Any]]:
    """Load a JSONL history window; blank/malformed lines are skipped."""
    file = Path(path).expanduser()
    if not file.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            event = json.loads(stripped)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _replay_pair(
    event: dict[str, Any], baseline_engine: Engine, candidate_engine: Engine
) -> tuple[NormalizedCall, str, str, str] | None:
    """Replay one event through both engines; ``None`` for an unusable event."""
    try:
        call = call_from_event(event)
        before = baseline_engine.evaluate(
            tool_name=call.tool, action=call.action, environment=call.environment,
            data_class=call.data_class, agent_id=call.agent_id,
        )
        after = candidate_engine.evaluate(
            tool_name=call.tool, action=call.action, environment=call.environment,
            data_class=call.data_class, agent_id=call.agent_id,
        )
    except Exception:
        return None
    return call, before.decision, after.decision, after.reason_code


def backtest(
    events: Iterable[dict[str, Any]],
    candidate: Policy,
    *,
    baseline: Policy | None = None,
    emit: Callable[..., None] | None = None,
) -> BacktestReport:
    """Replay *events* against the baseline and candidate policies.

    Args:
        events: The recorded agentwatch decision events (the history window).
        candidate: The candidate policy under review.
        baseline: The policy currently in force (defaults to the balanced preset).
        emit: A fleet-event emitter hook. **The backtest never calls it** — it is
            accepted so a caller can prove the backtest emits no fleet events.

    Returns:
        A :class:`BacktestReport` (watermarked ``backtest``, advisory).
    """
    del emit  # the backtest emits no fleet events (read-only)
    baseline_engine = Engine(baseline if baseline is not None else default_policy("balanced"))
    candidate_engine = Engine(candidate)
    ordered = sorted(events, key=lambda e: str(e.get("event_id", "")))
    denied: list[Flip] = []
    asked: list[Flip] = []
    allowed: list[Flip] = []
    unchanged = 0
    stamps: list[str] = []
    for event in ordered:
        pair = _replay_pair(event, baseline_engine, candidate_engine)
        if pair is None:
            continue
        call, before_decision, after_decision, after_reason = pair
        transition = classify_transition(_classify(before_decision), _classify(after_decision))
        if transition == UNCHANGED:
            unchanged += 1
        else:
            flip = Flip(
                event_id=str(event.get("event_id", "")), tool=call.tool, action=call.action,
                environment=call.environment, data_class=call.data_class,
                agent_id=call.agent_id, before=_classify(before_decision),
                after=_classify(after_decision), reason_code=after_reason,
            )
            {"newly_denied": denied, "newly_asked": asked, "newly_allowed": allowed}[
                transition
            ].append(flip)
        stamp = event.get("timestamp")
        if isinstance(stamp, str):
            stamps.append(stamp)
    total = len(denied) + len(asked) + len(allowed) + unchanged
    window_start = min(stamps) if stamps else None
    window_end = max(stamps) if stamps else None
    note = (
        f"covers {total} recorded action(s) from {window_start} to {window_end}; "
        "history is a sample, not a proof — advisory input to review, never auto-merge"
    )
    return BacktestReport(
        total=total, unchanged=unchanged, newly_denied=tuple(denied),
        newly_asked=tuple(asked), newly_allowed=tuple(allowed),
        window_start=window_start, window_end=window_end, coverage_note=note,
    )


__all__ = [
    "BacktestReport",
    "Flip",
    "backtest",
    "call_from_event",
    "classify_transition",
    "load_history",
]
