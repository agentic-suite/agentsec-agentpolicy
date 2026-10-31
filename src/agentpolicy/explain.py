"""The explain-decision facade (WBS M5 ``5.1``/``5.3``).

Turns a finished Cedar :class:`~agentpolicy.cedar.models.Decision` plus its
canonical call into the machine-readable **explain artifact** (PRD 17): the
``reason_code``, ``criticality``, ``explanation``, ``factors[]``, the
``matched_rule`` and its ``clause``, the ``suggested_change``, and the policy
provenance (``policy_version``/``policy_hash``). It also computes the
**actionability** answer — the one change that flips the outcome — by trying a
fixed, ordered set of candidate modifications against the evaluator, so the
suggestion is deterministic and *verified* (the PDP never suggests a variant it
would itself deny).
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, replace
from typing import Any, Protocol

from agentpolicy import reason_codes
from agentpolicy.cedar.models import Decision, Factor
from agentpolicy.types import NormalizedCall


class _Evaluator(Protocol):
    """The slice of the Cedar evaluator the actionability search needs."""

    def evaluate(
        self,
        call: NormalizedCall,
        *,
        budget_exhausted: bool = ...,
        retry_after: int = ...,
        extra_context: dict[str, Any] | None = ...,
    ) -> Decision: ...


#: The closed vocabulary of levers a suggested change may name. A human reading
#: only the explanation text must be able to name one of these (PRD 17).
LEVERS: frozenset[str] = frozenset(
    {"read-only", "non-production", "staging", "data class", "approval", "retry"}
)

#: Outcomes that count as "the action may proceed" (mirrors ``Decision.allowed``
#: plus ``ask``: a gated action can proceed once approved).
_PERMITTED: frozenset[str] = frozenset({"allow", "redact", "ask"})

#: The one-change lever for the mandatory human gate.
_APPROVAL_LEVER = (
    "Request human approval for this action (approve the pending ask); "
    "no policy change is required."
)

_DESTRUCTIVE = frozenset({"delete", "drop", "destroy", "force_push", "revoke", "purge", "truncate"})


def new_event_id() -> str:
    """A fresh decision event id (``evt_<hex>``)."""
    return "evt_" + secrets.token_hex(8)


def new_decision_id() -> str:
    """A fresh decision id (``dec_<hex>``); the audit/event join key."""
    return "dec_" + secrets.token_hex(8)


@dataclass(frozen=True)
class ExplainArtifact:
    """The ``explain-decision`` artifact (PRD 17).

    Attributes:
        decision: The five-outcome decision literal.
        reason_code: A registered, stable reason code.
        criticality: The severity literal.
        explanation: The one human sentence.
        factors: The per-dimension contribution breakdown.
        matched_rule: The deciding Cedar rule id, or ``None``.
        clause: ``matched_rule`` or, when there is no rule, the reason-code
            class — always non-empty for a deny/ask/rate-limit.
        suggested_change: The one change that flips the outcome, or ``None``
            for an allow.
        policy_version: The policy version that governed the decision.
        policy_hash: The stable content hash of the policy (``sha256:<hex>``).
        event_id: The emitted event id (the telemetry join key).
        decision_id: The decision id (matches the audit entry's join key).
    """

    decision: str
    reason_code: str
    criticality: str
    explanation: str
    factors: tuple[Factor, ...]
    matched_rule: str | None
    clause: str
    suggested_change: str | None
    policy_version: str
    policy_hash: str
    event_id: str
    decision_id: str

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation (the explain contract, PRD 17)."""
        return {
            "decision": self.decision,
            "reason_code": self.reason_code,
            "reason": reason_codes.meaning(self.reason_code),
            "criticality": self.criticality,
            "explanation": self.explanation,
            "factors": [f.to_dict() for f in self.factors],
            "matched_rule": self.matched_rule,
            "clause": self.clause,
            "suggested_change": self.suggested_change,
            "policy_version": self.policy_version,
            "policy_hash": self.policy_hash,
            "event_id": self.event_id,
            "decision_id": self.decision_id,
        }


def _candidates(call: NormalizedCall) -> list[tuple[str, NormalizedCall]]:
    """Ordered candidate modifications of *call* (text, variant).

    The order is frozen so the suggestion is stable across installs.
    """
    candidates: list[tuple[str, NormalizedCall]] = []
    if call.environment == "production":
        candidates.append(
            (
                "Move the action to a non-production environment (staging).",
                replace(call, environment="staging"),
            )
        )
    if call.action in _DESTRUCTIVE:
        candidates.append(
            (
                "Use a read-only alternative instead of the destructive action.",
                replace(call, action="read", action_class="read"),
            )
        )
    if call.data_class in ("customer_pii", "restricted"):
        candidates.append(
            (
                "Lower the data class (reduce the scope of data the action touches).",
                replace(call, data_class="internal"),
            )
        )
    return candidates


def _safe_outcome(evaluator: _Evaluator | None, variant: NormalizedCall) -> str | None:
    """Evaluate *variant*, returning its outcome or ``None`` on any failure.

    The actionability search must never break an explanation: a candidate the
    evaluator rejects simply does not count as a flip.
    """
    if evaluator is None:
        return None
    try:
        return evaluator.evaluate(variant).decision
    except Exception:
        return None


def flip_variant(
    decision: Decision, call: NormalizedCall, evaluator: _Evaluator | None
) -> NormalizedCall | None:
    """The first candidate variant whose outcome differs from *decision*.

    Returns ``None`` when this decision has no action-level flip (an ``allow``
    is already permitted; an ``ask``/``rate-limit`` flips by approval/waiting,
    not by changing the call), or when no candidate changes the outcome.
    """
    if decision.decision == "allow" or evaluator is None:
        return None
    if decision.decision in ("ask", "rate-limit"):
        return None
    for _text, variant in _candidates(call):
        new = _safe_outcome(evaluator, variant)
        if new in _PERMITTED and new != decision.decision:
            return variant
    return None


def suggested_change(
    decision: Decision, call: NormalizedCall, evaluator: _Evaluator | None = None
) -> str | None:
    """The one change that flips the outcome (PRD 17 actionability).

    ``None`` for an ``allow`` (nothing needs to change). An ``ask`` names the
    approval lever; a ``rate-limit`` names the retry lever; a ``deny``/``redact``
    names a verified call modification when one exists, else a safe generic
    alternative.
    """
    if decision.decision == "allow":
        return None
    if decision.decision == "ask":
        return _APPROVAL_LEVER
    if decision.decision == "rate-limit":
        after = decision.retry_after if decision.retry_after is not None else 60
        return f"Wait {after}s (the session budget resets) and retry the action."
    if decision.decision == "redact":
        for text, variant in _candidates(call):
            if _safe_outcome(evaluator, variant) == "allow":
                return text
        return "No change is needed — sensitive content is scrubbed from the result."
    # deny
    for text, variant in _candidates(call):
        new = _safe_outcome(evaluator, variant)
        if new in _PERMITTED and new != decision.decision:
            return text
    return "Use a read-only alternative, or move the action to a non-production environment."


def build_artifact(
    decision: Decision,
    call: NormalizedCall,
    *,
    evaluator: _Evaluator | None = None,
    event_id: str | None = None,
    decision_id: str | None = None,
) -> ExplainArtifact:
    """Build the explain artifact for *decision* over *call*.

    Args:
        decision: The finished Cedar decision.
        call: The canonical call that produced it.
        evaluator: The Cedar evaluator, used to compute a *verified*
            ``suggested_change``. When ``None``, the suggestion is the generic
            per-outcome text.
        event_id: The event join key; generated when omitted.
        decision_id: The decision join key; generated when omitted.

    Returns:
        A fully-populated :class:`ExplainArtifact`.
    """
    return ExplainArtifact(
        decision=decision.decision,
        reason_code=decision.reason_code,
        criticality=decision.criticality,
        explanation=decision.explanation,
        factors=tuple(decision.factors),
        matched_rule=decision.matched_rule,
        clause=decision.matched_rule or decision.reason_code,
        suggested_change=suggested_change(decision, call, evaluator),
        policy_version=decision.policy_version,
        policy_hash=decision.policy_hash,
        event_id=event_id or new_event_id(),
        decision_id=decision_id or new_decision_id(),
    )


__all__ = [
    "LEVERS",
    "ExplainArtifact",
    "build_artifact",
    "flip_variant",
    "new_decision_id",
    "new_event_id",
    "suggested_change",
]
