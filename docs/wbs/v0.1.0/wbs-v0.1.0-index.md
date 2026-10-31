# WBS — agentpolicy v0.1.0 (Index)

**BLUF:** **M0 is a bulk port of the entire predecessor policy-engine codebase** (urgent — it makes agentpolicy
self-contained; the predecessor is retained and made private, never deleted). After the port, v0.1.0 delivers the
**entire PRD scope** — the Cedar PDP core (five outcomes), the shipped rule packs, explain-decision + evidence,
the audit log, blast-radius budgets, adversarial resilience, AuthZEN interop, and the world-class additions
(freeze windows, data-class derivation, enrollment/probation, approval analytics, break-glass, dual-control,
multi-agent governance, nearest-permissible-action, NL drafting, secrets-in-args, backtesting, narrow-only
layering, coverage report, self-attack, allow-justification). **Twenty-six milestones (M0–M25)** across
**thirteen detail files**; **field tests (M24) and release readiness (M25) are last.**

> **Milestone ranges by intent:** **M0–M11** = the v0.1.0 core (P0 requirements) · **M12–M23** = the P1/P2
> additions (PRD 18/22/23) · **M24–M25** = field tests + release. The WBS builds the whole set to one release;
> a leaner v0.1.0 may stop after **M11** (the core) and defer M12–M23 to a later version.

## Standard milestone exit criteria (applies to EVERY milestone)

Every milestone is worked in this order:

1. **Design docs written first** — the milestone's `.D0` work item opens it (design + reference docs for the
   subsystem, written before code).
2. **Implement** the milestone's work items (one ticket at a time: test first (RED) → implement (GREEN)).
3. **Close with the standing gates:**
   - [ ] **All tests pass** (`make test`) — the `.T` work item
   - [ ] **Coverage ≥ 95%** (enforced in CI) — the `.C` work item
   - [ ] **Lint strict clean** — `ruff` zero violations; `mypy --strict` clean — the `.L` work item
   - [ ] **Code review complete** — findings in [codereview-log.md](codereview-log.md), all resolved — `.CR`
   - [ ] **Docs updated** — design/reference docs + the [PRD 12](../../prd/12-traceability.md) requirement → test
     row moves with the work — `.D`
   - [ ] **Committed & pushed** — the work is on the feature branch — `.CI`
   - [ ] **WBS updated** — a dated checkpoint (commit refs + gate result) appended to the Progress section — `.W`

> Every milestone therefore carries **eight standing gate work items** — `.D0` design · `.T` tests · `.C`
> coverage · `.L` lint/types · `.CR` review · `.D` docs · `.CI` commit · `.W` WBS — in addition to its
> implementation items.

## Standard milestone closure (applies to EVERY milestone)

A milestone is **closed** only when all of these hold:

1. **Implemented** — every work item done; no "core slice", no partials.
2. **Tests green** — the milestone's tests pass, and the standard gates run **once at milestone end** (full
   suite, coverage ≥95%, `ruff`, `mypy --strict`) — not per ticket.
3. **Committed & pushed** — the work is on the feature branch, pushed.
4. **Tracking issue closed** — or explicitly commented with status.
5. **Docs updated** — the milestone's design/reference docs updated and linked from this WBS.
6. **Checkpoint recorded** — a dated line appended to the Progress section (commit refs + gate result).
7. **Field tests (M24) and release readiness (M25) are the final milestones** — **M25 tags `v0.1.0`**.

> **One ticket at a time:** per work item, write the test first (RED) → implement (GREEN) → next. Do **not** run
> the full suite between tickets; run it at milestone end only.

## Milestones

