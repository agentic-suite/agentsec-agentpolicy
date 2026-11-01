"""M13 — exfil-sink rule class, argument validators, tool hiding.

WBS M13: ``13.1`` exfil-sink · ``13.2`` argument validation · ``13.3`` tool
hiding. CUJ-13 (R10, R19, R21).
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from agentpolicy.engine.argument_policy import ArgumentSpec, check_arguments
from agentpolicy.engine.engine import Engine
from agentpolicy.engine.exfil import exfil_violation
from agentpolicy.engine.normalize import normalize
from agentpolicy.errors import DENY_EXFIL_SINK
from agentpolicy.pack_format import run_pack_dir, validate_pack_dir
from agentpolicy.policy.models import Rule, default_policy

REPO = Path(__file__).resolve().parent.parent
PACK = REPO / "packs/exfil-sink"


def _call(tool, action, environment, data_class, tool_category, action_class="write"):
    return normalize(
        tool=tool, action=action, environment=environment, data_class=data_class,
        agent_id="bot", agent_class="general",
    )


class TestExfilSink:
    def _engine(self) -> Engine:
        return Engine(default_policy("balanced"))

    def test_sensitive_to_external_sink_is_denied_naming_source_and_sink(self) -> None:
        decision = self._engine().evaluate(
            tool_name="send_email", action="write", environment="production",
            data_class="restricted", agent_id="release-bot",
        )
        assert decision.decision == "deny"
        assert decision.reason_code == DENY_EXFIL_SINK
        assert "restricted" in decision.explanation
        assert "send_email" in decision.explanation

    def test_slack_pii_is_denied(self) -> None:
        decision = self._engine().evaluate(
            tool_name="send_slack", action="write", environment="production",
            data_class="customer_pii", agent_id="release-bot",
        )
        assert decision.decision == "deny"
        assert decision.reason_code == DENY_EXFIL_SINK

    def test_benign_read_is_allowed(self) -> None:
        decision = self._engine().evaluate(
            tool_name="query_logs", action="read", environment="staging",
            data_class="internal", agent_id="debug-bot",
        )
        assert decision.decision == "allow"

    def test_exfil_violation_unit(self) -> None:
        assert exfil_violation(_call("send_email", "write", "production", "restricted", "email"))
        assert exfil_violation(_call("query_logs", "read", "staging", "internal", "search")) is None


class TestExfilPack:
    def test_pack_validates(self) -> None:
        assert validate_pack_dir(PACK) == []

    def test_pack_replay_passes(self) -> None:
        results = run_pack_dir(PACK)
        assert results and all(r.passed for r in results)

    def test_pack_blocks_the_exfil_chain(self) -> None:
        results = {r.name: r for r in run_pack_dir(PACK)}
        assert results["exfil-send-email-restricted"].got == "deny"
        assert results["benign-internal-read"].got == "allow"


class TestArgumentValidators:
    def test_regex_select_only(self) -> None:
        policy = {"db": {"query": ArgumentSpec(regex=r"(?i)^\s*select\b")}}
        assert check_arguments("db", {"query": "DELETE FROM users"}, policy) == "query"
        assert check_arguments("db", {"query": "SELECT * FROM users"}, policy) is None

    def test_enum(self) -> None:
        policy = {"t": {"mode": ArgumentSpec(enum=("fast", "safe"))}}
        assert check_arguments("t", {"mode": "yolo"}, policy) == "mode"
        assert check_arguments("t", {"mode": "safe"}, policy) is None

    def test_refund_cap(self) -> None:
        policy = {"refund": {"amount": ArgumentSpec(max=100)}}
        assert check_arguments("refund", {"amount": 101}, policy) == "amount"
        assert check_arguments("refund", {"amount": 100}, policy) is None

    def test_path_containment(self, tmp_path: Path) -> None:
        policy = {"read_file": {"path": ArgumentSpec(path_root=str(tmp_path))}}
        assert check_arguments("read_file", {"path": "../../etc/passwd"}, policy) == "path"
        assert check_arguments("read_file", {"path": "notes.txt"}, policy) is None

    def test_url_allowlist_blocks_ssrf(self) -> None:
        policy = {"http_get": {"url": ArgumentSpec(url_allowlist=("api.example.com",))}}
        assert check_arguments(
            "http_get", {"url": "http://169.254.169.254/latest/meta-data"}, policy
        ) == "url"
        assert check_arguments("http_get", {"url": "https://api.example.com/x"}, policy) is None

    def test_engine_enforces_validator(self) -> None:
        base = default_policy("balanced")
        policy = replace(
            base, args_policy={"query_logs": {"query": ArgumentSpec(regex=r"^select")}}
        )
        decision = Engine(policy).evaluate(
            tool_name="query_logs", action="read", environment="staging",
            data_class="internal", agent_id="bot", arguments={"query": "drop table x"},
        )
        assert decision.decision == "deny"
        assert decision.reason_code == "deny_argument_policy"


class TestToolHiding:
    def test_unconditionally_denied_tool_is_hidden(self) -> None:
        base = default_policy("balanced")
        policy = replace(base, rules=(Rule(decision="deny", tool="drop_database", reason="never"),))
        caps = Engine(policy).capabilities("release-bot")
        assert "drop_database" not in caps
        assert "query_logs" in caps

    def test_hidden_for_still_works(self) -> None:
        base = default_policy("balanced")
        policy = replace(base, tool_visibility={"query_logs": {"hidden_for": ("ci-bot",)}})
        assert "query_logs" not in Engine(policy).capabilities("release-bot")

    def test_hiding_does_not_weaken_enforcement(self) -> None:
        base = default_policy("balanced")
        policy = replace(base, rules=(Rule(decision="deny", tool="drop_database", reason="never"),))
        engine = Engine(policy)
        decision = engine.evaluate(
            tool_name="drop_database", action="delete", environment="production",
            data_class="customer_pii", agent_id="release-bot",
        )
        assert decision.decision == "deny"

    def test_default_policy_hides_nothing(self) -> None:
        assert "drop_database" in Engine(default_policy("balanced")).capabilities("release-bot")


@pytest.mark.parametrize("tool,action,env,data,expect", [
    ("send_email", "write", "production", "restricted", "deny"),
    ("send_slack", "write", "production", "customer_pii", "deny"),
])
def test_exfil_matrix(tool, action, env, data, expect) -> None:
    decision = Engine(default_policy("balanced")).evaluate(
        tool_name=tool, action=action, environment=env, data_class=data, agent_id="bot",
    )
    assert decision.decision == expect
