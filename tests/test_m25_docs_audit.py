"""M25 25.6 — docs audit: ADRs accepted + relative links resolve.

``scripts/release/docs_audit.py`` walks the docs tree, checks every ADR carries
an **accepted** status (no lingering *Proposed*), and resolves every relative
markdown link. These tests lock the auditor, then assert the repo itself is
clean (the release condition).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location(
        "_docs_audit", REPO / "scripts" / "release" / "docs_audit.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestAuditorUnit:
    def test_broken_link_is_detected(self, tmp_path: Path) -> None:
        da = _load()
        (tmp_path / "a.md").write_text("see [missing](./nope.md)\n", encoding="utf-8")
        problems = da.check_links([tmp_path / "a.md"])
        assert any("nope.md" in p for p in problems)

    def test_valid_link_is_clean(self, tmp_path: Path) -> None:
        da = _load()
        (tmp_path / "b.md").write_text("target\n", encoding="utf-8")
        (tmp_path / "a.md").write_text("see [ok](./b.md)\n", encoding="utf-8")
        assert da.check_links([tmp_path / "a.md"]) == []

    def test_proposed_adr_is_flagged(self, tmp_path: Path) -> None:
        da = _load()
        (tmp_path / "0001-x.md").write_text("**Status:** proposed\n", encoding="utf-8")
        problems = da.check_adrs(tmp_path)
        assert any("proposed" in p.lower() for p in problems)


class TestRepoDocsClean:
    def test_repo_links_resolve(self) -> None:
        da = _load()
        problems = da.check_links(da.doc_files())
        assert problems == [], "broken links:\n" + "\n".join(problems)

    def test_all_adrs_accepted(self) -> None:
        da = _load()
        problems = da.check_adrs(REPO / "docs" / "adr")
        assert problems == [], "ADR issues:\n" + "\n".join(problems)
