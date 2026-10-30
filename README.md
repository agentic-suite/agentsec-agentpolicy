<div align="center">

# agentpolicy

[![CI](https://github.com/agentic-suite/agentsec-agentpolicy/actions/workflows/ci.yml/badge.svg)](https://github.com/agentic-suite/agentsec-agentpolicy/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![Status: in development](https://img.shields.io/badge/status-in%20development-orange)](docs/wbs/v0.1.0/wbs-v0.1.0-index.md)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000)](https://github.com/astral-sh/ruff)
[![Type checked](https://img.shields.io/badge/mypy-strict-blue)](https://github.com/python/mypy)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/agentic-suite/agentsec-agentpolicy/badge)](https://scorecard.dev/viewer/?uri=github.com/agentic-suite/agentsec-agentpolicy)

**A local-first Cedar policy decision point for AI-agent actions. Allow, deny, ask, rate-limit, or redact — with
explainable, deterministic, auditable policy.**

Part of the [agentic-suite](https://github.com/agentic-suite) — open-source, harness-agnostic security for AI agents.

</div>

> [!NOTE]
> **Status:** in development — the engine is **ported (M0)**; `v0.1.0` is not on PyPI yet.
> The ported engine currently returns the predecessor's decision model (`allow` / `audit` / `escalate` / `deny`);
> the [WBS](docs/wbs/v0.1.0/wbs-v0.1.0-index.md) re-points it to **Cedar** with the five outcomes below across
> **M2–M23**, and `v0.1.0` tags at **M25**. · **License:** Apache-2.0

---

## Why

Giving an agent a tool is easy. Defining *when* it should be allowed to use it — in which environment, on what
data, under what approval model — is the real problem.

Every vendor ships a proprietary policy console; every open-source enforcer invents its own YAML. Most teams
manage agent tool permissions with **flat allow-lists**: this tool is allowed, that tool is denied. But the same
tool is harmless in staging and dangerous in production. A read query over public docs is not equivalent to a
query over customer-PII. **Flat allow-lists are a reachability control, not an authorization decision.** And the
incident register keeps paying for it: the Replit agent deleted a production database *during a declared code
freeze* — a freeze the agent was told about, but the stack never enforced.

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
  agentkeys, agenthalt, harness hooks); a conformant
  [AuthZEN](https://openid.net/specs/authorization-api-1_0.html) Authorization API 1.0 surface for any caller;
  policies compiled outward to each harness's native format by policyweave.

**Research backing:** <18% of MCP server deployments scope tool permissions; ~80% of orgs report agent actions
beyond intended scope; OWASP classifies tool misuse (ASI02) and privilege abuse (ASI03) as first-class agentic
risks. agentpolicy implements the Policy Decision Point (PDP) pattern converged on by Permit0, Microsoft AGT,
the OPA ecosystem, and OWASP guidance. It absorbs — and supersedes — the shipped predecessor policy engine's
decision model, re-pointed at Cedar.

---

## What It Is

### The Decision Pipeline

```
 Tool Call → NORMALIZE → SCORE → DECIDE → EXPLAIN → AUDIT
```

agentpolicy scores every tool invocation across five risk dimensions and returns one of five outcomes:

| Outcome | Meaning | When |
|---------|---------|------|
| **Allow** | Execute normally | Low risk (read-only in staging, public data) |
| **Deny** | Blocked with reason | Critical risk (delete in production, PII access, destructive ops) |
| **Ask** | Human approval required | High risk / irreversible (write in production, sensitive-data mutation) |
| **Rate-limit** | Throttled — retry after `retry_after` | Budget/burst exhausted by a runaway agent |
| **Redact** | Allow, but scrub secrets/PII from the result | Sensitive tool output |

> **(Current ported engine:** `allow` / `audit` / `escalate` / `deny` — `audit` folds into always-on event
> emission, `escalate` becomes `ask`, and `rate-limit` + `redact` are added at the Cedar re-point, M2–M23.)**

### Risk Dimensions

| Dimension | Examples | Default weight |
|-----------|----------|---------------|
| Tool category | fs, shell, http, db, git, email, cloud, secrets, iam, payment | 1.0 (domain-dependent) |
| Action class | read (weight 0), write (3), delete (10), grant (10) | 1.0 |
| Environment | staging (0.1), production (0.8), pre-prod (0.6) | 1.0 (org-configurable) |
| Data sensitivity | public (0.0), internal (0.3), restricted (0.7), customer-PII (1.0) | 1.0 (org-configurable) |
| Agent class | ci-bot, support-bot, admin-bot, untrusted | 1.0 (configurable) |

### Starter Action Taxonomy (13 domains, 60+ verbs)

| Domain | Verbs | Baseline risk |
|--------|-------|---------------|
| `fs` (filesystem) | read, write, delete, list, move | low→high |
| `shell` | exec, pipe | high |
| `http` | get, post, put, delete, patch | low→med |
| `db` (database) | query, execute, migrate, drop | low→critical |
| `git` (version control) | status, diff, log, commit, push, force_push | low→critical |
| `email` | read, send, delete, search | low→high |
| `cloud` (infra) | list, describe, create, update, delete, scale | low→critical |
| `secrets` | read, write, rotate, revoke | critical |
| `iam` (identity) | read_role, assign_role, revoke_role, create_key | high→critical |
| `payment` | read, refund, transfer, charge | med→critical |
| `approval` | read, approve, deny, delegate | med→critical |
| `search` | query, index, delete_index | low→med |
| `notify` | send_slack, send_teams, send_webhook, page | low→high |

### Policy Posture Presets (never a blank slate)

```bash
agentpolicy init --posture balanced    # Recommended default
agentpolicy init --posture strict      # Prod fleets, compliance
agentpolicy init --posture permissive  # Local dev, sandboxes
```

### Delivery Modes

| Mode | How | Best for |
|------|-----|----------|
| **Python library** | `pip install agentsec-agentpolicy`; `Engine(...).evaluate(...)` in-process | Zero infra, 15-line integration |
| **MCP client wrapper** | Proxies `tools/call` through the engine | Agents using MCP tool servers |
| **MCP server** | Exposes `evaluate` + `explain` + `authorize_data_source` as MCP tools | Any MCP agent queries authorization |
| **HTTP PDP** | `POST /authorize` returns Decision JSON — language-agnostic | Non-Python fleets, gateways |
| **CLI** | `agentpolicy evaluate`, `audit`, `analytics sessions`, `calibrate report`, `baseline check`, `pack list` | Shell, CI gates |
| **OPAL sync** | Distributed policy propagation to all PDP nodes | Multi-instance fleets |
| **Framework adapters** | Decorators/guards for LangGraph, PydanticAI, OpenAI Agents SDK, CrewAI | Framework-native integration |

---

## Install

`v0.1.0` is not on PyPI yet — the ported engine lands first (**M0**). Install from source:

```sh
git clone https://github.com/agentic-suite/agentsec-agentpolicy.git
cd agentsec-agentpolicy
python -m venv .venv && . .venv/bin/activate
pip install -e .
agentpolicy --help
```

## Quickstart

```bash
agentpolicy init --posture balanced          # -> ./agentpolicy.yaml

# evaluate one tool call
agentpolicy evaluate --tool drop_database --action delete \
  --env production --data customer_pii --agent release-bot
#   Decision      ✗ DENY
#   Reason code   deny_critical_op
#   Explanation   drop_database (delete) in production on customer_pii data is blocked: ...

agentpolicy evaluate --tool query_logs --action read \
  --env staging --data internal --agent debug-bot
#   Decision      ✓ ALLOW   (reason_code allow_low_risk)

# explain *why*, or emit JSON for a harness
agentpolicy explain --tool query_logs --action read \
  --env staging --data internal --agent debug-bot
agentpolicy evaluate --tool query_logs --action read \
  --env staging --data internal --agent debug-bot --format json
```

```python
from agentpolicy.engine.engine import Engine
from agentpolicy.policy.models import default_policy

engine = Engine(default_policy("balanced"))

# Safe read in staging
result = engine.evaluate(
    tool_name="query_logs", action="read",
    environment="staging", data_class="internal",
    agent_id="debug-bot",
)
print(result.decision)    # "allow"
print(result.reason_code) # "allow_low_risk"

# Write in production on sensitive data — human gate
result = engine.evaluate(
    tool_name="deploy_service", action="write",
    environment="production", data_class="restricted",
    agent_id="release-bot",
)
print(result.decision)    # "escalate" (→ "ask" after the Cedar re-point)

# Destructive operation — blocked
result = engine.evaluate(
    tool_name="drop_database", action="delete",
    environment="production", data_class="customer_pii",
    agent_id="release-bot",
)
print(result.decision)    # "deny"

# Framework integration — pick your adapter
from agentpolicy.adapters.langgraph import AgentPolicyToolNode
node = AgentPolicyToolNode(tools, engine=engine)
```

Run `agentpolicy --help` for the full surface (`check`, `audit`, `pack`, `lint`, `report`, `doctor`,
`serve`, `field-test`, …).

---

## Framework Support

| Framework | Adapter | Integration point |
|-----------|---------|-------------------|
| **Raw Python** | `@engine.guard` decorator / `with engine.session():` | Function wrappers |
| **MCP client** | `AgentPolicyMCPWrapper(mcp_client, engine)` | `tools/call` proxy |
| **LangGraph** | `AgentPolicyToolNode(tools, engine)` | ToolNode pre-call interceptor |
| **PydanticAI** | `@agentpolicy_guard(engine)` on `@agent.tool` | Tool decorator |
| **OpenAI Agents SDK** | `agentpolicy_guardrail(engine)` → `@tool_input_guardrail` | Native guardrail API |
| **CrewAI** | `wrap_tool(tool, engine)` | Tool `_run()` wrapper |
| **SWE-bench** | `SWEBenchGuard(engine)` / `agentpolicy swebench` | Coding-agent benchmark wrapper + per-task decision trace |

---

## Security Compliance Baseline

agentpolicy targets three concrete, audit-level security baselines:

| Baseline | v0.1 | v0.2 | v0.3 |
|----------|------|------|------|
| **OWASP Agentic AI Top 10** | 5/10 covered | **10/10 covered** | 10/10 full |
| **OpenSSF Best Practices** | Silver | **Silver+** | Gold aspirational |
| **agentpolicy Security Baseline** | Essential | **Hardened** (15/15 checks) | Certified |

See [SECURITY.md](SECURITY.md) for the full OWASP mapping and [SECURITY_BASELINE.md](docs/SECURITY_BASELINE.md)
for the tier-by-tier checklist. Verify your posture locally with `agentpolicy baseline check essential`.

---

## Understanding Criticality — Risk Scenarios

agentpolicy scores every tool call across five dimensions. Here's how the risk ladder works in practice:

| Risk Level | Outcome | Example |
|------------|---------|---------|
| **Low** | Allow | `query_logs` (read) in staging on public data by a CI bot |
| **Medium** | Redact | `read_secrets` (read) in production on restricted data — allowed, secret scrubbed from the result |
| **High** | Ask | `deploy_service` (write) in production on restricted data — requires human approval |
| **Critical** | Deny | `drop_database` (delete) in production on customer PII — blocked |

### Scenario 1 — The CI Bot

A CI/CD pipeline bot queries application logs in staging for debugging:
- **Tool:** `query_logs` | **Action:** `read` | **Env:** `staging` | **Data:** `internal`
- **Result:** **ALLOW** — read-only log query in staging on internal data is low risk.
  All dimensions contribute minimally: action_class=0.00, environment=0.10, data=0.20.

### Scenario 2 — The Support Bot Reads Customer Data

A support bot needs to read customer information to resolve a ticket:
- **Tool:** `read_secrets` | **Action:** `read` | **Env:** `production` | **Data:** `restricted`
- **Result:** **REDACT** — reading sensitive data in production is permitted, but secrets/PII are scrubbed from
  the result and the access is recorded with full context for compliance review.

### Scenario 3 — The Release Bot Deploys

A scheduled release bot pushes a deployment to production:
- **Tool:** `deploy_service` | **Action:** `write` | **Env:** `production` | **Data:** `restricted`
- **Result:** **ASK** — write actions in production require explicit human approval. The bot cannot deploy until
  an on-call engineer approves.

### Scenario 4 — Destructive Operation

An agent attempts to delete a production database containing customer data:
- **Tool:** `drop_database` | **Action:** `delete` | **Env:** `production` | **Data:** `customer_pii`
- **Result:** **DENY** — destructive operation on sensitive data is blocked outright. The explanation suggests:
  "Use a read-only alternative or move to a lower-risk environment."

### Scenario 5 — The Runaway Agent

An agent loops on a tool after its session budget is exhausted:
- **Session budget:** `10 files, 20 requests, $5` | **Call:** the 21st request
- **Result:** **RATE-LIMIT** — the call is throttled with a `retry_after`, and the exhaustion is emitted as a
  security event for [agenthalt](https://github.com/agentic-suite/agentsec-agenthalt) to act on.

---

## The ecosystem

agentpolicy is the **decision layer** of the agentic-suite: every enforcer calls it,
[agentwatch](https://github.com/agentic-suite/agentsec-agentwatch) records its decisions,
[agentdrill](https://github.com/agentic-suite/agentsec-agentdrill) proves its rule packs,
[agentcomply](https://github.com/agentic-suite/agentsec-agentcomply) maps its decisions to controls, and
[agenthalt](https://github.com/agentic-suite/agentsec-agenthalt) acts on its budget exhaustion. It absorbs — and
supersedes — the shipped predecessor policy engine's decision model, re-pointed at Cedar.

---

## Documentation

| Document | Content |
|---|---|
| [PRD 00–23](docs/prd/README.md) | The design of record: why, features (R1–R47), CUJs (33), parity, traceability, budgets, rule packs, standards, evidence |
| [ADRs](docs/adr/README.md) | The load-bearing decisions (Cedar-primary, decide-only, five outcomes, no ML in the decision path, fail-closed, AuthZEN, event schema, predecessor absorption) |
| [Compliance](docs/compliance/README.md) | Authorization standards + OWASP ASI/LLM, ATLAS, NIST AI RMF, ISO 42001, EU AI Act, OpenSSF/SLSA mappings and the certification ladder |
| [WBS](docs/wbs/v0.1.0/wbs-v0.1.0-index.md) | The build of record: **M0–M25**, 277 issues |
| [Architecture](docs/architecture/architecture-v0.1.0.md) | System design, 5-stage pipeline, components, data model |
| [API Reference](docs/reference/api.md) | Engine API, CLI, MCP tools, framework adapters, SWE-bench integration, error codes |
| [Quickstart](docs/reference/quickstart.md) · [Design Decisions](docs/design/design-decisions.md) | Getting started; recorded design decisions with rationale |
| [Demo Scenario](docs/design/demo-scenario.md) · [Demo Agent](examples/demo-agent/README.md) | Runnable 5-call narrative + adversarial variant, with captured output |
| [CONTRIBUTING.md](CONTRIBUTING.md) · [GOVERNANCE.md](GOVERNANCE.md) | Development setup; project decision-making and releases |
| [SECURITY.md](SECURITY.md) · [Security Baseline](docs/SECURITY_BASELINE.md) | Vulnerability reporting + OWASP coverage; tier-by-tier checklist |

---

## Milestones

v0.1.0 delivers the entire PRD scope: the Cedar PDP core (five outcomes), the shipped rule packs,
explain-decision + evidence, the audit log, blast-radius budgets, adversarial resilience, AuthZEN interop, and
the world-class additions (freeze windows, enrollment/probation, approval analytics, break-glass, dual-control,
multi-agent governance, nearest-permissible-action, NL drafting, secrets-in-args, backtesting, narrow-only
layering, coverage report, self-attack, allow-justification). **Twenty-six milestones (M0–M25)** across
thirteen detail files — field tests (**M24**) and release readiness (**M25**, which tags `v0.1.0`) are last.

| Range | Intent |
|---|---|
| **M0** | **Port the predecessor policy engine** — the codebase now lives here (done) |
| **M1–M11** | The v0.1.0 core (P0): foundation, Cedar decision core, normalization, packs, explain, audit, ask, surfaces, postures, shadow, CI |
| **M12–M23** | The P1/P2 additions (PRD 18/22/23): budgets, exfil-sink, step-up/AuthZEN, freeze, enrollment, break-glass, drafting, backtest, layering, self-attack, NFRs |
| **M24–M25** | **Field tests** and **release readiness** (tags `v0.1.0`) |

See the [WBS index](docs/wbs/v0.1.0/wbs-v0.1.0-index.md) for the full milestone table and the release gate.

---

## Community

- [Report a bug](https://github.com/agentic-suite/agentsec-agentpolicy/issues/new?template=bug.md)
- [Request a feature](https://github.com/agentic-suite/agentsec-agentpolicy/issues/new?template=feature.md)
- [Security policy](SECURITY.md) — private vulnerability reporting

---

## License

Apache-2.0 © 2026 Debashish Ghosal — see [LICENSE](LICENSE). Incorporates MIT-licensed work from the
predecessor policy engine; see `THIRD_PARTY_NOTICES` for attribution.
