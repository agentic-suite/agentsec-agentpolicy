"""M22 — allow-justification (matched rule on every outcome).

WBS M22: ``22.3`` allow-justification. CUJ-33 (R47).
"""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from agentpolicy.approvals import analyze_approvals
from agentpolicy.audit.models import AuditEntry
from agentpolicy.canonical import canonicalize
from agentpolicy.engine.engine import Engine
from agentpolicy.policy.models import Rule, default_policy


def _allow_policy():
    base = default_policy("balanced")
    return replace(
        base,
        rules=(
            Rule(
                decision="allow", tool="deploy_service", action="write",
                environment="production", reason="explicit allow",
            ),
        ),
    )


class TestAllowJustification:
    def test_explicit_allow_names_its_permitting_rule(self) -> None:
        policy = _allow_policy()
        decision = Engine(policy).evaluate(
            tool_name="deploy_service", action="write", environment="production",
            data_class="internal", agent_id="release-bot",
        )
        assert decision.decision == "allow"
        assert decision.matched_rule == "rule[0]"
        assert decision.clause == "rule[0]"
        assert decision.policy_version == policy.version

    def test_deny_names_its_rule(self) -> None:
        base = default_policy("balanced")
        policy = replace(
            base,
            rules=(Rule(decision="deny", tool="drop_database", action="delete",
                        environment="production", reason="no"),),
        )
        decision = Engine(policy).evaluate(
            tool_name="drop_database", action="delete", environment="production",
            data_class="customer_pii", agent_id="bot",
        )
        assert decision.decision == "deny"
        assert decision.matched_rule == "rule[0]"

    def test_band_decision_clause_is_the_reason_code(self) -> None:
        decision = Engine(default_policy("balanced")).evaluate(
            tool_name="query_logs", action="read", environment="staging",
            data_class="internal", agent_id="bot",
        )
        assert decision.matched_rule is None
        assert decision.clause == decision.reason_code

    def test_audit_entry_names_the_permitting_rule_and_version(self) -> None:
        policy = _allow_policy()
        engine = Engine(policy)
        decision = engine.evaluate(
            tool_name="deploy_service", action="write", environment="production",
            data_class="internal", agent_id="release-bot",
        )
        call = canonicalize(
            tool="deploy_service", action="write", environment="production",
            data_class="internal", agent_id="release-bot",
        )
        entry = AuditEntry.from_decision(decision, call)
        assert entry.decision == "allow"
        assert entry.matched_rule == "rule[0]"
        assert entry.policy_version == policy.version


class TestAllowSideAnalytics:
    def test_always_allowed_patterns_flagged(self) -> None:
        entries = [
            SimpleNamespace(decision="allow", matched_rule="rule[0]", reason_code="allow_low_risk",
                            dry_run=False)
            for _ in range(5)
        ]
        report = analyze_approvals(audit_entries=entries)
        assert "rule[0]" in report.always_allowed_patterns

    def test_mixed_pattern_not_flagged(self) -> None:
        entries = [
            SimpleNamespace(decision="allow", matched_rule="rule[0]", reason_code="allow_low_risk",
                            dry_run=False),
            SimpleNamespace(decision="deny", matched_rule="rule[0]", reason_code="policy_match",
                            dry_run=False),
        ]
        report = analyze_approvals(audit_entries=entries)
        assert "rule[0]" not in report.always_allowed_patterns
