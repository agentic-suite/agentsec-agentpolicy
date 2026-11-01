"""Tests for ``agentpolicy doctor`` — self-observability (WBS M1 1.5)."""

from __future__ import annotations

import argparse
import json

from agentpolicy.cli import doctor, main


class TestDoctor:
    def test_healthy_environment_exits_zero(self, tmp_path, monkeypatch, capsys) -> None:
        monkeypatch.setenv("HOME", str(tmp_path))
        assert main(["doctor"]) == 0
        assert "verdict: healthy" in capsys.readouterr().out

    def test_json_output_shape(self, tmp_path, monkeypatch, capsys) -> None:
        monkeypatch.setenv("HOME", str(tmp_path))
        assert main(["doctor", "--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["ok"] is True
        names = {c["name"] for c in payload["checks"]}
        assert {"python", "policy", "engine", "audit_sink"} <= names

    def test_bad_policy_reports_unhealthy(self, tmp_path, monkeypatch, capsys) -> None:
        monkeypatch.setenv("HOME", str(tmp_path))
        bad = tmp_path / "bad.yaml"
        bad.write_text("version: [1, 2\n", encoding="utf-8")
        assert main(["doctor", "--policy", str(bad)]) == 1
        assert "FAIL" in capsys.readouterr().out

    def test_audit_sink_failure_reported(self, monkeypatch, capsys) -> None:
        monkeypatch.setenv("HOME", "/proc/nonexistent-agentpolicy")
        assert main(["doctor"]) == 1
        out = capsys.readouterr().out
        assert "audit_sink" in out and "FAIL" in out

    def test_add_parser_registers_doctor(self) -> None:
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        doctor.add_parser(sub)
        ns = parser.parse_args(["doctor", "--json"])
        assert ns.func is doctor._run
