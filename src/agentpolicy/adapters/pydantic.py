"""PydanticAI adapter — ``@agentpolicy_guard`` decorator for PydanticAI tools.

Wraps a PydanticAI ``@agent.tool`` decorated function so that every invocation
passes through the AgentPolicy engine. A deny decision raises ``ModelRetry`` to
signal the agent to retry with a different approach, or returns a tool error
message the model can see.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any

from agentpolicy.adapters.base import BaseAdapter, CallContext
from agentpolicy.types import Decision


class PydanticAIAdapter(BaseAdapter):
    """Guard PydanticAI tools with AgentPolicy evaluation.

    Args:
        engine: A configured Engine instance.
    """

    def intercept(self, ctx: CallContext) -> Decision:
        return self.engine.evaluate(
            tool_name=ctx.tool_name,
            action=ctx.action,
            environment=ctx.environment,
            data_class=ctx.data_class,
            agent_id=ctx.agent_id,
            arguments=ctx.arguments,
            context=ctx.context,
        )

    def guard(
        self,
        *,
        tool_name: str = "",
        action: str = "",
        environment: str = "production",
        data_class: str = "internal",
        agent_id: str = "",
        on_deny: str = "error",
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator that guards a PydanticAI tool function.

        Args:
            tool_name: Tool identity (defaults to function name).
            action: Action (defaults to ``"call"``).
            environment: Deployment environment.
            data_class: Data sensitivity label.
            agent_id: Agent identity.
            on_deny: ``"retry"`` raises ``ModelRetry``; ``"error"`` returns
                an error string as the tool result.

        Returns:
            A decorator for PydanticAI tool functions.
        """

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            name = tool_name or fn.__name__

            @functools.wraps(fn)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                ctx = CallContext(
                    tool_name=name,
                    action=action or "call",
                    environment=environment,
                    data_class=data_class,
                    agent_id=agent_id,
                    arguments=kwargs or None,
                )
                decision = self.intercept(ctx)

                if decision.decision in ("deny", "escalate"):
                    if on_deny == "retry":
                        try:
                            from pydantic_ai.exceptions import ModelRetry

                            raise ModelRetry(
                                f"[AgentPolicy] {decision.decision}: {decision.explanation}"
                            )
                        except ImportError:
                            raise RuntimeError(
                                "pydantic-ai required for ModelRetry; "
                                "install `agentsec-agentpolicy[pydantic-ai]`"
                            ) from None
                    return f"[AgentPolicy] {decision.decision}: {decision.explanation}"
                return fn(*args, **kwargs)

            return wrapper

        return decorator
