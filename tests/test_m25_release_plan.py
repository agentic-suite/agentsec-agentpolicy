"""M25 25.D0 — the release plan must exist and stay complete.

``docs/release/v0.1.0/RELEASE_PLAN.md`` is the reviewed-before-code design for
M25 (Release readiness): the versioning policy, the artifact set (SBOM /
SHA256SUMS / SLSA provenance), the evidence, and the tag/release steps. These
tests fail if the plan is missing or drops any required section, and they pin
the safety rules (hashes match SHA256SUMS; the predecessor is retained private,
never deleted).
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLAN = REPO / "docs" / "release" / "v0.1.0" / "RELEASE_PLAN.md"

#: Section headings the plan must carry (case-insensitive substring match).
REQUIRED_SECTIONS = [
    "versioning",
    "artifact",
    "evidence",
    "tag",
    "release steps",
]


class TestReleasePlan:
    def test_plan_exists(self) -> None:
        assert PLAN.is_file(), f"missing release plan: {PLAN}"

    def test_plan_has_required_sections(self) -> None:
        text = PLAN.read_text(encoding="utf-8").lower()
        missing = [s for s in REQUIRED_SECTIONS if s not in text]
        assert not missing, f"release plan missing sections: {missing}"

    def test_plan_names_the_artifact_set(self) -> None:
        text = PLAN.read_text(encoding="utf-8")
        for token in ("CycloneDX", "SBOM", "SHA256SUMS", "SLSA", "provenance"):
            assert token in text, f"release plan must name the artifact {token!r}"

    def test_plan_states_hash_and_retention_rules(self) -> None:
        text = PLAN.read_text(encoding="utf-8").lower()
        # hashes must match SHA256SUMS; predecessor retained private, never deleted
        assert "sha256sums" in text
        assert "private" in text and "never delete" in text

    def test_plan_names_the_release_target(self) -> None:
        text = PLAN.read_text(encoding="utf-8")
        assert "v0.1.0" in text
        assert "agentsec-agentpolicy" in text
