"""ServerCore — shared state container for the MCP server.

Wraps the Engine, SessionStore, and AuditLogger so both the MCP tools and
the /audit HTTP endpoint share the same instances.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from typing import Any

from agentpolicy.agenthalt import HaltController
from agentpolicy.audit.logger import AuditLogger
from agentpolicy.audit.models import AuditEntry
from agentpolicy.engine.engine import Engine
from agentpolicy.engine.escalation import EscalationManager
from agentpolicy.engine.explain import session_risk_increment
from agentpolicy.server.session_store import SessionStore


class ServerCore:
    """Shared server state: Engine + SessionStore + AuditLogger.

    Args:
        engine: The AgentPolicy decision engine.
        session_store: In-memory session state tracker.
        audit_logger: Audit sink for persisting and querying decisions.
        halt_controller: Optional agenthalt controller (M12) fired on budget
            exhaustion.
    """

    def __init__(
        self,
        engine: Engine,
        session_store: SessionStore,
        audit_logger: AuditLogger,
        halt_controller: HaltController | None = None,
    ) -> None:
        self._engine = engine
        self._session_store = session_store
        self._audit_logger = audit_logger
        self._halt = halt_controller or HaltController()

    @property
    def engine(self) -> Engine:
        """The decision engine."""
        return self._engine

    @property
    def session_store(self) -> SessionStore:
        """The session state tracker."""
        return self._session_store

    @property
    def audit_logger(self) -> AuditLogger:
        """The audit sink."""
        return self._audit_logger

    @property
    def escalation_manager(self) -> EscalationManager:
        """The escalation registry for human approval (M3)."""
        return self._engine.escalation_manager

    def evaluate(
        self,
        tool_name: str,
        action: str,
        environment: str,
        data_class: str,
        agent_id: str,
        session_id: str | None = None,
        arguments: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        call_budget: int | None = None,
        token_budget: int | None = None,
        consent_scopes: list[dict[str, str]] | None = None,
        budgets: dict[str, float] | None = None,
        rate_limit: float | None = None,
        burst_limit: int | None = None,
        usage: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Evaluate a tool call through Engine, track session, audit.

        Args:
            tool_name: The tool being called.
            action: The action verb.
            environment: The deployment environment.
            data_class: The data classification.
            agent_id: The calling agent's identity.
            session_id: Optional session identifier for state tracking.
            arguments: Optional tool arguments.
            context: Optional additional context.
            call_budget: Per-session call budget ceiling (session creation only).
            token_budget: Per-session token budget ceiling (session creation only).
            consent_scopes: Per-session consent scopes (session creation only).

        Returns:
            A dict with decision fields plus ``session_risk_score`` and ``call_id``.
        """
        decision = self._engine.evaluate(
            tool_name=tool_name,
            action=action,
            environment=environment,
            data_class=data_class,
            agent_id=agent_id,
            arguments=arguments,
            context=context,
        )

        decision_dict = decision.to_dict()

        session_risk_score: float = 0.0
        budget_state: dict[str, Any] = {"budgets": {}, "usage": {}, "over": []}
        halt_event: Any = None
        if session_id is not None:
            merged_budgets = dict(budgets or {})
            if call_budget is not None:
                merged_budgets.setdefault("calls", float(call_budget))
            self._session_store.get_or_create(
                session_id,
                call_budget=call_budget,
                token_budget=token_budget,
                consent_scopes=consent_scopes,
                budgets=merged_budgets,
                rate_limit=rate_limit,
                burst_limit=burst_limit,
            )

            # M12: accumulate capability usage (implicit requests/calls + any
            # explicit usage counters the caller supplies).
            self._session_store.record_usage(
                session_id, {"requests": 1.0, "calls": 1.0, **(usage or {})}
            )
            if decision_dict["decision"] not in ("deny",):
                self._session_store.update(
                    session_id,
                    risk_increment=session_risk_increment(decision_dict["criticality"]),
                    call_id="pending",
                )

            # M12 12.3: rate/burst limit → rate-limit with retry_after.
            rate_ok, retry_after = self._session_store.rate_allow(session_id)
            # M12 12.2: capability-budget exhaustion → rate-limit with a reason.
            exceeded, reason = self._session_store.exceeds_budgets(session_id)
            budget_state = self._session_store.budget_state(session_id)

            decision_dict = dict(decision_dict)
            if not rate_ok:
                decision_dict["decision"] = "rate-limit"
                decision_dict["reason_code"] = "rate_limited"
                decision_dict["explanation"] = (
                    f"Rate/burst limit reached; retry in {retry_after}s."
                )
                decision_dict["retry_after"] = retry_after
            if exceeded:
                decision_dict["decision"] = "rate-limit"
                decision_dict["reason_code"] = "budget_exhausted"
                decision_dict["explanation"] = f"Session budget exceeded: {reason}"
                decision_dict["retry_after"] = 60
                # M12 12.4: hard exhaustion raises a halt event (with evidence).
                halt_event = self._halt.maybe_halt(session_id, budget_state)
            if not exceeded and rate_ok and not self._session_store.within_consent(
                session_id, tool_name, environment, data_class
            ):
                decision_dict["decision"] = "escalate"
                decision_dict["reason_code"] = "scope_boundary"
                decision_dict["explanation"] = (
                    "Tool call outside session consent scopes. Escalation required."
                )

            state = self._session_store.get(session_id)
            session_risk_score = state.risk_score if state else 0.0

        entry = AuditEntry(
            session_id=session_id,
            timestamp=datetime.now(UTC).isoformat(),
            tool=tool_name,
            tool_category=None,
            action=action,
            action_class=None,
            environment=environment,
            data_class=data_class,
            agent_id=agent_id,
            agent_class=None,
            decision=decision_dict["decision"],
            criticality=decision_dict["criticality"],
            reason_code=decision_dict["reason_code"],
            explanation=decision_dict["explanation"],
            factors=list(decision.factors),
            policy_version=decision_dict.get("policy_version", "0.0.0"),
            dry_run=decision_dict.get("dry_run", False),
            escalation_id=decision_dict.get("escalation_id"),
        )
        try:
            self._audit_logger.sink.write(entry)
        except Exception as exc:
            print(f"agentpolicy audit: log failed: {exc}", file=sys.stderr)

        if session_id is not None and decision_dict["decision"] not in ("deny",):
            self._session_store.patch_last_call_id(session_id, entry.call_id)

        result = dict(decision_dict)
        result["session_risk_score"] = session_risk_score
        result["call_id"] = entry.call_id
        # M12: every decision carries the session's budget state.
        result["budget_state"] = budget_state
        if halt_event is not None:
            result["halt"] = halt_event.to_dict()
        return result

    def explain_from_audit(self, call_id: str) -> dict[str, Any] | None:
        """Look up an explanation from the audit trail by call_id.

        Args:
            call_id: The call_id from a previous evaluate response.

        Returns:
            A dict with explanation, factors, reason_code, and criticality,
            or None if no matching entry is found.
        """
        entries = self._audit_logger.query()
        for entry in entries:
            if entry.call_id == call_id:
                return {
                    "explanation": entry.explanation,
                    "factors": [f.to_dict() for f in entry.factors],
                    "reason_code": entry.reason_code,
                    "criticality": entry.criticality,
                }
        return None