| M | Name | Detail file |
|---|---|---|
| **M0** | **Port the predecessor policy engine** (urgent) | [Part 1](wbs-v0.1.0-part1-port-foundation.md) |
| M1 | Foundation & identity | [Part 1](wbs-v0.1.0-part1-port-foundation.md) |
| M2 | Cedar decision core (five outcomes) | [Part 2](wbs-v0.1.0-part2-decision-core-normalization.md) |
| M3 | Action normalization, taxonomy & contextual model | [Part 2](wbs-v0.1.0-part2-decision-core-normalization.md) |
| M4 | Rule packs, pack tooling & policy backends | [Part 3](wbs-v0.1.0-part3-packs-explain.md) |
| M5 | Explain-decision, reason codes & event schema | [Part 3](wbs-v0.1.0-part3-packs-explain.md) |
| M6 | Audit, policy versioning & tamper evidence | [Part 4](wbs-v0.1.0-part4-audit-ask.md) |
| M7 | Ask round-trip, redaction & secrets-in-args | [Part 4](wbs-v0.1.0-part4-audit-ask.md) |
| M8 | Delivery surfaces & adapters | [Part 5](wbs-v0.1.0-part5-surfaces-postures.md) |
| M9 | Posture presets, init, diff & lint | [Part 5](wbs-v0.1.0-part5-surfaces-postures.md) |
| M10 | Shadow mode, calibration & canary | [Part 6](wbs-v0.1.0-part6-shadow-ci.md) |
| M11 | CI regression suite & fail-closed hardening | [Part 6](wbs-v0.1.0-part6-shadow-ci.md) |
| M12 | Session state, blast-radius budgets & rate limits | [Part 7](wbs-v0.1.0-part7-budgets-exfil.md) |
| M13 | Exfil-sink, argument validation & tool hiding | [Part 7](wbs-v0.1.0-part7-budgets-exfil.md) |
| M14 | Step-up, AuthZEN interop & adversarial suite | [Part 8](wbs-v0.1.0-part8-stepup-freeze.md) |
| M15 | Freeze windows & data-class derivation | [Part 8](wbs-v0.1.0-part8-stepup-freeze.md) |
| M16 | Enrollment/probation & approval analytics | [Part 9](wbs-v0.1.0-part9-enrollment-alternatives.md) |
| M17 | Nearest-permissible-action & multi-agent governance | [Part 9](wbs-v0.1.0-part9-enrollment-alternatives.md) |
| M18 | Break-glass & dual-control | [Part 10](wbs-v0.1.0-part10-breakglass-drafting.md) |
| M19 | NL policy drafting | [Part 10](wbs-v0.1.0-part10-breakglass-drafting.md) |
| M20 | Policy backtest & PR decision-diff | [Part 11](wbs-v0.1.0-part11-backtest-layering.md) |
| M21 | Narrow-only layering & action-space coverage report | [Part 11](wbs-v0.1.0-part11-backtest-layering.md) |
| M22 | Self-attack pack & allow-justification | [Part 12](wbs-v0.1.0-part12-selfattack-hardening.md) |
| M23 | NFRs, hardening, parity closure & deferred-optional | [Part 12](wbs-v0.1.0-part12-selfattack-hardening.md) |
| **M24** | **Field tests** (last) | [Part 13](wbs-v0.1.0-part13-fieldtest-release.md) |
| **M25** | **Release readiness** (last; tags `v0.1.0`) | [Part 13](wbs-v0.1.0-part13-fieldtest-release.md) |

## Issues & milestones (GitHub)

**Created 2026-10-26.** Every work item ships as a **GitHub issue** under milestone `0.1.0 — M<n> <name>`
(labels `0.1.0`, `wbs`). Body standard: Why · Behavior/What · How · Data & schema impact · Security & privacy ·
Edge cases · Testing · Risks & mitigations · Acceptance criteria · Dependencies · References · Definition of
done; marker `<!-- wbs:<item_id> -->`. **The `Issue` column in each part file holds the live number.** The two
process items per milestone (`.CI` commit, `.W` WBS checkpoint) are tracked here, not as issues.

**26 milestones · 277 issues** (`agentic-suite/agentsec-agentpolicy`).

