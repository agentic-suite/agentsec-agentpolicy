"""M22 — self-attack pack & release-cadence gate.

WBS M22: ``22.1`` self-attack pack · ``22.2`` release-cadence CI job.
CUJ-32 (R46).
"""

from __future__ import annotations

from pathlib import Path

from agentpolicy.cli import main
from agentpolicy.pack_format import run_pack_dir, validate_pack_dir
from agentpolicy.selfattack import SelfAttackResult, gate, self_attack_pack

REPO = Path(__file__).resolve().parent.parent
PACK = REPO / "packs/self-attack"

_ATTACK_CLASSES = (
    "tamper", "bypass", "replay", "budget_split", "audit_truncation", "event_forgery",
)


def _miss_pack(tmp_path: Path) -> Path:
    """A pack whose attack fixture is expected blocked but is not."""
    pack = tmp_path / "badpack"
    pack.mkdir()
    (pack / "metadata.yaml").write_text(
        "name: badpack\nversion: 0.1.0\ndescription: seeded miss\ntrust: community\n",
        encoding="utf-8",
    )
    (pack / "rules.cedar").write_text("// no rules: the attack is not blocked\n", encoding="utf-8")
    (pack / "tests.yaml").write_text(
        "fixtures:\n"
        "  - name: leaked-attack\n    tool: query_logs\n    action: read\n"
        "    environment: staging\n    data_class: internal\n"
        "    context: {self_attack: tamper}\n    expect: deny\n",
        encoding="utf-8",
    )
    return pack


class TestSelfAttackPack:
    def test_validates_and_all_attacks_are_blocked(self) -> None:
        assert validate_pack_dir(PACK) == []
        results = {r.name: r for r in run_pack_dir(PACK)}
        assert all(r.passed for r in results.values())
        for attack in _ATTACK_CLASSES:
            assert results[f"self-attack-{attack}"].got in {"deny", "ask", "rate-limit", "redact"}

    def test_benign_fixture_is_not_denied(self) -> None:
        results = {r.name: r for r in run_pack_dir(PACK)}
        assert results["benign-allowed"].got == "allow"


class TestSelfAttackGate:
    def test_shipped_pack_has_no_misses(self) -> None:
        assert gate([PACK]) == ()
        results = self_attack_pack(PACK)
        assert all(isinstance(r, SelfAttackResult) and r.passed for r in results)

    def test_a_seeded_miss_is_reported(self, tmp_path: Path) -> None:
        misses = gate([_miss_pack(tmp_path)])
        assert len(misses) == 1
        assert misses[0].name == "leaked-attack"
        assert misses[0].missed is True


class TestSelfAttackCli:
    def test_check_passes_on_the_shipped_pack(self, capsys) -> None:
        assert main(["self-attack", "check", "--pack", str(PACK)]) == 0
        assert "self-attack" in capsys.readouterr().out

    def test_check_fails_on_a_miss(self, tmp_path: Path, capsys) -> None:
        assert main(["self-attack", "check", "--pack", str(_miss_pack(tmp_path))]) == 1
        assert "leaked-attack" in capsys.readouterr().out
