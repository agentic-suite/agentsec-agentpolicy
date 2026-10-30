"""The Cedar evaluator (M2 ``2.1``) — deterministic, sub-100 ms inline.

Wraps :mod:`cedarpy` (the Cedar Rust evaluator) over the canonical action. There
is **no ML and no network** in this path: the same input + policy always yields
the same decision.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import cedarpy

from agentpolicy.cedar import policy as policy_mod
from agentpolicy.cedar.models import Decision
from agentpolicy.cedar.shaper import ShaperContext, shape

if TYPE_CHECKING:
    from agentpolicy.types import NormalizedCall


def _matched_rule(result: Any) -> str | None:
    """Best-effort extraction of the deciding rule id from the diagnostics."""
    diagnostics = getattr(result, "diagnostics", None)
    reason = getattr(diagnostics, "reason", None)
    if isinstance(reason, str) and reason and reason not in ("None", ""):
        return reason
    return None


class CedarEvaluator:
    """A deterministic Cedar PDP over a policy set."""

    def __init__(
        self, policies: str = policy_mod.BASE_POLICY, *, policy_version: str = "0.1.0"
    ) -> None:
        self._policies = policies
        self._policy_version = policy_version
        # Fail fast on a malformed policy (pure parse; no evaluation, so a rule
        # may reference context attributes this evaluator does not set yet).
        try:
            cedarpy.format_policies(self._policies)
        except ValueError as exc:
            raise ValueError(f"invalid Cedar policy: {exc}") from exc

    @property
    def policy_version(self) -> str:
        """The policy version stamped onto every decision."""
        return self._policy_version

    def authorize(
        self, call: NormalizedCall, *, extra_context: dict[str, Any] | None = None
    ) -> bool:
        """Return whether Cedar permits *call* (deterministic)."""
        request = policy_mod.to_request(call, extra_context=extra_context)
        entities = policy_mod.build_entities(call)
        result = cedarpy.is_authorized(request, self._policies, entities)
        return bool(result.decision == cedarpy.Decision.Allow)

    def evaluate(
        self,
        call: NormalizedCall,
        *,
        budget_exhausted: bool = False,
        retry_after: int = 60,
        extra_context: dict[str, Any] | None = None,
    ) -> Decision:
        """Evaluate *call* end to end → a five-outcome :class:`Decision`."""
        request = policy_mod.to_request(call, extra_context=extra_context)
        entities = policy_mod.build_entities(call)
        result = cedarpy.is_authorized(request, self._policies, entities)
        allowed = result.decision == cedarpy.Decision.Allow
        return shape(
            cedar_allowed=allowed,
            call=call,
            matched_rule=_matched_rule(result),
            ctx=ShaperContext(
                policy_version=self._policy_version,
                budget_exhausted=budget_exhausted,
                retry_after=retry_after,
            ),
        )
