"""M5 — explain-decision, reason-code registry, actionability, event emitter.

WBS M5: ``5.1`` explain artifact · ``5.2`` reason-code registry · ``5.3``
actionability · ``5.4`` ``agentpolicy explain`` · ``5.5`` event emitter.
CUJ-3, R5, R6.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentpolicy import reason_codes
from agentpolicy.agentwatch import event_args_hash, event_for, to_event
from agentpolicy.canonical import canonicalize
from agentpolicy.cedar import CedarEvaluator
from agentpolicy.cli import main
from agentpolicy.explain import (
    ExplainArtifact,
    build_artifact,
    flip_variant,
    suggested_change,
)

#: The levers a suggested change may name (closed vocabulary — a human can name
#: the change from the text alone).
LEVERS = ("read-only", "non-production", "staging", "data class", "approval", "retry")

#: Calls that must always explain themselves: one per gated outcome.
_GATED = {
    "deny": dict(
        tool="drop_database", action="delete", environment="production",
        data_class="customer_pii", agent_id="release-bot",
    ),
    "ask": dict(
        tool="deploy_service", action="write", environment="production",
        data_class="restricted", agent_id="release-bot",
    ),
    "rate-limit": dict(
        tool="query_logs", action="read", environment="staging",
        data_class="internal", agent_id="debug-bot",
    ),
    "redact": dict(
        tool="read_secrets", action="read", environment="production",
        data_class="restricted", agent_id="release-bot",
    ),
}


def _call(**kwargs):
    return canonicalize(**kwargs)


class TestReasonCodeRegistry:
    def test_registry_is_closed_and_unique(self) -> None:
        codes = [rc.code for rc in reason_codes.REASON_CODES.values()]
        assert len(codes) == len(set(codes))
        assert reason_codes.CODES == frozenset(codes)

    @pytest.mark.parametrize(
        "code",
        [
            "allow_low_risk",
            "default_deny",
            "irreversible_action",
            "human_gate_required",
            "budget_exhausted",
            "secret_detected",
        ],
    )
    def test_every_emitted_code_is_registered(self, code: str) -> None:
        assert reason_codes.is_known(code)
        assert reason_codes.require(code).meaning

    def test_require_rejects_unknown_code(self) -> None:
        with pytest.raises(KeyError, match="unknown reason_code"):
            reason_codes.require("definitely_not_a_code")

    def test_alertable_subset(self) -> None:
        alertable = reason_codes.alertable_codes()
        assert "default_deny" in alertable
        assert "irreversible_action" in alertable
        assert "allow_low_risk" not in alertable

    def test_cedar_path_codes_are_all_registered(self) -> None:
        evaluator = CedarEvaluator()
        for outcome, kwargs in _GATED.items():
            kw = dict(kwargs)
            if outcome == "rate-limit":
                decision = evaluator.evaluate(_call(**kw), budget_exhausted=True)
            else:
                decision = evaluator.evaluate(_call(**kw))
            assert decision.decision == outcome, outcome
            assert reason_codes.is_known(decision.reason_code), decision.reason_code


class TestExplainArtifact:
    def _evaluator(self) -> CedarEvaluator:
        return CedarEvaluator()

    @pytest.mark.parametrize("outcome", list(_GATED))
    def test_every_gated_decision_names_a_clause(self, outcome: str) -> None:
        evaluator = self._evaluator()
        kwargs = _GATED[outcome]
        call = _call(**kwargs)
        decision = (
            evaluator.evaluate(call, budget_exhausted=True)
            if outcome == "rate-limit"
            else evaluator.evaluate(call)
        )
        artifact = build_artifact(decision, call, evaluator=evaluator)
        assert artifact.decision == outcome
        assert artifact.clause, f"{outcome} has no clause"
        assert artifact.suggested_change

    def test_deny_matched_rule_is_the_cedar_clause(self) -> None:
        evaluator = self._evaluator()
        call = _call(**_GATED["deny"])
        artifact = build_artifact(evaluator.evaluate(call), call, evaluator=evaluator)
        assert artifact.matched_rule is not None
        assert artifact.matched_rule.startswith("forbid-destructive")
        assert artifact.clause == artifact.matched_rule

    def test_default_deny_falls_back_to_the_class(self) -> None:
        evaluator = self._evaluator()
        # A read on production has no permit → default_deny (no matched rule).
        call = _call(
            tool="query_logs", action="read", environment="production",
            data_class="internal", agent_id="bot",
        )
        artifact = build_artifact(evaluator.evaluate(call), call, evaluator=evaluator)
        assert artifact.decision == "deny"
        assert artifact.matched_rule is None
        assert artifact.clause == "default_deny"

    def test_artifact_to_dict_shape(self) -> None:
        evaluator = self._evaluator()
        call = _call(**_GATED["deny"])
        payload = build_artifact(evaluator.evaluate(call), call, evaluator=evaluator).to_dict()
        assert set(payload) >= {
            "decision",
            "reason_code",
            "criticality",
            "explanation",
            "factors",
            "matched_rule",
            "clause",
            "suggested_change",
            "policy_version",
            "policy_hash",
            "event_id",
        }
        assert payload["policy_hash"].startswith("sha256:")


class TestActionability:
    def _evaluator(self) -> CedarEvaluator:
        return CedarEvaluator()

    def test_deny_suggests_a_read_only_alternative(self) -> None:
        evaluator = self._evaluator()
        call = _call(**_GATED["deny"])
        decision = evaluator.evaluate(call)
        text = suggested_change(decision, call, evaluator)
        assert any(lever in text.lower() for lever in LEVERS)

    def test_applying_the_flip_changes_the_outcome(self) -> None:
        evaluator = self._evaluator()
        call = _call(**_GATED["deny"])
        decision = evaluator.evaluate(call)
        variant = flip_variant(decision, call, evaluator)
        assert variant is not None
        assert evaluator.evaluate(variant).decision != decision.decision

    def test_ask_suggests_approval(self) -> None:
        evaluator = self._evaluator()
        call = _call(**_GATED["ask"])
        decision = evaluator.evaluate(call)
        assert "approval" in suggested_change(decision, call, evaluator).lower()

    def test_rate_limit_suggests_retry(self) -> None:
        evaluator = self._evaluator()
        call = _call(**_GATED["rate-limit"])
        decision = evaluator.evaluate(call, budget_exhausted=True, retry_after=30)
        text = suggested_change(decision, call, evaluator)
        assert "retry" in text.lower() or "wait" in text.lower()

    def test_every_suggestion_uses_the_closed_vocabulary(self) -> None:
        evaluator = self._evaluator()
        for outcome, kwargs in _GATED.items():
            call = _call(**kwargs)
            decision = (
                evaluator.evaluate(call, budget_exhausted=True)
                if outcome == "rate-limit"
                else evaluator.evaluate(call)
            )
            text = suggested_change(decision, call, evaluator)
            assert text
            if outcome == "redact":
                # The action already proceeds (scrubbed); nothing needs to change.
                assert "scrub" in text.lower()
            else:
                assert any(lever in text.lower() for lever in LEVERS), (outcome, text)

    def test_allow_has_no_suggested_change(self) -> None:
        evaluator = self._evaluator()
        call = _call(
            tool="query_logs", action="read", environment="staging",
            data_class="internal", agent_id="debug-bot",
        )
        assert suggested_change(evaluator.evaluate(call), call, evaluator) is None


class TestEventEmitter:
    def test_event_shape_and_join_key(self) -> None:
        evaluator = CedarEvaluator()
        call = _call(**_GATED["deny"])
        artifact = build_artifact(evaluator.evaluate(call), call, evaluator=evaluator)
        event = event_for(artifact, call, session_id="sess_1")
        assert event["schema"] == "agentwatch.security_event.v1"
        assert event["event_type"] == "policy.decision"
        assert event["event_id"] == artifact.event_id
        assert event["decision_id"] == artifact.decision_id
        assert event["decision"] == "deny"
        assert event["reason_code"] == "irreversible_action"
        assert event["matched_rule"].startswith("forbid-destructive")
        assert event["policy_version"] == artifact.policy_version
        assert event["policy_hash"] == artifact.policy_hash
        assert event["session_id"] == "sess_1"

    def test_to_event_defaults_and_args_hash(self) -> None:
        evaluator = CedarEvaluator()
        call = _call(**_GATED["ask"])
        call = _call(
            tool="deploy_service", action="write", environment="production",
            data_class="restricted", agent_id="release-bot",
            arguments={"target": "prod", "token": "abc"},
        )
        decision = evaluator.evaluate(call)
        event = to_event(
            decision, call, event_id="evt_x", decision_id="dec_x",
            timestamp="2026-10-26T18:03:00Z",
        )
        assert event["event_id"] == "evt_x" and event["decision_id"] == "dec_x"
        assert event["action"]["args_hash"] == event_args_hash(call.arguments)
        assert event["timestamp"] == "2026-10-26T18:03:00Z"
        assert event["principal"]["agent_id"] == "release-bot"
        assert event["resource"]["environment"] == "production"
        assert event["policy_hash"] == decision.policy_hash

    def test_no_arguments_has_null_args_hash(self) -> None:
        assert event_args_hash(None) is None
        assert event_args_hash({}) is None

    def test_blank_join_key_is_a_bug(self) -> None:
        evaluator = CedarEvaluator()
        call = _call(**_GATED["ask"])
        with pytest.raises(ValueError, match="event_id"):
            to_event(evaluator.evaluate(call), call, event_id="", decision_id="dec_x")


class TestExplainCli:
    def test_explain_offline_prints_breakdown(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main([
            "explain", "--tool", "drop_database", "--action", "delete",
            "--env", "production", "--data", "customer_pii", "--agent", "release-bot",
        ]) == 0
        out = capsys.readouterr().out
        assert "DENY" in out
        assert "irreversible_action" in out
        assert "factor" in out.lower()
        assert "forbid-destructive" in out

    def test_explain_json_emits_the_artifact(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main([
            "explain", "--tool", "query_logs", "--action", "read",
            "--env", "staging", "--data", "internal", "--agent", "debug-bot", "--json",
        ]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["decision"] == "allow"
        assert payload["reason_code"] == "allow_low_risk"
        assert "clause" in payload

    def test_explain_unknown_tool_fails_loudly(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main([
            "explain", "--tool", "made_up_tool", "--action", "read",
            "--env", "staging", "--data", "internal", "--agent", "x",
        ]) == 1
        assert capsys.readouterr().err


def test_explain_artifact_exported_from_package() -> None:
    # The public facade is importable from the documented module.
    assert ExplainArtifact.__name__ == "ExplainArtifact"


def test_reference_doc_links_codes() -> None:
    doc = (Path(__file__).resolve().parent.parent / "docs/reference/reason-codes.md")
    assert doc.exists()
