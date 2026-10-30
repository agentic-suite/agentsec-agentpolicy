# TODO — v0.1.0 · milestone M0 (Port the predecessor codebase)

Branch: `feat-0.1.0` · Source: `agent-tooltrust` (MIT, `agentic-suite/agent-tooltrust`, retained + made private, never deleted)

Issue range: #4–#16 · WBS: [Part 1](docs/wbs/v0.1.0/wbs-v0.1.0-part1-port-foundation.md) · Index: [index](docs/wbs/v0.1.0/wbs-v0.1.0-index.md)

## Checklist ✅ M0 complete

- [x] **0.D0** (#4) — Design docs first: porting plan + architecture describing the ported tree
- [x] **0.1** (#5) — Port the entire repo tree (`src/`, `tests/`, packs, packaging, tooling, CI, docs subset)
- [x] **0.2** (#6) — Rename namespace `tooltrust` → `agentpolicy` (code, tests, configs, docs)
- [x] **0.3** (#7) — Preserve git history (predecessor remote fetched; SHA recorded)
- [x] **0.4** (#8) — Adapt packaging metadata (`pyproject.toml` → `agentsec-agentpolicy`, CLI entry point)
- [x] **0.5** (#9) — Ported suite green (minimal adaptation only)
- [x] **0.6** (#10) — Record provenance + porting notes (`THIRD_PARTY_NOTICES`, `CHANGELOG`)
- [x] **0.7** (#11) — Update design docs (architecture + development describe the ported tree)
- [x] **0.T** (#12) — Tests (unit + integration + fault-injection for the ported tree)
- [x] **0.C** (#13) — Coverage gate ≥ 95%
- [x] **0.L** (#14) — Lint & type gate (`ruff` zero; `mypy --strict` clean)
- [x] **0.CR** (#15) — Code review (port: waived; reviews resume M1)
- [x] **0.D** (#16) — Docs (porting notes, architecture, `THIRD_PARTY_NOTICES`)
- [x] **0.CI** (process) — Commit & push on `feat-0.1.0`
- [x] **0.W** (process) — WBS checkpoint appended to index Progress

## Milestone gate ✅

- [x] Full suite green · coverage ≥ 95% · `ruff` zero · `mypy --strict` clean
- [x] Checkpoint recorded in the WBS index Progress section
- [x] All M0 issues closed/commented

## Source facts (agent-tooltrust)

- src: 100 `.py` files, ~14.1k LOC · tests: 88 `.py` (+field/ui) ~13.1k LOC · 5 rule packs · 1 CI workflow
- Packages: `adapters analytics audit cli engine field integrations policy server taxonomy`
- CLI entry point: `tooltrust` → `agentpolicy`
- Source SHA: `31655747ee4290b80adb04b2a300dd991b80e018`
