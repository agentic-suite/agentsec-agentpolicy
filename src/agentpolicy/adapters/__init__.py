"""Integration adapters — pluggable framework guards for AgentPolicy.

Each adapter wraps an :class:`~agentpolicy.engine.engine.Engine` and
provides a framework-native interception point that evaluates every tool call
before side effects execute.
"""

from __future__ import annotations

from agentpolicy.adapters.adk import AdkAdapter
from agentpolicy.adapters.autogen import AutoGenAdapter
from agentpolicy.adapters.base import BaseAdapter, CallContext
from agentpolicy.adapters.llamaindex import LlamaIndexAdapter
from agentpolicy.adapters.smolagents import SmolagentsAdapter

__all__ = [
    "AdkAdapter",
    "AutoGenAdapter",
    "BaseAdapter",
    "CallContext",
    "LlamaIndexAdapter",
    "SmolagentsAdapter",
]
