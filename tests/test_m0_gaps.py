"""Extra coverage for the M0 ported tree — CLI branches and model guards.

These complement the ported suite for paths the predecessor never exercised
(CSV/empty report output, failing golden fixtures, dead-rule analytics, pack
error branches, OPAL/escalation route helpers, and condition/profile guards).
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from agentpolicy.cli import analytics as analytics_cli
from agentpolicy.cli import pack as pack_cli
from agentpolicy.cli import report as report_cli
from agentpolicy.cli import test as test_cli
from agentpolicy.cli.errors import CliError
from agentpolicy.field.report import build_report
from agentpolicy.policy.models import AgentProfile, Condition, condition_from_dict
from agentpolicy.server import escalation_routes

# --------------------------------------------------------------------------- #
# policy/models.py — condition + profile guards
# --------------------------------------------------------------------------- #


def _leaf(field: str = "action", value: str = "read") -> Condition:
    return Condition(op="eq", field=field, value=value)


def _call(action: str = "read") -> SimpleNamespace:
    return SimpleNamespace(action=action, action_class=action)


def test_condition_not_group_constructs_and_matches() -> None:
    node = Condition(op="not", condition=_leaf())
    assert node.matches(_call()) is False


def test_condition_and_or_group_constructs_and_matches() -> None:
    node = Condition(op="and", conditions=(_leaf(),))
    assert node.matches(_call()) is True
    node_or = Condition(op="or", conditions=(_leaf(value="write"),))
    assert node_or.matches(_call()) is False


def test_condition_from_dict_not_without_condition_raises() -> None:
    with pytest.raises(ValueError, match="requires a `condition` dict"):
        condition_from_dict({"op": "not"})


def test_profile_blank_environment_raises() -> None:
    with pytest.raises(ValueError, match="non-blank"):
        AgentProfile(agent_class="c", risk=0.5, environments=("  ",))


# --------------------------------------------------------------------------- #
# field/report.py — failure section
# --------------------------------------------------------------------------- #


def _case() -> SimpleNamespace:
    return SimpleNamespace(
        scenario=SimpleNamespace(id="scn-1", type="decision"),
        agent=SimpleNamespace(agent_id="ag-1", framework="langgraph"),
        agent_class="general",
        expected={"decision": "deny"},
        actual="allow",
        criticality="low",
        reason_code="allow_low_risk",
        passed=False,
        notes="mismatch",
    )


def test_build_report_includes_failures_section() -> None:
    case = _case()
    report = SimpleNamespace(
        total=1,
        passed=0,
        failed=1,
        decision_cases=[case],
        adversarial_cases=[],
        framework_pass_rates=lambda: {"langgraph": 0.0},
        cases=[case],
        failures=lambda: [case],
        pass_rate=lambda *a: 0.0,
    )
    text = build_report(report)
    assert "## Failures" in text
    assert "scn-1" in text


# --------------------------------------------------------------------------- #
# cli/report.py — CSV + empty HTML
# --------------------------------------------------------------------------- #


def _entry() -> SimpleNamespace:
    return SimpleNamespace(
        decision="allow",
        tool="query_logs",
        agent_id="debug-bot",
        to_dict=lambda: {"decision": "allow", "tool": "query_logs", "agent_id": "debug-bot"},
    )


def test_report_csv(capsys: pytest.CaptureFixture[str]) -> None:
    report_cli._csv_report([_entry(), _entry()])
    assert "decision,tool,agent_id" in capsys.readouterr().out


def test_report_csv_empty(capsys: pytest.CaptureFixture[str]) -> None:
    report_cli._csv_report([])
    assert "No audit entries" in capsys.readouterr().out


def test_report_html_empty(capsys: pytest.CaptureFixture[str]) -> None:
    report_cli._html_report([], "compliance", "all")
    assert "No audit entries found" in capsys.readouterr().out


def test_report_dispatch_csv(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = SimpleNamespace(query=lambda: [_entry()])
    monkeypatch.setattr(report_cli, "AuditLogger", lambda: fake)
    assert report_cli._report(argparse.Namespace(format="csv", type="summary", period="all")) == 0


# --------------------------------------------------------------------------- #
# cli/test.py — failing fixtures + loader variants
# --------------------------------------------------------------------------- #

_FIXTURE_MISS = """
agent_id: test-agent
cells:
  - tool: drop_database
    action: delete
    environment: production
    data_class: customer_pii
    expected: allow
