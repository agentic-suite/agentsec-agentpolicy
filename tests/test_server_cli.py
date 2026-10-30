"""Coverage for ``agentpolicy serve`` (agentpolicy.server.cli) — M0 ported tree.

The server is started with a real ``FastMCP`` instance (so every route
registration runs) but ``FastMCP.run`` is patched so no socket is opened.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import fastmcp
import pytest

from agentpolicy.cli.errors import CliError
from agentpolicy.server import cli as server_cli


def _args(**overrides: Any) -> argparse.Namespace:
    base: dict[str, Any] = {
        "port": 8000,
        "policy_path": None,
        "posture": "balanced",
        "host": "127.0.0.1",
    }
    base.update(overrides)
    return argparse.Namespace(**base)


@pytest.fixture
def no_run(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Patch FastMCP.run to record its arguments instead of serving."""
    calls: dict[str, Any] = {}

    def _run(self: object, **kwargs: Any) -> None:
        calls.update(kwargs)

    monkeypatch.setattr(fastmcp.FastMCP, "run", _run)
    return calls


def test_serve_with_default_preset(no_run: dict[str, Any]) -> None:
    assert server_cli._serve(_args()) == 0
    assert no_run["transport"] == "sse"
    assert no_run["host"] == "127.0.0.1"
    assert no_run["port"] == 8000


def test_serve_with_policy_path(tmp_path: Path, no_run: dict[str, Any]) -> None:
    policy = tmp_path / "agentpolicy.yaml"
    policy.write_text("version: '1.0.0'\n", encoding="utf-8")
    assert server_cli._serve(_args(policy_path=str(policy), port=9001)) == 0
    assert no_run["port"] == 9001


def test_serve_env_policy_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, no_run: dict[str, Any]
) -> None:
    policy = tmp_path / "agentpolicy.yaml"
    policy.write_text("version: '1.0.0'\n", encoding="utf-8")
    monkeypatch.setenv("AGENTPOLICY_POLICY_PATH", str(policy))
    assert server_cli._serve(_args()) == 0


def test_serve_bad_policy_path_fails_closed(tmp_path: Path, no_run: dict[str, Any]) -> None:
    with pytest.raises(CliError, match="Failed to load policy"):
        server_cli._serve(_args(policy_path=str(tmp_path / "missing.yaml")))


def test_serve_loads_persisted_escalations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, no_run: dict[str, Any]
) -> None:
    monkeypatch.setenv("AGENTPOLICY_ESCALATIONS_FILE", str(tmp_path / "esc.json"))
    assert server_cli._serve(_args()) == 0


def test_serve_keyboard_interrupt_returns_zero(
    monkeypatch: pytest.MonkeyPatch, no_run: dict[str, Any]
) -> None:
    def _interrupt(self: object, **kwargs: Any) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(fastmcp.FastMCP, "run", _interrupt)
    assert server_cli._serve(_args()) == 0


def test_serve_runtime_error_raises_cli_error(
    monkeypatch: pytest.MonkeyPatch, no_run: dict[str, Any]
) -> None:
    def _boom(self: object, **kwargs: Any) -> None:
        raise RuntimeError("bind failed")

    monkeypatch.setattr(fastmcp.FastMCP, "run", _boom)
    with pytest.raises(CliError, match="Server error"):
        server_cli._serve(_args())


def test_add_parser_registers_serve() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    server_cli.add_parser(sub)
    ns = parser.parse_args(["serve", "--port", "9002", "--posture", "strict"])
    assert ns.port == 9002
    assert ns.posture == "strict"
    assert ns.func is server_cli._serve
