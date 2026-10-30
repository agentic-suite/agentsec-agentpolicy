# TODO — v0.1.0 · milestone M0 (Port the predecessor codebase)

Branch: `feat-0.1.0` · Source: `agent-tooltrust` (MIT, `agentic-suite/agent-tooltrust`, retained + made private, never deleted)

Issue range: #4–#16 · WBS: [Part 1](docs/wbs/v0.1.0/wbs-v0.1.0-part1-port-foundation.md) · Index: [index](docs/wbs/v0.1.0/wbs-v0.1.0-index.md)

## Checklist (one ticket at a time — RED → GREEN)

- [ ] **0.D0** (#4) — Design docs first: porting plan + architecture describing the ported tree
- [x] **0.1** (#5) — Port the entire repo tree (`src/`, `tests/`, packs, packaging, tooling, CI, docs subset)
- [x] **0.2** (#6) — Rename namespace `tooltrust` → `agentpolicy` (code, tests, configs, docs)
- [ ] **0.3** (#7) — Preserve git history (`git filter-repo` / subtree merge); record SHA
- [ ] **0.4** (#8) — Adapt packaging metadata (`pyproject.toml` → `agentsec-agentpolicy`, CLI entry point)
- [ ] **0.5** (#9) — Ported suite green (minimal adaptation only)
- [ ] **0.6** (#10) — Record provenance + porting notes (`THIRD_PARTY_NOTICES`, `CHANGELOG`)
- [ ] **0.7** (#11) — Update design docs (architecture + development describe the ported tree)
- [ ] **0.T** (#12) — Tests (unit + integration + fault-injection for the ported tree)
- [ ] **0.C** (#13) — Coverage gate ≥ 95%
- [ ] **0.L** (#14) — Lint & type gate (`ruff` zero; `mypy --strict` clean)
- [ ] **0.CR** (#15) — Code review (port: waived; reviews resume M1)
- [ ] **0.D** (#16) — Docs (porting notes, architecture, `THIRD_PARTY_NOTICES`)
- [ ] **0.CI** (process) — Commit & push on `feat-0.1.0`
- [ ] **0.W** (process) — WBS checkpoint appended to index Progress

## Milestone gate (run once, at the end)

- [ ] Full suite green · coverage ≥ 95% · `ruff` zero · `mypy --strict` clean
- [ ] Checkpoint recorded in the WBS index Progress section
- [ ] All M0 issues closed/commented

## Source facts (agent-tooltrust)

- src: 100 `.py` files, ~14.1k LOC · tests: 88 `.py` (+field/ui) ~13.1k LOC · 5 rule packs · 1 CI workflow
- Packages: `adapters analytics audit cli engine field integrations policy server taxonomy`
- CLI entry point: `tooltrust` → `agentpolicy`
