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
