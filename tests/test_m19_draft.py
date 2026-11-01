"""M19 — NL policy drafting (advisory, authoring-time only).

WBS M19: ``19.1`` agentpolicy draft · ``19.2`` generated tests · ``19.3``
human-review gate + boundary lock. CUJ-27 (R42).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentpolicy.canonical import canonicalize
from agentpolicy.cedar import CedarEvaluator
from agentpolicy.cli import main
from agentpolicy.draft import Draft, DraftError, draft, lint_draft, pin, run_draft
from agentpolicy.engine.engine import Engine
from agentpolicy.policy.models import default_policy

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src/agentpolicy"


class TestDraftRule:
    def test_deny_sentence_emits_forbid(self) -> None:
        d = draft("deny deploy in production")
        assert isinstance(d, Draft)
        assert d.rule_id.startswith("draft-")
        assert "forbid" in d.cedar
        assert 'context.verb == "deploy"' in d.cedar
        assert 'context.environment == "production"' in d.cedar

    def test_allow_sentence_emits_permit(self) -> None:
        d = draft("allow delete in staging")
        assert "permit" in d.cedar
        assert 'context.environment == "staging"' in d.cedar

    def test_draft_compiles_and_its_tests_pass(self) -> None:
        d = draft("deny deploy in production")
        results = run_draft(d)
        assert results
        assert all(r.passed for r in results)

    def test_tests_yaml_round_trips(self) -> None:
        import yaml

        d = draft("deny deploy in production")
        doc = yaml.safe_load(d.tests_yaml())
        assert isinstance(doc["fixtures"], list) and doc["fixtures"]

    def test_draft_is_never_auto_reviewed(self) -> None:
        assert draft("deny deploy in production").reviewed is False

    def test_lint_is_clean_for_a_normal_draft(self) -> None:
        assert lint_draft(draft("deny deploy in production")) == []

    def test_data_class_only_draft(self) -> None:
        d = draft("deny query restricted data")
        assert 'context.data_class == "restricted"' in d.cedar
        assert all(r.passed for r in run_draft(d))

    def test_plain_verb_draft(self) -> None:
        d = draft("deny write")
        assert all(r.passed for r in run_draft(d))

    def test_custom_model_is_honored(self) -> None:
        d = draft(
            "anything",
            model=lambda _s: {
                "effect": "forbid", "verb": "write", "environment": "staging",
                "data_class": None,
            },
        )
        assert d.effect == "forbid"
        assert 'context.environment == "staging"' in d.cedar


class TestDraftRejection:
    def test_unachievable_intent_is_rejected(self) -> None:
        # A permit cannot override the base forbid-destructive-production rule,
        # so the generated test fails and the draft is rejected.
        with pytest.raises(DraftError, match="test"):
            draft("allow delete in production")


class TestReviewGate:
    def test_pin_without_review_is_rejected(self) -> None:
        d = draft("deny deploy in production")
        with pytest.raises(DraftError, match="review"):
            pin(d)

    def test_pin_after_review(self) -> None:
        d = draft("deny deploy in production")
        pinned = pin(d, reviewed=True)
        assert pinned.reviewed is True


class TestBoundaryLock:
    def test_runtime_path_never_calls_the_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import agentpolicy.draft as draft_mod

        def _boom(_sentence: str) -> dict:
            raise AssertionError("the runtime decision path called the model")

        monkeypatch.setattr(draft_mod, "default_model", _boom)
        # The engine + the Cedar core must run without ever touching the model.
        Engine(default_policy("balanced")).evaluate(
            tool_name="deploy_service", action="write", environment="production",
            data_class="internal", agent_id="release-bot",
        )
        CedarEvaluator().evaluate(
            canonicalize(
                tool="deploy_service", action="write", environment="production",
                data_class="internal", agent_id="release-bot",
            )
        )

    def test_decision_modules_do_not_reference_draft(self) -> None:
        for module in ("engine/engine.py", "cedar/evaluator.py", "cedar/shaper.py"):
            text = (SRC / module).read_text(encoding="utf-8")
            assert "import draft" not in text
            assert "from agentpolicy.draft" not in text
            assert "agentpolicy.draft" not in text


class TestDraftCli:
    def test_draft_writes_a_candidate_pack_never_pinned(self, tmp_path: Path, capsys) -> None:
        out = tmp_path / "candidate"
        assert main(["draft", "deny deploy in production", "--out", str(out)]) == 0
        capsys.readouterr()
        assert (out / "rules.cedar").is_file()
        assert (out / "tests.yaml").is_file()
        assert (out / "metadata.yaml").is_file()
        assert "reviewed: false" in (out / "metadata.yaml").read_text(encoding="utf-8")

    def test_json_output(self, capsys) -> None:
        import json

        assert main(["draft", "deny deploy in production", "--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["reviewed"] is False

    def test_rejected_draft_fails_the_cli(self, capsys) -> None:
        assert main(["draft", "allow delete in production"]) == 1
        assert capsys.readouterr().err
