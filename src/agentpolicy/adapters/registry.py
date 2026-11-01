"""The adapter registry (WBS M8 ``8.4``).

Maps an adapter **name** to its class, the install **extra** that supplies its
dependency, and a builder. Load is **validated at load time**: an unknown name,
a missing optional dependency, or a missing required kwarg raises
:class:`~agentpolicy.cli.errors.ConfigError` (exit 2) — never a bare
``ImportError`` or an ``AttributeError`` deep inside a call.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from agentpolicy.cli.errors import ConfigError


@dataclass(frozen=True)
class AdapterSpec:
    """One registered adapter.

    Attributes:
        name: The registry key (``raw``, ``langgraph``, …).
        extra: The pip extra that provides the dependency, or ``None``.
        requires: The importable modules the adapter needs.
        builder: ``(engine, **kwargs) -> adapter``.
    """

    name: str
    extra: str | None
    requires: tuple[str, ...]
    builder: Callable[..., Any]


def _build_raw(engine: Any, **_kw: Any) -> Any:
    from agentpolicy.adapters.raw import RawAdapter

    return RawAdapter(engine)


def _build_mcp(engine: Any, **kw: Any) -> Any:
    from agentpolicy.adapters.mcp import AgentPolicyMCPWrapper

    client = kw.get("mcp_client")
    if client is None:
        raise ConfigError("adapter 'mcp' requires an 'mcp_client' argument")
    return AgentPolicyMCPWrapper(client, engine)


def _build_langgraph(engine: Any, **kw: Any) -> Any:
    from agentpolicy.adapters.langgraph import AgentPolicyToolNode

    tools = kw.get("tools")
    if tools is None:
        raise ConfigError("adapter 'langgraph' requires a 'tools' argument")
    return AgentPolicyToolNode(
        tools,
        engine,
        agent_id=kw.get("agent_id", "agent"),
        environment=kw.get("environment", "production"),
        data_class=kw.get("data_class", "internal"),
    )


def _build_pydantic(engine: Any, **_kw: Any) -> Any:
    from agentpolicy.adapters.pydantic import PydanticAIAdapter

    return PydanticAIAdapter(engine)


def _build_openai(engine: Any, **_kw: Any) -> Any:
    from agentpolicy.adapters.openai import OpenAIAdapter

    return OpenAIAdapter(engine)


def _build_crewai(engine: Any, **_kw: Any) -> Any:
    from agentpolicy.adapters.crewai import CrewAIAdapter

    return CrewAIAdapter(engine)


def _build_smolagents(engine: Any, **_kw: Any) -> Any:
    from agentpolicy.adapters.smolagents import SmolagentsAdapter

    return SmolagentsAdapter(engine)


def _build_autogen(engine: Any, **_kw: Any) -> Any:
    from agentpolicy.adapters.autogen import AutoGenAdapter

    return AutoGenAdapter(engine)


def _build_llamaindex(engine: Any, **_kw: Any) -> Any:
    from agentpolicy.adapters.llamaindex import LlamaIndexAdapter

    return LlamaIndexAdapter(engine)


def _build_adk(engine: Any, **_kw: Any) -> Any:
    from agentpolicy.adapters.adk import AdkAdapter

    return AdkAdapter(engine)


#: The registry. Order is the doc/report order.
SPECS: dict[str, AdapterSpec] = {
    spec.name: spec
    for spec in (
        AdapterSpec("raw", None, (), _build_raw),
        AdapterSpec("mcp", "mcp", ("mcp",), _build_mcp),
        AdapterSpec("langgraph", "langgraph", ("langgraph", "langchain_core"), _build_langgraph),
        AdapterSpec("pydanticai", "pydanticai", ("pydantic_ai",), _build_pydantic),
        AdapterSpec("openai", "openai-agents", ("agents",), _build_openai),
        AdapterSpec("crewai", "crewai", (), _build_crewai),
        AdapterSpec("smolagents", "smolagents", (), _build_smolagents),
        AdapterSpec("autogen", "autogen", (), _build_autogen),
        AdapterSpec("llamaindex", "llamaindex", (), _build_llamaindex),
        AdapterSpec("adk", "adk", (), _build_adk),
    )
}


def available() -> list[str]:
    """Every registered adapter name (in registry order)."""
    return list(SPECS)


def get(name: str) -> AdapterSpec:
    """Return the spec for *name*, or raise ``ConfigError`` for an unknown name."""
    spec = SPECS.get(name)
    if spec is None:
        raise ConfigError(
            f"unknown adapter {name!r}; available adapters: {', '.join(available())}"
        )
    return spec


def _missing_deps(spec: AdapterSpec) -> list[str]:
    missing: list[str] = []
    for module in spec.requires:
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(module)
    return missing


def validate(name: str | None = None) -> list[str]:
    """Return the adapter name(s) whose dependencies are importable.

    Args:
        name: A single adapter to check, or ``None`` for every adapter.

    Returns:
        The subset of checked names that are loadable here.
    """
    names = [name] if name is not None else available()
    result: list[str] = []
    for candidate in names:
        spec = get(candidate)
        if not _missing_deps(spec):
            result.append(candidate)
    return result


def load(name: str, engine: Any, **kwargs: Any) -> Any:
    """Build the adapter *name*, validated at load.

    Args:
        name: The registered adapter name.
        engine: A configured engine to wrap.
        **kwargs: Adapter-specific constructor args (e.g. ``mcp_client``).

    Returns:
        The adapter instance.

    Raises:
        ConfigError: The name is unknown, its optional dependency is not
            installed, or a required kwarg is missing.
    """
    spec = get(name)
    missing = _missing_deps(spec)
    if missing:
        extra = (
            f" (install with `pip install 'agentsec-agentpolicy[{spec.extra}]'`)"
            if spec.extra
            else ""
        )
        raise ConfigError(
            f"adapter {name!r} requires {', '.join(missing)} which is not installed{extra}"
        )
    return spec.builder(engine, **kwargs)


__all__ = ["SPECS", "AdapterSpec", "available", "get", "load", "validate"]
