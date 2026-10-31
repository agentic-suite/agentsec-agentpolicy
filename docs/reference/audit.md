# Audit, provenance & offline evidence — reference (v0.1.0)

The decision log is forensic evidence ([PRD 17](../prd/17-explain-decision-and-evidence.md) · [PRD 15](../prd/15-data-model.md) · WBS M6).
This page is the operator reference; the design is [audit-tamper-evidence.md](../design/audit-tamper-evidence.md).

## The audit entry

One `AuditEntry` per decision. The provenance + chain fields:

| Field | Meaning |
|---|---|
| `seq` | monotonic position in the log (0-based); part of the chain hash |
| `prev_hash` | the predecessor's `entry_hash` (`None` at the root) |
| `entry_hash` / `chain_hash` | `sha256(prev_hash ‖ sha256(content))` — the link |
| `policy_version` | the governing policy version ("which policy governed this?") |
| `policy_hash` | the governing policy content hash (`sha256:<hex>`) |
| `matched_rule` | the deciding clause (the M5 `clause`) |
| `decision_id` | the M5 join key shared with the emitted agentwatch event |
| `policy_reviewed` | whether the governing policy was reviewed (`null` if unknown) |
| `escalation_id`, `approver` | the linked approval workflow |

## CLI

```sh
agentpolicy audit show   --session sess_abc            # reconstruct a session (JSON)
agentpolicy audit query  --session sess_abc --decision deny --format csv
agentpolicy audit export --format json                 # all entries
agentpolicy audit session --replay sess_abc            # replay (verifies the chain first)
agentpolicy audit verify  --sign                        # verify chain integrity + sign the root
agentpolicy audit evidence --tool drop_database --action delete \
    --env production --data customer_pii --agent release-bot   # offline EvidenceArtifact
```

`audit session --replay` verifies the **whole** log's hash chain before replaying; a tampered, missing, or
un-chained entry aborts with exit 1 rather than reporting invented state. Sinks: `--sink jsonl|sqlite|postgres`
(`--path` / `--url`).

## Tamper evidence

- Each entry's `chain_hash` commits to `prev_hash` + the entry content (including `seq`). Modifying, deleting,
  inserting, or **renumbering** an entry breaks a link — `verify_entries` reports the exact index.
- The head is signed with **ed25519** (`sign_root`); without the private key an attacker cannot produce a valid
  signature, so a rebuilt log fails verification.
- On rotation the sink writes an **anchor** (`audit_rotation_anchor`) committing to the prior segment's head, so a
  rotated segment links to its predecessor across files.

## Offline evidence

`agentpolicy audit evidence …` emits a self-contained `EvidenceArtifact`:

```json
{
  "action": { "tool": "drop_database", "action": "delete", "environment": "production", … },
  "matched_rule": "forbid-destructive-customer-pii",
  "decision": "deny",
  "reason_code": "irreversible_action",
  "policy_version": "0.1.0",
  "policy_hash": "sha256:…",
  "event_ref": "evt_…",
  "hash": "sha256:…"
}
```

A third party re-derives the decision offline (`artifact.verify(evaluator)`): re-evaluates the canonical action
against the pinned policy and confirms the same outcome **and** matched rule, and re-checks the artifact's own
hash. `valid` is `false` on an artifact-hash mismatch, a policy-pin mismatch, or a re-derived mismatch.

## Python

```python
from agentpolicy.audit.evidence import evidence_for
from agentpolicy.audit.versioning import policy_revision, review_warning
from agentpolicy.canonical import canonicalize
from agentpolicy.cedar import CedarEvaluator
from agentpolicy.cedar import policy as policy_mod
from agentpolicy.explain import build_artifact

evaluator = CedarEvaluator()
call = canonicalize(tool="drop_database", action="delete", environment="production",
                    data_class="customer_pii", agent_id="release-bot")
artifact = build_artifact(evaluator.evaluate(call), call, evaluator=evaluator)
evidence = evidence_for(artifact, call)
assert evidence.verify(evaluator)["valid"]

rev = policy_revision(policy_mod.BASE_POLICY, version="0.1.0")
review_warning(rev, set())   # "unreviewed_policy_change"
```
