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
    """Extract the deciding rule id (the Cedar ``@id`` annotation) from diagnostics.

    ``cedarpy`` reports the satisfied policies as ``reasons`` (``policy0`` …) and
    maps each to its ``@id`` annotation in ``id_annotations_by_reason``. We
    return the lexicographically smallest decisive annotation — stable across
    runs (``cedarpy`` orders ``reasons`` by hash) — which names the clause that
    decided the outcome: ``forbid-*`` for a deny, ``permit-*`` for the allowed
    outcomes.
    """
    diagnostics = getattr(result, "diagnostics", None)
    annotations = getattr(diagnostics, "id_annotations_by_reason", None)
    reasons = getattr(diagnostics, "reasons", None)
    ids: list[str] = []
    if isinstance(annotations, dict):
        for reason in reasons if isinstance(reasons, (list, tuple)) else ():
            rule_id = annotations.get(reason)
            if isinstance(rule_id, str) and rule_id and rule_id not in ids:
                ids.append(rule_id)
        if not ids:
            ids = sorted(
                v for v in annotations.values() if isinstance(v, str) and v
            )
    if ids:
        # ``cedarpy`` reports satisfied policies in an unstable (hash) order, so
        # pick the lexicographically smallest id: deterministic across runs.
        return sorted(ids)[0]
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

    @property
    def policy_hash(self) -> str:
        """The stable content hash of the policy set (``sha256:<hex>``)."""
        return policy_mod.policy_hash(self._policies)

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
                policy_hash=self.policy_hash,
                budget_exhausted=budget_exhausted,
                retry_after=retry_after,
            ),
        )
