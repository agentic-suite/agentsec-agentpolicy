"""M4 — rule packs: format, path-safety, launch-pack incident replays, backends.

WBS M4: ``4.1`` pack format · ``4.2`` destructive-commands (Replit rule) ·
``4.3`` secret-in-output · ``4.4`` mcp-allowlist · ``4.5`` ``pack validate`` /
``pack test`` · ``4.6`` OPA/Rego peer backend. CUJ-5.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentpolicy.cli import main
from agentpolicy.errors import DENY_OPA_BACKEND_DOWN, OpaUnavailableError
from agentpolicy.pack_format import (
    PackFormatError,
    load_manifest,
    load_pack,
    run_pack_dir,
    validate_pack_dir,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKS = REPO_ROOT / "packs"
LAUNCH_PACKS = ("destructive-commands", "secret-in-output", "mcp-allowlist")
LEGACY_PACKS = ("cloud-read", "db-queries", "fs-basics", "http-crud", "shell-safe")


def _write_pack(
    root: Path, name: str, *, manifest_name: str | None = None, rules: str = ""
) -> Path:
    d = root / name
    d.mkdir(parents=True)
    (d / "metadata.yaml").write_text(
        f"name: {manifest_name or name}\nversion: 0.1.0\ndescription: test\nincident_ref: inc#1\n",
        encoding="utf-8",
    )
    (d / "rules.cedar").write_text(rules, encoding="utf-8")
    (d / "tests.yaml").write_text("fixtures: []\n", encoding="utf-8")
    return d


class TestPackFormat:
    @pytest.mark.parametrize("name", LAUNCH_PACKS)
    def test_launch_pack_loads_with_incident_anchor(self, name: str) -> None:
        pack = load_pack(PACKS / name)
        assert pack.manifest.name == name
        assert pack.manifest.incident_ref.startswith("incident-register#")
        assert pack.manifest.trust == "launch"

    def test_missing_metadata_rejected(self, tmp_path: Path) -> None:
        d = tmp_path / "no-meta"
        d.mkdir()
        with pytest.raises(PackFormatError, match=r"missing metadata\.yaml"):
            load_manifest(d)

    def test_name_must_match_directory(self, tmp_path: Path) -> None:
        d = _write_pack(tmp_path, "dir-name", manifest_name="other-name")
        with pytest.raises(PackFormatError, match="does not match its directory"):
            load_manifest(d)

    def test_unsafe_name_rejected(self, tmp_path: Path) -> None:
        d = tmp_path / "unsafe"
        d.mkdir()
        (d / "metadata.yaml").write_text("name: ../escape\nversion: 0.1.0\n", encoding="utf-8")
        with pytest.raises(PackFormatError, match="unsafe pack name"):
            load_manifest(d)

    def test_malformed_cedar_rejected(self, tmp_path: Path) -> None:
        d = _write_pack(tmp_path, "bad-cedar", rules="permit(principal, action")
        with pytest.raises(ValueError, match="invalid Cedar policy"):
            load_pack(d)


class TestLaunchPackReplays:
    @pytest.mark.parametrize("name", LAUNCH_PACKS)
    def test_pack_validates_and_replay_passes(self, name: str) -> None:
        assert validate_pack_dir(PACKS / name) == []
        results = run_pack_dir(PACKS / name)
        assert results, "a launch pack must ship fixtures"
        failed = [r for r in results if not r.passed]
        assert not failed, f"{name} failed: {[(r.name, r.expected, r.got) for r in failed]}"

    @pytest.mark.parametrize("name", LAUNCH_PACKS)
    def test_replay_is_deterministic(self, name: str) -> None:
        first = [(r.name, r.got) for r in run_pack_dir(PACKS / name)]
        second = [(r.name, r.got) for r in run_pack_dir(PACKS / name)]
        assert first == second

    def test_replit_rule_blocks_its_incident(self) -> None:
        results = {r.name: r for r in run_pack_dir(PACKS / "destructive-commands")}
        assert results["replit-prod-db-delete"].got == "deny"

    def test_secret_in_output_scrubs(self) -> None:
        results = {r.name: r for r in run_pack_dir(PACKS / "secret-in-output")}
        assert results["secret-read-redacted"].got == "redact"

    def test_mcp_allowlist_blocks_shadow_tool(self) -> None:
        results = {r.name: r for r in run_pack_dir(PACKS / "mcp-allowlist")}
        assert results["shadow-tool-unlisted-denied"].got == "deny"


class TestPackCli:
    @pytest.mark.parametrize("name", LAUNCH_PACKS)
    def test_pack_test_exit_zero(self, name: str, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["pack", "test", str(PACKS / name)]) == 0
        assert "passed" in capsys.readouterr().out

    @pytest.mark.parametrize("name", LEGACY_PACKS)
    def test_legacy_catalog_packs_also_pass(self, name: str) -> None:
        assert main(["pack", "validate", str(PACKS / name)]) == 0

    def test_malformed_pack_fails_closed_exit_two(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        d = tmp_path / "broken"
        d.mkdir()
        (d / "rules.cedar").write_text("forbid(principal", encoding="utf-8")
        assert main(["pack", "validate", str(d)]) == 2
        assert "metadata.yaml" in capsys.readouterr().err

    def test_pack_list_includes_launch_packs(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main(["pack", "list"]) == 0
        out = capsys.readouterr().out
        for name in LAUNCH_PACKS:
            assert name in out


class TestOpaPeerBackend:
    def test_unreachable_opa_is_a_deny_reason(self) -> None:
        assert OpaUnavailableError.reason_code == DENY_OPA_BACKEND_DOWN

    def test_missing_binary_fails_independently(self) -> None:
        from agentpolicy.policy.opa import opa_evaluate
        from agentpolicy.types import NormalizedCall

        call = NormalizedCall(
            tool="query_logs",
            tool_category="search",
            action="read",
            action_class="read",
            environment="staging",
            data_class="internal",
            agent_id="debug-bot",
            agent_class="general",
        )
        with pytest.raises(OpaUnavailableError):
            opa_evaluate(call, "/nope/policy.rego", opa_binary="no_such_opa_binary")
