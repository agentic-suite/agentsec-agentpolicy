"""M7 — ask round-trip, redact-and-allow, secrets-in-arguments.

WBS M7: ``7.1`` ask-gate broker · ``7.2`` ``approve``/``deny`` · ``7.3``
redact-and-allow · ``7.4`` secrets-in-arguments. CUJ-10, CUJ-15 (R18, R20, R38).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from agentpolicy import reason_codes
from agentpolicy.ask import AskBroker, AskStatus, gate
from agentpolicy.canonical import canonicalize
from agentpolicy.cedar import CedarEvaluator
from agentpolicy.cli import main
from agentpolicy.engine.escalation import action_identity
from agentpolicy.redaction import (
    RedactionReceipt,
    redact_argument_values,
    redact_output,
    redact_text,
)

SECRET = "sk-proj-" + "A" * 40
SSN = "123-45-6789"


def _ask_call():
    return canonicalize(
        tool="deploy_service", action="write", environment="production",
        data_class="restricted", agent_id="release-bot",
    )


def _resolves(decision):
    return decision.decision == "ask"


class TestAskBroker:
    def test_create_is_pending_with_ask_id(self) -> None:
        broker = AskBroker()
        ask = broker.create(_ask_call(), reason="write in production")
        assert ask.ask_id.startswith("ask_")
        assert ask.status == AskStatus.PENDING
        assert ask.action_identity == action_identity(
            "deploy_service", "write", None
        )
        assert len(broker.pending()) == 1

    def test_approve_then_resolve_allows(self) -> None:
        broker = AskBroker()
        call = _ask_call()
        ask = broker.create(call)
        broker.approve(ask.ask_id, approver="alice")
        result = broker.resolve(ask.ask_id, call=call)
        assert result["status"] == "allow"
        assert result["reason_code"] == reason_codes.ALLOW_ASK_APPROVED
        assert broker.find_by_action_identity(ask.action_identity) == ask.ask_id

    def test_deny_then_resolve_denies_with_reason(self) -> None:
        broker = AskBroker()
        call = _ask_call()
        ask = broker.create(call)
        broker.deny(ask.ask_id, approver="alice", reason="not this quarter")
        result = broker.resolve(ask.ask_id, call=call)
        assert result["status"] == "deny"
        assert result["reason_code"] == reason_codes.DENY_ASK_DENIED
        assert "not this quarter" in result["explanation"]

    def test_pending_resolve_denies(self) -> None:
        broker = AskBroker()
        call = _ask_call()
        ask = broker.create(call)
        result = broker.resolve(ask.ask_id, call=call)
        assert result["reason_code"] == reason_codes.DENY_ASK_PENDING

    def test_unknown_ask_denies(self) -> None:
        broker = AskBroker()
        result = broker.resolve("ask_nope", call=_ask_call())
        assert result["reason_code"] == reason_codes.DENY_ASK_UNKNOWN

    def test_expiry_is_a_timeout_deny(self) -> None:
        broker = AskBroker(ttl_seconds=60)
        call = _ask_call()
        start = datetime(2026, 1, 1, tzinfo=UTC)
        ask = broker.create(call, now=start)
        later = start + timedelta(seconds=120)
        result = broker.resolve(ask.ask_id, call=call, now=later)
        assert result["status"] == "deny"
        assert result["reason_code"] == reason_codes.HUMAN_GATE_TIMEOUT
        assert broker.records[ask.ask_id].status == AskStatus.EXPIRED

    def test_approval_for_x_cannot_release_y(self) -> None:
        broker = AskBroker()
        x = canonicalize(
            tool="deploy_service", action="write", environment="production",
            data_class="restricted", agent_id="release-bot",
            arguments={"target": "prod-a"},
        )
        y = canonicalize(
            tool="deploy_service", action="write", environment="production",
            data_class="restricted", agent_id="release-bot",
            arguments={"target": "prod-b"},
        )
        ask = broker.create(x)
        broker.approve(ask.ask_id, approver="alice")
        result = broker.resolve(ask.ask_id, call=y)
        assert result["status"] == "deny"
        assert result["reason_code"] == reason_codes.DENY_ACTION_IDENTITY_MISMATCH

    def test_blank_approver_rejected(self) -> None:
        broker = AskBroker()
        ask = broker.create(_ask_call())
        with pytest.raises(ValueError, match="approver"):
            broker.approve(ask.ask_id, approver="  ")

    def test_resolved_ask_cannot_be_resolved_again(self) -> None:
        broker = AskBroker()
        ask = broker.create(_ask_call())
        broker.approve(ask.ask_id, approver="alice")
        with pytest.raises(ValueError, match="already resolved"):
            broker.approve(ask.ask_id, approver="bob")

    def test_save_load_round_trip(self, tmp_path: Path) -> None:
        broker = AskBroker()
        call = _ask_call()
        ask = broker.create(call)
        broker.approve(ask.ask_id, approver="alice")
        path = tmp_path / "asks.json"
        broker.save(path)
        reloaded = AskBroker.load(path)
        assert reloaded.records[ask.ask_id].status == AskStatus.APPROVED
        assert reloaded.find_by_action_identity(ask.action_identity) == ask.ask_id
        assert reloaded.resolve(ask.ask_id, call=call)["status"] == "allow"

    def test_load_missing_file_is_empty(self, tmp_path: Path) -> None:
        assert AskBroker.load(tmp_path / "nope.json").pending() == []


class TestGate:
    def test_gate_stamps_ask_id_on_ask_decision(self) -> None:
        call = _ask_call()
        decision = CedarEvaluator().evaluate(call)
        assert decision.decision == "ask"
        broker = AskBroker()
        stamped, ask = gate(decision, call, broker)
        assert stamped.ask_id is not None
        assert ask is not None
        assert stamped.ask_id == ask.ask_id
        assert stamped.to_dict()["ask_id"] == ask.ask_id

    def test_gate_leaves_allow_untouched(self) -> None:
        call = canonicalize(
            tool="query_logs", action="read", environment="staging",
            data_class="internal", agent_id="debug-bot",
        )
        decision = CedarEvaluator().evaluate(call)
        stamped, ask = gate(decision, call, AskBroker())
        assert stamped is decision
        assert ask is None


class TestRedaction:
    def test_redact_text_scrubs_secret_with_receipt(self) -> None:
        scrubbed, receipts = redact_text(f"token={SECRET}")
        assert SECRET not in scrubbed
        assert "[REDACTED-SECRET]" in scrubbed
        assert receipts == [RedactionReceipt("secret", 1, ("output",))]

    def test_redact_text_scrubs_pii(self) -> None:
        scrubbed, receipts = redact_text(f"ssn {SSN}")
        assert SSN not in scrubbed
        assert receipts[0].redaction_class == "pii"
        assert receipts[0].to_dict() == {
            "class": "pii", "count": 1, "locations": ["output"],
        }

    def test_clean_text_has_no_receipts(self) -> None:
        scrubbed, receipts = redact_text("nothing sensitive here")
        assert receipts == []
        assert scrubbed == "nothing sensitive here"

    def test_receipt_counts_multiple_matches(self) -> None:
        _, receipts = redact_text(f"{SECRET} and {SECRET}")
        assert receipts[0].count == 2

    def test_redact_output_alias(self) -> None:
        scrubbed, receipts = redact_output(SECRET, location="result")
        assert receipts[0].locations == ("result",)
        assert SECRET not in scrubbed

    def test_argument_values_scrub_pasted_secret(self) -> None:
        args = {"command": f"curl -H 'Authorization: Bearer {SECRET}'"}
        scrubbed, receipts = redact_argument_values(args)
        assert scrubbed is not None
        assert SECRET not in scrubbed["command"]
        assert receipts and receipts[0].redaction_class == "secret"
        assert receipts[0].locations == ("command",)

    def test_argument_values_scrub_named_and_pasted(self) -> None:
        args = {"token": "abc", "nested": {"note": f"pii {SSN}"}}
        scrubbed, receipts = redact_argument_values(args)
        assert scrubbed is not None
        assert scrubbed["token"] == "***REDACTED***"  # noqa: S105
        assert SSN not in scrubbed["nested"]["note"]
        assert any(r.redaction_class == "pii" for r in receipts)

    def test_no_arguments_returns_none(self) -> None:
        assert redact_argument_values(None) == (None, [])


class TestAskCli:
    def _seed(self, tmp_path: Path) -> tuple[str, Path]:
        broker = AskBroker()
        ask = broker.create(_ask_call(), reason="write in production")
        path = tmp_path / "asks.json"
        broker.save(path)
        return ask.ask_id, path

    def test_ask_list_json(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _, path = self._seed(tmp_path)
        assert main(["ask", "list", "--store", str(path), "--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload[0]["reason"] == "write in production"

    def test_approve_round_trips(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        ask_id, path = self._seed(tmp_path)
        assert main(["approve", ask_id, "--store", str(path), "--approver", "alice"]) == 0
        assert json.loads(capsys.readouterr().out)["status"] == "approved"

    def test_deny_round_trips(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        ask_id, path = self._seed(tmp_path)
        assert main([
            "deny", ask_id, "--store", str(path), "--approver", "alice",
            "--reason", "no",
        ]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["status"] == "denied"
        assert payload["denied_reason"] == "no"

    def test_approve_unknown_exits_one(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _, path = self._seed(tmp_path)
        assert main(["approve", "ask_nope", "--store", str(path)]) == 1
        assert capsys.readouterr().err
