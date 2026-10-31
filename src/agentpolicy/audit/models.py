"""The ``AuditEntry`` — one immutable record of one evaluated tool call.

Matches the architecture §2.5 audit-entry structure and the ``audit_entries``
table in ``docs/architecture/db-schema-sketch.md``. Every field beyond the
decision itself is copied from the decision pipeline so the audit trail is
self-contained and replayable without reprocessing.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from agentpolicy.types import Decision, Factor, NormalizedCall


def _utc_now() -> str:
    """ISO-8601 UTC timestamp string for audit entries and their sorts."""
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class AuditEntry:
    """An immutable, self-contained record of one decision.

    All fields are copied flat from the pipeline (tool, action, environment,
    data class, agent) so a downstream compliance query never needs to re-run
    the engine. ``factors`` holds the per-dimension risk breakdown; JSON sinks
    serialize it as a JSON array.
    """

    session_id: str | None
    timestamp: str
    tool: str
    tool_category: str | None
    action: str
    action_class: str | None
    environment: str
    data_class: str
    agent_id: str
    agent_class: str | None
    decision: str
    criticality: str
    reason_code: str
    explanation: str
    call_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    factors: list[Factor] = field(default_factory=list)
    policy_version: str = "0.0.0"
    dry_run: bool = False
    escalation_id: str | None = None
    approver: str | None = None
    chain_hash: str | None = None
    prev_hash: str | None = None
    arguments: dict[str, Any] | None = None
    redacted: bool = False
    credential_status: str | None = None
    counterfactual: float | None = None
    # --- M6 provenance / chain (additive) ---------------------------------
    seq: int | None = None
    policy_hash: str = ""
    matched_rule: str | None = None
    decision_id: str | None = None
    policy_reviewed: bool | None = None

    @property
    def entry_hash(self) -> str | None:
        """PRD 15's name for the entry's chain link (alias of ``chain_hash``)."""
        return self.chain_hash

    @classmethod
    def from_decision(
        cls,
        decision: Decision,
        call: NormalizedCall,
        *,
        session_id: str | None = None,
        timestamp: str | None = None,
        approver: str | None = None,
        dry_run: bool | None = None,
        arguments: dict[str, Any] | None = None,
        redacted: bool = False,
        credential_status: str | None = None,
        policy_hash: str | None = None,
        matched_rule: str | None = None,
        decision_id: str | None = None,
        reviewed: bool | None = None,
    ) -> AuditEntry:
        """Build an audit entry from a finished decision and its call.

        Tolerant of both decision paths: the ported ``types.Decision`` and the
        Cedar ``cedar.models.Decision``. Fields unique to one path
        (``dry_run``/``escalation_id``/``counterfactual``) are read with
        ``getattr``; the M5 provenance fields (``policy_hash``/``matched_rule``)
        are read from the decision unless passed explicitly.

        Args:
            decision: The Decision returned by the evaluator (Cedar or ported).
            call: The NormalizedCall that produced the decision.
            session_id: Session id to record (defaults to the call's).
            timestamp: ISO-8601 timestamp (defaults to now, UTC).
            approver: Human approver identity for escalation entries.
            dry_run: Recorded dry_run flag. Defaults to the decision's; pass
                explicitly so the engine can mark shadowed decisions that were
                logged before the allowance was applied.
            arguments: The tool-call arguments (pre-redaction). Defaults to
                ``call.arguments``.
            redacted: Whether arguments were redacted.
            credential_status: Post-decision credential status (e.g. ``"stale"``)
                when the engine allowed the call but the underlying API rejected it.
            policy_hash: The governing policy's content hash (M6 provenance).
            matched_rule: The deciding clause (M5 ``clause``).
            decision_id: The M5 join key shared with the emitted event.
            reviewed: Whether the governing policy was reviewed (M6 review flag).
        """
        resolved_hash = policy_hash if policy_hash is not None else getattr(
            decision, "policy_hash", ""
        )
        resolved_rule = matched_rule if matched_rule is not None else getattr(
            decision, "matched_rule", None
        )
        return cls(
            session_id=session_id if session_id is not None else call.session_id,
            timestamp=timestamp if timestamp is not None else _utc_now(),
            tool=call.tool,
            tool_category=call.tool_category,
            action=call.action,
            action_class=call.action_class,
            environment=call.environment,
            data_class=call.data_class,
            agent_id=call.agent_id,
            agent_class=call.agent_class,
            decision=decision.decision,
            criticality=decision.criticality,
            reason_code=decision.reason_code,
            explanation=decision.explanation,
            factors=[
                Factor(dimension=f.dimension, value=f.value, contribution=f.contribution)
                for f in decision.factors
            ],
            policy_version=decision.policy_version,
            dry_run=bool(getattr(decision, "dry_run", False)) if dry_run is None else dry_run,
            escalation_id=getattr(decision, "escalation_id", None),
            approver=approver,
            arguments=arguments if arguments is not None else call.arguments,
            redacted=redacted,
            credential_status=credential_status,
            counterfactual=getattr(decision, "counterfactual", None),
            policy_hash=resolved_hash,
            matched_rule=resolved_rule,
            decision_id=decision_id,
            policy_reviewed=reviewed,
        )

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly dict: factors serialized to plain dicts."""
        data = asdict(self)
        data["factors"] = [f.to_dict() for f in self.factors]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditEntry:
        """Rebuild an entry from a ``to_dict()`` payload (JSONL/CSV import)."""
        factors = [Factor(**f) for f in data.get("factors") or []]
        kwargs: dict[str, Any] = dict(
            session_id=data.get("session_id"),
            timestamp=data["timestamp"],
            tool=data["tool"],
            tool_category=data.get("tool_category"),
            action=data["action"],
            action_class=data.get("action_class"),
            environment=data["environment"],
            data_class=data["data_class"],
            agent_id=data["agent_id"],
            agent_class=data.get("agent_class"),
            decision=data["decision"],
            criticality=data["criticality"],
            reason_code=data["reason_code"],
            explanation=data["explanation"],
            factors=factors,
            policy_version=data.get("policy_version", "0.0.0"),
            dry_run=bool(data.get("dry_run", False)),
            escalation_id=data.get("escalation_id"),
            approver=data.get("approver"),
            chain_hash=data.get("chain_hash"),
            prev_hash=data.get("prev_hash"),
            arguments=data.get("arguments"),
            redacted=bool(data.get("redacted", False)),
            credential_status=data.get("credential_status"),
            counterfactual=data.get("counterfactual"),
            seq=int(data["seq"]) if data.get("seq") is not None else None,
            policy_hash=data.get("policy_hash", ""),
            matched_rule=data.get("matched_rule"),
            decision_id=data.get("decision_id"),
            policy_reviewed=data.get("policy_reviewed"),
        )
        if "call_id" in data:
            kwargs["call_id"] = data["call_id"]
        return cls(**kwargs)
