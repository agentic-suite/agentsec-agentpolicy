"""Coverage for ``agentpolicy field-test`` (agentpolicy.cli.field_test) — M0 ported tree.

The runner, replan sweep, and report builder are stubbed so the CLI's argument
handling, output branches, and exit codes are exercised deterministically.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from agentpolicy.cli import field_test as ft
from agentpolicy.cli.errors import CliError


class _FakeReport:
    def __init__(self, total: int = 3, failed: int = 0) -> None:
        self.total = total
        self.failed = failed

    @property
    def passed(self) -> int:
        return self.total - self.failed

    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 1.0

    def framework_pass_rates(self) -> dict[str, float]:
        return {"langgraph": 1.0}

    def failures(self) -> list[Any]:
        if not self.failed:
            return []
        return [
            SimpleNamespace(
                scenario=SimpleNamespace(id=f"scn-{i}"),
                agent=SimpleNamespace(agent_id=f"ag-{i}"),
                notes=f"note-{i}",
            )
            for i in range(self.failed)
        ]


class _FakeRunner:
    def __init__(self, report: _FakeReport, agents: list[Any] | None = None) -> None:
        self._report = report
        self._agents = agents if agents is not None else [
            SimpleNamespace(framework="langgraph"),
            SimpleNamespace(framework="crewai"),
        ]
        self.seen: dict[str, Any] = {}

    @classmethod
    def from_files(cls, scenarios: str, roster: str) -> _FakeRunner:
        if "missing" in scenarios:
            raise FileNotFoundError(scenarios)
        return cls(_FakeReport())

    def run(self, agents: Any = None, scenario_types: Any = None) -> _FakeReport:
        self.seen = {"agents": agents, "scenario_types": scenario_types}
        return self._report


def _args(**overrides: Any) -> argparse.Namespace:
    base: dict[str, Any] = {
        "replan": "off",
        "json": False,
        "verbose": False,
        "scenarios": "tests/field/scenarios.yaml",
        "roster": "tests/field/agents.yaml",
        "framework": None,
        "agents": "all",
        "matrix": "both",
        "report": "none",
    }
    base.update(overrides)
    return argparse.Namespace(**base)


@pytest.fixture
def stub_runner(monkeypatch: pytest.MonkeyPatch) -> dict[str, _FakeRunner]:
    holder: dict[str, _FakeRunner] = {}

    def _from_files(scenarios: str, roster: str) -> _FakeRunner:
        if "missing" in scenarios:
            raise FileNotFoundError(scenarios)
        runner = _FakeRunner(_FakeReport())
        holder["runner"] = runner
        return runner

    monkeypatch.setattr(ft.FieldTestRunner, "from_files", staticmethod(_from_files))
    monkeypatch.setattr("agentpolicy.field.report.build_report", lambda report: "# report")
    return holder


def _patch_runner(monkeypatch: pytest.MonkeyPatch, report: _FakeReport | None = None) -> None:
    runner_report = report or _FakeReport()
    monkeypatch.setattr(
        ft.FieldTestRunner,
        "from_files",
        staticmethod(lambda s, r: _FakeRunner(runner_report)),
    )


def test_all_pass_returns_zero(stub_runner: dict[str, _FakeRunner], capsys) -> None:
    assert ft._field_test(_args()) == 0
    out = capsys.readouterr().out
    assert "Total cases:" in out


def test_failures_return_one(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    _patch_runner(monkeypatch, _FakeReport(total=12, failed=11))
    monkeypatch.setattr("agentpolicy.field.report.build_report", lambda report: "# r")
    assert ft._field_test(_args(verbose=True)) == 1
    out = capsys.readouterr().out
    assert "more failures" in out


def test_json_output(stub_runner: dict[str, _FakeRunner], capsys) -> None:
    assert ft._field_test(_args(json=True)) == 0
    assert json.loads(capsys.readouterr().out)["total"] == 3


def test_report_written(tmp_path: Path, stub_runner: dict[str, _FakeRunner]) -> None:
    target = tmp_path / "out" / "report.md"
    assert ft._field_test(_args(report=str(target))) == 0
    assert target.read_text() == "# report"


def test_framework_filter_applies(stub_runner: dict[str, _FakeRunner]) -> None:
    assert ft._field_test(_args(framework="crewai")) == 0
    assert [a.framework for a in stub_runner["runner"]._agents] == ["crewai"]


def test_framework_filter_no_match_raises(stub_runner: dict[str, _FakeRunner]) -> None:
    with pytest.raises(CliError, match="no agents found"):
        ft._field_test(_args(framework="does-not-exist"))


def test_matrix_and_agent_selection(stub_runner: dict[str, _FakeRunner]) -> None:
    assert ft._field_test(_args(matrix="decision", agents="a,b")) == 0
    assert stub_runner["runner"].seen == {"agents": ["a", "b"], "scenario_types": ["decision"]}


def test_load_inputs_error_raises(stub_runner: dict[str, _FakeRunner]) -> None:
    with pytest.raises(CliError, match="failed to load field test inputs"):
        ft._field_test(_args(scenarios="missing.yaml"))


def _fake_sweep(passed: int, total: int) -> Any:
    results = [
        SimpleNamespace(
            passed=i < passed,
            agent_id=f"ag-{i}",
            denied="tool",
            denial_reason="reason",
            replacement="other",
            notes="",
        )
        for i in range(total)
    ]
    return SimpleNamespace(
        total=total,
        passed=passed,
        results=results,
        to_report=lambda: [{"i": i} for i in range(total)],
    )


def test_replan_scripted_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("agentpolicy.field.replan.run_replan_sweep", lambda live: _fake_sweep(2, 2))
    _patch_runner(monkeypatch)
    monkeypatch.setattr("agentpolicy.field.report.build_report", lambda report: "# r")
    assert ft._field_test(_args(replan="scripted", json=True)) == 0
    out = capsys.readouterr().out
    assert '"replan"' in out
    assert '"passed": 2' in out


def test_replan_scripted_text_and_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("agentpolicy.field.replan.run_replan_sweep", lambda live: _fake_sweep(1, 2))
    _patch_runner(monkeypatch)
    monkeypatch.setattr("agentpolicy.field.report.build_report", lambda report: "# r")
    assert ft._field_test(_args(replan="scripted")) == 1
    assert "Model replan sweep:" in capsys.readouterr().out


def test_add_parser_registers_field_test() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    ft.add_parser(sub)
    ns = parser.parse_args(["field-test", "--replan", "scripted", "--matrix", "decision"])
    assert ns.replan == "scripted"
    assert ns.matrix == "decision"
    assert ns.func is ft._field_test