| M | Milestone | Issues | M | Milestone | Issues |
|---|---|---|---|---|---|
| M0 | Port the predecessor codebase | #4–#16 | M13 | Exfil-sink, argument validation & tool hiding | #148–#156 |
| M1 | Foundation & identity | #17–#29 | M14 | Step-up, AuthZEN interop & adversarial suite | #157–#166 |
| M2 | Cedar decision core (five outcomes) | #30–#40 | M15 | Freeze windows & data-class derivation | #167–#175 |
| M3 | Action normalization, taxonomy & contextual model | #41–#51 | M16 | Enrollment/probation & approval analytics | #176–#185 |
| M4 | Rule packs, pack tooling & policy backends | #52–#63 | M17 | Nearest-permissible-action & multi-agent governance | #186–#195 |
| M5 | Explain-decision, reason codes & event schema | #64–#74 | M18 | Break-glass & dual-control | #196–#205 |
| M6 | Audit, policy versioning & tamper evidence | #75–#85 | M19 | NL policy drafting | #206–#214 |
| M7 | Ask round-trip, redaction & secrets-in-args | #86–#95 | M20 | Policy backtest & PR decision-diff | #215–#223 |
| M8 | Delivery surfaces & adapters | #96–#106 | M21 | Narrow-only layering & action-space coverage report | #224–#232 |
| M9 | Posture presets, init, diff & lint | #107–#117 | M22 | Self-attack pack & allow-justification | #233–#241 |
| M10 | Shadow mode, calibration & canary | #118–#127 | M23 | NFRs, hardening, parity closure & deferred-optional | #242–#254 |
| M11 | CI regression suite & fail-closed hardening | #128–#137 | M24 | Field tests | #255–#266 |
| M12 | Session state, blast-radius budgets & rate limits | #138–#147 | M25 | Release readiness | #267–#280 |

## Progress

**M0 — Port the predecessor codebase — ✅ closed (2026-10-30).** Branch `feat-0.1.0`.

- **Commits:** `c760f68` (0.1/0.2/0.4) · `8428a74` (0.5) · `354d069` (0.6–0.CR + gates).
- **Ported:** `agent-tooltrust` (MIT; source SHA `31655747ee4290b80adb04b2a300dd991b80e018`) → `agentpolicy`;
  namespace / CLI / dist renamed; project version reset to `0.1.0`.
- **Gate:** suite **1084 passed, 18 skipped** · coverage **95.7%** (`fail_under = 95`) · `ruff` zero ·
  `mypy --strict` clean. Docker CI tests verified locally (16 passed).
- **Items closed:** 0.D0 · 0.1–0.7 · 0.T · 0.C · 0.L · 0.CR · 0.D; 0.CI / 0.W recorded here.
- **Noted (not an M0 defect):** the shipped `packs/*/tools.yaml` use the predecessor's older schema and fail
  `PolicyDocument` validation — pre-existing upstream; **M4** owns pack content.

**M1 — Foundation & identity — ✅ closed (2026-10-30).**

- **Commit:** `91ba95c`. Identity / CLI / config / loader / `check` / `doctor`; reserved exit codes (0/1/2) with
  fail-closed `ConfigError` (exit 2); `make setup`/`cov`/`lint`/`typecheck`; CI coverage gate (`fail_under = 95`);
  foundation design + CLI reference docs.
- **Gate:** suite **1105 passed** · coverage **95.8%** (≥ 95) · `ruff` zero · `mypy --strict` clean.
- **Items closed:** 1.D0 · 1.1–1.7 · 1.T · 1.C · 1.L · 1.CR · 1.D.
- **Noted:** the v0.1.0 **Cedar** policy language is introduced by **M2**; M1 delivers the
  loader/validator/`check` *framework*.

**M2 — Cedar decision core (five outcomes) — ✅ closed (2026-10-30).**

- **Commit:** `2ad5a09`. `src/agentpolicy/cedar/` — Cedar PDP (`cedarpy`), five-outcome shaper, mandatory
  human-gate class, PRD 15/17 decision model (`Decision`/`Factor`/`Explanation`), sub-100 ms p99 latency;
  `cedarpy` added as a dependency.
- **Gate:** suite **1129 passed** · coverage **95.8%** (≥ 95) · `ruff` zero · `mypy --strict` clean.
- **Items closed:** 2.D0 · 2.1–2.5 · 2.T · 2.C · 2.L · 2.CR · 2.D.

