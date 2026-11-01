"""M2 Cedar decision core — five-outcome acceptance matrix, model, and gates.

WBS M2: ``2.1`` evaluator · ``2.2`` five-outcome shaper · ``2.3`` mandatory
human-gate class · ``2.4`` decision model. CUJ-1.
"""

from __future__ import annotations

import pytest

from agentpolicy.cedar import OUTCOMES, CedarEvaluator, Decision, Factor, gates
from agentpolicy.cedar import policy as policy_mod
from agentpolicy.cedar.shaper import ShaperContext, shape
from agentpolicy.types import NormalizedCall


def _call(
    tool: str = "query_logs",
    action: str = "read",
    environment: str = "staging",
    data_class: str = "internal",
    tool_category: str = "search",
    action_class: str = "read",
    agent_id: str = "debug-bot",
    agent_class: str = "general",
) -> NormalizedCall:
    return NormalizedCall(
        tool=tool,
        tool_category=tool_category,
        action=action,
        action_class=action_class,  # type: ignore[arg-type]
        environment=environment,
        data_class=data_class,
        agent_id=agent_id,
        agent_class=agent_class,
    )


# The acceptance matrix (tool x env x action x data-class) -> the five outcomes.
_MATRIX = [
    ("allow", "allow_low_risk", _call()),
    (
        "deny",
        "irreversible_action",
        _call("drop_database", "delete", "production", "customer_pii", "db", "delete"),
    ),
    (
        "ask",
        "human_gate_required",
        _call("deploy_service", "write", "production", "restricted", "cloud", "write"),
    ),
    (
        "redact",
        "secret_detected",
        _call("read_secrets", "read", "production", "restricted", "secrets", "read"),
    ),
]


class TestFiveOutcomeMatrix:
    @pytest.fixture
    def evaluator(self) -> CedarEvaluator:
        return CedarEvaluator()

    @pytest.mark.parametrize("outcome,reason,call", _MATRIX)
    def test_outcome_and_reason(
        self, evaluator: CedarEvaluator, outcome: str, reason: str, call: NormalizedCall
    ) -> None:
        decision = evaluator.evaluate(call)
        assert decision.decision == outcome
        assert decision.reason_code == reason

    def test_rate_limit_outcome(self, evaluator: CedarEvaluator) -> None:
        decision = evaluator.evaluate(_call(), budget_exhausted=True, retry_after=30)
        assert decision.decision == "rate-limit"
        assert decision.reason_code == "budget_exhausted"
        assert decision.retry_after == 30

    def test_all_five_outcomes_are_demonstrable(self, evaluator: CedarEvaluator) -> None:
        seen = {evaluator.evaluate(call).decision for _, _, call in _MATRIX}
        seen.add(evaluator.evaluate(_call(), budget_exhausted=True).decision)
        assert seen == set(OUTCOMES)


class TestDeterminism:
    def test_same_input_same_decision(self) -> None:
        evaluator = CedarEvaluator()
        call = _call("drop_database", "delete", "production", "customer_pii", "db", "delete")
        assert evaluator.evaluate(call).to_dict() == evaluator.evaluate(call).to_dict()

    def test_authorize_matches_shaper_allow(self) -> None:
        evaluator = CedarEvaluator()
        assert evaluator.authorize(_call()) is True
        destructive = _call("drop_database", "delete", "production", "customer_pii")
        assert evaluator.authorize(destructive) is False


class TestHumanGateClass:
    def test_irreversible_production_is_gate(self) -> None:
        assert gates.is_human_gate(_call("deploy_service", "write", "production")) is True

    def test_destructive_is_not_gate(self) -> None:
        assert gates.is_human_gate(_call("drop_database", "delete", "production")) is False

    def test_gate_does_not_apply_outside_production(self) -> None:
        assert gates.is_human_gate(_call("deploy_service", "write", "staging")) is False

    def test_amendment_record_is_reasoned(self) -> None:
        record = gates.amendment_record(action="add", added=frozenset({"rotate"}))
        assert record["kind"] == "gate_class_amendment"
        assert record["added"] == ["rotate"]
        assert "at" in record and "verb_set" in record


class TestDecisionModel:
    def test_to_dict_prd15_shape(self) -> None:
        decision = CedarEvaluator().evaluate(_call())
        payload = decision.to_dict()
        assert set(payload) >= {
            "decision",
            "reason_code",
            "criticality",
            "explanation",
            "factors",
            "policy_version",
            "matched_rule",
        }

    def test_rate_limit_and_redact_extras(self) -> None:
        evaluator = CedarEvaluator()
        assert "retry_after" in evaluator.evaluate(_call(), budget_exhausted=True).to_dict()
        redact = evaluator.evaluate(_call("read_secrets", "read", "production", "restricted"))
        assert "redactions" in redact.to_dict()

    def test_unknown_outcome_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown outcome"):
            Decision(decision="maybe", reason_code="x", criticality="low", explanation="e")  # type: ignore[arg-type]

    def test_blank_reason_code_rejected(self) -> None:
        with pytest.raises(ValueError, match="reason_code"):
            Decision(decision="allow", reason_code=" ", criticality="low", explanation="e")

    def test_explanation_artifact(self) -> None:
        decision = CedarEvaluator().evaluate(_call())
        artifact = decision.explanation_artifact().to_dict()
        assert artifact["matched_rule"] is None
        assert artifact["factors"]

    def test_factor_requires_unit_interval(self) -> None:
        with pytest.raises(ValueError):
            Factor("d", "v", 2.0)


class TestFailClosed:
    def test_malformed_policy_fails_at_construction(self) -> None:
        with pytest.raises(ValueError, match="invalid Cedar policy"):
            CedarEvaluator("permit(principal, action")

    def test_no_permit_is_deny(self) -> None:
        # A policy that permits nothing → allow-nothing is a deny (fail closed).
        evaluator = CedarEvaluator("forbid(principal, action, resource);")
        assert evaluator.evaluate(_call()).decision == "deny"

    def test_shape_helper_denies_on_no_cedar_allow(self) -> None:
        decision = shape(cedar_allowed=False, call=_call(), ctx=ShaperContext())
        assert decision.decision == "deny"
        assert decision.reason_code == "default_deny"

    def test_policy_module_exposes_base_policy(self) -> None:
        assert "permit" in policy_mod.BASE_POLICY and "forbid" in policy_mod.BASE_POLICY
