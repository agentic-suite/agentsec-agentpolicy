"""M25 25.3 — security audit: own-threat-model + dependency scan, 0 unresolved.

``scripts/release/security_audit.py`` computes the shipped package's **runtime
dependency closure** (pyproject ``[project].dependencies`` + transitives),
scans it with ``pip-audit``, and writes ``SECURITY_AUDIT.md`` (the own threat
model + the scan result). These tests lock the doc, the closure, and the
finding summariser.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "docs" / "release" / "v0.1.0" / "SECURITY_AUDIT.md"


def _load():
    spec = importlib.util.spec_from_file_location(
        "_security_audit", REPO / "scripts" / "release" / "security_audit.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestSummarize:
    def test_flags_a_vulnerable_package(self) -> None:
        sa = _load()
        audit = {"dependencies": [
            {"name": "foo", "version": "1.0", "vulns": [{"id": "CVE-1", "fix_versions": ["1.1"]}]},
            {"name": "bar", "version": "2.0", "vulns": []},
        ]}
        findings = sa.summarize(audit)
        assert [f["name"] for f in findings] == ["foo"]

    def test_clean_audit_has_no_findings(self) -> None:
        sa = _load()
        audit = {"dependencies": [{"name": "bar", "version": "2.0", "vulns": []}]}
        assert sa.summarize(audit) == []


class TestRuntimeClosure:
    def test_closure_includes_shipped_deps(self) -> None:
        sa = _load()
        closure = sa.runtime_closure()
        low = {n.lower() for n in closure}
        for required in ("pydantic", "cryptography", "pyyaml", "starlette", "cedarpy"):
            assert required in low, f"runtime closure missing {required}"


class TestSecurityAuditDoc:
    def test_doc_exists(self) -> None:
        assert DOC.is_file(), f"missing security audit: {DOC}"

    def test_doc_records_threat_model_and_scan(self) -> None:
        text = DOC.read_text(encoding="utf-8").lower()
        for token in ("threat model", "pip-audit", "dependency", "unresolved", "0 unresolved"):
            assert token in text, f"security audit must record {token!r}"
