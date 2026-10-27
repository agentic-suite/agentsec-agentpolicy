# agentpolicy docs

Documentation for **agentpolicy** — the local-first Cedar policy decision point (**PDP**) for AI-agent
actions: **allow / deny / ask / rate-limit / redact**. Part of the [agentic-suite](https://github.com/agentic-suite).

> **Status: planned — PRD complete.** The full requirement set is written and published early on purpose so we
> can be held to it: [PRD 00–22](prd/README.md) (why, features, CUJs, parity, standards, evidence) plus the
> [compliance mappings](compliance/README.md), the [ADRs](adr/README.md), and the [WBS](wbs/v0.1.0/wbs-v0.1.0-index.md)
> (**M0–M25**). **The PRD set (00–23) and the WBS are complete.** Code has not started; everything here is the
> design + build plan of record.

## Sections

| Directory / file | Purpose |
|---|---|
| [prd/](prd/) | Product requirements — why, architecture, landscape, CUJs, features, security, metrics, risks, roadmap, decisions, traceability, non-goals, data model, rule packs |
| [design/](design/) | Subsystem designs + decisions + threat model (evaluator, rule packs, explain-decision, budgets) |
| [reference/](reference/) | CLI, policy/rule-pack spec, API, compatibility, errors, limitations, policies |
| [adr/](adr/) | Architecture Decision Records |
| [architecture/](architecture/) | Spec + component architecture (v0.1.0) |
| [wbs/](wbs/) | Work breakdown, by version (index + parts, 2 milestones per file) |
| [plans/](plans/) | Execution plans + testing strategy |
| [field-test/](field-test/) | Field-test plan + report, by version |
| [release/](release/) | Release notes, security audit, claims ledger, verifier |
| [runbooks/](runbooks/) | Operational runbooks |
| [tutorials/](tutorials/) | Hands-on guides |
| [guides/](guides/) | User guide |
| [compliance/](compliance/) | OWASP/ATLAS/NIST/EU/OpenSSF mappings |
| [adapters/](adapters/) | Harness adapters (Claude Code, Cursor, Codex CLI, Gemini CLI, Copilot, MCP clients) |
| [examples/](examples/) · [articles/](articles/) · [skills/](skills/) | Samples, posts, the read-only policy skill |
| [testing/](testing/) | Test plans (unit, conformance, field-test agents, docker) |

## Start here

- [PRD index](prd/README.md) · [Why](prd/01-why.md) · [Architecture](prd/02-architecture.md)
- [ADRs](adr/README.md) · [Compliance & certification](compliance/README.md) · [WBS](wbs/v0.1.0/wbs-v0.1.0-index.md)
- Design docs, runbooks, and tutorials are authored with the build; the PRD set + WBS are the plan of record today.

## Conventions

- **BLUF** — Bottom Line Up Front in major documents.
- **Honesty** — misses and limitations are documented, not hidden.
- **Versioned directories** — each documentation type is organized by version.
