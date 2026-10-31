"""agentwatch security-event emitter (WBS M5 ``5.5``, R6).

Renders a finished decision as an ``agentwatch.security_event.v1`` event
(``event_type: policy.decision``) per [ADR-0007] and PRD 15/17. A decision, its
emitted event, and its hash-chained audit entry (M6) share one join key
(``event_id`` == ``decision_id``), so a deny, the tool call it denied, and the
halt it triggered are one query away in agentwatch/SIEM.

Emission is **pure** — no clock, no network, no sink. The caller decides where
the event goes; agentpolicy does not store the lake (ADR-0007).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from agentpolicy.cedar.models import Decision
from agentpolicy.explain import ExplainArtifact
from agentpolicy.types import NormalizedCall

#: The agentwatch schema the event is emitted in.
SCHEMA = "agentwatch.security_event.v1"
#: The event type for a policy decision.
EVENT_TYPE = "policy.decision"


def event_args_hash(arguments: dict[str, Any] | None) -> str | None:
    """The stable ``sha256:<hex>`` hash of a call's arguments, or ``None``.

    A hash — never the raw argument values — travels in the event, so secrets
    pasted into a tool call are not replicated into the telemetry lake.
    """
    if not arguments:
        return None
    payload = json.dumps(arguments, sort_keys=True, default=str).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class DecisionEvent:
    """One ``agentwatch.security_event.v1`` (``policy.decision``) event."""

    event_id: str
    decision_id: str
    call: NormalizedCall
    decision: Decision
    session_id: str | None = None
    timestamp: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """The nested event payload (PRD 15 shape)."""
        if not self.event_id or not self.event_id.strip():
            raise ValueError("event_id must be a non-blank string")
        if not self.decision_id or not self.decision_id.strip():
            raise ValueError("decision_id must be a non-blank string")
        call = self.call
        return {
            "schema": SCHEMA,
            "event_type": EVENT_TYPE,
            "event_id": self.event_id,
            "decision_id": self.decision_id,
            "principal": {"agent_id": call.agent_id, "agent_class": call.agent_class},
            "action": {
                "verb": call.action,
                "tool": call.tool,
                "args_hash": event_args_hash(call.arguments),
            },
            "resource": {
                "tool_category": call.tool_category,
                "environment": call.environment,
                "data_class": call.data_class,
            },
            "decision": self.decision.decision,
            "reason_code": self.decision.reason_code,
            "criticality": self.decision.criticality,
            "matched_rule": self.decision.matched_rule,
            "policy_version": self.decision.policy_version,
            "policy_hash": self.decision.policy_hash,
            "session_id": self.session_id,
            "timestamp": self.timestamp or _utc_now(),
        }


def decision_event(
    decision: Decision,
    call: NormalizedCall,
    *,
    event_id: str,
    decision_id: str,
    session_id: str | None = None,
    timestamp: str | None = None,
) -> DecisionEvent:
    """Build the event for a decision. ``event_id``/``decision_id`` are the join keys."""
    return DecisionEvent(
        event_id=event_id,
        decision_id=decision_id,
        call=call,
        decision=decision,
        session_id=session_id,
        timestamp=timestamp,
    )


def to_event(
    decision: Decision,
    call: NormalizedCall,
    *,
    event_id: str,
    decision_id: str,
    session_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Render a decision as an agentwatch event dict (validates the join keys)."""
    return decision_event(
        decision,
        call,
        event_id=event_id,
        decision_id=decision_id,
        session_id=session_id,
        timestamp=timestamp,
    ).to_dict()


def event_for(
    artifact: ExplainArtifact,
    call: NormalizedCall,
    *,
    session_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Render the event for an explain artifact, reusing its join key.

    The artifact carries the decision literal + provenance, so the emitted event
    joins the artifact and (via ``decision_id``) the M6 audit entry.
    """
    if not artifact.event_id or not artifact.event_id.strip():
        raise ValueError("event_id must be a non-blank string")
    if not artifact.decision_id or not artifact.decision_id.strip():
        raise ValueError("decision_id must be a non-blank string")
    return {
        "schema": SCHEMA,
        "event_type": EVENT_TYPE,
        "event_id": artifact.event_id,
        "decision_id": artifact.decision_id,
        "principal": {"agent_id": call.agent_id, "agent_class": call.agent_class},
        "action": {
            "verb": call.action,
            "tool": call.tool,
            "args_hash": event_args_hash(call.arguments),
        },
        "resource": {
            "tool_category": call.tool_category,
            "environment": call.environment,
            "data_class": call.data_class,
        },
        "decision": artifact.decision,
        "reason_code": artifact.reason_code,
        "criticality": artifact.criticality,
        "matched_rule": artifact.matched_rule,
        "policy_version": artifact.policy_version,
        "policy_hash": artifact.policy_hash,
        "session_id": session_id,
        "timestamp": timestamp or _utc_now(),
    }


__all__ = [
    "EVENT_TYPE",
    "SCHEMA",
    "DecisionEvent",
    "decision_event",
    "event_args_hash",
    "event_for",
    "to_event",
]
