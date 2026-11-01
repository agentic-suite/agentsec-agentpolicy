"""M17 — nearest-permissible-action & multi-agent governance.

WBS M17: ``17.1`` permitted_alternatives · ``17.2`` delegation chain/scope-subset
· ``17.3`` inter-agent decisions · ``17.4`` multi-agent-delegation pack.
CUJ-24, CUJ-28 (R37, R39, R25).
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from agentpolicy.canonical import canonicalize
from agentpolicy.cedar import CedarEvaluator
from agentpolicy.engine.delegation import DelegationManager
from agentpolicy.engine.engine import Engine
from agentpolicy.errors import ALLOW_DELEGATION, DENY_DELEGATION_EXCEEDS_SCOPE
from agentpolicy.explain import build_artifact, permitted_alternatives
from agentpolicy.pack_format import run_pack_dir, validate_pack_dir
from agentpolicy.policy.models import AgentProfile, default_policy

REPO = Path(__file__).resolve().parent.parent
PACK = REPO / "packs/multi-agent-delegation"

_PERMITTED = {"allow", "redact", "ask"}


class TestPermittedAlternatives:
    def _deny(self):
        evaluator = CedarEvaluator()
        call = canonicalize(
            tool="drop_database", action="delete", environment="production",
            data_class="customer_pii", agent_id="release-bot",
        )
        return evaluator, call, evaluator.evaluate(call)

    def test_alternatives_are_verified_permissible(self) -> None:
        evaluator, call, decision = self._deny()
        alternatives = permitted_alternatives(decision, call, evaluator)
        assert alternatives
        for alt in alternatives:
            assert alt["outcome"] in _PERMITTED
            # each is evaluated-true: re-evaluate the alternative shape
            variant = canonicalize(
                tool=call.tool, action=alt["action"], environment=alt["environment"],
                data_class=alt["data_class"], agent_id=call.agent_id,
            )
            assert evaluator.evaluate(variant).decision in _PERMITTED

    def test_alternatives_leak_no_policy_internals(self) -> None:
        evaluator, call, decision = self._deny()
        for alt in permitted_alternatives(decision, call, evaluator):
            assert set(alt) == {"action", "environment", "data_class", "outcome", "description"}
            assert "rule" not in alt["description"].lower()

    def test_allow_has_no_alternatives(self) -> None:
        evaluator = CedarEvaluator()
        call = canonicalize(
            tool="query_logs", action="read", environment="staging",
            data_class="internal", agent_id="debug-bot",
        )
        assert permitted_alternatives(evaluator.evaluate(call), call, evaluator) == []

    def test_artifact_carries_alternatives(self) -> None:
        evaluator, call, decision = self._deny()
        payload = build_artifact(decision, call, evaluator=evaluator).to_dict()
        assert payload["permitted_alternatives"]
        assert payload["permitted_alternatives"][0]["outcome"] in _PERMITTED


class TestDelegationScope:
    def _policy(self):
        base = default_policy("balanced")
        return replace(
            base,
            agents={
                **base.agents,
                "parent": AgentProfile("ci-bot", 0.1, environments=("staging",)),
            },
        )

    def test_effective_environments_none_for_unknown(self) -> None:
        assert DelegationManager().effective_environments("ghost", self._policy()) is None

    def test_child_out_of_scope_denied_naming_chain(self) -> None:
        engine = Engine(self._policy())
        result = engine.delegate("child", "parent", environments=("staging",))
        assert result.allowed
        decision = engine.evaluate(
            tool_name="query_logs", action="read", environment="production",
            data_class="internal", agent_id="child",
        )
        assert decision.decision == "deny"
        assert decision.reason_code == DENY_DELEGATION_EXCEEDS_SCOPE
        assert "parent" in decision.explanation  # the chain link is named

    def test_child_in_scope_allowed(self) -> None:
        engine = Engine(self._policy())
        engine.delegate("child", "parent", environments=("staging",))
        decision = engine.evaluate(
            tool_name="query_logs", action="read", environment="staging",
            data_class="internal", agent_id="child",
        )
        assert decision.decision == "allow"

    def test_non_delegated_agent_unconstrained(self) -> None:
        engine = Engine(self._policy())
        decision = engine.evaluate(
            tool_name="query_logs", action="read", environment="staging",
            data_class="internal", agent_id="random",
        )
        assert decision.decision == "allow"


class TestInterAgent:
    def _engine(self) -> Engine:
        base = default_policy("balanced")
        policy = replace(
            base,
            agents={
                **base.agents,
                "source": AgentProfile("ci-bot", 0.1, environments=("staging",)),
            },
        )
        return Engine(policy)

    def test_in_scope_child_allowed(self) -> None:
        decision = self._engine().inter_agent("source", "target", environments=("staging",))
        assert decision.decision == "allow"
        assert decision.reason_code == ALLOW_DELEGATION

    def test_out_of_scope_child_denied(self) -> None:
        decision = self._engine().inter_agent("source", "target", environments=("production",))
        assert decision.decision == "deny"
        assert decision.reason_code == DENY_DELEGATION_EXCEEDS_SCOPE


class TestDelegationPack:
    def test_pack_validates_and_replays(self) -> None:
        assert validate_pack_dir(PACK) == []
        results = {r.name: r for r in run_pack_dir(PACK)}
        assert all(r.passed for r in results.values())
        assert results["delegated-child-prod-write-denied"].got == "deny"
        assert results["non-delegated-staging-read-allowed"].got == "allow"
