"""AuthZEN Authorization API 1.0 binding (WBS M14 ``14.2``, CUJ-14 / R27).

A conformant ``POST /access/v1/evaluation`` surface: an AuthZEN caller sends
``{subject, action, resource, context}`` and gets ``{decision, context}`` with
the machine reason code + policy version in the decision context. **Boxcarring**
(``evaluations[]`` + a semantic) evaluates many requests in one call. The
decision is the **same** as every other surface (it delegates to ``ServerCore``).
See [ADR-0006] / ``docs/reference/authzen.md``.
"""

from __future__ import annotations

from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

#: The AuthZEN-compatible schema id carried in the decision context.
SCHEMA = "authzen.evaluation.v1"

#: Outcomes that permit the action (AuthZEN ``decision: true``).
PERMITTED: frozenset[str] = frozenset({"allow", "audit", "redact"})

#: Boxcarring semantics.
SEMANTICS = ("execute_all", "deny_on_first_deny", "permit_on_first_permit")


def _field(container: Any, key: str, default: Any = None) -> Any:
    """Read *key* from an AuthZEN object (top-level or its ``properties``)."""
    if not isinstance(container, dict):
        return default
    if key in container and container[key] is not None:
        return container[key]
    props = container.get("properties")
    if isinstance(props, dict) and props.get(key) is not None:
        return props[key]
    return default


def _call_kwargs(body: dict[str, Any]) -> dict[str, Any]:
    """Map an AuthZEN evaluation request to ``ServerCore.evaluate`` kwargs."""
    subject = body.get("subject") or {}
    action = body.get("action") or {}
    resource = body.get("resource") or {}
    context = body.get("context") or {}
    tool = _field(resource, "tool") or resource.get("id") if isinstance(resource, dict) else None
    verb = _field(action, "verb") or action.get("name") if isinstance(action, dict) else None
    return {
        "tool_name": tool,
        "action": verb,
        "environment": (
            _field(resource, "environment") or context.get("environment") or "production"
        ),
        "data_class": (
            _field(resource, "data_class") or context.get("data_class") or "internal"
        ),
        "agent_id": (subject.get("id") if isinstance(subject, dict) else None) or "unknown",
        "session_id": context.get("session_id"),
        "arguments": context.get("arguments"),
        "context": context,
    }


def evaluate_single(body: dict[str, Any], core: Any) -> dict[str, Any]:
    """Evaluate one AuthZEN request → ``{decision, context}``."""
    kwargs = _call_kwargs(body)
    if not kwargs["tool_name"] or not kwargs["action"]:
        return {
            "decision": False,
            "context": {
                "schema": SCHEMA,
                "reason_code": "unknown_action",
                "reason_admin": {"reason_code": "unknown_action"},
                "reason_user": "request is missing resource.tool or action.verb",
            },
        }
    result = core.evaluate(**kwargs)
    permitted = result.get("decision") in PERMITTED
    return {
        "decision": permitted,
        "context": {
            "schema": SCHEMA,
            "reason_code": result.get("reason_code"),
            "reason_admin": {
                "reason_code": result.get("reason_code"),
                "policy_version": result.get("policy_version"),
                "matched_rule": result.get("matched_rule"),
            },
            "reason_user": result.get("explanation"),
        },
    }


def _combine(decisions: list[bool], semantic: str) -> bool:
    if semantic == "permit_on_first_permit":
        return any(decisions)
    # execute_all / deny_on_first_deny: all must permit.
    return all(decisions)


def evaluate(body: dict[str, Any], core: Any) -> dict[str, Any]:
    """Handle a single evaluation or a boxcared batch.

    Args:
        body: The AuthZEN request (single or ``{evaluations, options}``).
        core: A :class:`ServerCore`.

    Returns:
        A single ``{decision, context}`` or
        ``{evaluations: [...], decision: bool}`` for a batch.
    """
    evaluations = body.get("evaluations")
    if not isinstance(evaluations, list):
        return evaluate_single(body, core)
    options = body.get("options") or {}
    semantic = options.get("evaluations_semantic") or "execute_all"
    responses = [
        evaluate_single(item, core) for item in evaluations if isinstance(item, dict)
    ]
    return {
        "evaluations": responses,
        "decision": _combine([bool(r["decision"]) for r in responses], str(semantic)),
        "context": {"schema": SCHEMA, "evaluations_semantic": semantic},
    }


def register_authzen_routes(mcp: Any, core: Any) -> None:
    """Register ``POST /access/v1/evaluation`` on a FastMCP server."""

    @mcp.custom_route("/access/v1/evaluation", methods=["POST"])  # type: ignore[untyped-decorator]
    async def access_evaluation(request: Request) -> JSONResponse:
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "request body must be valid JSON"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "request body must be a JSON object"}, status_code=400)
        return JSONResponse(evaluate(body, core))


__all__ = [
    "PERMITTED",
    "SCHEMA",
    "SEMANTICS",
    "evaluate",
    "evaluate_single",
    "register_authzen_routes",
]
