"""Scope-escalation / step-up (WBS M14 ``14.1``, CUJ-19 / R11).

When a downstream service answers with an authorization **challenge** (HTTP
403), the agent should not repeat the same over-broad request — it should
**narrow its scope** and re-issue with a step-up context. This module turns a
denial into a least-privilege :class:`StepUpRequest`: the narrowed action is
derived (via the M5 actionability search, so it is *verified* to change the
outcome) and carried with an AuthZEN ``acr_values`` step-up marker.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from agentpolicy.explain import flip_variant

if TYPE_CHECKING:
    from agentpolicy.cedar.models import Decision
    from agentpolicy.types import NormalizedCall

#: The AuthZEN ``acr_values`` marker for a narrow-scope step-up.
STEP_UP_ACR = "urn:agentpolicy:stepup:narrow-scope"

#: The canonical-call fields a narrowed request carries.
_FIELDS = ("tool", "tool_category", "action", "action_class", "environment",
           "data_class", "agent_id", "agent_class")


@dataclass(frozen=True)
class StepUpRequest:
    """A narrower-scope re-issuance request for a challenged action."""

    acr_values: tuple[str, ...]
    narrowed: dict[str, Any]
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "acr_values": list(self.acr_values),
            "narrowed": dict(self.narrowed),
            "reason": self.reason,
        }


def is_challenge(status_code: int) -> bool:
    """Whether an HTTP status is an authorization challenge (step-up trigger)."""
    return status_code == 403


def step_up(
    decision: Decision, call: NormalizedCall, evaluator: Any
) -> StepUpRequest | None:
    """Build a least-privilege step-up request for a denied *call*.

    The narrowed scope is the M5 actionability variant — verified to change the
    outcome — so the re-issued request is genuinely narrower and permitted.
    Returns ``None`` when the outcome has no action-level narrowing (an allow,
    or a hard class denial with no flip).

    Args:
        decision: The Cedar decision for *call*.
        call: The canonical call.
        evaluator: The Cedar evaluator (for the verified narrowing).

    Returns:
        A :class:`StepUpRequest`, or ``None``.
    """
    variant = flip_variant(decision, call, evaluator)
    if variant is None:
        return None
    narrowed = {field: getattr(variant, field) for field in _FIELDS}
    return StepUpRequest(
        acr_values=(STEP_UP_ACR,),
        narrowed=narrowed,
        reason=(
            f"narrow the scope of {call.tool!r} (was denied: {decision.reason_code}) "
            "and re-issue with a step-up"
        ),
    )


__all__ = ["STEP_UP_ACR", "StepUpRequest", "is_challenge", "step_up"]
