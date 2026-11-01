"""The canonical action (WBS M3 ``3.1``).

One shape from every surface — MCP ``tools/call``, a framework tool node, raw
Python, HTTP, or a coarse dispatcher string — into a single canonical
``NormalizedCall`` ``(principal, action, resource, context)`` that the Cedar
decision core evaluates. This is the M3 facade over the ported normalizer,
tool-name folding, and dispatcher parser.
"""

from __future__ import annotations

from typing import Any

from agentpolicy.cedar.policy import to_request
from agentpolicy.engine.dispatcher import parse_aws, parse_bash, parse_git, parse_http
from agentpolicy.engine.normalize import normalize
from agentpolicy.taxonomy import action_class_for, domain_for, is_known_tool
from agentpolicy.types import NormalizedCall

#: Coarse-input dispatchers keyed by kind.
_PARSERS = {"bash": parse_bash, "git": parse_git, "http": parse_http, "aws": parse_aws}


def canonicalize(
    *,
    tool: str,
    action: str,
    environment: str,
    data_class: str,
    agent_id: str,
    agent_class: str = "general",
    arguments: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    resource_tag: str | None = None,
) -> NormalizedCall:
    """Canonicalize a raw tool call.

    Folds the tool name (case/whitespace/Unicode) and resolves the taxonomy
    domain + action class. Raises ``UnknownToolError`` for an unknown tool and
    ``MalformedInputError`` for a blank field — the engine maps both to a
    fail-closed deny.
    """
    return normalize(
        tool=tool,
        action=action,
        environment=environment,
        data_class=data_class,
        agent_id=agent_id,
        agent_class=agent_class,
        arguments=arguments,
        context=context,
        resource_tag=resource_tag,
    )


def canonicalize_command(
    raw: str,
    *,
    kind: str = "bash",
    environment: str,
    data_class: str,
    agent_id: str,
    agent_class: str = "general",
) -> NormalizedCall:
    """Canonicalize a coarse command string (``bash``/``git``/``http``/``aws``).

    Parses ``raw`` into a canonical ``(tool, action)`` and normalizes it, so a
    smuggled action (``bash: "git push --force"`` → ``force_push``) evaluates
    against the same policy as a direct call.
    """
    parser = _PARSERS.get(kind)
    if parser is None:
        raise ValueError(f"unsupported dispatch kind {kind!r}; use one of {sorted(_PARSERS)}")
    parsed = parser(raw)
    return normalize(
        tool=parsed.tool,
        action=parsed.action,
        environment=environment,
        data_class=data_class,
        agent_id=agent_id,
        agent_class=agent_class,
        arguments=parsed.args,
    )


def to_cedar_request(
    call: NormalizedCall, *, extra_context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Build the Cedar ``(principal, action, resource, context)`` request for a canonical call."""
    return to_request(call, extra_context=extra_context)


def taxonomy_view(call: NormalizedCall) -> dict[str, Any]:
    """The taxonomy-derived view of a canonical call (for explain/audit)."""
    return {
        "tool": call.tool,
        "tool_category": call.tool_category,
        "action": call.action,
        "action_class": call.action_class,
        "known_tool": is_known_tool(call.tool),
        "domain": domain_for(call.tool),
        "resolved_action_class": action_class_for(call.action),
    }
