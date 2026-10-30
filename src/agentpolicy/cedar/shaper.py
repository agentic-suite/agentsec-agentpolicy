"""The five-outcome decision shaper (M2 ``2.2``).

Maps the Cedar authorization result **plus decision metadata** (the human-gate
class, session budget state, and the redaction class) to exactly one of the
five outcomes: ``allow`` / ``deny`` / ``ask`` / ``rate-limit`` / ``redact``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from agentpolicy.cedar import gates
from agentpolicy.cedar.models import Decision, Factor

if TYPE_CHECKING:
    from agentpolicy.types import NormalizedCall

#: Verbs whose output may carry sensitive content (→ ``redact`` when allowed).
SENSITIVE_VERBS: frozenset[str] = frozenset({"read", "list", "query", "search"})

#: Data classes that make an allowed read redactable.
SENSITIVE_DATA_CLASSES: frozenset[str] = frozenset({"restricted", "customer_pii"})

#: Destructive verbs (hard-deny reason code).
DESTRUCTIVE_VERBS: frozenset[str] = frozenset({"delete", "drop", "destroy", "force_push", "revoke"})


@dataclass(frozen=True)
class ShaperContext:
    """Non-Cedar inputs the shaper needs to pick the final outcome."""

    policy_version: str = "0.1.0"
    budget_exhausted: bool = False
    retry_after: int = 60


def _factors(call: NormalizedCall) -> tuple[Factor, ...]:
    return (
        Factor("action_class", call.action_class, 1.0 if call.action_class == "delete" else 0.3),
        Factor("environment", call.environment, 0.8 if call.environment == "production" else 0.1),
        Factor(
            "data_class",
            call.data_class,
            1.0 if call.data_class == "customer_pii" else 0.5,
        ),
        Factor("tool_category", call.tool_category, 0.4),
    )


def shape(
    *,
    cedar_allowed: bool,
    call: NormalizedCall,
    matched_rule: str | None = None,
    ctx: ShaperContext | None = None,
) -> Decision:
    """Shape a Cedar result + metadata into one of the five outcomes.

    Precedence: a Cedar deny is final; otherwise
    ``rate-limit`` > ``ask`` (gate class) > ``redact`` > ``allow``.
    """
    context = ctx or ShaperContext()
    factors = _factors(call)
    where = f"{call.tool} ({call.action}) in {call.environment} on {call.data_class}"

    if not cedar_allowed:
        destructive = call.action in DESTRUCTIVE_VERBS
        return Decision(
            decision="deny",
            reason_code="irreversible_action" if destructive else "no_matching_permit",
            criticality="critical" if call.environment == "production" else "high",
            explanation=(
                f"{where} is blocked: "
                f"{'destructive operation' if destructive else 'no permit matches'}."
            ),
            factors=factors,
            policy_version=context.policy_version,
            matched_rule=matched_rule,
        )

    if context.budget_exhausted:
        return Decision(
            decision="rate-limit",
            reason_code="budget_exhausted",
            criticality="med",
            explanation=f"{where} is throttled: the session budget is exhausted.",
            factors=factors,
            policy_version=context.policy_version,
            matched_rule=matched_rule,
            retry_after=context.retry_after,
        )

    if gates.is_human_gate(call):
        return Decision(
            decision="ask",
            reason_code="human_gate_required",
            criticality="high",
            explanation=f"{where} requires human approval (irreversible action in production).",
            factors=factors,
            policy_version=context.policy_version,
            matched_rule=matched_rule,
        )

    if call.action in SENSITIVE_VERBS and call.data_class in SENSITIVE_DATA_CLASSES:
        classes = ("pii",) if call.data_class == "customer_pii" else ("secret",)
        return Decision(
            decision="redact",
            reason_code="sensitive_output",
            criticality="med",
            explanation=(
                f"{where} is allowed, but {classes[0]} content is scrubbed from the result."
            ),
            factors=factors,
            policy_version=context.policy_version,
            matched_rule=matched_rule,
            redactions=classes,
        )

    return Decision(
        decision="allow",
        reason_code="allow_low_risk",
        criticality="low",
        explanation=f"{where} is within the allow band. Proceeding.",
        factors=factors,
        policy_version=context.policy_version,
        matched_rule=matched_rule,
    )