**M3 — Action normalization, taxonomy & contextual model — ✅ closed (2026-10-30).**

- **Commit:** `65a1391`. `agentpolicy/canonical.py` (one canonical action → the Cedar request); tool-name
  folding, dispatcher-bypass safety (`git push --force` → `force_push` denied), the 13-domain taxonomy, and the
  contextual matrix.
- **Gate:** suite **1141 passed** · coverage **95.8%** · `ruff` zero · `mypy --strict` clean.
- **Items closed:** 3.D0 · 3.1–3.5 · 3.T · 3.C · 3.L · 3.CR · 3.D.

**M4 — Rule packs, pack tooling & policy backends — ✅ closed (2026-10-30).**

- **Commit:** `c6b6683`. Cedar rule-pack format (`pack_format.py`); the three incident-anchored launch packs
  (destructive-commands / secret-in-output / mcp-allowlist); `pack validate`/`pack test` (both formats); the 5
  legacy catalog packs migrated to the current schema; OPA/Rego peer backend.
- **Gate:** suite **1169 passed** · coverage **95.6%** · `ruff` zero · `mypy --strict` clean.
- **Items closed:** 4.D0 · 4.1–4.6 · 4.T · 4.C · 4.L · 4.CR · 4.D.

**M5 — Explain-decision, reason codes & event schema — ✅ closed (2026-10-31).**

- **Commit:** `fab651e` (see `5.CI`). `agentpolicy/reason_codes.py` (the closed registry — single source of
  truth), `agentpolicy/explain.py` (explain artifact + verified actionability `suggested_change`), the offline
  `agentpolicy explain` CLI (+`--json`), and `agentpolicy/agentwatch.py` (the
  `agentwatch.security_event.v1` / `policy.decision` emitter with the shared `event_id`/`decision_id` join key).
  The Cedar core now extracts the real matched rule (`forbid-*`/`permit-*` `@id`) and stamps
  `policy_version` + `policy_hash` on every decision.
- **Gate:** suite **1201 passed, 2 skipped** · coverage **95.46%** (≥ 95) · `ruff` zero · `mypy --strict` clean.
- **Items closed:** 5.D0 · 5.1–5.5 · 5.T · 5.C · 5.L · 5.CR · 5.D.
- **Re-pointed:** the shaper now emits the PRD-canonical `default_deny` / `secret_detected` (M2 seeds
  `no_matching_permit` / `sensitive_output` retired); `agentpolicy explain` runs the Cedar path offline.

**M6 — Audit, policy versioning & tamper evidence — ✅ closed (2026-10-31).**

- **Commit:** `1796da5` (see `6.CI`). `AuditEntry` carries provenance + the chain
  (`seq`/`prev_hash`/`entry_hash`(=`chain_hash`)/`policy_version`/`policy_hash`/`matched_rule`/`decision_id`);
  every sink (JSONL/SQLite/Postgres) assigns `seq` and persists the provenance; `rotation_anchor` links a rotated
  segment to the prior head; `audit/versioning.py` pins the reviewed policy (`unreviewed_policy_change` flag);
  `audit/evidence.py` produces the **offline EvidenceArtifact** (`verify()` re-derives the decision against the
  pinned policy); `agentpolicy audit evidence` exposes it.
- **Gate:** suite **1223 passed, 2 skipped** · coverage **95.54%** (≥ 95) · `ruff` zero · `mypy --strict` clean.
- **Items closed:** 6.D0 · 6.1–6.5 · 6.T · 6.C · 6.L · 6.CR · 6.D.
- **Re-pointed:** one `AuditEntry` model now serves both the ported engine and the Cedar core; `from_decision`
  reads the path-specific fields via `getattr`. The on-disk format is unchanged apart from the additive columns.

**M7 — Ask round-trip, redaction & secrets-in-args — ✅ closed (2026-10-31).**

