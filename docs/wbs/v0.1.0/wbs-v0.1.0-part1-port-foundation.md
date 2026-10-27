# WBS v0.1.0 — Part 1: Port the Codebase & Foundation (M0–M1)

**BLUF:** **M0 is a bulk port of the entire predecessor policy-engine codebase** (urgent — it makes agentpolicy
self-contained; the predecessor is retained and made private, never deleted). M1 rebrands and adapts the
foundation (CLI, config, fail-closed, CI gate, policy loader).

> **Standard exit criteria + closure apply to every milestone** — see the [index](wbs-v0.1.0-index.md):
> **design docs first (`.D0`)**, then implement, then close with **`.T` tests · `.C` coverage ≥95% · `.L` ruff +
> `mypy --strict` · `.CR` review · `.D` docs + traceability · `.CI` commit · `.W` WBS checkpoint**.

---

## Milestone M0 — Port the predecessor codebase

**Goal:** move **all** of the predecessor policy-engine codebase (`agent-tooltrust`, MIT) into agentpolicy,
rename the namespace, and get the ported test suite green — after which the source repository is **retained and
made private** (never deleted). This makes agentpolicy self-contained; later milestones re-point the decision
mechanics from a bespoke Python risk scorer to a **Cedar PDP**.

**CUJ:** — (bulk port; no user journey) · **Requirements:** [PRD 10](../../prd/10-feature-parity.md) (absorption
is mandatory and in-repo), [PRD 03](../../prd/03-landscape.md) (migration).

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 0.D0 | **Design docs first** | Porting plan + architecture describing the ported tree | docs | plan reviewed before the port | #4 | — | — |
| 0.1 | **Port** the entire repo tree | Bulk-move `src/`, `tests/`, packs, packaging, tooling, CI, and the docs subset into agentpolicy | full tree present | tree mirrors the source | #5 | — | — |
| 0.2 | **Rename namespace** | predecessor package/CLI (`tooltrust`) → `agentpolicy` across code, tests, configs, docs | renamed | zero predecessor-namespace references remain | #6 | — | — |
| 0.3 | **Preserve git history** | `git filter-repo` / subtree merge | merged history | provenance intact (SHA recorded) | #7 | — | — |
| 0.4 | Adapt packaging metadata | `pyproject.toml` for `agentpolicy` / `agentsec-agentpolicy`, CLI entry point | packaging | `pip install -e .` works | #8 | — | — |
| 0.5 | **Ported suite green** | Get the ported test suite passing with minimal adaptation only | passing tests | ported suite passes | #9 | — | — |
| 0.6 | Record provenance + porting notes | `THIRD_PARTY_NOTICES`, `CHANGELOG` | docs | MIT attribution recorded | #10 | — | — |
| 0.7 | Update design docs | architecture + development describe the ported tree | docs | docs describe the port | #11 | — | — |
| 0.T | Tests | Unit + integration + fault-injection for the ported tree | tests | all new paths covered; coverage ≥ 95% | #12 | — | — |
| 0.C | Coverage gate | Enforce coverage ≥ 95% on this milestone's modules | coverage report | ≥ 95%; no untested new path | #13 | — | — |
| 0.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #14 | — | — |
| 0.CR | Code review | Record findings in [codereview-log.md](codereview-log.md); resolve all | review log | no open findings (port: waived, reviews resume M1) | #15 | — | — |
| 0.D | Docs | Porting notes, architecture, THIRD_PARTY_NOTICES | docs | docs updated + linked here | #16 | — | — |
| 0.CI | Commit & push | Single import commit on the feature branch | git | pushed | — | — | — |
| 0.W | Update WBS | Checkpoint appended to the [index](wbs-v0.1.0-index.md) Progress | WBS | checkpoint recorded | — | — | — |

**Exit criteria**

- [ ] Design docs written first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] The full predecessor codebase is represented in agentpolicy
- [ ] Zero predecessor-namespace references remain; history preserved as a single import commit (SHA recorded)
- [ ] Ported suite green → **predecessor retained and made private (not deleted)** at M25

---

## Milestone M1 — Foundation & identity

**Goal:** agentpolicy identity, CLI, configuration, packaging, and CI — rebranded from the ported tooling — plus
the policy loader/validator and `check` that every later milestone builds on.

**CUJ:** — (foundation) · **Requirements:** [PRD 02](../../prd/02-architecture.md), [PRD 11](../../prd/11-decisions.md)
(DD-15..DD-19), [PRD 13](../../prd/13-non-functional-requirements.md) (R8 partial).

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 1.D0 | **Design docs first** | Foundation design: CLI surface, config model, fail-closed contract, `check` semantics | docs | reviewed before code | #17 | — | — |
| 1.1 | Rebrand build config | Port pyproject/quality-gate tooling; name/bin = `agentpolicy` | build config | `make setup` green | #18 | — | — |
| 1.2 | CLI framework + subcommands | Full command surface (`evaluate`, `explain`, `check`, `init`, `audit`, `pack`, `lint`, `report`, `doctor`, `version`) with **reserved exit codes** | CLI | `agentpolicy --help` lists commands | #19 | — | — |
| 1.3 | Configuration model | Policy/config loading: precedence, `strict`, **fail-closed** on invalid config | config loader | invalid config fails closed (exit 2) | #20 | — | R8 |
| 1.4 | CI & quality gate | `ruff` + `mypy --strict` + `pytest` + coverage ≥95% + DCO | GitHub Actions | CI green on PR | #21 | — | R8 |
| 1.5 | Self-observability | `agentpolicy doctor` + structured logging + per-run audit-log skeleton | CLI + logs | doctor reports a verdict | #22 | — | — |
| 1.6 | Policy loader + validator + `check` | Parse/validate Cedar policy; line/column errors; never operate broken | loader + CLI | malformed policy refused; `check` reports location | #23 | — | R2, R8 |
| 1.7 | Identity & governance docs | README/LICENSE/CODEOWNERS/SECURITY finalized; PRD traceability wired | docs | docs match identity | #24 | — | — |
| 1.T | Tests | Config fail-closed, CLI smoke, doctor, loader/`check` errors | tests | all new paths covered; coverage ≥ 95% | #25 | — | — |
| 1.C | Coverage gate | Enforce coverage ≥ 95% on this milestone's modules | coverage report | ≥ 95%; no untested new path | #26 | — | — |
| 1.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #27 | — | — |
| 1.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | review log | no open findings | #28 | — | — |
| 1.D | Docs | Development guide, CLI reference, README, traceability | docs | docs updated + linked here | #29 | — | — |
| 1.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 1.W | Update WBS | Checkpoint appended to the index Progress | WBS | checkpoint recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] `make setup/lint/typecheck/test` work; `agentpolicy --help` lists subcommands
- [ ] Bad config / malformed policy fails closed; CI green

---

Part 1 green ⇒ agentpolicy is self-contained (the predecessor is retained privately); proceed to
[Part 2 (M2–M3)](wbs-v0.1.0-part2-decision-core-normalization.md).
