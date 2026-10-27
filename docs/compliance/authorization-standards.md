# Authorization & Policy Standards — Conformance

agentpolicy is a **Policy Decision Point (PDP)**. It is built on the established authorization standards and
exposes a **conformant AuthZEN** surface. This document states exactly what is implemented and how it maps.

## NIST SP 800-162 — Guide to ABAC (the model)

NIST SP 800-162 defines Attribute-Based Access Control and the PDP/PEP split. agentpolicy adopts it directly:

| NIST 800-162 concept | agentpolicy |
|---|---|
| **Subject / principal** (attributes) | `principal` — `agent_id`, `agent_class`, `delegation_chain[]` |
| **Resource** (attributes) | `resource` — `tool`, `target`, `data_class`, `attributes{}` |
| **Action / operation** | `action` — canonical `verb` + `args` + `tool_category` |
| **Environment / context** | `context` — `environment`, `session_id`, `budget_state`, `time`, `prior_decisions[]` |
| **Policy Decision Point (PDP)** | **agentpolicy** — evaluates policy, returns a decision |
| **Policy Enforcement Point (PEP)** | agentgate, agentseatbelt/agentkernel, agentkeys, agenthalt, harness hooks |
| **Policy Administration Point (PAP)** | git (the policy repo) — reviewed like code |
| **Obligations / advice** | Cedar `advice` (e.g. `human_gate = "required"`, step-up `acr_values`) |

## XACML (OASIS) — the origin of the pattern

agentpolicy adopts XACML's **PDP/PEP/PAP** architecture and its decision-with-obligations model, without the XML
encoding. Cedar replaces the XACML policy language; the decision contract is preserved.

## ISO/IEC 29146 — access control framework

Terminology alignment: agentpolicy separates **policy decision** (agentpolicy) from **policy enforcement**
(the enforcers) from **policy administration** (git + review). It does not conflate them.

## AuthZEN Authorization API 1.0 — the interop binding (conformant)

Published **Final** by the OpenID Foundation on **11 January 2026**, the Authorization API standardizes PDP↔PEP
communication. agentpolicy implements it:

**Access Evaluation** — `POST /access/v1/evaluation`

```json
{
  "subject":  { "type": "agent", "id": "release-bot", "properties": { "agent_class": "ci-bot" } },
  "action":   { "name": "delete", "properties": { "tool": "drop_database", "args_hash": "sha256:..." } },
  "resource": { "type": "database", "id": "prod", "properties": { "environment": "production", "data_class": "customer_pii" } },
  "context":  { "session_id": "sess_...", "time": "2026-10-26T18:03:00Z" }
}
```

Response (Decision + context):

```json
{
  "decision": false,
  "context": {
    "reason_admin": { "403": "matched rule destructive-command-gate" },
    "reason_user":  { "403": "Delete on production customer-PII data is blocked." },
    "policy_version": "0.1.0"
  }
}
```

| AuthZEN feature | agentpolicy support |
|---|---|
| Access Evaluation API (`/access/v1/evaluation`) | ✅ conformant |
| Access Evaluations API (boxcarring, `evaluations[]`, semantics) | ✅ (`execute_all` / `deny_on_first_deny` / `permit_on_first_permit`) |
| Decision `context` with reasons | ✅ (`reason_admin` / `reason_user`, `policy_version`) |
| **Step-up authentication** in `context` (`acr_values`, `amr_values`) | ✅ (the scope-escalation rule, R11) |
| Search APIs (subject/resource/action discovery, pagination) | ◐ (which actions a subject may perform on a resource) |
| PDP Metadata (`/.well-known/authzen-*`) | ◐ (capabilities advertised) |

> **Swap test:** because the surface is conformant, a conformant AuthZEN PEP can point at agentpolicy, and
> agentpolicy can be replaced by another conformant PDP without changing the ecosystem (R27).

## Cedar — the policy language (CNCF Sandbox)

- Cedar is a **typed, analyzable** policy language, **formally verified** (Lean) and a **CNCF Sandbox** project.
- agentpolicy uses Cedar as the **primary** language; the emerging agent-sandbox default (Leash, brood-box,
  cmcp, CPEX all chose it).
- Because Cedar is analyzable, agentpolicy can **lint** policy (unused/shadowed/over-permissive, R12) and
  **unit-test** it deterministically (R22).

## OPA / Rego — peer backend (import, not replace)

- Orgs already invested in OPA/Rego can evaluate their policy as a **peer backend** with the same decision
  contract (R2, DD-14).
- The Rego backend fails independently: if it is unreachable, Rego-path calls **deny** (`opa_backend_unavailable`)
  while the native Cedar path is unaffected (CUJ-9).
- An OPA→Cedar **migration assistant** is planned for v0.3.0 (R13).

## OpenFGA — relationship context (consumed)

Where an org uses OpenFGA (ReBAC), relationship tuples (agent→tool→resource) are consumed as **context** for a
decision; agentpolicy does not replace the ReBAC store.

## Conformance testing

- An **AuthZEN conformance test** runs in CI against the published spec (target: v0.1.0).
- A **Cedar conformance suite** validates the engine against the Cedar spec examples.
- The results are published in the release's compatibility/standards table.
