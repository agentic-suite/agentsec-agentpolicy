"""M21 — narrow-only policy layering.

WBS M21: ``21.1`` layered composition · ``21.2`` narrow-only invariant.
CUJ-30 (R44).
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from agentpolicy.cli import main
from agentpolicy.engine.engine import Engine
from agentpolicy.layering import Layer, compose, narrow_only_violations
from agentpolicy.policy.models import Rule, default_policy


def _org():
    return default_policy("balanced")


class TestCompose:
    def test_effective_policy_is_the_intersection(self) -> None:
        org = _org()
        project = replace(
            org,
            rules=(Rule("deny", tool="*", action="write", environment="staging", reason="proj"),),
        )
        effective = compose([Layer("org", org), Layer("project", project)])
        engine = Engine(effective)
        # the org already escalated prod writes; the project's staging deny also applies
        prod = engine.evaluate(
            tool_name="deploy_service", action="write", environment="production",
            data_class="internal", agent_id="bot",
        )
        staging = engine.evaluate(
            tool_name="deploy_service", action="write", environment="staging",
            data_class="internal", agent_id="bot",
        )
        assert prod.decision == "escalate"
        assert staging.decision == "deny"

    def test_compose_requires_a_layer(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="at least one layer"):
            compose([])

    def test_compose_is_deterministic(self) -> None:
        org = _org()
        project = replace(
            org, rules=(Rule("deny", tool="*", action="write", environment="staging"),)
        )
        a = compose([Layer("org", org), Layer("project", project)])
        b = compose([Layer("org", org), Layer("project", project)])
        assert a.rules == b.rules


class TestNarrowOnly:
    def test_child_deny_is_not_a_violation(self) -> None:
        org = _org()
        child = replace(
            org, rules=(Rule("deny", tool="*", action="write", environment="staging"),)
        )
        assert narrow_only_violations(org, child) == []

    def test_child_allow_not_backed_by_parent_is_a_violation(self) -> None:
        org = _org()
        child = replace(
            org,
            rules=(Rule("allow", tool="deploy_service", action="write", environment="production"),),
        )
        violations = narrow_only_violations(org, child)
        assert len(violations) == 1
        assert "rules[0]" in violations[0]

    def test_child_allow_backed_by_parent_is_ok(self) -> None:
        parent = replace(
            _org(),
            rules=(Rule("allow", tool="deploy_service", action="write", environment="production"),),
        )
        child = replace(
            parent,
            rules=(
                Rule("allow", tool="deploy_service", action="write", environment="production",
                     data_class="internal"),
            ),
        )
        assert narrow_only_violations(parent, child) == []


class TestCheckParentCli:
    def _write(self, tmp_path: Path, name: str, rules_yaml: str) -> str:
        path = tmp_path / name
        path.write_text(
            'version: "1.0.0"\nposture: balanced\nrules:\n' + rules_yaml, encoding="utf-8"
        )
        return str(path)

    def test_widening_overlay_fails_check(self, tmp_path: Path, capsys) -> None:
        parent = self._write(
            tmp_path, "org.yaml",
            "- decision: deny\n  tool: '*'\n  action: write\n  environment: staging\n"
            "  data_class: '*'\n  reason: org floor\n",
        )
        child = self._write(
            tmp_path, "project.yaml",
            "- decision: allow\n  tool: '*'\n  action: write\n  environment: production\n"
            "  data_class: '*'\n  reason: widening\n",
        )
        assert main(["check", child, "--parent", parent]) == 2
        assert "rules[0]" in capsys.readouterr().err

    def test_narrowing_overlay_passes_check(self, tmp_path: Path, capsys) -> None:
        parent = self._write(
            tmp_path, "org.yaml",
            "- decision: deny\n  tool: '*'\n  action: write\n  environment: staging\n"
            "  data_class: '*'\n  reason: org floor\n",
        )
        child = self._write(
            tmp_path, "project.yaml",
            "- decision: deny\n  tool: '*'\n  action: write\n  environment: production\n"
            "  data_class: '*'\n  reason: stricter\n",
        )
        assert main(["check", child, "--parent", parent]) == 0
        assert "ok:" in capsys.readouterr().out