- **Commit:** `ee25525` (see `7.CI`). `agentpolicy/ask.py` (ask-gate broker keyed on `ask_id`, action-identity
  bound, **timeout = deny** → `human_gate_timeout`); `agentpolicy approve`/`deny`/`ask list`; `agentpolicy/redaction.py`
  (**redact-and-allow** + **secrets-in-arguments** value scanning, `class`/`count`/`location` receipts; raw value
  never returned or persisted).
- **Gate:** suite **1248 passed, 2 skipped** · coverage **95.37%** (≥ 95) · `ruff` zero · `mypy --strict` clean.
- **Items closed:** 7.D0 · 7.1–7.4 · 7.T · 7.C · 7.L · 7.CR · 7.D.
- **Reused:** the ask identity hash is escalation's `action_identity` (one canonical hash); the redaction pattern
  set is `engine/output_inspector.py` (one pattern list).

**M8 — Delivery surfaces & adapters — ✅ closed (2026-10-31).**

- **Commit:** `5c88224` (see `8.CI`). Library surface `agentpolicy.api.evaluate` (+ exported as
  `agentpolicy.evaluate`); the **validated adapter registry** (`adapters/registry.py`: unknown adapter / missing
  extra / missing kwarg → `ConfigError`, exit 2); a shared `denial_message` rejection shape; all adapters
  re-exported.
- **Gate:** suite **1263 passed, 2 skipped** · coverage **95.07%** (≥ 95) · `ruff` zero · `mypy --strict` clean.
- **Items closed:** 8.D0 · 8.1–8.5 · 8.T · 8.C · 8.L · 8.CR · 8.D.
- **Parity:** library / CLI / MCP / HTTP all delegate to the same engine (MCP+HTTP via `ServerCore`), so a caller
  gets the same decision on every surface (R28).

**M9 — Posture presets, init, diff & lint — ✅ closed (2026-10-31).**

- **Commit:** `ccb2a6a` (see `9.CI`). Commented posture presets; `init` scaffold (`--adapter`/`--scaffold-dir` →
  adapter stub + `QUICKSTART.md`); `diff` now classifies **kept / overridden / gaps** (+`--json`); new
  `agentpolicy lint` (unreachable/over-permissive/unknown-tool/conflict/literal-secret findings, CI-failable);
  new `agentpolicy export` (Cedar source + **policyweave** artifact).
- **Gate:** suite **1286 passed, 2 skipped** · coverage **95.09%** (≥ 95) · `ruff` zero · `mypy --strict` clean.
- **Items closed:** 9.D0 · 9.1–9.5 · 9.T · 9.C · 9.L · 9.CR · 9.D.
- **Reused:** `taxonomy.is_known_tool`, the `output_inspector` pattern set, and the M5 `policy_hash` (no drift).

**M10 — Shadow mode, calibration & canary — ✅ closed (2026-10-31).**

- **Commit:** `61627a9` (see `10.CI`). `agentpolicy/calibration.py` (shadow **false-block/miss** rates +
  counterfactual threshold table); `agentpolicy/canary.py` (**deterministic** session-percentage canary,
  `STAGES = 5/50/100`) integrated into `Engine._finalize` as `canary_percent`; `agentpolicy audit query --dry-run`;
  `agentpolicy calibrate report` (+`--json`).
- **Gate:** suite **1298 passed, 2 skipped** · coverage **95.11%** (≥ 95) · `ruff` zero · `mypy --strict` clean.
- **Items closed:** 10.D0 · 10.1–10.4 · 10.T · 10.C · 10.L · 10.CR · 10.D.
- **Determinism:** canary cohort = `sha256(session_id) % 100`; calibration rates are pure functions of the trail.

**M11 — CI regression suite & fail-closed hardening — ✅ closed (2026-10-31).**

- **Commit:** `748ade9` (see `11.CI`). `agentpolicy/goldens.py` (golden replay + **deny→allow flip** detection);
  `agentpolicy/agentdrill.py` (incident-replay gate: an un-blocked named incident fails the build);
  `agentpolicy/compliance.py` (**computed** OWASP ASI/LLM + ATLAS coverage matrix → agentcomply);
  `agentpolicy goldens check` / `drill check` / `compliance export`; **hypothesis** fuzz (never raises, never
  allows a destructive production-PII action) + a distinct-failure-reason sweep.
