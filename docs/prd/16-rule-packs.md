# PRD 16 — Rule Packs

**BLUF:** A **rule pack** is a versioned, incident-anchored set of Cedar rules + validators + tests. agentpolicy
ships **three launch packs** — the **Replit rule** (destructive-command gate), **secret/PII-in-output**, and the
**MCP-server allowlist** — each of which must demonstrably block its **named incident replay** (verified by
agentdrill). Later versions add the **exfil-sink**, **scope-escalation/step-up**, and domain packs
(cloud/IAM/payment).

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## Pack format

```
packs/<name>/
  metadata.yaml     # name, version, description, incident_ref, min_agentpolicy, license, trust, tags
  rules.cedar       # the Cedar policy (permit/forbid + advice)
  validators.yaml   # optional argument-level semantic validators (regex/range/enum/path/url)
  tests.yaml        # expected decisions (golden fixtures) — `agentpolicy pack test`
  README.md         # one page: what incident it stops, how to adopt, how to tune
```

- Packs are **versioned (semver)** and **signed** on release; a pack change is a reviewed policy change.
- `agentpolicy pack validate` checks schema + Cedar parse + identifier safety; `agentpolicy pack test` runs
  `tests.yaml` deterministically.
- Trust levels: `built-in` / `local` / `external` (external = declarative Cedar + pure validators only).

## Launch packs (v0.1.0) — each anchored to a named incident

| Pack | Stops | Decision | Incident anchor |
|---|---|---|---|
| **destructive-commands** (the **Replit rule**) | Irreversible destructive actions (drop/delete/force-push/destroy) in production | `deny` (hard) or `ask` (irreversible class) | Replit agent deleted a production database during a code freeze (July 2025) |
| **secret-in-output** | Tool outputs carrying secrets/PII reaching the model or an external sink | `redact` (allow + scrub) or `deny` | Credential/exfiltration incidents; secret-in-output patterns |
| **mcp-allowlist** | Calls to MCP servers/tools not on the org allowlist | `deny` (default-deny for unknown servers) | MCP tool poisoning / shadow-tool / rug-pull (Invariant Labs) |

Each launch pack's acceptance test is: **it blocks its named incident replay**, driven by agentdrill against
the deployed stack, with **zero false positives** on the benign twin.

## Later packs

| Pack | Stops | Decision | Version |
|---|---|---|---|
| **exfil-sink** | Tool outputs carrying secrets/PII flowing to external-sink tools (taint-lite, no ML) | `deny` / `redact` | v0.1.x |
| **scope-escalation** | Actions outside a session's consented scope; reacts to 403 step-up challenges | `ask` + step-up request | v0.1.x |
| **cloud-ops** | Destructive/over-broad cloud actions (delete/scale/permission changes) | `ask` / `deny` | v0.2.0 |
| **iam-admin** | Role/key grant or revoke (privilege escalation) | `ask` / `deny` | v0.2.0 |
| **payment** | Transfers/charges/refunds above thresholds | `ask` / `deny` | v0.2.0 |
| **filesystem-write** | Writes/deletes outside project roots (path containment) | `deny` | v0.2.0 |
| **network-egress** | Outbound requests to non-allowlisted hosts (SSRF) | `deny` | v0.2.0 |
| **rate-budget** | Cumulative capability ceilings (files/requests/spend) — see [PRD 18](18-blast-radius-budgets.md) | `rate-limit` | v0.1.x |
| **code-freeze** | Actions during a declared freeze/maintenance window (the Replit condition) — a context-condition pack any policy can reference | tightens to `ask`/`deny` | v0.2.0 ([PRD 22](22-policy-intelligence-and-governance.md) R33) |
| **secrets-in-args** | Secrets/PII pasted into tool-call **arguments** (input side; sibling of the output pack) | `redact` / `deny` | v0.2.0 (R38) |
| **multi-agent-delegation** | Child-agent scope ⊆ parent scope; inter-agent request decisions (delegation-chain rules) | `deny` / `ask` | v0.3.0 (R39) |
| **enrollment-probation** | First-seen unknown agents: read + audit + ask-on-write until classified | `ask` | v0.2.0 (R35) |
| **self-attack** | agentpolicy's **own** decision surface: policy tamper, normalization bypass, ask replay, budget splitting, audit truncation, event forgery — run every release, misses published | blocks the release on a hit | v0.2.0 (R46, [PRD 23](23-enterprise-adoption-and-governance-hardening.md)) |

## Action taxonomy (the canonical vocabulary)

Every tool call from every framework normalizes to a domain + verb. A rule written for `db.drop` covers
PostgreSQL, SQLite, and the MCP database adapter. Baseline risk per verb (shipped default, overridable):

| Domain | Verbs | Baseline risk |
|---|---|---|
| `fs` | read, write, delete, list, move | low→high (delete = critical) |
| `shell` | exec, pipe | high |
| `http` | get, post, put, delete, patch | low→med |
| `db` | query, execute, migrate, drop | low→critical (drop = critical) |
| `git` | status, diff, log, commit, push, force_push, branch, merge, clone | low→critical (force_push = critical) |
| `email` | read, send, delete, search | low→high (send = high) |
| `cloud` | list, describe, create, update, delete, scale | low→critical |
| `secrets` | read, write, rotate, revoke | critical |
| `iam` | read_role, assign_role, revoke_role, create_key | high→critical |
| `payment` | read, refund, transfer, charge | med→critical |
| `approval` | read, approve, deny, delegate | med→critical |
| `search` | query, index, delete_index | low→med |
| `notify` | send_slack, send_teams, send_webhook, page | low→high |

## Pack governance

- **Reviewed like code** — a pack PR is one `metadata.yaml` + `rules.cedar` + `tests.yaml` + a one-page README.
- **Incident anchor required** — every shipped pack names the incident it stops; a pack without a replay is not
  shipped (the "no pack without a proof" rule).
- **Signed + versioned** — packs are semver'd and signed on release; `agentpolicy pack list/info` shows origin.
- **Deprecation** — a superseded pack is deprecated with a migration note, never silently removed.
- **Community packs** — land via the contribution flow (R29), validated by `pack validate`/`pack test`, tagged
  to OWASP ASI/LLM + ATLAS ([PRD 20](20-standards-and-claims.md)).

## What a pack is *not*

- Not a detection rule — packs are **deterministic policy**, not classifiers.
- Not enforcement — a pack produces a **decision**; the enforcer acts on it.
- Not a scanner — tool-description scanning is agentgate's job; the MCP allowlist pack consumes its verdict.
