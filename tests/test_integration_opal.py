"""Coverage for the OPAL distributed policy-sync integration (M0 ported tree).

Exercises :class:`agentpolicy.integrations.opal.OpalClient` without the optional
``opal-client`` dependency: construction, update application + hot reload,
version history, rollback (known / unknown / missing snapshot), and the
install-guard on ``start()``. ``start()`` with a stubbed ``opal_client`` module
covers the connect path.
"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from pathlib import Path

import pytest

from agentpolicy.engine.engine import Engine
from agentpolicy.integrations.opal import OpalClient
from agentpolicy.policy.models import default_policy


def _engine() -> Engine:
    return Engine(default_policy("balanced"))


def test_constructor_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("OPAL_SERVER_URL", "https://opal.env.example")
    client = OpalClient(_engine(), policy_path=str(tmp_path))
    assert client.versions == []


def test_apply_update_records_version_and_reloads(tmp_path: Path) -> None:
    client = OpalClient(_engine(), policy_path=str(tmp_path))
    client._apply_update({"version": "v1", "policy": {"version": "1.0.0"}})
    assert client.versions == ["v1"]
    assert (tmp_path / "policy-v1.yaml").exists()
    # No explicit version -> auto-numbered from the history length.
    client._apply_update({"policy": {"version": "1.0.0"}})
    assert client.versions == ["v1", "v1"]


def test_rollback_unknown_version_is_false(tmp_path: Path) -> None:
    client = OpalClient(_engine(), policy_path=str(tmp_path))
    assert client.rollback("does-not-exist") is False


def test_rollback_known_then_missing_snapshot(tmp_path: Path) -> None:
    client = OpalClient(_engine(), policy_path=str(tmp_path))
    client._apply_update({"version": "v2", "policy": {"version": "1.0.0"}})
    assert client.rollback("v2") is True
    (tmp_path / "policy-v2.yaml").unlink()
    assert client.rollback("v2") is False


def test_stop_without_start_is_noop(tmp_path: Path) -> None:
    OpalClient(_engine(), policy_path=str(tmp_path)).stop()


def test_start_without_opal_client_raises(tmp_path: Path) -> None:
    if importlib.util.find_spec("opal_client") is not None:  # pragma: no cover
        pytest.skip("opal_client is installed; install-guard not exercised")
    client = OpalClient(_engine(), policy_path=str(tmp_path))
    with pytest.raises(RuntimeError, match="opal-client is not installed"):
        client.start()


def test_start_and_stop_with_stub_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    recorded: dict[str, object] = {}

    class _FakeOpal:
        def __init__(self, server_url: str | None = None, callback: object = None) -> None:
            recorded["server_url"] = server_url
            recorded["callback"] = callback

        def start(self) -> None:
            recorded["started"] = True

        def stop(self) -> None:
            recorded["stopped"] = True

    pkg = types.ModuleType("opal_client")
    inner = types.ModuleType("opal_client.client")
    inner.OpalClient = _FakeOpal  # type: ignore[attr-defined]
    pkg.client = inner  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "opal_client", pkg)
    monkeypatch.setitem(sys.modules, "opal_client.client", inner)

    client = OpalClient(_engine(), server_url="https://opal.stub", policy_path=str(tmp_path))
    client.start()
    assert recorded["server_url"] == "https://opal.stub"
    assert recorded["started"] is True

    callback = recorded["callback"]
    assert callable(callback)
    asyncio.run(callback({"version": "vv", "policy": {"version": "1.0.0"}}))
    assert "vv" in client.versions

    client.stop()
    assert recorded["stopped"] is True
