"""M20 — policy backtest & PR decision-diff (read-only, advisory).

WBS M20: ``20.1`` backtest engine · ``20.2`` PR decision-diff · ``20.3``
advisory + watermark. CUJ-29 (R43).
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from agentpolicy.backtest import (
    BacktestReport,
    backtest,
    call_from_event,
    classify_transition,
    load_history,
)
from agentpolicy.cli import main
from agentpolicy.policy.models import Rule, default_policy


def _event(event_id: str, tool: str, verb: str, env: str, data_class: str, ts: str) -> dict:
    return {
        "schema": "agentwatch.security_event.v1",
        "event_type": "policy.decision",
        "event_id": event_id,
        "decision_id": "dec-" + event_id,
        "principal": {"agent_id": "release-bot", "agent_class": "general"},
        "action": {"verb": verb, "tool": tool, "args_hash": None},
        "resource": {"tool_category": "cloud", "environment": env, "data_class": data_class},
        "decision": "allow",
        "reason_code": "allow_low_risk",
        "criticality": "low",
        "session_id": None,
        "timestamp": ts,
    }


def _history() -> list[dict]:
    return [
        _event("evt_1", "deploy_service", "write", "staging", "internal",
               "2026-10-20T00:00:00+00:00"),
        _event("evt_2", "query_logs", "read", "staging", "internal",
               "2026-10-21T00:00:00+00:00"),
    ]


def _candidate():
    base = default_policy("balanced")
    return replace(
        base,
        rules=(
            Rule(decision="deny", tool="*", action="write", environment="staging",
                 reason="candidate rule"),
            *base.rules,
        ),
    )


class TestClassifyTransition:
    def test_transitions(self) -> None:
        assert classify_transition("allow", "allow") == "unchanged"
        assert classify_transition("allow", "deny") == "newly_denied"
        assert classify_transition("allow", "ask") == "newly_asked"
        assert classify_transition("deny", "allow") == "newly_allowed"
        assert classify_transition("ask", "deny") == "newly_denied"
        assert classify_transition("deny", "ask") == "newly_asked"
        assert classify_transition("ask", "allow") == "newly_allowed"


class TestBacktest:
    def test_flip_set_is_exact(self) -> None:
        report = backtest(_history(), _candidate())
        assert isinstance(report, BacktestReport)
        assert report.total == 2
        assert len(report.newly_denied) == 1
        assert report.newly_denied[0].tool == "deploy_service"
        assert report.newly_asked == ()
        assert report.newly_allowed == ()
        assert report.unchanged == 1

    def test_reproducible(self) -> None:
        assert backtest(_history(), _candidate()).to_dict() == backtest(
            _history(), _candidate()
        ).to_dict()

    def test_read_only_no_fleet_events(self) -> None:
        def _boom(*_a: object, **_k: object) -> None:
            raise AssertionError("backtest emitted a fleet event")

        report = backtest(_history(), _candidate(), emit=_boom)
        assert report.advisory is True
        assert report.emits_events is False

    def test_watermark_and_golden_gate_exclusion(self) -> None:
        report = backtest(_history(), _candidate())
        assert report.watermark == "backtest"
        assert report.excluded_from_golden_gate is True

    def test_coverage_window_and_limits(self) -> None:
        report = backtest(_history(), _candidate())
        assert report.window_start == "2026-10-20T00:00:00+00:00"
        assert report.window_end == "2026-10-21T00:00:00+00:00"
        assert report.coverage_note

    def test_empty_history(self) -> None:
        report = backtest([], _candidate())
        assert report.total == 0
        assert report.newly_denied == ()

    def test_malformed_event_is_skipped(self) -> None:
        bad = {
            "event_id": "evt_bad",
            "principal": {"agent_id": "x"},
            "action": {"tool": "definitely-not-a-real-tool", "verb": "read"},
            "resource": {"environment": "staging", "data_class": "internal"},
        }
        report = backtest([bad], _candidate())
        assert report.total == 0

    def test_call_from_event_reconstructs_the_call(self) -> None:
        call = call_from_event(_history()[0])
        assert call.tool == "deploy_service"
        assert call.action == "write"
        assert call.environment == "staging"


class TestLoadHistory:
    def test_jsonl_round_trip(self, tmp_path: Path) -> None:
        path = tmp_path / "history.jsonl"
        path.write_text("\n".join(json.dumps(e) for e in _history()), encoding="utf-8")
        assert len(load_history(path)) == 2

    def test_blank_and_malformed_lines_skipped(self, tmp_path: Path) -> None:
        path = tmp_path / "history.jsonl"
        path.write_text(json.dumps(_history()[0]) + "\n\nnot-json\n", encoding="utf-8")
        assert len(load_history(path)) == 1

    def test_missing_file_is_empty(self, tmp_path: Path) -> None:
        assert load_history(tmp_path / "nope.jsonl") == []


class TestBacktestCli:
    def _files(self, tmp_path: Path) -> tuple[str, str]:
        hist = tmp_path / "history.jsonl"
        hist.write_text("\n".join(json.dumps(e) for e in _history()), encoding="utf-8")
        cand = tmp_path / "candidate.yaml"
        cand.write_text(
            'version: "1.0.0"\nposture: balanced\nrules:\n'
            "- decision: deny\n  tool: '*'\n  action: write\n  environment: staging\n"
            "  data_class: '*'\n  reason: candidate rule\n",
            encoding="utf-8",
        )
        return str(hist), str(cand)

    def test_ci_attaches_step_summary(self, tmp_path: Path, monkeypatch) -> None:
        hist, cand = self._files(tmp_path)
        summary = tmp_path / "summary.md"
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
        assert main(["backtest", "--history", hist, "--candidate", cand, "--ci"]) == 0
        text = summary.read_text(encoding="utf-8")
        assert "newly-denied" in text

    def test_plain_output(self, tmp_path: Path, capsys) -> None:
        hist, cand = self._files(tmp_path)
        assert main(["backtest", "--history", hist, "--candidate", cand]) == 0
        assert "newly-denied" in capsys.readouterr().out

    def test_json_output(self, tmp_path: Path, capsys) -> None:
        hist, cand = self._files(tmp_path)
        assert main(["backtest", "--history", hist, "--candidate", cand, "--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["watermark"] == "backtest"
        assert len(payload["newly_denied"]) == 1

    def test_bad_candidate_fails_the_cli(self, tmp_path: Path, capsys) -> None:
        hist, _ = self._files(tmp_path)
        args = ["backtest", "--history", hist, "--candidate", str(tmp_path / "nope.yaml")]
        assert main(args) == 1
        assert capsys.readouterr().err
