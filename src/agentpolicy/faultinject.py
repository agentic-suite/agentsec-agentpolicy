"""Fail-closed fault injection (WBS M23 ``23.2``, R8).

A deterministic way to fail any engine stage. ``fault_hook`` returns a callable
that raises :class:`InjectedFault` (an :class:`AgentPolicyError`), so the
engine's ``fail_closed`` decorator converts it into a **deny with a reason
code** — never an allow and never a crash. The engine never aborts on a fault.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agentpolicy.errors import DENY_ENGINE_UNAVAILABLE, AgentPolicyError


class InjectedFault(AgentPolicyError):
    """An injected failure carrying a chosen ``reason_code``."""

    def __init__(
        self, reason_code: str = DENY_ENGINE_UNAVAILABLE, message: str = "fault injected"
    ) -> None:
        self.reason_code = reason_code
        super().__init__(message)


def fault_hook(reason_code: str = DENY_ENGINE_UNAVAILABLE) -> Callable[..., Any]:
    """Return a callable that raises :class:`InjectedFault` when invoked."""

    def _hook(*_args: Any, **_kwargs: Any) -> Any:
        raise InjectedFault(reason_code)

    return _hook


__all__ = ["InjectedFault", "fault_hook"]
