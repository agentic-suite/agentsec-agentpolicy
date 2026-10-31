"""M16 — enrollment/probation & approval analytics.

WBS M16: ``16.1`` enrollment ledger + probation · ``16.2`` probation pack ·
``16.3`` approval analytics · ``16.4`` agentwatch inventory link. CUJ-22, CUJ-23.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from agentpolicy.agentwatch import CLASSIFICATION_EVENT, classification_event
from agentpolicy.approvals import analyze_approvals
from agentpolicy.audit.models import AuditEntry
from agentpolicy.cli import main
from agentpolicy.engine.engine import Engine
from agentpolicy.engine.escalation import EscalationManager
from agentpolicy.engine.normalize import normalize
from agentpolicy.enrollment import EnrollmentLedger, EnrollmentStatus
from agentpolicy.pack_format import run_pack_dir, validate_pack_dir
from agentpolicy.policy.models import default_policy

REPO = Path(__file__).resolve().parent.parent
PACK = REPO / "packs/enrollment-probation"


def _call(tool="deploy_service", action="write", env="production", data="internal"):
    return normalize(
        tool=tool, action=action, environment=env, data_class=data,
        agent_id="new-agent", agent_class="general",
    )


class TestEnrollmentLedger:
    def test_first_seen_is_probation_and_logged(self) -> None:
        ledger = EnrollmentLedger()
        record = ledger.observe("new-agent", agent_class="general")
        assert record.status == EnrollmentStatus.PROBATION
        assert ledger.is_probation("new-agent")
        assert ledger.events[0]["kind"] == "probation"

    def test_observe_is_idempotent(self) -> None:
        ledger = EnrollmentLedger()
        ledger.observe("a")
        ledger.observe("a")
        assert len(ledger.events) == 1

    def test_classify_is_logged(self) -> None:
        ledger = EnrollmentLedger()
        ledger.observe("a")
        record = ledger.classify("a", EnrollmentStatus.ENROLLED, by="alice")
        assert record.status == EnrollmentStatus.ENROLLED
        assert record.classified_by == "alice"
        assert ledger.events[-1]["kind"] == "classification"

    def test_classify_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown agent"):
            EnrollmentLedger().classify("ghost", EnrollmentStatus.ENROLLED, by="alice")

    def test_classify_blank_or_probation_raises(self) -> None:
        ledger = EnrollmentLedger()
        ledger.observe("a")
        with pytest.raises(ValueError, match="classifier"):
            ledger.classify("a", EnrollmentStatus.ENROLLED, by="  ")
        with pytest.raises(ValueError, match="ENROLLED or BLOCKED"):
            ledger.classify("a", EnrollmentStatus.PROBATION, by="alice")

    def test_save_load(self, tmp_path: Path) -> None:
        ledger = EnrollmentLedger()
        ledger.observe("a")
        ledger.classify("a", EnrollmentStatus.BLOCKED, by="bob")
        path = tmp_path / "enroll.json"
        ledger.save(path)
        reloaded = EnrollmentLedger.load(path)
        assert reloaded.get("a").status == EnrollmentStatus.BLOCKED  # type: ignore[union-attr]


class TestEngineProbation:
    def _engine(self) -> Engine:
        return Engine(default_policy("balanced"), enrollment=EnrollmentLedger())

    def test_first_write_escalates_with_agent_probation(self) -> None:
        decision = self._engine().evaluate(
            tool_name="deploy_service", action="write", environment="production",
            data_class="internal", agent_id="new-agent",
        )
        assert decision.decision == "escalate"
        assert decision.reason_code == "agent_probation"

    def test_read_proceeds_and_observes(self) -> None:
        engine = self._engine()
        decision = engine.evaluate(
            tool_name="query_logs", action="read", environment="staging",
            data_class="internal", agent_id="reader",
        )
        assert decision.decision == "allow"
        assert engine.enrollment_ledger is not None
        assert engine.enrollment_ledger.is_probation("reader")

    def test_enrolled_agent_is_not_gated(self) -> None:
        engine = self._engine()
        assert engine.enrollment_ledger is not None
        engine.enrollment_ledger.observe("known")
        engine.enrollment_ledger.classify("known", EnrollmentStatus.ENROLLED, by="alice")
        decision = engine.evaluate(
            tool_name="deploy_service", action="write", environment="production",
            data_class="internal", agent_id="known",
        )
        assert decision.reason_code != "agent_probation"


class TestClassificationEvent:
    def test_event_shape(self) -> None:
        event = classification_event("a", "enrolled", agent_class="ci-bot")
        assert event["event_type"] == CLASSIFICATION_EVENT
        assert event["schema"] == "agentwatch.security_event.v1"
        assert event["principal"]["agent_id"] == "a"
        assert event["status"] == "enrolled"
        assert event["event_id"].startswith("evt_")


class TestApprovalAnalytics:
    def test_rate_latency_and_rubber_stamp(self) -> None:
        manager = EscalationManager(ttl_seconds=3600)
        t0 = datetime(2026, 1, 1, tzinfo=UTC)
        # Three rapid approvals on the same gate → rubber stamp.
        for _ in range(3):
            esc = manager.create(_call(), now=t0)
            manager.approve(esc.escalation_id, approver="alice", now=t0 + timedelta(seconds=20))
        denied = manager.create(_call(tool="drop_database"), now=t0)
        manager.deny(
            denied.escalation_id, approver="bob", reason="no",
            now=t0 + timedelta(seconds=40),
        )

        report = analyze_approvals(list(manager.records.values()))
        assert report.total == 4
        assert report.approved == 3 and report.denied == 1
        assert report.approval_rate == 0.75
        assert report.mean_latency_seconds == 25.0
        assert "deploy_service" in report.rubber_stamp_gates
        assert "drop_database" not in report.rubber_stamp_gates

    def test_pending_and_expired_counted(self) -> None:
        manager = EscalationManager(ttl_seconds=1)
        t0 = datetime(2026, 1, 1, tzinfo=UTC)
        manager.create(_call(), now=t0)
        expired = manager.create(_call(tool="drop_database"), now=t0)
        # Resolving the second one after its TTL expires it (timeout = deny).
        manager.resolve(expired.escalation_id, call=_call(), now=t0 + timedelta(seconds=10))
        report = analyze_approvals(list(manager.records.values()))
        assert report.total == 2
        assert report.pending == 1
        assert report.expired == 1
        assert report.approval_rate == 0.0

    def test_shadow_delta(self) -> None:
        entries = [
            AuditEntry(session_id="s", timestamp="t", tool="x", tool_category=None,
                       action="delete", action_class="delete", environment="production",
                       data_class="customer_pii", agent_id="a", agent_class=None,
                       decision="deny", criticality="critical", reason_code="deny_critical_op",
                       explanation="", dry_run=True),
            AuditEntry(session_id="s", timestamp="t", tool="x", tool_category=None,
                       action="read", action_class="read", environment="staging",
                       data_class="internal", agent_id="a", agent_class=None,
                       decision="allow", criticality="low", reason_code="allow_low_risk",
                       explanation="", dry_run=False),
        ]
        report = analyze_approvals(audit_entries=entries)
        assert report.shadow_delta == 1.0

    def test_empty(self) -> None:
        report = analyze_approvals()
        assert report.total == 0 and report.approval_rate == 0.0
        assert report.mean_latency_seconds is None
        assert report.shadow_delta is None

    def test_cli_report_approvals_json(self, tmp_path: Path, capsys) -> None:
        assert main(["report", "approvals", "--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert "approval_rate" in payload and "rubber_stamp_gates" in payload

    def test_cli_report_still_works(self, capsys) -> None:
        assert main(["report"]) == 0


class TestProbationPack:
    def test_pack_validates_and_replays(self) -> None:
        assert validate_pack_dir(PACK) == []
        results = {r.name: r for r in run_pack_dir(PACK)}
        assert all(r.passed for r in results.values())
        assert results["probation-write-gated"].got == "deny"
        assert results["enrolled-read-allowed"].got == "allow"


class TestEdges:
    def test_is_probation_unknown_false(self) -> None:
        assert EnrollmentLedger().is_probation("ghost") is False

    def test_load_missing_is_empty(self, tmp_path: Path) -> None:
        assert EnrollmentLedger.load(tmp_path / "nope.json").records == {}

    def test_classification_event_at(self) -> None:
        event = classification_event("a", "blocked", at="2026-01-01T00:00:00+00:00")
        assert event["timestamp"] == "2026-01-01T00:00:00+00:00"

    def test_analytics_to_dict_and_no_latency(self) -> None:
        from agentpolicy.ask import Ask, AskStatus

        ask = Ask(
            ask_id="ask_1", status=AskStatus.APPROVED, tool="t", action="read",
            agent_id="x", environment="staging", data_class="internal",
            action_identity="i", reason="", created_at="2026-01-01T00:00:00+00:00",
            expires_at="2999-01-01T00:00:00+00:00", resolved_at=None,
        )
        report = analyze_approvals(asks=[ask])
        assert report.approved == 1
        assert report.mean_latency_seconds is None
        assert "rubber_stamp_gates" in report.to_dict()

    def test_report_approvals_text(self, capsys) -> None:
        assert main(["report", "approvals"]) == 0
        assert "Approval analytics" in capsys.readouterr().out
