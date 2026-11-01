"""M25 25.2 — first-run evidence: install → first correct decision, measured.

``scripts/release/first_run.py`` records the time-to-first-decision journey
(`agentpolicy init` → a correct `evaluate`) and enforces the SLOs
(< 5 min install→decision; < 2 min with `init`). These tests cover the SLO
check (pass/fail) and lock the recorded evidence doc.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EVIDENCE = REPO / "docs" / "release" / "v0.1.0" / "FIRST_RUN_EVIDENCE.md"


def _load():
    spec = importlib.util.spec_from_file_location(
        "_first_run", REPO / "scripts" / "release" / "first_run.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestFirstRunSlo:
    def test_within_budget_is_green(self) -> None:
        fr = _load()
        assert fr.check_slo(install_s=20.0, init_s=1.0, decide_s=2.0) == []

    def test_over_five_minutes_fails(self) -> None:
        fr = _load()
        # install dominates the install→decision SLO
        assert fr.check_slo(install_s=400.0, init_s=1.0, decide_s=2.0)

    def test_over_two_minutes_with_init_fails(self) -> None:
        fr = _load()
        # a slow scaffolded first decision must fail the < 2 min SLO
        assert fr.check_slo(install_s=20.0, init_s=130.0, decide_s=5.0)


class TestFirstRunEvidence:
    def test_evidence_doc_exists(self) -> None:
        assert EVIDENCE.is_file(), f"missing first-run evidence: {EVIDENCE}"

    def test_evidence_records_the_journey_and_slos(self) -> None:
        text = EVIDENCE.read_text(encoding="utf-8").lower()
        for token in ("pip install", "agentpolicy init", "evaluate", "sha256", "< 5", "< 2"):
            assert token in text, f"evidence must record {token!r}"
