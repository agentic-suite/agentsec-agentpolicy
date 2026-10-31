# Audit, Policy Versioning & Tamper Evidence — Design (M6, v0.1.0)

**BLUF:** M6 makes the decision log **forensic evidence**. Decision entries are **append-only**, carry the
`policy_version` + `policy_hash` that governed them, and are linked into a **hash chain** (`seq` / `prev_hash` /
`entry_hash`) whose head is **signed** (ed25519) and **committed across rotation**, so a truncated or rebuilt log
is detectable. Every decision also produces an **offline-verifiable EvidenceArtifact**
(`action` + `matched_rule` + `policy_version` + `policy_hash` + `event_ref`) a third party can re-derive without
installing agentpolicy. This is the design of record (`6.D0`); it delivers **CUJ-6** and **CUJ-20**
([PRD 17](../../prd/17-explain-decision-and-evidence.md), [PRD 15](../../prd/15-data-model.md), R7).

> Status: **Done** — branch `feat-0.1.0`. Modules: `src/agentpolicy/audit/` (`models.py`, `logger.py`,
> `tamper_proof.py`, `versioning.py`, `evidence.py`, `sinks/`); CLI `agentpolicy audit`.

---

## 1. The audit entry (`6.1`)

One `AuditEntry` per decision, copied flat from the decision + canonical call so a compliance query never re-runs
the engine (PRD 15 `AuditEntry`):

| Field | Meaning |
|---|---|
| `seq` | monotonic position in the log (0-based); covered by the chain hash |
| `prev_hash` | the predecessor's `entry_hash` (`None` at the root) |
| `chain_hash` (PRD alias `entry_hash`) | `sha256(prev_hash + content)` — the entry's link |
| `policy_version`, `policy_hash` | the reviewed artifact that governed the decision (**provenance**) |
| `matched_rule` | the deciding clause (the M5 `clause`) |
| `decision_id` | the M5 join key — a decision, its event, and this entry share one id |
| `timestamp`, `session_id`, `tool`, `action`, `environment`, `data_class`, `agent_id`, `decision`, `criticality`, `reason_code`, `explanation`, `factors`, … | the decision |

`AuditEntry.from_decision(decision, call)` is **tolerant of both decision paths** (the ported engine and the
Cedar core): it reads the common fields directly and the optional ones (`dry_run`, `escalation_id`,
`counterfactual`, `policy_hash`, `matched_rule`) via `getattr`, so the same entry model serves both.

**Sinks.** JSONL (the zero-dependency default), SQLite, and Postgres all persist the same fields; every sink
assigns the next `seq` from its own tail before chaining, so the on-disk order defines the chain. A sink failure
is reported to stderr and never blocks a decision (the decision is already safe to return).

## 2. `audit query` / `audit show` (`6.2`)

`agentpolicy audit show --session <id>` reconstructs a session; `audit query` filters by
`--session/--decision/--agent/--since`; `audit export` writes JSON or CSV. The output includes the provenance
(`policy_version`, `policy_hash`, `matched_rule`, `seq`) and the linked approval fields (`escalation_id`,
`approver`), so a reviewer answers "what happened, under which policy, and who approved it" from one view.
`audit session --replay` reconstructs the session's cumulative risk **only after** verifying the whole log's
chain — a tampered/missing entry aborts (exit 1) rather than replaying invented state.

## 3. Tamper-evident hash chain (`6.3`)

`tamper_proof.py`:

* `chain_entry(entry, prev_hash, *, seq=None)` → a copy with `seq`, `prev_hash`, and
  `chain_hash` (= `entry_hash`) = `sha256(prev_hash ‖ sha256(content))`, where content excludes the derived
  chain fields (`chain_hash`, `prev_hash`, `entry_hash`, `signature`, `public_key`, `root_hash`) but **includes**
  `seq`, so renumbering an entry is detectable.
* `build_hash_chain(entries)` → the chained dicts; `sign_root(chained)` → an ed25519 signature over the head.
* `verify_entries(entries)` → walks the persisted chain; a modified, deleted, inserted, un-chained, or
  renumbered entry fails at a precise index. `verify_chain(chained)` verifies the chain **and** the root
  signature.
* **Rotation.** `rotation_anchor(entries, *, at)` commits to the prior head
  (`{kind: audit_rotation_anchor, prev_head, count, at}`); `verify_rotation(anchor, prior_head)` checks it. The
  JSONL sink writes the anchor before rotating, so a rotated segment links to its predecessor across files.

**Trust model.** An attacker who rewrites an entry must recompute every following `chain_hash`; without the
ed25519 private key they cannot produce a valid root signature, so the chain fails verification.

## 4. Policy versioning + review flag (`6.4`)

`audit/versioning.py`:

* `PolicyRevision(version, policy_hash, reviewed, reviewed_by?, reviewed_at?)` — the pinned provenance record.
* `policy_revision(policies, *, version, reviewed=False, reviewed_by=None, reviewed_at=None)` — builds it; the
  `policy_hash` is the M5 `cedar.policy.policy_hash` (one hash function, no drift).
* `is_reviewed(revision, reviewed_hashes)` and `review_warning(revision, reviewed_hashes)` — a policy whose hash
  is **not** in the reviewed set is flagged (`unreviewed_policy_change`).

Every decision records `policy_version` + `policy_hash` (provenance is answerable: *"which policy governed
this?"*); an unreviewed change is **flagged**, not silently accepted.

## 5. Evidence artifact, offline (`6.5`)

`audit/evidence.py`:

* `EvidenceArtifact(action, matched_rule, decision, reason_code, policy_version, policy_hash, event_ref, hash)`.
* `evidence_for(artifact, call)` — built from the M5 explain artifact; `event_ref` is the artifact's `event_id`
  (the join key), and `hash` is the artifact's content hash over the canonical fields.
* `artifact.verify(evaluator)` — a third party **re-derives the decision offline**: re-evaluates the canonical
  `action` against the pinned policy and confirms the same outcome and matched rule, and re-checks the artifact's
  own hash. Returns `{valid, rederived_decision, expected_decision, artifact_hash}`.

## 6. Fail-closed & invariants

* **No silent allow / provenance:** every decision records `policy_version` + `policy_hash`; a decision without
  provenance is a bug.
* **Integrity:** the log is a hash chain; a broken link (or a missing segment across rotation) is a loud finding
  (`audit verify` / `audit session --replay` exit non-zero).
* **Redaction:** entries never persist raw secret argument values (`audit.redact`); the raw value is never
  written.
* **Determinism:** the chain and the signature inputs are computed from entry content only (no clock/network).

## 7. WBS M6 item mapping

| Item | Where |
|---|---|
| 6.D0 design docs first | this document |
| 6.1 audit log | `audit/models.py`, `audit/logger.py`, `audit/sinks/*` |
| 6.2 `audit query`/`show` | `agentpolicy/cli/audit.py` |
| 6.3 tamper-evident hash chain | `audit/tamper_proof.py` |
| 6.4 policy versioning + review flag | `audit/versioning.py` |
| 6.5 evidence artifact (offline) | `audit/evidence.py` |
| 6.T/6.C/6.L/6.CR/6.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [audit reference](../reference/audit.md) |