"""


def test_test_cli_reports_failure(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    fixture = tmp_path / "fx.yaml"
    fixture.write_text(_FIXTURE_MISS, encoding="utf-8")
    rc = test_cli._test(argparse.Namespace(policy=None, fixtures=str(fixture), json=False))
    assert rc == 1
    out = capsys.readouterr().out
    assert "expected allow" in out


def test_test_cli_json_failure(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    fixture = tmp_path / "fx.yaml"
    fixture.write_text(_FIXTURE_MISS, encoding="utf-8")
    assert test_cli._test(argparse.Namespace(policy=None, fixtures=str(fixture), json=True)) == 1
    assert json.loads(capsys.readouterr().out)["failed"] == 1


def test_load_fixtures_variants(tmp_path: Path) -> None:
    for key in ("scenarios", "fixtures"):
        p = tmp_path / f"{key}.yaml"
        p.write_text(f"{key}:\n  - tool: t\n    action: read\n", encoding="utf-8")
        _, cells = test_cli._load_fixtures(str(p))
        assert cells == [{"tool": "t", "action": "read"}]
    listed = tmp_path / "list.yaml"
    listed.write_text("- tool: t\n  action: read\n", encoding="utf-8")
    _, cells = test_cli._load_fixtures(str(listed))
    assert cells == [{"tool": "t", "action": "read"}]


def test_load_fixtures_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(CliError, match="Fixture file not found"):
        test_cli._load_fixtures(str(tmp_path / "nope.yaml"))


# --------------------------------------------------------------------------- #
# cli/analytics.py — unknown subcommand + dead-rule rendering
# --------------------------------------------------------------------------- #


def test_analytics_unknown_subcommand_raises() -> None:
    with pytest.raises(CliError, match="Unknown analytics subcommand"):
        analytics_cli._run_analytics(argparse.Namespace(analytics_command="bogus"))


def test_analytics_print_text_dead_rules(capsys: pytest.CaptureFixture[str]) -> None:
    findings = SimpleNamespace(
        recurring_denials=[],
        deny_to_allow_transitions=[],
        over_hit_rules=[],
        dead_rules=[
            SimpleNamespace(
                rule_index=2,
                decision="deny",
                tool="drop_database",
                action="delete",
                environment="production",
                data_class="customer_pii",
                reason="never matched",
            )
        ],
    )
    analytics_cli._print_text(findings)
    out = capsys.readouterr().out
    assert "Dead Rules" in out
    assert "#2 deny" in out


# --------------------------------------------------------------------------- #
# cli/pack.py — empty catalog + missing tests.yaml + validate error
# --------------------------------------------------------------------------- #


def test_pack_list_empty(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(pack_cli, "_PACKS_DIR", Path("/nonexistent-agentpolicy-packs"))
    assert pack_cli._run_list(argparse.Namespace()) == 0
    assert "No packs found" in capsys.readouterr().out


def test_pack_run_test_without_tests_yaml(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "src" / "agentpolicy" / "policy" / "postures" / "balanced.yaml"
    (tmp_path / "tools.yaml").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    assert pack_cli._run_test(argparse.Namespace(path=str(tmp_path))) == 0
    assert "no tests.yaml" in capsys.readouterr().out


def test_pack_validate_error_raises(tmp_path: Path) -> None:
    with pytest.raises(CliError):
        pack_cli._run_validate(argparse.Namespace(path=str(tmp_path / "missing")))


# --------------------------------------------------------------------------- #
# server/escalation_routes.py — helpers
# --------------------------------------------------------------------------- #


class _FakeManager:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.saved: str | None = None

    def save(self, path: str) -> None:
        if self.fail:
            raise OSError("disk full")
        self.saved = path


def test_persist_writes_when_configured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "esc.json"
    monkeypatch.setenv("AGENTPOLICY_ESCALATIONS_FILE", str(target))
    manager = _FakeManager()
    escalation_routes._persist(manager)
    assert manager.saved == str(target)


def test_persist_swallows_oserror(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AGENTPOLICY_ESCALATIONS_FILE", str(tmp_path / "esc.json"))
    escalation_routes._persist(_FakeManager(fail=True))  # must not raise


def test_persist_noop_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGENTPOLICY_ESCALATIONS_FILE", raising=False)
    manager = _FakeManager()
    escalation_routes._persist(manager)
    assert manager.saved is None


def test_default_user_returns_string() -> None:
    assert isinstance(escalation_routes._default_user(), str)


class _Req:
    def __init__(self, body: Any, raise_exc: bool = False) -> None:
        self._body = body
        self._raise = raise_exc

    async def body(self) -> Any:
        if self._raise:
            raise RuntimeError("read failed")
        return self._body


def test_json_body_variants() -> None:
    assert asyncio.run(escalation_routes._json_body(_Req(b""))) is None
    assert asyncio.run(escalation_routes._json_body(_Req(b"not json"))) is None
    assert asyncio.run(escalation_routes._json_body(_Req(b"[1,2]"))) is None
    assert asyncio.run(escalation_routes._json_body(_Req(b'{"a": 1}'))) == {"a": 1}
    assert asyncio.run(escalation_routes._json_body(_Req(b"", raise_exc=True))) is None
