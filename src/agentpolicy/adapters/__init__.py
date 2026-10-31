"""Integration adapters — pluggable framework guards for AgentPolicy.

Each adapter wraps an :class:`~agentpolicy.engine.engine.Engine` and provides a
framework-native interception point that evaluates every tool call before side
effects execute. The registry (:mod:`agentpolicy.adapters.registry`) maps an
adapter name to its class and validates it at load.
"""

from __future__ import annotations

from agentpolicy.adapters.adk import AdkAdapter
from agentpolicy.adapters.autogen import AutoGenAdapter
from agentpolicy.adapters.base import BaseAdapter, CallContext, denial_message
from agentpolicy.adapters.crewai import CrewAIAdapter
from agentpolicy.adapters.langgraph import AgentPolicyToolNode
from agentpolicy.adapters.llamaindex import LlamaIndexAdapter
from agentpolicy.adapters.mcp import AgentPolicyMCPWrapper
from agentpolicy.adapters.openai import OpenAIAdapter
from agentpolicy.adapters.pydantic import PydanticAIAdapter
from agentpolicy.adapters.raw import AgentPolicyDecisionError, RawAdapter
from agentpolicy.adapters.registry import SPECS, AdapterSpec, available, get, load, validate
from agentpolicy.adapters.smolagents import SmolagentsAdapter

__all__ = [
    "SPECS",
    "AdapterSpec",
    "AdkAdapter",
    "AgentPolicyDecisionError",
    "AgentPolicyMCPWrapper",
    "AgentPolicyToolNode",
    "AutoGenAdapter",
    "BaseAdapter",
    "CallContext",
    "CrewAIAdapter",
    "LlamaIndexAdapter",
    "OpenAIAdapter",
    "PydanticAIAdapter",
    "RawAdapter",
    "SmolagentsAdapter",
    "available",
    "denial_message",
    "get",
    "load",
    "validate",
]
