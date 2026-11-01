"""CrewAI adapter — ``wrap_tool`` that guards ``_run()`` with AgentPolicy.

Wraps a CrewAI tool's ``_run()`` method so every invocation passes through the
AgentPolicy engine. A deny decision returns an error string in the tool output,
which CrewAI agents can read and handle without crashing.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agentpolicy.adapters.base import BaseAdapter, CallContext
from agentpolicy.types import Decision


class CrewAIAdapter(BaseAdapter):
    """Guard CrewAI tools with AgentPolicy evaluation.

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

    def wrap_tool(
        self,
        tool: Any,
        *,
        tool_name: str = "",
        action: str = "",
        environment: str = "production",
        data_class: str = "internal",
        agent_id: str = "",
    ) -> Any:
        """Wrap a CrewAI tool so ``_run()`` is guarded by AgentPolicy.

        Args:
            tool: A CrewAI tool instance with a ``_run()`` method.
            tool_name: Tool identity (defaults to the tool's name attribute).
            action: Action (defaults to ``"call"``).
            environment: Deployment environment.
            data_class: Data sensitivity label.
            agent_id: Agent identity.

        Returns:
            The tool with ``_run()`` replaced by a guarded version.
        """
        name = tool_name or getattr(tool, "name", "unknown")
        original_run: Callable[..., Any] = tool._run

        def guarded_run(*args: Any, **kwargs: Any) -> Any:
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
                return f"[AgentPolicy] {decision.decision}: {decision.explanation}"
            return original_run(*args, **kwargs)

        tool._run = guarded_run
        return tool
