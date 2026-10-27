# agentpolicy

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-green.svg)](LICENSE)
[![Status: planned](https://img.shields.io/badge/status-planned-orange.svg)](docs/prd/README.md)
[![Docs: PRD 00–23](https://img.shields.io/badge/docs-PRD%2000--23-blue.svg)](docs/prd/README.md)

> **Block / limit** — A local-first Cedar policy decision point that returns **allow, deny, ask, rate-limit, or
> redact** for every agent action, explains every decision to the clause, and emits it in the open agentwatch
> security-event schema.

[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/agentic-suite/agentsec-agentpolicy/badge)](https://scorecard.dev/viewer/?uri=github.com/agentic-suite/agentsec-agentpolicy)

Part of the [agentic-suite](https://github.com/agentic-suite) — open-source,
harness-agnostic security for AI agents.

**Status: planned — the PRD is complete, code has not started.** The full requirement set is published early on
purpose so we can be held to it: [PRD 00–23](docs/prd/README.md) (why, features, CUJs, parity, risks,
standards, evidence), eight [ADRs](docs/adr/README.md), and the
[compliance & certification surface](docs/compliance/README.md) (Cedar, XACML/NIST SP 800-162, AuthZEN,
OWASP Agentic Top-10 2026, MITRE ATLAS, NIST AI RMF, ISO/IEC 42001, EU AI Act, OpenSSF/SLSA). Watch or star to
follow progress.

## Why

Every vendor ships a proprietary policy console; every open-source enforcer invents its own YAML. Harness-native
rules (Claude Code `allow`/`ask`/`deny`, Cursor `permissions.json`) are pattern-matching only — they cannot
express *"ask a human before a production write,"* *"10 files per session, then stop,"* or *"block secrets in
tool output from reaching external tools."* And the incident register keeps paying for it: the Replit agent
deleted a production database **during a declared code freeze** — a freeze the agent was told about, but the
stack never enforced.

agentpolicy makes the decision explicit, testable, and portable:

- **Standard language** — policies are written in [Cedar](https://cedarpolicy.com/) (CNCF Sandbox, formally
  verified): typed, analyzable, unit-testable, reviewable like code. OPA/Rego imports as a peer backend.
- **Five outcomes** — `allow` · `deny` · `ask` (human gate, the default for irreversible actions) ·
  `rate-limit` (per-session/budget) · `redact` (allow, but scrub secrets/PII).
- **Shipped rule packs** — the destructive-command gate (the "Replit rule"), secret-in-output, MCP-server
  allowlist, exfil-sink, change-freeze windows, and more — each anchored to a documented incident and verified
  by an [agentdrill](https://github.com/agentic-suite/agentsec-agentdrill) replay in CI.
- **Every decision explained** — `explain-decision` names the matched clause, the factors, and the one change
  that would flip it; allows are as traceable as denies.
- **Blast-radius budgets** — cumulative per-session capability ceilings (*10 files, 20 requests, $5 — then
  stop*). Nobody else ships this.
- **Fail-closed** — unknown tool, malformed policy, timeout, unreachable engine: every failure denies, loudly,
  with a distinct reason code. No path silently allows.
- **Harness-agnostic by construction** — a PDP behind the enforcers (agentgate, agentseatbelt/agentkernel,
  agentkeys, agenthalt, harness hooks); a conformant [AuthZEN](https://openid.net/specs/authorization-api-1_0.html)
  Authorization API 1.0 surface for any caller; policies compiled outward to each harness's native format by
  policyweave.

## Install

```sh
# coming soon — v0.1.0 will ship as:
# pip install agentsec-agentpolicy
```

## The ecosystem

agentpolicy is the **decision layer** of the agentic-suite: every enforcer calls it, [agentwatch](https://github.com/agentic-suite/agentsec-agentwatch)
records its decisions, [agentdrill](https://github.com/agentic-suite/agentsec-agentdrill) proves its rule packs,
[agentcomply](https://github.com/agentic-suite/agentsec-agentcomply) maps its decisions to controls, and
[agenthalt](https://github.com/agentic-suite/agentsec-agenthalt) acts on its budget exhaustion. It absorbs — and
supersedes — the shipped predecessor policy engine's decision model, re-pointed at Cedar.

## Documentation

| Document | Content |
|---|---|
| [PRD 00–23](docs/prd/README.md) | The design of record: why, features (R1–R47), CUJs (33), parity, traceability, budgets, rule packs, standards, evidence |
| [ADRs](docs/adr/README.md) | The load-bearing decisions (Cedar-primary, decide-only, five outcomes, no ML in the decision path, fail-closed, AuthZEN, event schema, predecessor absorption) |
| [Compliance](docs/compliance/README.md) | Authorization standards + OWASP ASI/LLM, ATLAS, NIST AI RMF, ISO 42001, EU AI Act, OpenSSF/SLSA mappings and the certification ladder |

## Security

Report vulnerabilities privately per [SECURITY.md](SECURITY.md) and the
[organization security policy](https://github.com/agentic-suite/.github/blob/main/SECURITY.md). Do not open
public issues for security problems.

## License

Apache-2.0 — see [LICENSE](LICENSE).
