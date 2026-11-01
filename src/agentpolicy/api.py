"""The library surface (WBS M8 ``8.1``) — the in-process 15-line path.

``evaluate(...)`` runs one tool call **in-process** through the same engine the
CLI, MCP server, and HTTP PDP use, and returns the same :class:`Decision`. Every
surface therefore agrees: a caller gets an identical decision regardless of
transport (R28). The engine is fail-closed, so an unknown tool or malformed
input yields a ``deny`` — never an exception and never an allow.
"""

from __future__ import annotations

from typing import Any

from agentpolicy.engine.engine import Engine
from agentpolicy.policy.models import default_policy
from agentpolicy.types import Decision

_DEFAULT_ENGINE: Engine | None = None


def default_engine() -> Engine:
    """The shared default engine (balanced posture), built once."""
    global _DEFAULT_ENGINE
    if _DEFAULT_ENGINE is None:
        _DEFAULT_ENGINE = Engine(default_policy("balanced"))
    return _DEFAULT_ENGINE


def evaluate(
    *,
    tool: str,
    action: str,
    environment: str,
    data_class: str,
    agent_id: str,
    arguments: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    engine: Engine | None = None,
) -> Decision:
    """Evaluate one tool call in-process (the library surface).

    Args:
        tool: The tool name.
        action: The action verb.
        environment: The deployment environment.
        data_class: The data-sensitivity label.
        agent_id: The calling agent identity.
        arguments: The tool-call arguments.
        context: Extra decision context.
        engine: A pre-built engine (defaults to the balanced default engine).

    Returns:
        The decision — identical to the CLI/MCP/HTTP surfaces for the same call.
    """
    eng = engine if engine is not None else default_engine()
    return eng.evaluate(
        tool_name=tool,
        action=action,
        environment=environment,
        data_class=data_class,
        agent_id=agent_id,
        arguments=arguments,
        context=context,
    )


__all__ = ["default_engine", "evaluate"]
