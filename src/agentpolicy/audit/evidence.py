"""The offline EvidenceArtifact (WBS M6 ``6.5``, CUJ-20).

A self-contained record — ``action`` + ``matched_rule`` + ``policy_version`` +
``policy_hash`` + ``event_ref`` (+ the outcome and a content ``hash``) — that a
third party can **re-derive offline, on another machine, without installing
agentpolicy**: re-evaluate the canonical action against the pinned policy and
confirm the same outcome and matched rule, and re-check the artifact's own hash
(PRD 17 §Evidence, PRD 15 ``EvidenceArtifact``).

The ``event_ref`` is the M5 join key (``event_id``), so an evidence artifact, the
emitted agentwatch event, and the hash-chained audit entry all reference one
decision.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from agentpolicy.types import NormalizedCall

if TYPE_CHECKING:
    from agentpolicy.explain import ExplainArtifact

#: The canonical-call fields an evidence artifact carries (arguments/context are
#: deliberately excluded — they may hold secrets and are not needed to re-derive).
_ACTION_FIELDS = (
    "tool",
    "tool_category",
    "action",
    "action_class",
    "environment",
    "data_class",
    "agent_id",
    "agent_class",
)


@dataclass(frozen=True)
class EvidenceArtifact:
    """A self-contained, offline-verifiable decision record.

    Attributes:
        action: The canonical action fields (no arguments/context).
        matched_rule: The deciding clause, or ``None``.
        decision: The recorded outcome.
        reason_code: The recorded reason code.
        policy_version: The governing policy version.
        policy_hash: The governing policy content hash (``sha256:<hex>``).
        event_ref: The M5 ``event_id`` join key.
        hash: The artifact's content hash (filled on construction when blank).
    """

    action: dict[str, Any]
    matched_rule: str | None
    decision: str
    reason_code: str
    policy_version: str
    policy_hash: str
    event_ref: str
    hash: str = ""

    def __post_init__(self) -> None:
        if not self.event_ref or not self.event_ref.strip():
            raise ValueError("event_ref must be a non-blank string")
        if not self.hash:
            object.__setattr__(self, "hash", self.content_hash())

    def content_hash(self) -> str:
        """``sha256:<hex>`` over the artifact's canonical fields (excludes ``hash``)."""
        payload = {
            "action": self.action,
            "matched_rule": self.matched_rule,
            "decision": self.decision,
            "reason_code": self.reason_code,
            "policy_version": self.policy_version,
            "policy_hash": self.policy_hash,
            "event_ref": self.event_ref,
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        return f"sha256:{digest}"

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly representation."""
        return {
            "action": dict(self.action),
            "matched_rule": self.matched_rule,
            "decision": self.decision,
            "reason_code": self.reason_code,
            "policy_version": self.policy_version,
            "policy_hash": self.policy_hash,
            "event_ref": self.event_ref,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceArtifact:
        """Rebuild an artifact from a ``to_dict()`` payload."""
        return cls(
            action=dict(data["action"]),
            matched_rule=data.get("matched_rule"),
            decision=data["decision"],
            reason_code=data["reason_code"],
            policy_version=data["policy_version"],
            policy_hash=data["policy_hash"],
            event_ref=data["event_ref"],
            hash=data.get("hash", ""),
        )

    def verify(self, evaluator: Any) -> dict[str, Any]:
        """Re-derive the decision offline against the pinned policy.

        Args:
            evaluator: A Cedar evaluator exposing ``evaluate`` and
                ``policy_hash``.

        Returns:
            A dict ``{valid, reason, rederived_decision, expected_decision,
            artifact_hash}``. ``valid`` is True only when the artifact's own
            hash is intact, the evaluator's policy matches the pin, and the
            re-derived outcome (and matched rule) match the record.
        """
        result: dict[str, Any] = {
            "valid": False,
            "reason": None,
            "rederived_decision": None,
            "expected_decision": self.decision,
            "artifact_hash": self.hash,
        }
        if self.content_hash() != self.hash:
            result["reason"] = "artifact_hash_mismatch"
            return result
        pinned = getattr(evaluator, "policy_hash", None)
        if pinned is not None and self.policy_hash and pinned != self.policy_hash:
            result["reason"] = "policy_hash_mismatch"
            return result
        call = NormalizedCall(**{k: self.action[k] for k in _ACTION_FIELDS})
        decision = evaluator.evaluate(call)
        result["rederived_decision"] = decision.decision
        outcome_ok = decision.decision == self.decision
        rule_ok = self.matched_rule is None or decision.matched_rule == self.matched_rule
        result["valid"] = bool(outcome_ok and rule_ok)
        if not result["valid"]:
            result["reason"] = "decision_mismatch"
        return result


def evidence_for(artifact: ExplainArtifact, call: NormalizedCall) -> EvidenceArtifact:
    """Build the offline evidence artifact for an explain artifact + its call.

    The ``event_ref`` is the explain artifact's ``event_id`` (the M5 join key),
    and the M5 ``policy_hash`` pins the governing policy for re-derivation.
    """
    action = {field: getattr(call, field) for field in _ACTION_FIELDS}
    return EvidenceArtifact(
        action=action,
        matched_rule=artifact.matched_rule,
        decision=artifact.decision,
        reason_code=artifact.reason_code,
        policy_version=artifact.policy_version,
        policy_hash=artifact.policy_hash,
        event_ref=artifact.event_id,
    )


__all__ = ["EvidenceArtifact", "evidence_for"]
