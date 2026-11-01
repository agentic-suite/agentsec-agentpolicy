"""M18 — dual-control (quorum) approvals & the break-glass composition guard.

WBS M18: ``18.3`` dual-control approvals · ``18.4`` composition guard.
CUJ-26 (R41).
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from agentpolicy.breakglass import BreakGlassLedger
from agentpolicy.canonical import canonicalize
from agentpolicy.dualcontrol import DualControlGate
from agentpolicy.engine.engine import Engine
from agentpolicy.freeze import FreezeLedger
from agentpolicy.policy.models import AgentProfile, Rule, default_policy

FUTURE = "2999-01-01T00:00:00+00:00"


def _call(**overrides):
    kwargs = dict(
        tool="deploy_service", action="write", environment="production",
        data_class="internal", agent_id="release-bot",
    )
    kwargs.update(overrides)
    return canonicalize(**kwargs)


class TestDualControlGate:
    def test_one_approval_does_not_release(self) -> None:
        gate = DualControlGate(quorum=2)
        rec = gate.request(_call())
        after = gate.approve(rec.dual_control_id, approver="alice")
        assert after.status == "pending"
        assert not gate.released(rec.dual_control_id)

    def test_two_distinct_approvers_release(self) -> None:
        gate = DualControlGate(quorum=2)
        rec = gate.request(_call())
        gate.approve(rec.dual_control_id, approver="alice")
        after = gate.approve(rec.dual_control_id, approver="bob")
        assert after.status == "released"
        assert gate.released(rec.dual_control_id)
        assert after.approvers == ("alice", "bob")

    def test_same_approver_rejected(self) -> None:
        gate = DualControlGate(quorum=2)
        rec = gate.request(_call())
        gate.approve(rec.dual_control_id, approver="alice")
        with pytest.raises(ValueError, match="distinct"):
            gate.approve(rec.dual_control_id, approver="alice")

    def test_resolve_requires_release_and_matching_identity(self) -> None:
        gate = DualControlGate(quorum=2)
        call = _call()
        rec = gate.request(call)
        gate.approve(rec.dual_control_id, approver="alice")
        pending = gate.resolve(rec.dual_control_id, call=call)
        assert pending["status"] == "deny"
        assert pending["reason_code"] == "deny_dual_control_pending"
        gate.approve(rec.dual_control_id, approver="bob")
        released = gate.resolve(rec.dual_control_id, call=call)
        assert released["status"] == "allow"
        assert released["reason_code"] == "allow_dual_control_approved"
        mismatch = gate.resolve(rec.dual_control_id, call=_call(action="send"))
        assert mismatch["status"] == "deny"
        assert mismatch["reason_code"] == "deny_action_identity_mismatch"

    def test_unknown_record_denies(self) -> None:
        result = DualControlGate().resolve("dc_nope", call=_call())
        assert result["status"] == "deny"
        assert result["reason_code"] == "deny_dual_control_unknown"

    def test_quorum_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="quorum"):
            DualControlGate(quorum=0)

    def test_approve_expired_is_rejected(self) -> None:
        gate = DualControlGate(quorum=2, ttl_seconds=0)
        rec = gate.request(_call())
        with pytest.raises(ValueError, match="expired"):
            gate.approve(rec.dual_control_id, approver="alice")

    def test_record_and_records_view(self) -> None:
        gate = DualControlGate(quorum=2)
        rec = gate.request(_call())
        assert rec.to_dict()["status"] == "pending"
        assert gate.records[rec.dual_control_id].quorum == 2

    def test_approve_unknown_record(self) -> None:
        with pytest.raises(ValueError, match="unknown"):
            DualControlGate().approve("dc_nope", approver="alice")

    def test_approve_blank_approver(self) -> None:
        gate = DualControlGate()
        rec = gate.request(_call())
        with pytest.raises(ValueError, match="non-blank"):
            gate.approve(rec.dual_control_id, approver="  ")

    def test_approve_after_release_is_rejected(self) -> None:
        gate = DualControlGate(quorum=1)
        rec = gate.request(_call())
        gate.approve(rec.dual_control_id, approver="alice")
        with pytest.raises(ValueError, match="already"):
            gate.approve(rec.dual_control_id, approver="bob")

    def test_save_load_round_trip(self, tmp_path) -> None:
        gate = DualControlGate(quorum=2)
        rec = gate.request(_call(), escalation_id="esc_1")
        gate.approve(rec.dual_control_id, approver="alice")
        path = tmp_path / "dc.json"
        gate.save(path)
        reloaded = DualControlGate.load(path)
        assert reloaded.records[rec.dual_control_id].approvers == ("alice",)
        assert reloaded.quorum == 2

    def test_load_missing_file_is_empty(self, tmp_path) -> None:
        assert DualControlGate.load(tmp_path / "nope.json").records == {}

    def test_load_skips_blank_and_malformed_lines(self, tmp_path) -> None:
        path = tmp_path / "dc.json"
        path.write_text("not json", encoding="utf-8")
        assert DualControlGate.load(path).records == {}

    def test_expiry_denies(self) -> None:
        gate = DualControlGate(quorum=2, ttl_seconds=0)
        rec = gate.request(_call())
        result = gate.resolve(rec.dual_control_id, call=_call())
        assert result["status"] == "deny"


class TestEngineDualControl:
    def _engine(self, *, gate: DualControlGate | None, freeze=None, breakglass=None) -> Engine:
        return Engine(
            default_policy("balanced"),
            freeze_ledger=freeze,
            break_glass_ledger=breakglass,
            dual_control_gate=gate,
        )

    def test_escalated_gate_class_carries_dual_control_id(self) -> None:
        freeze = FreezeLedger()
        freeze.declare(environments=["production"], ends_at=FUTURE, reason="release")
        engine = self._engine(gate=DualControlGate(quorum=2), freeze=freeze)
        decision = engine.evaluate(
            tool_name="deploy_service", action="write", environment="production",
            data_class="internal", agent_id="release-bot",
        )
        assert decision.decision == "escalate"
        assert decision.dual_control_id is not None

    def test_non_gate_escalation_has_no_dual_control(self) -> None:
        freeze = FreezeLedger()
        freeze.declare(environments=["staging"], ends_at=FUTURE, reason="release")
        engine = self._engine(gate=DualControlGate(quorum=2), freeze=freeze)
        decision = engine.evaluate(
            tool_name="deploy_service", action="write", environment="staging",
            data_class="internal", agent_id="release-bot",
        )
        assert decision.decision == "escalate"
        assert decision.dual_control_id is None

    def test_engine_exposes_its_governance_stores(self) -> None:
        engine = self._engine(
            gate=DualControlGate(), freeze=FreezeLedger(), breakglass=BreakGlassLedger()
        )
        assert engine.freeze_ledger is not None
        assert engine.break_glass_ledger is not None
        assert engine.dual_control_gate is not None
        assert engine.obligation_store is not None

    def test_composition_guard_breakglass_still_requires_quorum(self) -> None:
        base = default_policy("balanced")
        policy = replace(
            base,
            agents={
                **base.agents,
                "scoped-bot": AgentProfile("ci-bot", 0.1, environments=("staging",)),
            },
        )
        ledger = BreakGlassLedger()
        ledger.elevate(
            agent_id="scoped-bot", environments=["production"], ends_at=FUTURE, reason="incident"
        )
        gate = DualControlGate(quorum=2)
        engine = Engine(policy, break_glass_ledger=ledger, dual_control_gate=gate)
        decision = engine.evaluate(
            tool_name="deploy_service", action="write", environment="production",
            data_class="internal", agent_id="scoped-bot",
        )
        # break-glass widened the scope ceiling, but the human gate still applies
        assert decision.decision == "escalate"
        assert decision.break_glass_id is not None
        assert decision.dual_control_id is not None
        # and the quorum is genuinely required
        one = gate.resolve(decision.dual_control_id, call=_call(agent_id="scoped-bot"))
        assert one["status"] == "deny"

    def test_gate_floor_converts_an_allowed_gate_call(self) -> None:
        # An explicitly-allowed production write is otherwise permitted; inside a
        # break-glass window the mandatory human gate floors it to escalate.
        base = default_policy("balanced")
        policy = replace(
            base,
            rules=(
                Rule(
                    decision="allow", tool="deploy_service", action="write",
                    environment="production", reason="explicit allow",
                ),
                *base.rules,
            ),
        )
        ledger = BreakGlassLedger()
        ledger.elevate(
            agent_id="release-bot", environments=["production"], ends_at=FUTURE, reason="incident"
        )
        engine = Engine(
            policy, break_glass_ledger=ledger, dual_control_gate=DualControlGate(quorum=2),
        )
        decision = engine.evaluate(
            tool_name="deploy_service", action="write", environment="production",
            data_class="internal", agent_id="release-bot",
        )
        assert decision.decision == "escalate"
        assert decision.reason_code == "human_gate_required"
        assert decision.dual_control_id is not None
