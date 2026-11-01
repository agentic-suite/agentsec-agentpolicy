"""M25 25.4 — the compliance & standards matrix covers OWASP + ATLAS + NIST/ISO/EU.

The published matrix must span the required frameworks and state **explicit
gaps** (an uncovered control is listed, never hidden). These tests lock the
framework set, the gaps computation, and the published doc.
"""

from __future__ import annotations

from pathlib import Path

from agentpolicy import compliance

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "docs" / "compliance" / "standards-matrix.md"

REQUIRED_FRAMEWORKS = {"OWASP-ASI", "OWASP-LLM", "ATLAS", "NIST-AI-RMF", "ISO-42001", "EU-AI-Act"}


class TestStandardsMatrixFrameworks:
    def test_controls_span_all_required_frameworks(self) -> None:
        frameworks = {c.framework for c in compliance.CONTROLS}
        assert REQUIRED_FRAMEWORKS <= frameworks, REQUIRED_FRAMEWORKS - frameworks

    def test_matrix_has_an_explicit_gaps_key(self) -> None:
        matrix = compliance.coverage_matrix()
        assert "gaps" in matrix
        # gaps is a list of uncovered control ids (explicit, possibly empty)
        assert isinstance(matrix["gaps"], list)

    def test_every_control_maps_to_domains(self) -> None:
        for c in compliance.CONTROLS:
            assert c.domains, f"{c.control_id} has no domain mapping"


class TestStandardsMatrixDoc:
    def test_doc_exists(self) -> None:
        assert DOC.is_file(), f"missing standards matrix: {DOC}"

    def test_doc_names_the_frameworks_and_gaps(self) -> None:
        text = DOC.read_text(encoding="utf-8")
        for fw in REQUIRED_FRAMEWORKS:
            assert fw in text, f"matrix doc must name {fw}"
        assert "gap" in text.lower()
