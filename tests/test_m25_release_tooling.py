"""M25 25.1 — release tooling: SBOM + SHA256SUMS + SLSA provenance, verified.

``scripts/release/release_tooling.py`` turns a dist directory into a verifiable
release set — a CycloneDX SBOM, a ``SHA256SUMS`` manifest, and an in-toto/SLSA
provenance statement — and then **independently verifies** them. These tests
lock the happy path (verify green) and the loud failure path (a tampered
artifact or a missing hash fails verification, never passes silently).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _load_tooling():
    spec = importlib.util.spec_from_file_location(
        "_release_tooling", REPO / "scripts" / "release" / "release_tooling.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_dist(tmp_path: Path) -> Path:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "agentsec_agentpolicy-0.1.0-py3-none-any.whl").write_bytes(b"wheel-bytes")
    (dist / "agentsec_agentpolicy-0.1.0.tar.gz").write_bytes(b"sdist-bytes")
    return dist


class TestReleaseTooling:
    def test_manifest_generation_then_verify_is_green(self, tmp_path: Path) -> None:
        tooling = _load_tooling()
        dist = _make_dist(tmp_path)
        tooling.write_manifest(dist)
        assert (dist / "sbom.cdx.json").is_file()
        assert (dist / "SHA256SUMS").is_file()
        assert (dist / "provenance.intoto.jsonl").is_file()
        assert tooling.verify(dist) == []

    def test_sbom_is_cyclonedx(self, tmp_path: Path) -> None:
        tooling = _load_tooling()
        dist = _make_dist(tmp_path)
        tooling.write_manifest(dist)
        sbom = json.loads((dist / "sbom.cdx.json").read_text())
        assert sbom["bomFormat"] == "CycloneDX"
        assert sbom["specVersion"].startswith("1.")
        names = {c["name"] for c in sbom["components"]}
        assert any("agentsec_agentpolicy" in n for n in names)

    def test_sha256sums_cover_every_artifact(self, tmp_path: Path) -> None:
        tooling = _load_tooling()
        dist = _make_dist(tmp_path)
        tooling.write_manifest(dist)
        sums = (dist / "SHA256SUMS").read_text()
        assert "agentsec_agentpolicy-0.1.0-py3-none-any.whl" in sums
        assert "agentsec_agentpolicy-0.1.0.tar.gz" in sums
        assert "sbom.cdx.json" in sums

    def test_provenance_lists_artifacts_with_hashes(self, tmp_path: Path) -> None:
        tooling = _load_tooling()
        dist = _make_dist(tmp_path)
        tooling.write_manifest(dist)
        prov = json.loads((dist / "provenance.intoto.jsonl").read_text())
        assert prov["_type"].startswith("https://in-toto.io/Statement/")
        subjects = {s["name"] for s in prov["subject"]}
        assert "agentsec_agentpolicy-0.1.0-py3-none-any.whl" in subjects
        assert all(len(s["digest"]["sha256"]) == 64 for s in prov["subject"])

    def test_tampered_artifact_fails_verification(self, tmp_path: Path) -> None:
        tooling = _load_tooling()
        dist = _make_dist(tmp_path)
        tooling.write_manifest(dist)
        assert tooling.verify(dist) == []
        # tamper AFTER the manifest is written — verification must catch it
        (dist / "agentsec_agentpolicy-0.1.0.tar.gz").write_bytes(b"tampered")
        problems = tooling.verify(dist)
        assert problems, "tampered artifact must fail verification"

    def test_missing_sums_fails_loudly(self, tmp_path: Path) -> None:
        tooling = _load_tooling()
        dist = _make_dist(tmp_path)
        # no manifest written at all — verify must not report success
        assert tooling.verify(dist)
