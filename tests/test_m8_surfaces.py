"""M8 — delivery surfaces (library/MCP/HTTP parity) and the adapter registry.

WBS M8: ``8.1`` library surface · ``8.2`` MCP · ``8.3`` HTTP · ``8.4`` adapter
registry · ``8.5`` wire into an enforcer. CUJ-2 (R28).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import agentpolicy
from agentpolicy import api
from agentpolicy.adapters import registry
from agentpolicy.adapters.base import denial_message
from agentpolicy.adapters.mcp import AgentPolicyMCPWrapper
from agentpolicy.adapters.raw import AgentPolicyDecisionError, RawAdapter
from agentpolicy.audit.logger import AuditLogger
from agentpolicy.audit.sinks.jsonl import JsonlSink
from agentpolicy.cli import main
from agentpolicy.cli.errors import ConfigError
from agentpolicy.engine.engine import Engine
from agentpolicy.policy.models import default_policy
from agentpolicy.server.server_core import ServerCore
from agentpolicy.server.session_store import SessionStore

_CALL = dict(
    tool="drop_database", action="delete", environment="production",
    data_class="customer_pii", agent_id="release-bot",
)


def _core(tmp_path: Path) -> ServerCore:
    engine = Engine(default_policy("balanced"))
    return ServerCore(engine, SessionStore(), AuditLogger(JsonlSink(tmp_path / "audit.jsonl")))


class TestLibrarySurface:
    def test_library_evaluate_returns_a_decision(self) -> None:
        decision = api.evaluate(**_CALL)
        assert decision.decision == "deny"
        assert decision.reason_code == "deny_critical_op"
        assert decision.explanation

    def test_package_exports_evaluate(self) -> None:
        assert agentpolicy.evaluate is api.evaluate

    def test_unknown_tool_fails_closed(self) -> None:
        decision = api.evaluate(
            tool="definitely_not_a_tool", action="read", environment="staging",
            data_class="internal", agent_id="x",
        )
        assert decision.decision == "deny"
        assert decision.reason_code == "deny_unknown_tool"


class TestSurfaceParity:
    def test_library_matches_server_core(self, tmp_path: Path) -> None:
        lib = api.evaluate(**_CALL).to_dict()
        served = _core(tmp_path).evaluate(
            tool_name=_CALL["tool"], action=_CALL["action"],
            environment=_CALL["environment"], data_class=_CALL["data_class"],
            agent_id=_CALL["agent_id"],
        )
        for key in ("decision", "reason_code", "criticality", "explanation"):
            assert lib[key] == served[key]

    def test_allow_parity(self, tmp_path: Path) -> None:
        call = dict(tool="query_logs", action="read", environment="staging",
                    data_class="internal", agent_id="debug-bot")
        assert api.evaluate(**call).decision == "allow"
        served = _core(tmp_path).evaluate(
            tool_name=call["tool"], action=call["action"], environment=call["environment"],
            data_class=call["data_class"], agent_id=call["agent_id"],
        )
        assert served["decision"] == "allow"

    def test_cli_evaluate_matches_library(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main([
            "evaluate", "--tool", "drop_database", "--action", "delete",
            "--env", "production", "--data", "customer_pii", "--agent", "release-bot",
            "--format", "json",
        ]) == 2  # deny exits 2
        import json

        payload = json.loads(capsys.readouterr().out)
        assert payload["reason_code"] == api.evaluate(**_CALL).reason_code


class TestAdapterRegistry:
    def test_available_lists_the_adapters(self) -> None:
        names = registry.available()
        for expected in ("raw", "mcp", "langgraph", "pydanticai", "openai"):
            assert expected in names

    def test_unknown_adapter_is_a_config_error(self) -> None:
        with pytest.raises(ConfigError) as exc:
            registry.get("no_such_adapter")
        assert exc.value.exit_code == 2
        assert "unknown adapter" in str(exc.value)

    def test_load_raw_adapter(self) -> None:
        engine = Engine(default_policy("balanced"))
        adapter = registry.load("raw", engine)
        assert isinstance(adapter, RawAdapter)

    def test_load_mcp_requires_client(self) -> None:
        engine = Engine(default_policy("balanced"))
        with pytest.raises(ConfigError, match="mcp_client"):
            registry.load("mcp", engine)

    def test_load_mcp_with_client(self) -> None:
        class FakeClient:
            class tools:
                @staticmethod
                def call(name, arguments):
                    return {"ok": True}

        engine = Engine(default_policy("balanced"))
        adapter = registry.load("mcp", engine, mcp_client=FakeClient())
        assert isinstance(adapter, AgentPolicyMCPWrapper)

    def test_validate_includes_raw(self) -> None:
        assert "raw" in registry.validate()
        assert registry.validate("raw") == ["raw"]


class TestEnforcer:
    def test_denial_message_is_model_consumable(self) -> None:
        decision = api.evaluate(**_CALL)
        message = denial_message(decision)
        assert message.startswith("[AgentPolicy] deny:")
        assert decision.reason_code in message

    def test_raw_adapter_raises_replan_able_rejection(self) -> None:
        engine = Engine(default_policy("balanced"))
        adapter = RawAdapter(engine)

        @adapter.guard(tool_name="drop_database", action="delete",
                       environment="production", data_class="customer_pii",
                       agent_id="release-bot")
        def dangerous():
            return "executed"

        with pytest.raises(AgentPolicyDecisionError) as exc:
            dangerous()
        # The caller can name the reason and replan.
        assert exc.value.decision.reason_code == "deny_critical_op"

    def test_mcp_wrapper_deny_is_an_error_result(self) -> None:
        class FakeClient:
            class tools:
                @staticmethod
                def call(name, arguments):
                    return {"ok": True}

        engine = Engine(default_policy("balanced"))
        wrapper = AgentPolicyMCPWrapper(FakeClient(), engine)
        call = wrapper.wrap_call("drop_database", {
            "__agentpolicy_environment": "production",
            "__agentpolicy_data_class": "customer_pii",
        })
        result = call()
        assert result["isError"] is True
        assert result["content"][0]["text"].startswith("[AgentPolicy] ")