- **Gate:** suite **1324 passed, 2 skipped** · coverage **95.11%** (≥ 95) · `ruff` zero · `mypy --strict` clean.
- **Items closed:** 11.D0 · 11.1–11.4 · 11.T · 11.C · 11.L · 11.CR · 11.D.
- **Note:** this closes the **v0.1.0 core** (a leaner release may tag here).

**M12 — Session state, blast-radius budgets & rate limits — ✅ closed (2026-10-31).**

- **Commit:** `616c65b` (see `12.CI`). Generic usage counters + capability ceilings (files/requests/spend/calls);
  `rate_allow` token bucket with **`retry_after`**; budget state on **every** decision; exhaustion → **`rate-limit`**
  (`budget_exhausted`/`rate_limited`); `agenthalt.HaltController` fires a halt event with evidence on hard
  exhaustion.
- **Gate:** suite **1339 passed, 2 skipped** · coverage **95.17%** (≥ 95) · `ruff` zero · `mypy --strict` clean.
- **Items closed:** 12.D0 · 12.1–12.4 · 12.T · 12.C · 12.L · 12.CR · 12.D.
- **Re-pointed:** exhaustion is a reasoned `rate-limit`, not an opaque deny (PRD 18/R9); `call_budget` folds into
  the `calls` dimension.

**M13 — Exfil-sink, argument validation & tool hiding — ✅ closed (2026-10-31).**

- **Commit:** `0efe897` (see `13.CI`). `engine/exfil.py` + `packs/exfil-sink` (exfil-sink rule class — sensitive
  data to an `http`/`email`/`notify` sink is denied, naming **source + sink**); policy-declarable argument
  validators (`regex` / `enum` / `path_root` / `url_allowlist` on `args_policy`); `capabilities` now also hides
  tools the policy **unconditionally denies**.
- **Gate:** suite **1358 passed, 2 skipped** · coverage **95.21%** (≥ 95) · `ruff` zero · `mypy --strict` clean.
- **Items closed:** 13.D0 · 13.1–13.3 · 13.T · 13.C · 13.L · 13.CR · 13.D.

**⬜ M14 — Step-up, AuthZEN interop & adversarial suite.** Next.

## Porting map (predecessor → agentpolicy)

Source: the predecessor policy engine (`agent-tooltrust`, MIT; retired, retained privately, never deleted). The
port is a **bulk move (M0)**; later milestones re-point the decision mechanics from a bespoke Python risk scorer
to a **Cedar PDP**.

| Shipped artifact | Ported at |
|---|---|
| Entire repo tree (`src/`, `tests/`, packs, tooling, packaging, docs subset) | **M0** |
| Decision engine (4-state allow/audit/escalate/deny + risk dimensions) | M0 → re-pointed M2 (five outcomes) |
| Action taxonomy (13 domains) | M0 → re-pointed M3 |
| Explainability + reason codes + criticality | M0 → re-pointed M5 |
| Audit log (JSONL/SQLite/Postgres) + policy version | M0 → re-pointed M6 |
| Escalation round-trip (approval, expiry) | M0 → re-pointed M7 (ask) |
| Delivery surfaces (library, MCP server, HTTP, CLI) + framework adapters | M0 → re-pointed M8 |
| Posture presets + `init` scaffold + policy diff | M0 → re-pointed M9 |
| Shadow mode + score calibration | M0 → re-pointed M10 |
| Session state (cumulative risk, consent scope, budgets) | M0 → re-pointed M12 |
| Argument validation + output inspection | M0 → re-pointed M13/M7 |
| Adversarial normalization (tool names, dispatcher) | M0 → re-pointed M3/M14 |
| OWASP mapping + security baseline | M0 → re-pointed M23 |

> **Predecessor retention:** once M0 lands (code fully represented, ported suite green), agentpolicy is
> self-contained; the predecessor is **made private and retained at M25 — never deleted**.

