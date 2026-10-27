# WBS v0.1.0 — Part 4: Audit, Ask & Redaction (M6–M7)

**BLUF:** M6 ships the **audit log, policy versioning and tamper evidence** (CUJ-6, CUJ-20). M7 ships the
**ask round-trip** (the human gate), **redact-and-allow**, and **secrets-in-arguments** (CUJ-10, CUJ-15).

> Standard exit criteria + closure apply to every milestone — see the [index](wbs-v0.1.0-index.md).

---

## Milestone M6 — Audit, policy versioning & tamper evidence

**Goal:** an append-only, **hash-chained** decision log with the policy version + hash on every entry, a
review-required flag on policy changes, and an offline-verifiable evidence artifact.

**CUJ:** **CUJ-6**, **CUJ-20** · **Requirements:** R7.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 6.D0 | **Design docs first** | Audit-log design + hash-chain/anchoring/rotation design + policy-version model | docs | reviewed before code | #75 | — | — |
| 6.1 | Audit log | Append-only decision log; JSONL/SQLite/Postgres sinks; policy version per entry | log | entry per decision | #76 | CUJ-6 | R7 |
| 6.2 | `audit query` / `audit show` | Search/filter by session; export JSON/CSV; approvals linked | CLI | a session reconstructs in < 5 min | #77 | CUJ-6 | R7 |
| 6.3 | Tamper-evident hash chain | `seq`/`prev_hash`/`entry_hash`; rotation commits to the prior head; signed anchor | chain | verification proves unedited history | #78 | CUJ-20 | R7 |
| 6.4 | Policy versioning + review flag | `policy_version` + `policy_hash` in every decision; an unreviewed change is flagged | engine | "which policy governed this?" answerable | #79 | CUJ-6 | R7 |
| 6.5 | Evidence artifact (offline) | `action + matched_rule + policy_version + event_ref`, offline-verifiable | artifact | a third party re-derives the decision offline | #80 | CUJ-20 | R7 |
| 6.T | Tests | Chain integrity (incl. truncate/rotation), version flag, offline verification, export | tests | coverage ≥ 95% | #81 | CUJ-6, CUJ-20 | R7 |
| 6.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #82 | — | — |
| 6.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #83 | — | — |
| 6.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #84 | — | — |
| 6.D | Docs | Audit design + policy-versioning/evidence reference | docs | updated + linked | #85 | — | — |
| 6.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 6.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] A session's decision chain reconstructs and exports defensibly (**CUJ-6**)
- [ ] The chain is verifiable; a truncated/rebuilt log is detectable (**CUJ-20**)

---

## Milestone M7 — Ask round-trip, redaction & secrets-in-args

**Goal:** the **ask** outcome round-trips to a human (action-identity-bound, expiring, timeout=deny);
**redact-and-allow** scrubs secrets/PII from output with receipts; and secrets pasted into **arguments** are
scrubbed/blocked before the call leaves.

**CUJ:** **CUJ-10**, **CUJ-15** · **Requirements:** R18, R20, R38.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 7.D0 | **Design docs first** | Ask-gate state machine + redaction design (output + arguments) + receipt model | docs | reviewed before code | #86 | — | — |
| 7.1 | Ask-gate broker | `ask_id`, action-identity binding, expiry, **timeout = deny** | broker | an approval for X cannot release Y | #87 | CUJ-10 | R18 |
| 7.2 | `agentpolicy approve` / `deny` | CLI resolve an ask; agent resumes with the reason | CLI | approve/deny round-trips | #88 | CUJ-10 | R18 |
| 7.3 | Redact-and-allow | Scrub secrets/PII from tool output; `redact` outcome + receipts (class/count/location) | engine | the secret never reaches the model | #89 | CUJ-15 | R20 |
| 7.4 | Secrets-in-arguments | Detect/redact secrets+PII in tool-call args before the call leaves | engine | arg secret scrubbed with a receipt | #90 | CUJ-15 | R38 |
| 7.T | Tests | Ask replay/expiry/timeout, redaction receipts, arg secrets | tests | coverage ≥ 95% | #91 | CUJ-10, CUJ-15 | R18, R20, R38 |
| 7.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #92 | — | — |
| 7.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #93 | — | — |
| 7.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #94 | — | — |
| 7.D | Docs | Ask-gate design + redaction reference | docs | updated + linked | #95 | — | — |
| 7.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 7.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] Replay/expiry/timeout all deny; the approval is action-identity bound (**CUJ-10**)
- [ ] Output and argument secrets are scrubbed with receipts; the raw value is never persisted (**CUJ-15**)

---

Part 4 green ⇒ decisions are auditable and human-gated; proceed to
[Part 5 (M8–M9)](wbs-v0.1.0-part5-surfaces-postures.md).
