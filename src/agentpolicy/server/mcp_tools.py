"""MCP tool registrations for the AgentPolicy server.

Provides :func:`register_tools` which decorates and registers the three MCP
tools (``agentpolicy.evaluate``, ``agentpolicy.explain``,
``agentpolicy.session_status``) on a FastMCP server instance. Returns the
tool functions for test access.
"""

from __future__ import annotations

from typing import Any


def register_tools(
    mcp: Any,
    core: Any,
) -> dict[str, Any]:
    """Register AgentPolicy MCP tools on a FastMCP server.

    Args:
        mcp: A FastMCP server instance.
        core: A :class:`ServerCore` instance wrapping Engine + SessionStore + AuditLogger.

    Returns:
        A dict mapping tool names (``agentpolicy.evaluate``, etc.) to the
        registered tool function objects for test access.
    """

    @mcp.tool(  # type: ignore[untyped-decorator]
        name="agentpolicy.evaluate",
        description=(
            "Evaluate whether a proposed tool call should be allowed, audited, "
            "escalated for human approval, or denied. Returns a Decision with "
            "risk factors, criticality, reason code, and explanation."
        ),
    )
    def evaluate(
        tool_name: str,
        action: str,
        environment: str,
        data_class: str,
        agent_id: str,
        session_id: str | None = None,
        arguments: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return core.evaluate(  # type: ignore[no-any-return]
            tool_name=tool_name,
            action=action,
            environment=environment,
            data_class=data_class,
            agent_id=agent_id,
            session_id=session_id,
            arguments=arguments,
            context=context,
        )

    @mcp.tool(  # type: ignore[untyped-decorator]
        name="agentpolicy.explain",
        description=(
            "Explain why a tool call received a particular decision. "
            "Accepts either the same input as evaluate (runs the engine) "
            "or a call_id to look up a prior decision from the audit trail."
        ),
    )
    def explain(
        call_id: str | None = None,
        tool_name: str | None = None,
        action: str | None = None,
        environment: str | None = None,
        data_class: str | None = None,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        if call_id is not None:
            result = core.explain_from_audit(call_id)
            if result is None:
                return {"error": f"No audit entry found for call_id: {call_id}"}
            return result  # type: ignore[no-any-return]

        if not all([tool_name, action, environment, data_class, agent_id]):
            return {
                "error": (
                    "Provide either call_id or all of: "
                    "tool_name, action, environment, data_class, agent_id"
                )
            }

        decision = core.evaluate(
            tool_name=str(tool_name),
            action=str(action),
            environment=str(environment),
            data_class=str(data_class),
            agent_id=str(agent_id),
        )
        return {
            "explanation": decision["explanation"],
            "factors": decision.get("factors", []),
            "reason_code": decision["reason_code"],
            "criticality": decision["criticality"],
        }

    @mcp.tool(  # type: ignore[untyped-decorator]
        name="agentpolicy.session_status",
        description=(
            "Query the status of an active session: cumulative risk score, "
            "tool call count, budget state, consent scopes, and recent "
            "decision history."
        ),
    )
    def session_status(session_id: str) -> dict[str, Any]:
        state = core.session_store.get(session_id)
        if state is None:
            return {"session_id": session_id, "error": "Session not found"}
        return {
            "session_id": state.session_id,
            "risk_score": state.risk_score,
            "tool_call_count": state.tool_call_count,
            "token_budget": state.token_budget,
            "call_budget": state.call_budget,
            "consent_scopes": state.consent_scopes,
            "decision_history": state.decision_history[-10:],
            "created_at": state.created_at,
            "last_updated": state.last_updated,
        }

    @mcp.tool(  # type: ignore[untyped-decorator]
        name="agentpolicy.authorize_data_source",
        description=(
            "Authorize access to a named data source (read/write/delete) for a "
            "given agent and environment. Returns the AgentPolicy Decision with "
            "risk factors and reason code. Unregistered sources are denied."
        ),
    )
    def authorize_data_source(
        data_source_id: str,
        operation: str,
        agent_id: str,
        environment: str,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        from agentpolicy.mcp_data import DataAccessRequest
        from agentpolicy.mcp_data import authorize_data_source as _authorize

        return _authorize(
            DataAccessRequest(
                data_source_id=data_source_id,
                operation=operation,  # type: ignore[arg-type]
                agent_id=agent_id,
                environment=environment,
                session_id=session_id,
            ),
            core,
        )

    @mcp.tool(  # type: ignore[untyped-decorator]
        name="agentpolicy.ask_create",
        description=(
            "Create a pending human ask for a tool call (the M14 ask path). "
            "Returns the ask record with its ask_id; resolve it with "
            "agentpolicy.approve / agentpolicy.deny."
        ),
    )
    def ask_create(
        tool_name: str,
        action: str,
        environment: str,
        data_class: str,
        agent_id: str,
        arguments: dict[str, Any] | None = None,
        reason: str = "",
    ) -> dict[str, Any]:
        from agentpolicy.canonical import canonicalize

        try:
            call = canonicalize(
                tool=tool_name, action=action, environment=environment,
                data_class=data_class, agent_id=agent_id, arguments=arguments,
            )
        except Exception as exc:
            return {"error": str(exc)}
        return core.ask_broker.create(call, reason=reason).to_dict()  # type: ignore[no-any-return]

    @mcp.tool(name="agentpolicy.approve")  # type: ignore[untyped-decorator]
    def approve(ask_id: str, approver: str) -> dict[str, Any]:
        try:
            return core.ask_broker.approve(ask_id, approver=approver).to_dict()  # type: ignore[no-any-return]
        except ValueError as exc:
            return {"error": str(exc)}

    @mcp.tool(name="agentpolicy.deny")  # type: ignore[untyped-decorator]
    def deny(ask_id: str, approver: str, reason: str = "") -> dict[str, Any]:
        try:
            return core.ask_broker.deny(  # type: ignore[no-any-return]
                ask_id, approver=approver, reason=reason
            ).to_dict()
        except ValueError as exc:
            return {"error": str(exc)}

    @mcp.tool(name="agentpolicy.ask_resolve")  # type: ignore[untyped-decorator]
    def ask_resolve(
        ask_id: str,
        tool_name: str,
        action: str,
        environment: str,
        data_class: str,
        agent_id: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from agentpolicy.canonical import canonicalize

        try:
            call = canonicalize(
                tool=tool_name, action=action, environment=environment,
                data_class=data_class, agent_id=agent_id, arguments=arguments,
            )
        except Exception as exc:
            return {"error": str(exc)}
        return core.ask_broker.resolve(ask_id, call=call)  # type: ignore[no-any-return]

    return {
        "agentpolicy.evaluate": evaluate,
        "agentpolicy.explain": explain,
        "agentpolicy.session_status": session_status,
        "agentpolicy.authorize_data_source": authorize_data_source,
        "agentpolicy.ask_create": ask_create,
        "agentpolicy.approve": approve,
        "agentpolicy.deny": deny,
        "agentpolicy.ask_resolve": ask_resolve,
    }
