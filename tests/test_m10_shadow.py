"""M10 — shadow mode, calibration report, canary rollout.

WBS M10: ``10.1`` shadow mode · ``10.2`` ``audit query --dry-run`` ·
``10.3`` calibration report · ``10.4`` canary rollout. CUJ-4 (R30).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentpolicy.audit.logger import AuditLogger
from agentpolicy.audit.models import AuditEntry
from agentpolicy.audit.sinks.jsonl import JsonlSink
from agentpolicy.calibration import calibrate
from agentpolicy.canary import STAGES, CanaryConfig, canary_selected
from agentpolicy.cli import main
from agentpolicy.engine.engine import Engine
from agentpolicy.policy.models import default_policy


def _entry(**overrides) -> AuditEntry:
    values: dict[str, object] = dict(
        session_id="s1", timestamp="2026-01-01T00:00:00", tool="t1",
        tool_category=None, action="read", action_class="read",
        environment="staging", data_class="public", agent_id="a1",
        agent_class=None, decision="allow", criticality="low",
        reason_code="allow_low_risk", explanation="ok",
    )
    values.update(overrides)
    return AuditEntry(**values)  # type: ignore[arg-type]


class TestCanary:
    def test_deterministic(self) -> None:
        assert canary_selected("sess_a", 50) == canary_selected("sess_a", 50)
        assert canary_selected("sess_a", 0) is False
        assert canary_selected("sess_a", 100) is True

    def test_rejects_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="canary percent"):
            canary_selected("s", 101)
        with pytest.raises(ValueError):
            CanaryConfig(200)

    def test_half_cohort_is_roughly_half(self) -> None:
        ids = [f"sess_{i}" for i in range(2000)]
        selected = sum(canary_selected(i, 50) for i in ids)
        assert 950 <= selected <= 1050  # deterministic hash → tight band

    def test_config_enforces_missing_session_only_at_full(self) -> None:
        assert CanaryConfig(50).enforces(None) is False
        assert CanaryConfig(100).enforces(None) is True

    def test_stages(self) -> None:
        assert STAGES == (5, 50, 100)


def _session(in_cohort: bool, percent: int = 50) -> str:
    for i in range(500):
        candidate = f"agent-{i}"
        if canary_selected(candidate, percent) is in_cohort:
            return candidate
    raise AssertionError("no candidate found")


class TestEngineCanary:
    def _engine(self, tmp_path: Path, percent: int) -> Engine:
        return Engine(
            default_policy("balanced"),
            audit_logger=AuditLogger(JsonlSink(tmp_path / "audit.jsonl")),
            canary_percent=percent,
        )

    def test_selected_session_is_enforced(self, tmp_path: Path) -> None:
        engine = self._engine(tmp_path, 50)
        decision = engine.evaluate(
            tool_name="drop_database", action="delete", environment="production",
            data_class="customer_pii", agent_id=_session(in_cohort=True),
        )
        assert decision.decision == "deny"
        assert decision.dry_run is False

    def test_unselected_session_is_shadowed(self, tmp_path: Path) -> None:
        engine = self._engine(tmp_path, 50)
        decision = engine.evaluate(
            tool_name="drop_database", action="delete", environment="production",
            data_class="customer_pii", agent_id=_session(in_cohort=False),
        )
        assert decision.decision == "allow"
        assert decision.dry_run is True

    def test_full_canary_enforces_and_zero_is_off(self, tmp_path: Path) -> None:
        engine = self._engine(tmp_path, 100)
        decision = engine.evaluate(
            tool_name="drop_database", action="delete", environment="production",
            data_class="customer_pii", agent_id="whoever",
        )
        assert decision.decision == "deny"
        assert self._engine(tmp_path, 0).canary_percent == 0


class TestCalibration:
    def test_rates(self) -> None:
        entries = [
            _entry(dry_run=True, decision="deny", counterfactual=0.4),   # false-block cand
            _entry(dry_run=True, decision="deny", counterfactual=0.9),   # not near
            _entry(dry_run=True, decision="allow", counterfactual=0.8),  # false-miss cand
            _entry(dry_run=True, decision="allow", counterfactual=0.1),  # fine
            _entry(dry_run=False, decision="deny"),                      # not shadow
        ]
        report = calibrate(entries)
        assert report.total == 5
        assert report.shadow == 4
        assert report.would_block == 2
        assert report.false_block == 1
        assert report.false_block_rate == 0.5
        assert report.allowed == 2
        assert report.false_miss == 1
        assert report.false_miss_rate == 0.5
        assert report.threshold_table["0.4"] == 1

    def test_empty_is_zero(self) -> None:
        report = calibrate([])
        assert report.false_block_rate == 0.0
        assert report.false_miss_rate == 0.0

    def test_cli_report_json_smoke(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["calibrate", "report", "--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert "false_block_rate" in payload


class TestAuditDryRunQuery:
    def test_query_dry_run_filters_shadow(self, tmp_path: Path, capsys) -> None:
        path = tmp_path / "audit.jsonl"
        sink = JsonlSink(path)
        sink.write(_entry(decision="deny", dry_run=True))
        sink.write(_entry(decision="deny", dry_run=False))
        assert main(["audit", "query", "--path", str(path), "--dry-run"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert len(payload) == 1
        assert payload[0]["dry_run"] is True