## PRD coverage matrix (every doc 00–23)

| PRD | Topic | Milestone(s) |
|---|---|---|
| **PRD 00** | Press Release / FAQ | narrative; validated at M25 |
| **PRD 01** | Why | context (all milestones) |
| **PRD 02** | Architecture | M0–M14 |
| **PRD 03** | Landscape / migration / predecessor (private) | M0, M23 |
| **PRD 04** | Users & CUJs (CUJ-1..33) | M2–M22 |
| **PRD 05** | What (Features) R1–R47 | M1–M23 |
| **PRD 06** | Security baseline / own threat model | M14, M22, M23 |
| **PRD 07** | Success metrics / release gate | M11, M24, M25 |
| **PRD 08** | Risks (RK-1..RK-23) | cross-cutting; M23 |
| **PRD 09** | Roadmap | M25 |
| **PRD 10** | Feature parity (absorption ledger) | M0–M23; gate M23, M25 |
| **PRD 11** | Decisions DD-01..DD-32 | cross-cutting (honored every milestone) |
| **PRD 12** | Traceability (maintained) | every milestone |
| **PRD 13** | Non-Functional Requirements | M1, M2, M11, M23 |
| **PRD 14** | Non-goals (scope guard) | every milestone |
| **PRD 15** | Data model + lifecycle | M2, M6 |
| **PRD 16** | Rule packs | M4, M13 |
| **PRD 17** | Explain-decision & evidence | M5, M6 |
| **PRD 18** | Blast-radius budgets | M12 |
| **PRD 19** | Harness compatibility | M8, M25 |
| **PRD 20** | Standards, claims & interop | M14, M23 |
| **PRD 21** | Evidence register & method | cross-cutting |
| **PRD 22** | Policy intelligence & governance | M15–M19 |
| **PRD 23** | Enterprise adoption & governance hardening | M20–M22 |

## Requirements → milestone (R1–R47)

| Req | Milestone(s) | Req | Milestone(s) |
|---|---|---|---|
| R1 five outcomes | M2 | R25 child delegation | M17 |
| R2 Cedar + OPA import | M2, M4 | R26 adversarial suite | M14 |
| R3 3 launch rule packs | M4 | R27 AuthZEN interop | M14 |
| R4 human-gate class | M2 | R28 delivery surfaces | M8 |
| R5 explain-decision | M5 | R29 pack catalog + `pack test` | M4 |
| R6 agentwatch events | M5 | R30 shadow/calibration/canary | M10 |
| R7 versioned policies | M6 | R31 fleet sync (deferred-optional) | M23 |
| R8 local-first/sub-100ms/fail-closed | M1, M2, M11 | R32 compliance evidence export | M11, M23 |
| R9 blast-radius budgets | M12 | R33 freeze windows | M15 |
| R10 exfil-sink rule class | M13 | R34 data-class derivation | M15 |
| R11 scope-escalation + step-up | M14 | R35 enrollment + probation | M16 |
| R12 rule-pack lint | M9 | R36 approval analytics | M16 |
| R13 OPA→Cedar migration (deferred-optional) | M23 | R37 nearest-permissible-action | M17 |
| R14 marketplace (deferred-optional) | M23 | R38 secrets-in-args | M7 |
| R15 contextual model | M3 | R39 multi-agent governance | M17 |
| R16 posture presets + init | M9 | R40 break-glass | M18 |
| R17 session state | M12 | R41 dual-control | M18 |
| R18 ask round-trip | M7 | R42 NL policy drafting | M19 |
| R19 argument validation | M13 | R43 policy backtest | M20 |
| R20 redact-and-allow | M7 | R44 narrow-only layering | M21 |
| R21 tool hiding | M13 | R45 action-space coverage report | M21 |
| R22 CI regression suite | M11 | R46 self-attack pack | M22 |
| R23 rate/burst + retry_after | M12 | R47 allow-justification | M22 |
| R24 dispatcher safety + normalization | M3 | | |

## CUJ → milestone (CUJ-1..33) — the explicit map

