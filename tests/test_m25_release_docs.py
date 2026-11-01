"""M25 25.D — release docs: README status shipped, CHANGELOG entry, license.

Locks the release-facing docs in their shipped state: the README announces the
release and the PyPI install, the CHANGELOG carries a dated ``[0.1.0]`` entry,
and the package license is Apache-2.0 (matching ``LICENSE``).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


class TestReleaseDocs:
    def test_readme_announces_the_release(self) -> None:
        text = (REPO / "README.md").read_text(encoding="utf-8")
        assert "released" in text.lower()
        assert "v0.1.0" in text
        assert "pip install agentsec-agentpolicy" in text

    def test_changelog_has_a_dated_0_1_0_entry(self) -> None:
        text = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
        assert "## [0.1.0]" in text
        assert "2026-11-01" in text

    def test_license_is_apache_2_0_everywhere(self) -> None:
        data = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
        assert data["project"]["license"]["text"] == "Apache-2.0"
        assert "Apache License" in (REPO / "LICENSE").read_text(encoding="utf-8")
