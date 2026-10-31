# Code-review log — agentpolicy v0.1.0

Per-milestone code/design reviews. Each milestone's `.CR` work item records findings here; **all findings must
be resolved before the milestone closes** (see the [WBS index](wbs-v0.1.0-index.md) standard closure).

Format: `#<n> [<milestone> Review] <area> — <finding> → <resolution> (<commit>)`.

## Log

_No reviews yet — M0 (bulk port) waives review; reviews resume at M1._

### M0 — Port the predecessor codebase (0.CR)

Reviewed as a **bulk port** — WBS `0.CR` acceptance: *no open findings (port: waived, reviews resume M1)*.

- **Scope:** the entire ported tree (`src/agentpolicy` — 100 modules; `tests/` — 88 + `field/`/`ui/`; `packs/`;
  tooling; docs subset), renamed from `agent-tooltrust` (`agent_tooltrust` → `agentpolicy`, CLI `tooltrust` →
  `agentpolicy`, `ToolTrust` → `AgentPolicy`). Behavior is intentionally unchanged; the Cedar re-point is M2–M23.
- **Findings:** **none open.**
  - Rename verified mechanically — `tests/test_namespace_rename.py` asserts zero predecessor-namespace
    references in code/config.
  - Port is faithful to source commit `31655747ee4290b80adb04b2a300dd991b80e018` (file-level diff; rename-only).
  - **Noted, deferred (not an M0 defect):** the shipped `packs/*/tools.yaml` use the predecessor's older schema
    and fail `PolicyDocument` validation — **pre-existing upstream** (the predecessor's own loader rejects them);
    pack content is owned by **M4 (rule packs)**.
- **Gates:** suite 1084 passed · coverage ≥ 95% · `ruff` zero · `mypy --strict` clean.
- **Resolution:** waived for the port; substantive code review resumes at **M1**.

### M1 — Foundation & identity (1.CR)

- **Scope:** CLI surface + reserved exit codes; configuration precedence + fail-closed (`exit 2`); policy
  loader/validator + `check`; `doctor` self-observability; CI quality gate; identity docs.
- **Findings & resolutions:**
  - *`check` exited 1 on an invalid policy* → introduced `ConfigError` (exit 2); `main()` now returns
    `exc.exit_code`. Tests updated (`tests/test_check.py`). **Resolved.**
  - *No `doctor` command, no `make setup`, CI had no coverage step* → added `cli/doctor.py`, Makefile
    `setup/cov/lint/typecheck`, and the CI coverage gate (`fail_under = 95`). **Resolved.**
  - *No foundation design doc* → added `docs/design/foundation-design.md` + `docs/reference/cli.md`. **Resolved.**
- **Gates:** suite green · coverage ≥ 95% · `ruff` zero · `mypy --strict` clean.
- **Resolution:** all findings resolved; no open items.

### M2 — Cedar decision core (2.CR)

- **Scope:** the Cedar evaluator (`cedarpy`), the five-outcome shaper, the mandatory human-gate class, the
  PRD 15/17 decision model, and the latency budget (`src/agentpolicy/cedar/`).
- **Findings & resolutions:**
  - *Cedar `x in ["a","b"]` is not string-set membership under `cedarpy`* (silently made irreversible/sensitive
    permits fail) → rewrote `BASE_POLICY` with explicit `||` disjunctions. **Resolved; covered by the matrix.**
  - *A malformed policy returned `NoDecision` instead of raising* → `CedarEvaluator` now inspects
    `diagnostics.errors` and fails fast (`ValueError`). **Resolved; covered by `test_malformed_policy_...`.**
  - *`Factor` accepted out-of-range contributions* → added `__post_init__` validation. **Resolved.**
- **Gates:** suite green · coverage ≥ 95% · `ruff` zero · `mypy --strict` clean.
- **Resolution:** all findings resolved; no open items.

### M3 — Action normalization, taxonomy & contextual model (3.CR)

- **Scope:** the canonical action facade (`canonical.py`), tool-name folding, dispatcher-bypass safety, the
  13-domain taxonomy, and the contextual model.
- **Findings & resolutions:**
  - *No single canonical-action entry point tying every surface to the Cedar request* → added
    `agentpolicy/canonical.py` (`canonicalize` / `canonicalize_command` / `to_cedar_request` / `taxonomy_view`).
    **Resolved.**
  - Confirmed a smuggled dispatcher action (`git push --force`) canonicalizes to `force_push` (class `delete`)
    and is **denied** by the base Cedar policy in production — the predecessor G-1/G-2 gaps stay closed.
- **Gates:** suite green · coverage ≥ 95% · `ruff` zero · `mypy --strict` clean.
- **Resolution:** all findings resolved; no open items.

### M4 — Rule packs, pack tooling & policy backends (4.CR)

- **Scope:** the Cedar rule-pack format (`pack_format.py`), the three launch packs, `pack validate`/`pack test`,
  and the OPA/Rego peer backend.
- **Findings & resolutions:**
  - *The 5 legacy catalog packs failed `PolicyDocument` validation* (predecessor float schema; noted at M0) →
    their `tools.yaml`/`tests.yaml` were migrated to the current strict schema and their stale `allow` goldens
    (legacy 4-state `audit`) regenerated. All 8 packs now validate and pass. **Resolved (this is the M4 fix for
    the M0 finding).**
  - *The Cedar fail-fast probe evaluated the policy against a fixed context*, breaking packs that reference
    other context attributes → switched to a pure parse check (`cedarpy.format_policies`). **Resolved.**
  - *Reused variable for two result types in `cli/pack.py`* (mypy) → renamed. **Resolved.**
- **Gates:** suite green · coverage ≥ 95% · `ruff` zero · `mypy --strict` clean.
- **Resolution:** all findings resolved; no open items.

### M5 — Explain-decision, reason codes & event schema (5.CR)

- **Scope:** the explain artifact + reason-code registry (`reason_codes.py`), actionability (`explain.py`), the
  `agentwatch.security_event.v1` emitter (`agentwatch.py`), the offline `agentpolicy explain` CLI, and the Cedar
  model/evaluator additions (`policy_hash`, `Explanation.clause`, real matched-rule extraction).
- **Findings & resolutions:**
  - *`cedarpy` reports satisfied policies in an unstable (hash) order*, so picking the first rule id made the
    matched rule — and thus the whole `Decision` — **nondeterministic** for a call that matched two `forbid`
    rules (e.g. destructive on production **and** customer-PII) → `CedarEvaluator._matched_rule` now collects the
    annotations and returns the **lexicographically smallest** id, restoring determinism
    (`tests/test_cedar_core.py::TestDeterminism`). **Resolved.**
  - *The M2 reason-code seeds `no_matching_permit` / `sensitive_output` are not in the PRD 17 registry* → M5 is
    the milestone that owns the registry, so the shaper now emits the PRD-canonical `default_deny` /
    `secret_detected`; the dependents' assertions (`tests/test_cedar_core.py`) and the docs
    (`docs/reference/decisions.md`) moved with the work. `reason_codes.py` is now the single source of truth;
    no inline reason-code literals remain in the shaper. **Resolved.**
  - *The ported `agentpolicy explain` printed the legacy 4-state verdict* → re-pointed to the canonicalizer +
    Cedar core and added `--json` (the full explain artifact), per the M5 porting map. **Resolved.**
  - *An emitted event/deduction with a blank join key would silently emit `null`* → `DecisionEvent.to_dict`
    raises `ValueError`; a decision with no `event_id`/`decision_id` is a bug. **Resolved.**
  - *A broad `except` around the actionability search tripped `ruff` S112/RUF100* → extracted `_safe_outcome`
    (returns `None` on failure, no silent `continue`), so a candidate the evaluator rejects simply does not
    count as a flip. **Resolved.**
- **Gates:** suite **1201 passed, 2 skipped** · coverage **95.46%** (≥ 95) · `ruff` zero · `mypy --strict` clean.
- **Resolution:** all findings resolved; no open items.

### M6 — Audit, policy versioning & tamper evidence (6.CR)

- **Scope:** the `AuditEntry` provenance + chain fields, the JSONL/SQLite/Postgres sinks, the tamper-evident hash
  chain + rotation anchor (`tamper_proof.py`), policy versioning + the review flag (`versioning.py`), the offline
  `EvidenceArtifact` (`evidence.py`), and the `agentpolicy audit` CLI (+ the `evidence` subcommand).
- **Findings & resolutions:**
  - *The ported `AuditEntry.from_decision` was bound to the legacy `types.Decision`* (it read
    `decision.dry_run`/`escalation_id`/`counterfactual` directly) → it now reads the shared fields directly and
    the path-specific ones via `getattr`, so **one** entry model serves both the ported engine and the Cedar
    core; the whole audit surface is re-pointable without a parallel model. **Resolved.**
  - *A Cedar decision's `factors` round-tripped unequal* (Cedar `Factor` vs `types.Factor`) → `from_decision`
    normalizes factors to `types.Factor`, so persisted→reloaded entries compare equal
    (`tests/test_m6_audit.py::test_from_dict_round_trips_new_fields`). **Resolved.**
  - *The sinks hardcoded columns and dropped provenance* (`policy_hash`/`matched_rule`/`decision_id`/`seq`) →
    added the columns + migrations to the SQLite and Postgres sinks; JSONL persists the full payload. Provenance
    ("which policy governed this?") is now answerable from every sink. **Resolved.**
  - *No `seq` was assigned, so entry order was implicit* → each sink assigns the next `seq` from its own tail;
    `seq` is folded into the content hash, so **renumbering** an entry is detectable
    (`tests/test_m6_audit.py::test_renumbering_is_detected`). **Resolved.**
  - *JSONL rotation renamed the file without committing to the retiring head* → the sink writes a
    `rotation_anchor` before rotating, and `verify_rotation` checks it, so a rotated segment links to its
    predecessor (rotation never breaks the chain). **Resolved.**
  - *Renaming the chain-bookkeeping field would have invalidated persisted logs* → kept the persisted
    `chain_hash` and exposed PRD 15's `entry_hash` as a read-only alias (`AuditEntry.entry_hash`); the on-disk
    format is unchanged apart from the additive columns. **Resolved.**
- **Gates:** suite **1223 passed, 2 skipped** · coverage **95.54%** (≥ 95) · `ruff` zero · `mypy --strict` clean
  (114 files).
- **Resolution:** all findings resolved; no open items.

### M7 — Ask round-trip, redaction & secrets-in-args (7.CR)

- **Scope:** the ask-gate broker (`ask.py`), `agentpolicy approve`/`deny`/`ask list` (`cli/ask.py`),
  redact-and-allow + receipts (`redaction.py`), secrets-in-arguments value scanning, and the `ask_id` link on the
  Cedar `Decision`.
- **Findings & resolutions:**
  - *The Cedar `ask` outcome had no broker* (only the ported `escalate` path was tracked) → added `AskBroker`
    keyed on `ask_id` with **timeout = deny** (`human_gate_timeout`); `ask.gate(decision, call, broker)` stamps
    `decision.ask_id`. **Resolved.**
  - *A second action-identity hash would have drifted from escalation's* → reused
    `engine.escalation.action_identity` (one canonical hash), so an approval for X cannot release Y on either
    path. **Resolved; covered by `test_approval_for_x_cannot_release_y`.**
  - *The ask resolution reason codes were unregistered* → added `allow_ask_approved` / `deny_ask_denied` /
    `deny_ask_pending` / `deny_ask_unknown` / `deny_action_identity_mismatch` to the M5 registry, so the ask path
    emits only registered codes. **Resolved.**
  - *Redaction duplicated output-inspector patterns* → `redaction.py` imports the single pattern set from
    `engine/output_inspector.py`; no parallel pattern list. **Resolved.**
  - *The ported redactor only stripped named sensitive keys, not pasted secrets* → `redact_argument_values`
    scans argument **values** (free text) and composes with the key-based pass; both emit `class`/`count`/
    `location` receipts and never return the raw value. **Resolved.**
- **Gates:** suite **1248 passed, 2 skipped** · coverage **95.37%** (≥ 95) · `ruff` zero · `mypy --strict` clean
  (117 files).
- **Resolution:** all findings resolved; no open items.

### M8 — Delivery surfaces & adapters (8.CR)

- **Scope:** the library surface (`api.py`), the adapter registry (`adapters/registry.py`), adapter re-exports,
  and the shared rejection shape (`adapters/base.py.denial_message`).
- **Findings & resolutions:**
  - *A Cedar-backed library surface would have diverged from the running server* (MCP/HTTP go through
    `ServerCore` → the ported `Engine`) → the library surface (`api.evaluate`) wraps the **same** engine, so the
    library, CLI, MCP, and HTTP surfaces return the identical decision (R28); parity is proved by
    `tests/test_m8_surfaces.py::TestSurfaceParity`. Re-pointing the server core to Cedar is tracked by the
    budget/session milestones, not M8. **Resolved.**
  - *No adapter registry existed* (only lazy `ImportError`s at call time) → added `registry.py` with
    `available`/`get`/`validate`/`load`; an unknown name, a missing extra, or a missing required kwarg raises
    `ConfigError` (exit 2) **at load**. **Resolved.**
  - *Each adapter invented its own rejection string* → the MCP wrapper and raw adapter now render the shared
    `denial_message(decision)`, so a rejected call carries the outcome + explanation + reason code (replan-able).
    **Resolved.**
  - *Only 6 of ~11 adapters were re-exported* → `adapters/__init__.py` now exports all adapters + the registry
    API. **Resolved.**
- **Gates:** suite **1263 passed, 2 skipped** · coverage **95.07%** (≥ 95) · `ruff` zero · `mypy --strict` clean
  (119 files).
- **Resolution:** all findings resolved; no open items.

### M9 — Posture presets, init, diff & lint (9.CR)

- **Scope:** commented posture presets, the `init` scaffold, the kept/overridden/gaps `diff`, the new
  rule/policy `lint` (`lint.py`, `cli/lint.py`), and the policyweave `export` (`export.py`, `cli/export.py`).
- **Findings & resolutions:**
  - *A commented preset could drift from `default_policy`* → the comment header is emitted by
    `postures._preset_header` and regenerated into the shipped files; the loader ignores comments, so
    `load_policy_text(render_preset(name)) == default_policy(name)` still holds (no drift). **Resolved.**
  - *`lint` needed a taxonomy source for unknown tools* → uses `taxonomy.is_known_tool`; the literal-secret scan
    reuses the `engine/output_inspector` pattern set (one pattern list, no drift). **Resolved.**
  - *`export` needed a policy hash* → reuses `cedar.policy.policy_hash` (the M5/M6 hash function), so the export
    provenance matches the audit/explain provenance. **Resolved.**
  - *Enhancing `diff` risked breaking the shipped output contract* → the legacy `0.7 -> 0.95` / `0.0 -> 0.1`
    lines and the 0/1 exit codes are unchanged; kept/overridden/gaps are added alongside, plus `--json`.
    **Resolved.**
  - *`init` scaffold had to stay backward-compatible* → `--adapter`/`--scaffold-dir` are additive; the default
    `init` output is byte-for-byte the commented preset. **Resolved.**
- **Gates:** suite **1286 passed, 2 skipped** · coverage **95.09%** (≥ 95) · `ruff` zero · `mypy --strict` clean
  (123 files).
- **Resolution:** all findings resolved; no open items.

### M10 — Shadow mode, calibration & canary (10.CR)

- **Scope:** `audit query --dry-run`, the shadow calibration report (`calibration.py`), the deterministic canary
  (`canary.py`) and its engine integration, and shadow docs.
- **Findings & resolutions:**
  - *Canary selection had to be reproducible* (a session must not flicker between enforced and shadowed) → the
    cohort is a stable `sha256(session_id) % 100 < percent`; a missing session id is treated as not-selected
    (safe default) until `percent == 100`. **Resolved; covered by the determinism/cohort tests.**
  - *"False-block/miss rates" need a definition without ground truth* → an explicit, documented counterfactual
    heuristic over the audit trail's `dry_run` + `counterfactual` fields (no new state): a block whose governing
    boundary is low is a false-block candidate; an allow near the critical boundary is a false-miss candidate.
    The report also emits the raw threshold table so the heuristic is auditable. **Resolved.**
  - *Wiring the canary into the engine risked changing full-enforce behaviour* → the canary is folded into
    `_finalize` alongside `dry_run`; `canary_percent == 0` is the historical behaviour and `dry_run=True` always
    wins, so existing shadow tests are unchanged. **Resolved.**
  - *Both shadow modes needed one query in the CLI* → `audit query --dry-run` filters the trail to shadow
    decisions. **Resolved.**
- **Gates:** suite **1298 passed, 2 skipped** · coverage **95.11%** (≥ 95) · `ruff` zero · `mypy --strict` clean
  (125 files).
- **Resolution:** all findings resolved; no open items.
