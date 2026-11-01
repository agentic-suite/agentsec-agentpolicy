"""M6 — audit log, policy versioning, tamper-evident chain, offline evidence.

WBS M6: ``6.1`` audit log · ``6.2`` ``audit query``/``show`` · ``6.3``
tamper-evident hash chain · ``6.4`` policy versioning + review flag ·
``6.5`` evidence artifact (offline). CUJ-6, CUJ-20, R7.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentpolicy.audit.evidence import EvidenceArtifact, evidence_for
from agentpolicy.audit.logger import AuditLogger
from agentpolicy.audit.models import AuditEntry
from agentpolicy.audit.sinks.jsonl import JsonlSink
from agentpolicy.audit.tamper_proof import (
    chain_entry,
    entry_head,
    rotation_anchor,
    verify_entries,
    verify_rotation,
)
from agentpolicy.audit.versioning import (
    PolicyRevision,
    is_reviewed,
    policy_revision,
    review_warning,
)
from agentpolicy.canonical import canonicalize
from agentpolicy.cedar import CedarEvaluator
from agentpolicy.cedar import policy as policy_mod
from agentpolicy.cli import main
from agentpolicy.explain import build_artifact


def _call(tool="drop_database", action="delete", env="production", data="customer_pii",
          agent="release-bot"):
    return canonicalize(tool=tool, action=action, environment=env,
                        data_class=data, agent_id=agent)


def _deny():
    evaluator = CedarEvaluator()
    call = _call()
    return evaluator, call, evaluator.evaluate(call)


class TestAuditEntryProvenance:
    def test_print_row_and_provenance(self, tmp_path: Path) -> None:
        _evaluator, call, decision = _deny()
        sink = JsonlSink(tmp_path / "audit.jsonl")
        logger = AuditLogger(sink)
        entry = logger.log(
            decision, call, session_id="sess_1",
            decision_id="dec_1", policy_hash="sha256:abc", matched_rule="forbid-x",
        )
        assert entry.decision == "deny"
        assert entry.reason_code == "irreversible_action"
        assert entry.policy_version == "0.1.0"
        assert entry.policy_hash == "sha256:abc"
        assert entry.matched_rule == "forbid-x"
        assert entry.decision_id == "dec_1"
        # The sink assigns the sequence/link at write time; read it back.
        persisted = logger.query("sess_1")[0]
        assert persisted.seq == 0
        # PRD 15 names the link ``entry_hash``; it is the persisted ``chain_hash``.
        assert persisted.entry_hash == persisted.chain_hash
        assert persisted.entry_hash is not None

    def test_seq_is_monotonic_and_chained(self, tmp_path: Path) -> None:
        _evaluator, call, decision = _deny()
        sink = JsonlSink(tmp_path / "audit.jsonl")
        logger = AuditLogger(sink)
        for i in range(3):
            logger.log(decision, call, session_id="sess_1", decision_id=f"dec_{i}")
        entries = logger.query("sess_1")
        assert [e.seq for e in entries] == [0, 1, 2]
        assert entries[0].prev_hash is None
        assert entries[1].prev_hash == entries[0].chain_hash
        assert verify_entries(entries)["valid"]

    def test_review_flag_recorded(self, tmp_path: Path) -> None:
        _evaluator, call, decision = _deny()
        sink = JsonlSink(tmp_path / "audit.jsonl")
        logger = AuditLogger(sink)
        entry = logger.log(decision, call, session_id="s", reviewed=False)
        assert entry.policy_reviewed is False

    def test_from_dict_round_trips_new_fields(self, tmp_path: Path) -> None:
        _evaluator, call, decision = _deny()
        entry = AuditLogger(JsonlSink(tmp_path / "a.jsonl")).log(
            decision, call, session_id="s", decision_id="dec_1",
            policy_hash="sha256:abc", matched_rule="forbid-x", reviewed=True,
        )
        entry = chain_entry(entry, None, seq=0)
        assert AuditEntry.from_dict(entry.to_dict()) == entry


class TestTamperChain:
    def _entries(self) -> list[AuditEntry]:
        return [
            AuditEntry(session_id="s1", timestamp="2026-01-01T00:00:00", tool="t1",
                       tool_category=None, action="read", action_class="read",
                       environment="staging", data_class="public", agent_id="a1",
                       agent_class=None, decision="allow", criticality="low",
                       reason_code="ok", explanation="ok"),
            AuditEntry(session_id="s1", timestamp="2026-01-01T00:01:00", tool="t2",
                       tool_category=None, action="write", action_class="write",
                       environment="staging", data_class="public", agent_id="a1",
                       agent_class=None, decision="allow", criticality="low",
                       reason_code="ok", explanation="ok"),
        ]

    def test_chain_assigns_seq_and_entry_hash(self) -> None:
        first = chain_entry(self._entries()[0], None, seq=0)
        second = chain_entry(self._entries()[1], first.chain_hash, seq=1)
        assert first.seq == 0 and second.seq == 1
        assert second.prev_hash == first.chain_hash
        assert second.entry_hash == second.chain_hash

    def test_renumbering_is_detected(self) -> None:
        chained = []
        prev: str | None = None
        for i, e in enumerate(self._entries()):
            chained.append(chain_entry(e, prev, seq=i))
            prev = chained[-1].chain_hash
        import dataclasses

        # Renumber the second entry; its content hash changes → link mismatch.
        chained[1] = dataclasses.replace(chained[1], seq=99)
        result = verify_entries(chained)
        assert not result["valid"]
        assert result["tampered_index"] == 1

    def test_entry_head_is_the_last_link(self) -> None:
        chained = []
        prev: str | None = None
        for i, e in enumerate(self._entries()):
            chained.append(chain_entry(e, prev, seq=i))
            prev = chained[-1].chain_hash
        assert entry_head(chained) == chained[-1].chain_hash

    def test_rotation_anchor_commits_to_prior_head(self) -> None:
        entries = [chain_entry(self._entries()[0], None, seq=0)]
        anchor = rotation_anchor(entries, at="2026-01-02T00:00:00Z")
        assert anchor["kind"] == "audit_rotation_anchor"
        assert anchor["prev_head"] == entries[0].chain_hash
        assert anchor["count"] == 1
        assert verify_rotation(anchor, entries[0].chain_hash)
        assert not verify_rotation(anchor, "deadbeef")

    def test_rotation_anchor_of_empty_log(self) -> None:
        anchor = rotation_anchor([], at="2026-01-02T00:00:00Z")
        assert anchor["prev_head"] is None
        assert anchor["count"] == 0


class TestPolicyVersioning:
    def test_revision_hash_matches_policy(self) -> None:
        rev = policy_revision(policy_mod.BASE_POLICY, version="0.1.0")
        assert rev.policy_hash == policy_mod.policy_hash(policy_mod.BASE_POLICY)
        assert rev.policy_hash.startswith("sha256:")
        assert rev.reviewed is False

    def test_review_flag(self) -> None:
        rev = policy_revision(policy_mod.BASE_POLICY, version="0.1.0",
                              reviewed=True, reviewed_by="alice")
        assert rev.reviewed is True
        assert rev.reviewed_by == "alice"

    def test_is_reviewed_uses_the_reviewed_set(self) -> None:
        rev = policy_revision(policy_mod.BASE_POLICY, version="0.1.0")
        assert is_reviewed(rev, {rev.policy_hash})
        assert not is_reviewed(rev, {"sha256:other"})

    def test_unreviewed_change_is_flagged(self) -> None:
        rev = policy_revision(policy_mod.BASE_POLICY, version="0.1.0")
        assert review_warning(rev, {rev.policy_hash}) is None
        assert review_warning(rev, set()) == "unreviewed_policy_change"

    def test_an_explicit_review_is_never_flagged(self) -> None:
        rev = PolicyRevision(version="0.1.0", policy_hash="sha256:x", reviewed=True)
        assert review_warning(rev, set()) is None

    def test_changing_the_policy_changes_the_hash(self) -> None:
        a = policy_revision(policy_mod.BASE_POLICY, version="0.1.0")
        b = policy_revision(policy_mod.BASE_POLICY + "\n// change", version="0.1.0")
        assert a.policy_hash != b.policy_hash


class TestEvidenceArtifact:
    def test_evidence_binds_action_rule_version_event(self) -> None:
        evaluator, call, decision = _deny()
        artifact = build_artifact(decision, call, evaluator=evaluator)
        evidence = evidence_for(artifact, call)
        payload = evidence.to_dict()
        assert payload["decision"] == "deny"
        assert payload["matched_rule"] == artifact.matched_rule
        assert payload["policy_version"] == artifact.policy_version
        assert payload["policy_hash"] == artifact.policy_hash
        assert payload["event_ref"] == artifact.event_id
        assert payload["hash"].startswith("sha256:")

    def test_offline_verification_re_derives_the_decision(self) -> None:
        evaluator, call, decision = _deny()
        artifact = build_artifact(decision, call, evaluator=evaluator)
        evidence = evidence_for(artifact, call)
        result = evidence.verify(evaluator)
        assert result["valid"] is True
        assert result["rederived_decision"] == "deny"
        assert result["expected_decision"] == "deny"

    def test_tampered_hash_fails_verification(self) -> None:
        evaluator, call, decision = _deny()
        evidence = evidence_for(build_artifact(decision, call, evaluator=evaluator), call)
        tampered = EvidenceArtifact(**{**evidence.__dict__, "hash": "sha256:deadbeef"})
        assert tampered.verify(evaluator)["valid"] is False

    def test_wrong_policy_fails_re_derivation(self) -> None:
        evaluator, call, decision = _deny()
        evidence = evidence_for(build_artifact(decision, call, evaluator=evaluator), call)
        # Re-derive against a policy that permits nothing: outcome changes.
        deny_all = CedarEvaluator("forbid(principal, action, resource);")
        assert evidence.verify(deny_all)["valid"] is False

    def test_from_dict_round_trip(self) -> None:
        evaluator, call, decision = _deny()
        evidence = evidence_for(build_artifact(decision, call, evaluator=evaluator), call)
        assert EvidenceArtifact.from_dict(evidence.to_dict()) == evidence


class TestAuditCli:
    def test_audit_evidence_offline(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert main([
            "audit", "evidence", "--tool", "drop_database", "--action", "delete",
            "--env", "production", "--data", "customer_pii", "--agent", "release-bot",
        ]) == 0
        out = capsys.readouterr().out
        payload = json.loads(out)
        assert payload["decision"] == "deny"
        assert payload["event_ref"].startswith("evt_")
        assert payload["matched_rule"]

    def test_audit_query_shows_provenance(self, tmp_path: Path,
                                          capsys: pytest.CaptureFixture[str]) -> None:
        _evaluator, call, decision = _deny()
        path = tmp_path / "audit.jsonl"
        logger = AuditLogger(JsonlSink(path))
        logger.log(decision, call, session_id="sess_1", policy_hash="sha256:abc",
                   matched_rule="forbid-x")
        assert main(["audit", "query", "--path", str(path), "--session", "sess_1"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload[0]["policy_hash"] == "sha256:abc"
        assert payload[0]["matched_rule"] == "forbid-x"
        assert payload[0]["seq"] == 0
