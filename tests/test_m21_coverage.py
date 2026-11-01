"""M21 — action-space coverage report.

WBS M21: ``21.3`` coverage report (taxonomy x rules x fleet inventory).
CUJ-31 (R45).
"""

from __future__ import annotations

import json
from pathlib import Path

from agentpolicy.cli import main
from agentpolicy.coverage import CoverageReport, coverage_report, inventory_from_events
from agentpolicy.policy.models import default_policy


def _event(verb: str, tool: str = "run_tool") -> dict:
    return {
        "event_id": "evt_" + verb,
        "action": {"verb": verb, "tool": tool},
        "resource": {"environment": "staging", "data_class": "internal"},
        "principal": {"agent_id": "bot"},
    }


class TestCoverageReport:
    def test_four_quadrants(self) -> None:
        report = coverage_report(
            default_policy("balanced"), inventory={"delete": 2, "rotate": 3, "read": 1}
        )
        assert isinstance(report, CoverageReport)
        by_verb = {row.verb: row for row in report.rows}
        # delete is referenced by a balanced rule and was exercised
        assert by_verb["delete"].quadrant == "covered_exercised"
        # write is referenced by a rule but never exercised
        assert by_verb["write"].quadrant == "covered_never"
        # rotate is exercised but no rule mentions it
        assert by_verb["rotate"].quadrant == "uncovered_exercised"
        # a verb neither covered nor exercised
        assert by_verb["describe"].quadrant == "uncovered_never"

    def test_dangerous_quadrant_named_and_gap(self) -> None:
        report = coverage_report(
            default_policy("balanced"), inventory={"rotate": 3, "read": 1}
        )
        assert set(report.dangerous) == {"rotate", "read"}
        assert report.gap_unexplained == 2

    def test_out_of_scope_reduces_the_gap(self) -> None:
        report = coverage_report(
            default_policy("balanced"), inventory={"rotate": 3, "read": 1},
            out_of_scope=("read",),
        )
        assert report.dangerous == ("rotate",)
        assert report.gap_unexplained == 1

    def test_dead_rules_listed(self) -> None:
        report = coverage_report(default_policy("balanced"), inventory={})
        assert "write" in report.dead
        assert report.gap_unexplained == 0

    def test_inventory_from_events(self) -> None:
        counts = inventory_from_events([_event("rotate"), _event("rotate"), _event("read")])
        assert counts == {"rotate": 2, "read": 1}


class TestCoverageCli:
    def test_report_coverage_json(self, tmp_path: Path, capsys) -> None:
        inv = tmp_path / "inventory.jsonl"
        inv.write_text(
            "\n".join(json.dumps(_event(v)) for v in ("rotate", "read")), encoding="utf-8"
        )
        assert main(["report", "coverage", "--inventory", str(inv), "--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["gap_unexplained"] == 2
        assert "rotate" in payload["dangerous"]

    def test_report_coverage_plain_with_out_of_scope(self, tmp_path: Path, capsys) -> None:
        inv = tmp_path / "inventory.jsonl"
        inv.write_text(json.dumps(_event("rotate")), encoding="utf-8")
        assert main([
            "report", "coverage", "--inventory", str(inv), "--out-of-scope", "rotate",
        ]) == 0
        out = capsys.readouterr().out
        assert "gap:unexplained" in out
        assert "0" in out
