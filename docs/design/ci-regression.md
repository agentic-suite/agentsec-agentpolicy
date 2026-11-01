# CI Regression Suite & Fail-Closed Hardening — Design (M11, v0.1.0)

**BLUF:** M11 makes the policy engine **regression-gated and provably fail-closed**. Golden decision fixtures
are replayed and a **deny→allow flip fails the build**; a change that **un-blocks a named incident replay** is
rejected (`agentdrill`); the input space is **fuzzed** and every failure path must `deny` with a distinct reason
(0 silent allows); and the **standards coverage matrix** (OWASP ASI/LLM, ATLAS) is exported for agentcomply. M11
closes the **v0.1.0 core**. This is the design of record (`11.D0`); it delivers **CUJ-7**, **CUJ-9** (R22, R8,
R32 partial).

> Status: **Done** — branch `feat-0.1.0`. Modules: `agentpolicy/goldens.py`, `agentpolicy/agentdrill.py`,
> `agentpolicy/compliance.py`, `cli/ci.py`; fuzz tests in `tests/test_m11_ci.py`.

---

## 1. Golden regression suite (`11.1`)

`agentpolicy/goldens.py`:

* `GoldenCase` — `name`, the call fields, `expected_decision`, `expected_reason_code`; loaded from a fixture file
  (`load_cases`, reusing the acceptance-matrix shape).
* `capture(cases, engine)` → `{name: {decision, reason_code}}` — the current decisions (a candidate golden set).
* `detect_flips(baseline, cases, engine)` → `[DriftFinding]` — compares the current decisions to a committed
  **baseline**. A case whose baseline was a **block** (`deny`/`escalate`) and is now `allow` is a **flip** (a
  build-breaker); any other mismatch is `drift`. `GateResult.passed` is False when any flip exists.

The committed baseline is the acceptance matrix (`tests/fixtures/acceptance_matrix.yaml`) + the shipped packs'
`tests.yaml`; the deterministic engine makes capture stable.

## 2. `agentdrill` replay gate (`11.2`)

`agentpolicy/agentdrill.py`: every launch pack is **incident-anchored** (`metadata.yaml:incident_ref`) and ships
its incident **replay** (`tests.yaml`). `drill_pack(pack_dir)` runs the replay through the pack evaluator;
`unblocked(results)` returns the fixtures whose expected outcome was a **block** but whose current outcome is
`allow` — the "this change un-blocks the Replay incident" finding. `gate(pack_dirs)` fails the PR when any
incident replay is unblocked.

## 3. Fail-closed fuzz (`11.3`)

`tests/test_m11_ci.py`:

* **Property fuzz** (`hypothesis`): random tool/action/environment/data-class strings through the engine must
  **never raise** and must **never allow** a destructive action on production PII; the outcome is always a
  `Decision`.
* **Distinct reasons**: a sweep of every failure path (unknown tool, malformed input, policy parse, argument
  policy, out-of-scope, obligation failure, engine unavailable, …) asserts each `deny` carries a **distinct,
  non-empty** reason code — no two failure classes collapse onto one code and no path silently allows.

## 4. Coverage / evidence export (`11.4`)

`agentpolicy/compliance.py`:

* `CONTROLS` — a curated control list mapping each **OWASP ASI/LLM** and **ATLAS** control to the policy domains
  that cover it.
* `coverage_matrix(packs=…)` — walks the shipped packs (`metadata.yaml: domains`) and reports, per control,
  `covered` (a shipped pack covers one of its domains) — a **computed**, not hardcoded, matrix.
* `export_matrix(target="agentcomply")` — the agentcomply-facing artifact
  (`{target, schema, generated_from, frameworks: {OWASP: {covered, total, controls}, ATLAS: …}}`).
* `agentpolicy compliance export [--json]` exposes it; a CI job regenerates it per release.

## 5. WBS M11 item mapping

| Item | Where |
|---|---|
| 11.D0 design docs first | this document |
| 11.1 golden regression suite | `agentpolicy/goldens.py` |
| 11.2 agentdrill replay gate | `agentpolicy/agentdrill.py` |
| 11.3 fail-closed fuzz | `tests/test_m11_ci.py` (`hypothesis`) |
| 11.4 coverage/evidence export | `agentpolicy/compliance.py`, `cli/ci.py` |
| 11.T/11.C/11.L/11.CR/11.D | tests · coverage · ruff/mypy · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [CI reference](../reference/ci-regression.md) |
