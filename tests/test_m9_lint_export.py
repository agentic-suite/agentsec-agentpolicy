"""M9 — posture presets, init scaffold, diff, lint, export.

WBS M9: ``9.1`` presets · ``9.2`` init scaffold · ``9.3`` diff · ``9.4`` lint ·
``9.5`` export. CUJ-8, CUJ-16, CUJ-17 (R12, R16).
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from agentpolicy.cli import main
from agentpolicy.export import cedar_source, export_policy, render_export
from agentpolicy.lint import (
    LITERAL_SECRET,
    OUTCOME_CONFLICT,
    OVER_PERMISSIVE_ALLOW,
    UNKNOWN_TOOL_RULE,
    UNREACHABLE_RULE,
    lint_policy,
    lint_text,
)
from agentpolicy.policy.models import Rule, default_policy
from agentpolicy.policy.postures import render_preset

SECRET = "sk-proj-" + "A" * 40


def _policy(*rules: Rule):
    return replace(default_policy("balanced"), rules=tuple(rules))


class TestPresetsCommented:
    def test_render_preset_is_commented(self) -> None:
        text = render_preset("strict")
        assert text.startswith("#")
        assert "posture preset: strict" in text

    def test_commented_preset_still_loads_to_default(self) -> None:
        from agentpolicy.policy.loader import load_policy_text

        assert load_policy_text(render_preset("balanced")) == default_policy("balanced")


class TestLint:
    def test_over_permissive_allow(self) -> None:
        findings = lint_policy(_policy(Rule(decision="allow", reason="wide open")))
        assert OVER_PERMISSIVE_ALLOW in {f.code for f in findings}

    def test_shadowed_rule_is_unreachable(self) -> None:
        findings = lint_policy(
            _policy(
                Rule(decision="deny", action="*", reason="deny all"),
                Rule(decision="deny", action="read", reason="dead"),
            )
        )
        unreachable = [f for f in findings if f.code == UNREACHABLE_RULE]
        assert unreachable and unreachable[0].location == "rules[1]"

    def test_unknown_tool_rule(self) -> None:
        findings = lint_policy(_policy(Rule(decision="deny", tool="not_a_real_tool")))
        assert UNKNOWN_TOOL_RULE in {f.code for f in findings}

    def test_outcome_conflict(self) -> None:
        findings = lint_policy(
            _policy(
                Rule(decision="allow", action="read", reason="a"),
                Rule(decision="deny", action="read", reason="b"),
            )
        )
        assert OUTCOME_CONFLICT in {f.code for f in findings}

    def test_literal_secret_in_text(self) -> None:
        findings = lint_policy(default_policy("balanced"), text=f'reason: "{SECRET}"')
        assert LITERAL_SECRET in {f.code for f in findings}

    def test_clean_policy_has_no_findings(self) -> None:
        assert lint_policy(default_policy("balanced")) == []

    def test_lint_text_scans(self) -> None:
        assert lint_text(f'api_key: "{SECRET}"')[0].code == LITERAL_SECRET

    def test_finding_to_dict(self) -> None:
        finding = lint_text(SECRET)[0]
        payload = finding.to_dict()
        assert set(payload) == {"code", "severity", "message", "location"}

    def test_cli_lint_fails_on_findings(self, tmp_path: Path, capsys) -> None:
        path = tmp_path / "agentpolicy.yaml"
        path.write_text(
            'version: "1.0.0"\nposture: balanced\nrules:\n'
            '  - {decision: allow, tool: "*", action: "*", environment: "*",'
            ' data_class: "*", reason: wide}\n',
            encoding="utf-8",
        )
        assert main(["lint", str(path)]) == 1
        assert OVER_PERMISSIVE_ALLOW in capsys.readouterr().out

    def test_cli_lint_clean_exits_zero(self, tmp_path: Path, capsys) -> None:
        path = tmp_path / "agentpolicy.yaml"
        path.write_text(render_preset("balanced"), encoding="utf-8")
        assert main(["lint", str(path)]) == 0
        assert "no lint findings" in capsys.readouterr().out

    def test_cli_lint_json(self, tmp_path: Path, capsys) -> None:
        path = tmp_path / "agentpolicy.yaml"
        path.write_text(render_preset("strict"), encoding="utf-8")
        assert main(["lint", str(path), "--json"]) == 0
        assert json.loads(capsys.readouterr().out) == []


class TestDiff:
    def test_structured_diff_classifies(self) -> None:
        from agentpolicy.cli.diff import structured_diff

        org = replace(
            default_policy("balanced"),
            environments={**default_policy("balanced").environments, "production": 0.95},
            rules=default_policy("balanced").rules[:1],
        )
        diff = structured_diff(default_policy("balanced"), org)
        assert "production" in diff["overridden"]["environments"]
        assert diff["gaps"]["rules_removed"]

    def test_cli_diff_json(self, tmp_path: Path, capsys) -> None:
        path = tmp_path / "agentpolicy.yaml"
        path.write_text('version: "1.0.0"\nposture: balanced\n', encoding="utf-8")
        assert main(["diff", str(path), "--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["posture"] == "balanced"
        assert "kept" in payload and "gaps" in payload


class TestExport:
    def test_cedar_source_renders_rules(self) -> None:
        cedar = cedar_source(default_policy("balanced"))
        assert "forbid" in cedar and "permit" in cedar
        assert "@id(" in cedar
        assert "Deletes in production are blocked." in cedar

    def test_export_policyweave_artifact(self) -> None:
        artifact = export_policy(default_policy("balanced"))
        assert artifact["schema"] == "policyweave.policy.v1"
        assert artifact["policy_hash"].startswith("sha256:")
        assert artifact["rules"]

    def test_render_export_unknown_target(self) -> None:
        with pytest.raises(ValueError, match="unknown export target"):
            export_policy(default_policy("balanced"), target="nope")

    def test_cli_export_cedar(self, capsys) -> None:
        assert main(["export", "--format", "cedar"]) == 0
        assert "forbid (principal, action, resource)" in capsys.readouterr().out

    def test_cli_export_policyweave_writes_file(self, tmp_path: Path) -> None:
        out = tmp_path / "policy.json"
        assert main(["export", "--format", "policyweave", "-o", str(out)]) == 0
        assert json.loads(out.read_text())["schema"] == "policyweave.policy.v1"


class TestInitScaffold:
    def test_scaffold_writes_adapter_and_quickstart(self, tmp_path: Path) -> None:
        policy = tmp_path / "agentpolicy.yaml"
        scaffold = tmp_path / "scaffold"
        assert main([
            "init", "--posture", "balanced", "-o", str(policy),
            "--scaffold-dir", str(scaffold), "--adapter", "raw",
        ]) == 0
        assert policy.exists()
        assert (scaffold / "adapter.py").exists()
        assert "Quickstart" in (scaffold / "QUICKSTART.md").read_text()

    def test_adapter_without_scaffold_dir_fails(self, tmp_path: Path, capsys) -> None:
        assert main([
            "init", "-o", str(tmp_path / "p.yaml"), "--adapter", "raw",
        ]) == 1
        assert capsys.readouterr().err


class TestRenderHelpers:
    def test_render_export_cedar_is_text(self) -> None:
        assert render_export(default_policy("balanced"), target="cedar").startswith("//")
