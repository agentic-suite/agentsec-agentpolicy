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
