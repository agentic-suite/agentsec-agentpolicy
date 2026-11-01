"""Guard: automation must never clobber a hand-maintained field-test report.

The canonical ``docs/field-test/<version>/FIELD_TEST_REPORT.md`` is hand-edited;
a lossy automated rewrite destroyed its notes once. These tests lock the guard in
at three levels: the shared guard module, the ``build_report.py`` script, and the
``agentpolicy field-test`` CLI report writer.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

from agentpolicy.field.report_guard import (
    HAND_MAINTAINED_MARKER,
    is_hand_maintained,
    refuse_overwrite,
)

REPO = Path(__file__).resolve().parent.parent


def _load_build_report():
    spec = importlib.util.spec_from_file_location(
        "_build_report", REPO / "scripts" / "fieldtest" / "build_report.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestReportGuard:
    def test_missing_file_is_writable(self, tmp_path: Path) -> None:
        assert not is_hand_maintained(tmp_path / "nope.md")
        assert not refuse_overwrite(tmp_path / "nope.md")

    def test_marker_blocks_overwrite(self, tmp_path: Path) -> None:
        report = tmp_path / "FIELD_TEST_REPORT.md"
        report.write_text(f"<!-- {HAND_MAINTAINED_MARKER} -->\n# hand\n", encoding="utf-8")
        assert is_hand_maintained(report)
        assert refuse_overwrite(report)
        # explicit force is the only way through
        assert not refuse_overwrite(report, force=True)

    def test_plain_file_is_writable(self, tmp_path: Path) -> None:
        plain = tmp_path / "report.md"
        plain.write_text("# generated\n", encoding="utf-8")
        assert not refuse_overwrite(plain)


class TestBuildReportRefuses:
    def test_cannot_clobber_hand_maintained(self, tmp_path: Path, monkeypatch) -> None:
        mod = _load_build_report()
        report = tmp_path / "FIELD_TEST_REPORT.md"
        original = f"<!-- {HAND_MAINTAINED_MARKER} DOCUMENT -->\n# hand-authored\n"
        report.write_text(original, encoding="utf-8")
        generated = tmp_path / "FIELD_TEST_REPORT.generated.md"
        monkeypatch.setattr(mod, "REPORT", report)
        monkeypatch.setattr(mod, "GENERATED", generated)
        run = tmp_path / "results" / "s1"
        (run / "cases" / "FT-X").mkdir(parents=True)
        (run / "cases" / "FT-X" / "verdict.json").write_text(
            json.dumps({"id": "FT-X", "status": "pass", "grounded": True}), encoding="utf-8"
        )
        monkeypatch.setattr(mod, "_newest_run_dir", lambda: run)

        rc = mod.main(["-o", str(report)])

        assert rc == 0
        # The canonical hand-authored report is byte-for-byte unchanged.
        assert report.read_text(encoding="utf-8") == original
        # The draft was written to the generated sibling instead.
        assert generated.exists()


class TestCliRefuses:
    def test_field_test_cli_does_not_writereport_over_hand_maintained(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        from agentpolicy.cli import field_test as ft

        report = tmp_path / "FIELD_TEST_REPORT.md"
        original = f"<!-- {HAND_MAINTAINED_MARKER} -->\n# hand\n"
        report.write_text(original, encoding="utf-8")

        report_obj = SimpleNamespace(total=0, failed=0, passed=0, cases=[])
        report_obj.pass_rate = lambda: 1.0
        report_obj.framework_pass_rates = lambda: {}
        report_obj.failures = lambda: []

        class _R:
            _agents: tuple = ()

            def run(self, agents=None, scenario_types=None):
                return report_obj

        monkeypatch.setattr(ft.FieldTestRunner, "from_files", staticmethod(lambda s, r: _R()))
        monkeypatch.setattr("agentpolicy.field.report.build_report", lambda report: "# r")

        args = SimpleNamespace(
            replan="off", json=False, verbose=False,
            scenarios="tests/field/scenarios.yaml", roster="tests/field/agents.yaml",
            framework=None, agents="all", matrix="both", report=str(report),
        )
        rc = ft._field_test(args)

        assert rc == 0
        assert report.read_text(encoding="utf-8") == original  # untouched
        assert "REFUSING" in capsys.readouterr().err
