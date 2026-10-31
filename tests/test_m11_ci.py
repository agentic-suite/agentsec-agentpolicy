"""M11 — golden regression, agentdrill gate, fail-closed fuzz, coverage export.

WBS M11: ``11.1`` goldens · ``11.2`` agentdrill · ``11.3`` fail-closed fuzz ·
``11.4`` coverage export. CUJ-7, CUJ-9 (R22, R8, R32).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from agentpolicy import agentdrill, compliance, goldens
from agentpolicy.cli import main
from agentpolicy.engine.engine import Engine
from agentpolicy.engine.fail_closed import deny
from agentpolicy.errors import (
    AgentPolicyError,
    MalformedInputError,
    OpaUnavailableError,
    PolicyParseError,
    UnknownToolError,
)
from agentpolicy.policy.models import default_policy
from agentpolicy.types import Decision

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests/fixtures/acceptance_matrix.yaml"
PACKS = REPO / "packs"
LAUNCH_PACKS = ("destructive-commands", "secret-in-output", "mcp-allowlist")


class TestGoldens:
    def test_load_cases(self) -> None:
        cases = goldens.load_cases(FIXTURES)
        assert len(cases) >= 30
        assert all(c.tool and c.action for c in cases)

    def test_capture_and_no_drift_on_same_state(self) -> None:
        cases = goldens.load_cases(FIXTURES)
        baseline = goldens.capture(cases)
        result = goldens.detect_flips(baseline, cases)
        assert result.findings == ()
        assert result.passed is True

    def test_flip_is_detected_and_fails(self) -> None:
        cases = goldens.load_cases(FIXTURES)
        baseline = goldens.capture(cases)
        # Force a deny→allow flip by pretending a currently-allowed case was denied.
        name = next(
            n for n, v in baseline.items() if v["decision"] == "allow"
        )
        baseline[name] = {"decision": "deny", "reason_code": "deny_critical_op"}
        result = goldens.detect_flips(baseline, cases)
        assert result.passed is False
        assert result.flips and result.flips[0].kind == "flip"

    def test_baseline_round_trip(self, tmp_path: Path) -> None:
        cases = goldens.load_cases(FIXTURES)
        baseline = goldens.capture(cases)
        path = tmp_path / "baseline.json"
        path.write_text(goldens.dump_baseline(baseline))
        assert goldens.load_baseline(path) == baseline

    def test_cli_goldens_capture_and_check(self, tmp_path: Path, capsys) -> None:
        assert main(["goldens", "check", "--fixtures", str(FIXTURES)]) == 0
        baseline = json.loads(capsys.readouterr().out)
        path = tmp_path / "baseline.json"
        path.write_text(json.dumps(baseline))
        assert main([
            "goldens", "check", "--fixtures", str(FIXTURES), "--baseline", str(path),
        ]) == 0


class TestAgentdrill:
    @pytest.mark.parametrize("name", LAUNCH_PACKS)
    def test_launch_pack_replay_still_blocks(self, name: str) -> None:
        results = agentdrill.drill_pack(PACKS / name)
        assert results and all(r.passed for r in results)

    def test_unblocked_property(self) -> None:
        assert agentdrill.DrillResult("p", "n", "deny", "allow").unblocked is True
        assert agentdrill.DrillResult("p", "n", "deny", "deny").unblocked is False
        assert agentdrill.DrillResult("p", "n", "allow", "allow").unblocked is False

    def test_gate_passes_for_launch_packs(self) -> None:
        assert agentdrill.gate([PACKS / name for name in LAUNCH_PACKS]) == ()

    def test_cli_drill_check(self, capsys) -> None:
        assert main(["drill", "check", "--packs-dir", str(PACKS)]) == 0
        assert "block their replays" in capsys.readouterr().out


class TestCompliance:
    def test_shipped_domains_nonempty(self) -> None:
        assert compliance.shipped_domains(PACKS)

    def test_matrix_covers_controls(self) -> None:
        matrix = compliance.coverage_matrix(PACKS)
        assert set(matrix["frameworks"]) == {"OWASP-ASI", "OWASP-LLM", "ATLAS"}
        for bucket in matrix["frameworks"].values():
            assert bucket["total"] == len(bucket["controls"])
            assert 0 <= bucket["covered"] <= bucket["total"]

    def test_export_shape(self) -> None:
        artifact = compliance.export_matrix()
        assert artifact["schema"] == "agentcomply.coverage.v1"
        assert artifact["target"] == "agentcomply"
        assert artifact["covered_domains"]

    def test_cli_compliance_export(self, capsys) -> None:
        assert main(["compliance", "export"]) == 0
        assert json.loads(capsys.readouterr().out)["schema"] == "agentcomply.coverage.v1"


class TestFailClosedFuzz:
    @given(
        tool=st.text(max_size=40),
        action=st.text(max_size=40),
        environment=st.text(max_size=20),
        data_class=st.text(max_size=20),
        agent_id=st.text(max_size=40),
    )
    def test_random_input_never_raises_and_returns_a_decision(
        self, tool: str, action: str, environment: str, data_class: str, agent_id: str
    ) -> None:
        decision = Engine(default_policy("balanced")).evaluate(
            tool_name=tool, action=action, environment=environment,
            data_class=data_class, agent_id=agent_id,
        )
        assert isinstance(decision, Decision)

    @given(payload=st.binary(max_size=64))
    def test_binary_like_tool_never_allows(self, payload: bytes) -> None:
        # A non-text tool name must canonicalize/deny, never allow.
        decision = Engine(default_policy("balanced")).evaluate(
            tool_name=payload.decode("latin-1"), action="delete",
            environment="production", data_class="customer_pii", agent_id="x",
        )
        assert decision.decision == "deny"

    def test_destructive_production_pii_always_denied(self) -> None:
        decision = Engine(default_policy("balanced")).evaluate(
            tool_name="drop_database", action="delete", environment="production",
            data_class="customer_pii", agent_id="release-bot",
        )
        assert decision.decision == "deny"

    def test_failure_paths_have_distinct_reason_codes(self) -> None:
        paths = {
            UnknownToolError: "deny_unknown_tool",
            MalformedInputError: "deny_malformed_input",
            PolicyParseError: "deny_policy_parse_error",
            OpaUnavailableError: "deny_opa_backend_down",
        }
        codes = {exc.reason_code for exc in paths}
        assert len(codes) == len(paths)  # all distinct
        assert all(code for code in codes)
        # Each exception maps to its declared code through fail-closed deny.
        for exc, expected in paths.items():
            assert isinstance(exc(), AgentPolicyError)
            assert exc.reason_code == expected
        assert deny("deny_unknown_tool", "x").decision == "deny"


class TestCoverageEdges:
    def test_load_cases_list_and_named(self, tmp_path: Path) -> None:
        path = tmp_path / "f.yaml"
        path.write_text(
            "- {name: custom, tool: query_logs, action: read, environment: staging,"
            " data_class: internal, agent: bot, expected: allow}\n",
            encoding="utf-8",
        )
        cases = goldens.load_cases(path)
        assert cases[0].name == "custom"
        assert cases[0].expected_decision == "allow"

    def test_drift_kind(self) -> None:
        cases = goldens.load_cases(FIXTURES)
        baseline = goldens.capture(cases)
        name = next(n for n, v in baseline.items() if v["decision"] == "allow")
        baseline[name] = {"decision": "audit", "reason_code": "audit_sensitive_data"}
        result = goldens.detect_flips(baseline, cases)
        assert all(f.kind == "drift" for f in result.findings)
        assert result.passed is True

    def test_agentdrill_gate_reports_unblocked(self, monkeypatch) -> None:
        from agentpolicy.pack_format import PackTestResult

        monkeypatch.setattr(
            agentdrill, "run_pack_dir",
            lambda _p: [PackTestResult("replit", "deny", "allow", False)],
        )
        unblocked = agentdrill.gate([PACKS / "destructive-commands"])
        assert len(unblocked) == 1 and unblocked[0].unblocked

    def test_agentdrill_cli_json(self, capsys) -> None:
        assert main(["drill", "check", "--packs-dir", str(PACKS), "--json"]) == 0
        assert json.loads(capsys.readouterr().out) == []

    def test_shipped_domains_missing_dir(self, tmp_path: Path) -> None:
        assert compliance.shipped_domains(tmp_path / "nope") == set()

    def test_compliance_export_to_file(self, tmp_path: Path, capsys) -> None:
        out = tmp_path / "cov.json"
        assert main(["compliance", "export", "-o", str(out)]) == 0
        assert json.loads(out.read_text())["schema"] == "agentcomply.coverage.v1"

    def test_goldens_cli_json_flip(self, tmp_path: Path, capsys) -> None:
        cases = goldens.load_cases(FIXTURES)
        baseline = goldens.capture(cases)
        name = next(n for n, v in baseline.items() if v["decision"] == "allow")
        baseline[name] = {"decision": "deny", "reason_code": "deny_critical_op"}
        path = tmp_path / "b.json"
        path.write_text(json.dumps(baseline))
        assert main([
            "goldens", "check", "--fixtures", str(FIXTURES),
            "--baseline", str(path), "--json",
        ]) == 1
        assert json.loads(capsys.readouterr().out)
