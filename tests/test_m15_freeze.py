"""M15 — freeze windows & data-class derivation.

WBS M15: ``15.1`` freeze windows · ``15.2`` code-freeze pack · ``15.3``
data-class derivation. CUJ-21 (R33, R34).
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from agentpolicy.cli import main
from agentpolicy.data_class import DataClassConflictError, DataClassRule, derive_data_class
from agentpolicy.engine.engine import Engine
from agentpolicy.freeze import FreezeLedger
from agentpolicy.pack_format import run_pack_dir, validate_pack_dir
from agentpolicy.policy.loader import load_policy_text
from agentpolicy.policy.models import default_policy

REPO = Path(__file__).resolve().parent.parent
PACK = REPO / "packs/code-freeze"
FUTURE = "2999-01-01T00:00:00+00:00"
PAST = "2000-01-01T00:00:00+00:00"


class TestDataClassDerivation:
    def test_glob_match(self) -> None:
        rules = [DataClassRule("*/secrets/*", "customer_pii")]
        assert derive_data_class("srv/secrets/db", rules) == "customer_pii"
        assert derive_data_class("srv/public/x", rules) is None

    def test_tag_wins_over_glob(self) -> None:
        rules = [DataClassRule("*", "internal")]
        assert derive_data_class(
            "srv/x", rules, resource_tags=["pii"], tag_map={"pii": "customer_pii"}
        ) == "customer_pii"

    def test_schema_hint_fallback(self) -> None:
        assert derive_data_class("x", [], schema_hint="restricted") == "restricted"
        assert derive_data_class("x", []) is None

    def test_conflicting_globs_fail_loudly(self) -> None:
        rules = [DataClassRule("*.sql", "customer_pii"), DataClassRule("srv/*", "internal")]
        with pytest.raises(DataClassConflictError, match="conflicting glob"):
            derive_data_class("srv/a.sql", rules)

    def test_conflicting_tags_fail_loudly(self) -> None:
        with pytest.raises(DataClassConflictError, match="conflicting tags"):
            derive_data_class(
                "x", [], resource_tags=["a", "b"], tag_map={"a": "internal", "b": "customer_pii"}
            )

    def test_loader_parses_rules(self) -> None:
        policy = load_policy_text(
            'version: "1.0.0"\nposture: balanced\n'
            "data_class_rules:\n  - {pattern: '*/secrets/*', data_class: customer_pii}\n"
        )
        assert policy.data_class_rules[0].pattern == "*/secrets/*"


class TestEngineDataClass:
    def _engine(self, rules) -> Engine:
        return Engine(replace(default_policy("balanced"), data_class_rules=tuple(rules)))

    def test_auto_derives_and_evaluates(self) -> None:
        engine = self._engine([DataClassRule("*/secrets/*", "customer_pii")])
        decision = engine.evaluate(
            tool_name="query_logs", action="read", environment="staging",
            data_class="auto", agent_id="bot", resource_tag="srv/secrets/db",
        )
        assert decision.decision in {"allow", "audit", "escalate", "deny"}

    def test_auto_falls_back_to_internal(self) -> None:
        engine = self._engine([])
        decision = engine.evaluate(
            tool_name="query_logs", action="read", environment="staging",
            data_class="auto", agent_id="bot",
        )
        assert decision.decision == "allow"

    def test_conflict_fails_closed(self) -> None:
        engine = self._engine(
            [DataClassRule("*.sql", "customer_pii"), DataClassRule("srv/*", "internal")]
        )
        decision = engine.evaluate(
            tool_name="query_logs", action="read", environment="staging",
            data_class="auto", agent_id="bot", resource_tag="srv/a.sql",
        )
        assert decision.decision == "deny"
        assert decision.reason_code == "deny_data_class_conflict"


class TestFreezeLedger:
    def test_declare_and_active(self) -> None:
        ledger = FreezeLedger()
        window = ledger.declare(environments=["production"], ends_at=FUTURE, reason="release")
        assert window.freeze_id.startswith("frz_")
        assert ledger.active_freeze("production") is not None
        assert ledger.active_freeze("staging") is None
        assert ledger.events[0]["kind"] == "declare"

    def test_expire_is_audited(self) -> None:
        ledger = FreezeLedger()
        window = ledger.declare(environments=["production"], ends_at=FUTURE)
        ledger.expire(window.freeze_id, at=PAST)
        assert ledger.events[-1]["kind"] == "expire"

    def test_strictest_wins_on_overlap(self) -> None:
        ledger = FreezeLedger()
        ledger.declare(environments=["production", "staging"], ends_at=FUTURE)
        narrow = ledger.declare(environments=["production"], ends_at=FUTURE)
        chosen = ledger.active_freeze("production")
        assert chosen is not None and chosen.freeze_id == narrow.freeze_id

    def test_declare_requires_an_environment(self) -> None:
        with pytest.raises(ValueError, match="at least one environment"):
            FreezeLedger().declare(environments=[], ends_at=FUTURE)

    def test_save_load(self, tmp_path: Path) -> None:
        ledger = FreezeLedger()
        window = ledger.declare(environments=["production"], ends_at=FUTURE, reason="r")
        path = tmp_path / "freezes.json"
        ledger.save(path)
        reloaded = FreezeLedger.load(path)
        assert reloaded.windows[window.freeze_id].reason == "r"
        assert reloaded.events


class TestEngineFreeze:
    def _engine(self) -> Engine:
        ledger = FreezeLedger()
        ledger.declare(environments=["production"], ends_at=FUTURE, reason="release")
        return Engine(default_policy("balanced"), freeze_ledger=ledger)

    def test_write_is_escalated_and_stamped(self) -> None:
        decision = self._engine().evaluate(
            tool_name="deploy_service", action="write", environment="production",
            data_class="internal", agent_id="release-bot",
        )
        assert decision.decision == "escalate"
        assert decision.reason_code == "freeze_active"
        assert decision.freeze_id is not None

    def test_read_is_unchanged_but_stamped(self) -> None:
        decision = self._engine().evaluate(
            tool_name="query_logs", action="read", environment="production",
            data_class="internal", agent_id="debug-bot",
        )
        assert decision.freeze_id is not None

    def test_unfrozen_environment_unaffected(self) -> None:
        decision = self._engine().evaluate(
            tool_name="deploy_service", action="write", environment="development",
            data_class="internal", agent_id="release-bot",
        )
        assert decision.decision == "allow"
        assert decision.freeze_id is None


class TestCodeFreezePack:
    def test_pack_validates_and_replays(self) -> None:
        assert validate_pack_dir(PACK) == []
        results = {r.name: r for r in run_pack_dir(PACK)}
        assert all(r.passed for r in results.values())
        assert results["freeze-blocks-write"].got == "deny"
        assert results["no-freeze-allows-write"].got == "allow"


class TestFreezeCli:
    def test_declare_list_expire(self, tmp_path: Path, capsys) -> None:
        store = str(tmp_path / "f.json")
        assert main([
            "freeze", "declare", "--env", "production", "--until", FUTURE,
            "--reason", "release", "--store", store,
        ]) == 0
        freeze_id = json.loads(capsys.readouterr().out)["freeze_id"]
        assert main(["freeze", "list", "--store", store, "--json"]) == 0
        assert json.loads(capsys.readouterr().out)
        assert main(["freeze", "expire", freeze_id, "--store", store]) == 0

    def test_expire_unknown_fails(self, tmp_path: Path, capsys) -> None:
        assert main(["freeze", "expire", "frz_nope", "--store", str(tmp_path / "f.json")]) == 1
        assert capsys.readouterr().err

    def test_declare_without_env_fails(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit):
            main(["freeze", "declare", "--until", FUTURE, "--store", str(tmp_path / "f.json")])
