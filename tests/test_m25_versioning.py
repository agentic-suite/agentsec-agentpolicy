"""M25 25.5 — versioning policy + release notes + compatibility matrix.

The release must carry a **normative versioning policy** and release notes that
include a **harness x enforcer compatibility matrix**. These tests lock both.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VERSIONING = REPO / "docs" / "reference" / "VERSIONING.md"
NOTES = REPO / "docs" / "reference" / "release-notes-v0.1.0.md"


class TestVersioningPolicy:
    def test_policy_exists(self) -> None:
        assert VERSIONING.is_file(), f"missing versioning policy: {VERSIONING}"

    def test_policy_is_normative_and_covers_key_rules(self) -> None:
        text = VERSIONING.read_text(encoding="utf-8").lower()
        for token in ("semantic versioning", "normative", "pre-1.0", "deprecat",
                      "compatibility matrix", "tag"):
            assert token in text, f"versioning policy must cover {token!r}"


class TestReleaseNotesCompatibility:
    def test_notes_are_versioned(self) -> None:
        text = NOTES.read_text(encoding="utf-8")
        assert "0.1.0" in text and "agentsec-agentpolicy" in text

    def test_notes_carry_a_compatibility_matrix(self) -> None:
        text = NOTES.read_text(encoding="utf-8").lower()
        assert "compatibility matrix" in text
        # harness x enforcer axes must both be named
        for token in ("claude code", "codex", "mcp", "agentgate"):
            assert token in text, f"compatibility matrix must name {token!r}"