| CUJ | Journey (short) | Milestone |
|---|---|---|
| **CUJ-1** | Evaluate one action ("15 lines to a decision") | **M2** |
| **CUJ-2** | Wire into a harness/enforcer | **M8** |
| **CUJ-3** | Understand *why* (explainable) | **M5** |
| **CUJ-4** | Adopt in shadow mode | **M10** |
| **CUJ-5** | Extend with a rule pack | **M4** |
| **CUJ-6** | Prove compliance (decision log) | **M6** |
| **CUJ-7** | Gate a policy PR in CI | **M11** |
| **CUJ-8** | Customize the posture | **M9** |
| **CUJ-9** | Degraded & failure modes | **M11** |
| **CUJ-10** | Ask round-trip | **M7** |
| **CUJ-11** | Adversarial resilience | **M14** |
| **CUJ-12** | Budget the blast radius | **M12** |
| **CUJ-13** | Block an exfil chain | **M13** |
| **CUJ-14** | Ask the gate from anywhere (AuthZEN/MCP) | **M14** |
| **CUJ-15** | Redact a secret (output + arguments) | **M7** |
| **CUJ-16** | Compile one policy to every harness | **M9** |
| **CUJ-17** | Lint the policy | **M9** |
| **CUJ-18** | Rate-limit a runaway agent | **M12** |
| **CUJ-19** | Step-up on scope escalation | **M14** |
| **CUJ-20** | Verify a decision offline | **M6** |
| **CUJ-21** | Declare a change freeze | **M15** |
| **CUJ-22** | Enroll an unknown agent safely | **M16** |
| **CUJ-23** | Find the rubber-stamp gates | **M16** |
| **CUJ-24** | Get a denial I can act on | **M17** |
| **CUJ-25** | Break glass without breaking trust | **M18** |
| **CUJ-26** | Two humans for the irreversible class | **M18** |
| **CUJ-27** | Draft a policy from a sentence | **M19** |
| **CUJ-28** | Delegate without leaking scope | **M17** |
| **CUJ-29** | Backtest a policy change | **M20** |
| **CUJ-30** | Guarantee the floor | **M21** |
| **CUJ-31** | See the uncovered action space | **M21** |
| **CUJ-32** | Verify agentpolicy against itself | **M22** |
| **CUJ-33** | Justify an allow | **M22** |

> Every CUJ appears in exactly one milestone's **CUJ** column in its part file, and every milestone lists the
> CUJs it closes. No CUJ is orphaned; no milestone claims a CUJ it does not deliver.

## Decisions (PRD 11)

DD-01..DD-32 are honored across milestones (e.g., DD-01 decide-only → all; DD-02 Cedar-primary → M2/M4;
DD-03 five outcomes → M2; DD-04 no ML → all (M19 is authoring-time only); DD-05 event schema → M5; DD-06
fail-closed → M1/M11; DD-10 AuthZEN → M14; DD-23 tamper-evident audit → M6). **Open additions** (from
[PRD 21](../../prd/21-evidence-register-and-method.md) §PRD tensions): freeze scope (M15), probation duration
(M16), budget reset/inherit (M12) — to be recorded as DD entries before those milestones close.

## v0.1.0 release gate (all milestones)

- [ ] M0–M25 exit criteria satisfied (incl. absorption + parity closure + design docs)
- [ ] Full PRD coverage delivered + tested; every R1–R47 demonstrated by an acceptance test
- [ ] All five outcomes demonstrable; every deny explainable + actionable; allows justified
- [ ] A policy PR that un-blocks a known incident replay is rejected by CI (agentdrill); goldens deterministic
- [ ] Decisions emitted in the agentwatch schema; audit chain verifiable offline
- [ ] Fail-closed on every failure path; sub-100 ms p99 measured in CI
- [ ] Field tests pass (M24); security audit + compliance matrix + standards coverage + release notes (M25)
- [ ] SBOM + signed artifacts (SLSA/Sigstore); OpenSSF Scorecard grade recorded
- [ ] **Predecessor repository retained and made private (not deleted)**

Review log: [codereview-log.md](codereview-log.md).
