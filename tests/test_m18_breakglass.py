"""M18 — break-glass elevation & auto-revert.

WBS M18: ``18.1`` break-glass elevation · ``18.2`` auto-revert · ``18.4``
composition guard. CUJ-25 (R40).
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from agentpolicy.breakglass import BreakGlassLedger, BreakGlassWindow
from agentpolicy.cli import main
from agentpolicy.engine.engine import Engine
from agentpolicy.errors import DENY_OUT_OF_SCOPE
from agentpolicy.policy.models import AgentProfile, default_policy

FUTURE = "2999-01-01T00:00:00+00:00"
PAST = "2000-01-01T00:00:00+00:00"


def _ago(seconds: int) -> str:
    return (datetime.now(UTC) - timedelta(seconds=seconds)).isoformat()


def _ahead(seconds: int) -> str:
    return (datetime.now(UTC) + timedelta(seconds=seconds)).isoformat()


class TestBreakGlassLedger:
    def test_elevate_mints_id_and_is_active(self) -> None:
        ledger = BreakGlassLedger()
        window = ledger.elevate(
            agent_id="scoped-bot", environments=["production"], ends_at=FUTURE, reason="incident"
        )
        assert isinstance(window, BreakGlassWindow)
        assert window.break_glass_id.startswith("bg_")
        assert window.is_active(environment="production", agent_id="scoped-bot")
        assert not window.is_active(environment="staging", agent_id="scoped-bot")
        assert not window.is_active(environment="production", agent_id="other")
        assert ledger.events[0]["kind"] == "elevate"

    def test_elevate_requires_a_reason(self) -> None:
        with pytest.raises(ValueError, match="reason"):
            BreakGlassLedger().elevate(
                agent_id="a", environments=["production"], ends_at=FUTURE, reason="  "
            )

    def test_elevate_requires_an_environment(self) -> None:
        with pytest.raises(ValueError, match="at least one environment"):
            BreakGlassLedger().elevate(
                agent_id="a", environments=[], ends_at=FUTURE, reason="x"
            )

    def test_manual_revert_is_audited(self) -> None:
        ledger = BreakGlassLedger()
        window = ledger.elevate(
            agent_id="a", environments=["production"], ends_at=FUTURE, reason="x"
        )
        ledger.revert(window.break_glass_id, at=PAST)
        assert ledger.events[-1]["kind"] == "revert"
        assert ledger.active_window("a", "production") is None

    def test_save_load(self, tmp_path: Path) -> None:
        ledger = BreakGlassLedger()
        window = ledger.elevate(
            agent_id="a", environments=["production"], ends_at=FUTURE, reason="r"
        )
        path = tmp_path / "bg.json"
        ledger.save(path)
        reloaded = BreakGlassLedger.load(path)
        assert reloaded.windows[window.break_glass_id].reason == "r"

    def test_elevate_requires_an_agent(self) -> None:
        with pytest.raises(ValueError, match="agent_id"):
            BreakGlassLedger().elevate(
                agent_id="  ", environments=["production"], ends_at=FUTURE, reason="x"
            )

    def test_default_and_explicit_ttl(self) -> None:
        ledger = BreakGlassLedger()
        explicit = ledger.elevate(
            agent_id="a", environments=["production"], reason="x", ttl_seconds=60
        )
        assert explicit.ends_at > explicit.starts_at
        defaulted = ledger.elevate(agent_id="b", environments=["staging"], reason="y")
        assert defaulted.ends_at > defaulted.starts_at

    def test_load_missing_file_is_empty(self, tmp_path: Path) -> None:
        assert BreakGlassLedger.load(tmp_path / "nope.json").windows == {}

    def test_save_load_preserves_revert(self, tmp_path: Path) -> None:
        ledger = BreakGlassLedger()
        ledger.elevate(agent_id="a", environments=["production"], ends_at=PAST, reason="x")
        ledger.sweep()
        path = tmp_path / "bg.json"
        ledger.save(path)
        reloaded = BreakGlassLedger.load(path)
        # The reverted id is reconstructed, so a re-sweep does not double-log it.
        assert reloaded.sweep() == []


class TestAutoRevert:
    def test_expired_window_is_inactive_and_reverts_on_read(self) -> None:
        ledger = BreakGlassLedger()
        ledger.elevate(agent_id="a", environments=["production"], ends_at=PAST, reason="x")
        assert ledger.active_window("a", "production") is None
        # auto-revert logged without any manual action
        assert ledger.events[-1]["kind"] == "revert"

    def test_sweep_returns_reverted_ids(self) -> None:
        ledger = BreakGlassLedger()
        window = ledger.elevate(
            agent_id="a", environments=["production"], ends_at=_ago(5), reason="x"
        )
        assert ledger.sweep() == [window.break_glass_id]

    def test_live_window_survives_sweep(self) -> None:
        ledger = BreakGlassLedger()
        ledger.elevate(agent_id="a", environments=["production"], ends_at=_ahead(60), reason="x")
        assert ledger.sweep() == []
        assert ledger.active_window("a", "production") is not None


class TestEngineBreakGlass:
    def _policy(self):
        base = default_policy("balanced")
        return replace(
            base,
            agents={
                **base.agents,
                "scoped-bot": AgentProfile("ci-bot", 0.1, environments=("staging",)),
            },
        )

    def _engine(self, *, elevate: bool) -> Engine:
        ledger = BreakGlassLedger()
        if elevate:
            ledger.elevate(
                agent_id="scoped-bot", environments=["production"], ends_at=FUTURE,
                reason="incident",
            )
        return Engine(self._policy(), break_glass_ledger=ledger)

    def test_scope_deny_without_a_window(self) -> None:
        decision = self._engine(elevate=False).evaluate(
            tool_name="query_logs", action="read", environment="production",
            data_class="internal", agent_id="scoped-bot",
        )
        assert decision.decision == "deny"
        assert decision.reason_code == DENY_OUT_OF_SCOPE
        assert decision.break_glass_id is None

    def test_scope_ceiling_widened_by_a_window(self) -> None:
        decision = self._engine(elevate=True).evaluate(
            tool_name="query_logs", action="read", environment="production",
            data_class="internal", agent_id="scoped-bot",
        )
        assert decision.decision == "allow"
        assert decision.break_glass_id is not None

    def test_break_glass_id_stamped_on_every_decision(self) -> None:
        # A destructive action is still denied, but the window is recorded.
        decision = self._engine(elevate=True).evaluate(
            tool_name="drop_database", action="delete", environment="production",
            data_class="customer_pii", agent_id="scoped-bot",
        )
        assert decision.decision == "deny"
        assert decision.break_glass_id is not None

    def test_other_agent_not_elevated(self) -> None:
        decision = self._engine(elevate=True).evaluate(
            tool_name="query_logs", action="read", environment="production",
            data_class="internal", agent_id="someone-else",
        )
        assert decision.break_glass_id is None


class TestBreakGlassCli:
    def test_elevate_list_revert(self, tmp_path: Path, capsys) -> None:
        store = str(tmp_path / "bg.json")
        assert main([
            "breakglass", "elevate", "--agent", "scoped-bot", "--env", "production",
            "--until", FUTURE, "--reason", "incident", "--store", store,
        ]) == 0
        bg_id = json.loads(capsys.readouterr().out)["break_glass_id"]
        assert main(["breakglass", "list", "--store", store, "--json"]) == 0
        assert json.loads(capsys.readouterr().out)
        assert main(["breakglass", "revert", bg_id, "--store", store]) == 0

    def test_revert_unknown_fails(self, tmp_path: Path, capsys) -> None:
        assert main(["breakglass", "revert", "bg_nope", "--store", str(tmp_path / "b.json")]) == 1
        assert capsys.readouterr().err

    def test_elevate_without_reason_fails(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit):
            main([
                "breakglass", "elevate", "--agent", "a", "--env", "production",
                "--until", FUTURE, "--store", str(tmp_path / "b.json"),
            ])

    def test_list_plain_and_empty(self, tmp_path: Path, capsys) -> None:
        store = str(tmp_path / "b.json")
        main([
            "breakglass", "elevate", "--agent", "a", "--env", "production",
            "--until", FUTURE, "--reason", "x", "--store", store,
        ])
        capsys.readouterr()
        assert main(["breakglass", "list", "--store", store]) == 0
        assert "production" in capsys.readouterr().out
        assert main(["breakglass", "list", "--store", str(tmp_path / "empty.json")]) == 0
        assert "No declared elevations" in capsys.readouterr().out

    def test_elevate_blank_reason_fails_via_cli(self, tmp_path: Path, capsys) -> None:
        assert main([
            "breakglass", "elevate", "--agent", "a", "--env", "production",
            "--until", FUTURE, "--reason", "   ", "--store", str(tmp_path / "b.json"),
        ]) == 1
        assert capsys.readouterr().err
