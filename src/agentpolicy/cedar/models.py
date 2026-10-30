"""Cedar decision-core models (PRD 15 / PRD 17).

The five-outcome decision model for the Cedar PDP: :data:`Outcome`
(``allow`` / ``deny`` / ``ask`` / ``rate-limit`` / ``redact``), a :class:`Factor`
contribution, the :class:`Explanation` artifact, and the :class:`Decision`
itself (with its JSON shape per PRD 15).

These are separate from the legacy ported engine's ``agentpolicy.types`` model
on purpose: the Cedar core is the v0.1.0 decision path; the legacy model remains
for the ported compatibility surface until it is retired.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Outcome = Literal["allow", "deny", "ask", "rate-limit", "redact"]
Criticality = Literal["none", "low", "med", "high", "critical"]

OUTCOMES: frozenset[str] = frozenset({"allow", "deny", "ask", "rate-limit", "redact"})
_CRITICALITIES = frozenset({"none", "low", "med", "high", "critical"})


@dataclass(frozen=True)
class Factor:
    """A single contributing dimension of a decision (PRD 15)."""

    dimension: str
    value: str
    contribution: float

    def __post_init__(self) -> None:
        if not self.dimension or not self.dimension.strip():
            raise ValueError("dimension must be a non-blank string")
        if not 0.0 <= self.contribution <= 1.0:
            raise ValueError(f"contribution must be in [0, 1], got {self.contribution}")

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {"dimension": self.dimension, "value": self.value, "contribution": self.contribution}


@dataclass(frozen=True)
class Explanation:
    """The ``explain-decision`` artifact (PRD 17)."""

    matched_rule: str | None
    context: dict[str, Any] = field(default_factory=dict)
    suggested_change: str | None = None
    factors: tuple[Factor, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "matched_rule": self.matched_rule,
            "context": dict(self.context),
            "suggested_change": self.suggested_change,
            "factors": [f.to_dict() for f in self.factors],
        }


@dataclass(frozen=True)
class Decision:
    """A five-outcome decision (PRD 15 ``Decision``)."""

    decision: Outcome
    reason_code: str
    criticality: Criticality
    explanation: str
    factors: tuple[Factor, ...] = ()
    policy_version: str = "0.1.0"
    matched_rule: str | None = None
    retry_after: int | None = None
    redactions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.decision not in OUTCOMES:
            raise ValueError(f"unknown outcome {self.decision!r}; use one of {sorted(OUTCOMES)}")
        if self.criticality not in _CRITICALITIES:
            raise ValueError(f"unknown criticality {self.criticality!r}")
        if not self.reason_code or not self.reason_code.strip():
            raise ValueError("reason_code must be a non-blank string")

    @property
    def allowed(self) -> bool:
        """Whether the action may proceed (in any form)."""
        return self.decision in ("allow", "redact")

    def explanation_artifact(self) -> Explanation:
        """Build the ``explain-decision`` artifact for this decision."""
        return Explanation(
            matched_rule=self.matched_rule,
            context={"decision": self.decision, "reason_code": self.reason_code},
            suggested_change=(
                None
                if self.allowed
                else "move to a lower-risk environment or use a read-only alternative"
            ),
            factors=self.factors,
        )

    def to_dict(self) -> dict[str, Any]:
        """JSON shape per PRD 15 (``decision`` / ``reason_code`` / …)."""
        out: dict[str, Any] = {
            "decision": self.decision,
            "reason_code": self.reason_code,
            "criticality": self.criticality,
            "explanation": self.explanation,
            "factors": [f.to_dict() for f in self.factors],
            "policy_version": self.policy_version,
            "matched_rule": self.matched_rule,
        }
        if self.decision == "rate-limit":
            out["retry_after"] = self.retry_after if self.retry_after is not None else 60
        if self.decision == "redact":
            out["redactions"] = list(self.redactions)
        return out
