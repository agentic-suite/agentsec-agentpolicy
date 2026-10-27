# PRD 05 — What (Features)

**BLUF:** agentpolicy v0.1.0 is the **decision foundation**: a local-first Cedar PDP that returns
allow/deny/ask/rate-limit/redact for every agent action, with three shipped rule packs (Replit rule,
secret-in-output, MCP allowlist), an `explain-decision` contract, decisions emitted in the agentwatch schema,
and fail-closed degradation — in sub-100 ms (p99). It absorbs the decision model of the shipped predecessor
policy engine and the enforcement intent of **BehaviorGuard**, re-pointed at Cedar.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## v0.1.0 scope

Five outcomes (R1) from Cedar policies (R2), three launch rule packs (R3), a mandatory human-gate class (R4),
explain-decision (R5), decisions in the agentwatch schema (R6), git-reviewed policies (R7), and local-first
sub-100 ms decisions with fail-explicit degradation (R8) — plus the parity essentials: the contextual decision
model (R15), posture presets (R16), the ask round-trip (R18), redact-and-allow (R20), adversarial normalization
(R24), and the delivery surfaces (R28). Local-first, CI-second.

## Requirements

> Priority: **P0** (v0.1.0) · **P1** (v0.2.0) · **P2** (v0.3.0+).

| # | Requirement | Acceptance criterion | Pri |
|---|---|---|---|
| **R1** | Decide **allow / deny / ask / rate-limit / redact** per agent action | All five outcomes demonstrable in automated tests | P0 |
| **R2** | Policies authored in **Cedar**; **OPA/Rego import** supported | First policy written < 1 afternoon for a non-security engineer | P0 |
| **R3** | Ship 3 launch rule packs: (a) destructive-command gate (the **Replit rule**), (b) **secret/PII-in-output** block, (c) **MCP-server allowlist** | Each pack demonstrably blocks its named incident replay (agentdrill) | P0 |
| **R4** | **Mandatory human gate** class: irreversible actions (destructive shell, prod infra APIs, external sends) default to `ask` | Changing the default requires an explicit, logged policy amendment | P0 |
| **R5** | Every decision explainable: `explain-decision` includes matched clause + full action context | 100% of denies traceable to a clause + context | P0 |
| **R6** | Decision events emitted in the **agentwatch schema** | agentwatch record and decision join on a common id | P0 |
| **R7** | Policies as **versioned, reviewable artifacts** (git-compatible; two-party review) | A policy change without review is flagged as an event | P0 |
| **R8** | **Local-first** decisioning, **sub-100 ms p99** inline budget | Measured p99 latency in CI; documented fail-explicit degradation per action class | P0 |
| **R15** | **Contextual decision model** — decide from tool category, action class, environment, data sensitivity, agent class + session context | The same call scores differently across environments/data classes in a test matrix | P0 |
| **R16** | **Posture presets** (`strict`/`balanced`/`permissive`) + `init` scaffold | `agentpolicy init --posture` emits a commented, pre-populated policy (never blank) | P0 |
| **R18** | **Ask-gate round-trip** — `ask_id`, action-identity binding, expiry, timeout=deny | An approval for call X cannot be replayed for call Y; an expired/timed-out ask = deny | P0 |
| **R20** | **Redact-and-allow** — scrub secrets/PII from tool output with receipts | The secret is removed before the model sees it; the receipt records class/count/location | P0 |
| **R22** | **CI policy regression suite** — golden decision fixtures replayed per PR | A change that flips a golden deny→allow fails the build deterministically | P0 |
| **R23** | **Rate/burst limits** per session/agent (the `rate-limit` outcome) | A runaway loop is throttled at the ceiling with a structured reason **and a `retry_after` the agent can honor** | P0 |
| **R24** | **Dispatcher-bypass safety + tool-name normalization** | Obfuscated/smuggled actions normalize to canonical and evaluate against the same policy | P0 |
| **R28** | **Delivery surfaces** — library, CLI, MCP server, HTTP PDP | A non-Python caller and an in-process caller get the same decision | P0 |
| **R30** | **Shadow/dry-run mode + calibration report + canary rollout** | Shadow decisions logged; false-block/miss rates reported; flip is one filter; **enforce on a configurable session percentage (5%→50%→100%)** | P0 |
| **R9** | **Blast-radius budgets** — cumulative per-session capability budgets; exhaustion triggers halt | Budget state in every decision; exhaustion halts with a reason | P1 |
| **R10** | **Exfil-sink rule class** — block outputs carrying secrets/PII from reaching external-sink tools (taint-lite, no ML) | The rule blocks the documented exfil chain and names source + sink | P1 |
| **R11** | **Scope-escalation + step-up rules** — react to authorization-challenge events with narrower-scope issuance | The step-up loop is least-privilege by construction | P1 |
| **R12** | **Rule-pack lint** — unused/shadowed/over-permissive + **cross-pack outcome-conflict** detection + a **literal-secrets-in-policy** check | Lint reports findings with locations; CI can fail on them | P1 |
| **R17** | **Session/context state** — cumulative risk, consent scope, budgets, replayable | `session_id` reconstructs consent + running state for review | P1 |
| **R19** | **Argument-level semantic validation** — regex/range/enum/path-containment/URL allowlist | `SELECT`-only SQL, refund caps, SSRF allowlist, path containment enforced | P1 |
| **R21** | **Discovery-time tool hiding** — don't expose tools an agent can't call | An agent never sees a tool the policy would deny | P1 |
| **R26** | **Adversarial resilience suite** — replay detection, flood resistance | The adversarial sub-matrix passes; every attack logs a distinct reason | P1 |
| **R27** | **AuthZEN PDP interop** — Authorization API 1.0 binding | A conformant AuthZEN caller gets the same decision | P1 |
| **R29** | **Policy-pack catalog + `pack validate`/`pack test`** | A community pack lands via one file + one test file + one PR | P1 |
| **R32** | **Compliance-mapped evidence export** — OWASP ASI/LLM, ATLAS, NIST mappings | Evidence exportable to agentcomply; coverage matrix regenerated per release | P1 |
| **R13** | **OPA→Cedar migration assistant; AuthZEN interop (full)** | A Rego policy migrates with a report | P2 |
| **R14** | **Policy-pack marketplace** — community packs, verified badges | A signed community pack installs and passes `pack test` | P2 |
| **R25** | **Child-agent delegation scope** — delegated scope ⊆ parent scope | A child's escalated scope is rejected (confused-deputy protection) | P2 |
| **R31** | **Fleet/distributed policy sync** — one policy to N PDP nodes | A policy change propagates with drift detection | P2 |
| **R33** | **Change-freeze / maintenance-mode windows** — a policy condition that tightens posture for a declared, audited window | A declared freeze flips the posture for its window and is audited on/off ([PRD 22](22-policy-intelligence-and-governance.md)) | P1 |
| **R34** | **Declarative data-class derivation** — globs/tags/schema hints derive `data_class`, deterministically | An untagged resource resolves; a conflict fails loudly, never silently | P1 |
| **R35** | **Agent enrollment + probation** — first-seen unknown agents get a read-only + audit + ask-on-write posture until classified | An unknown agent's first write returns `ask` with `reason_code=agent_probation` | P1 |
| **R36** | **Approval analytics** — tuning report: top deny reasons, shadow→enforce delta, approval latency, **rubber-stamp gates** | An always-approved gate is flagged in a test corpus | P1 |
| **R37** | **Nearest-permissible-action** — decisions carry `permitted_alternatives[]` (agent-facing, verified-true) | A denied call returns a verified-permissible alternative; no policy internals leak | P1 |
| **R38** | **Secrets-in-arguments** — detect/redact secrets in tool-call arguments before the call leaves | A key pasted into an arg is scrubbed/blocked with a receipt; the raw value is never persisted | P1 |
| **R39** | **Multi-agent governance depth** — delegation-chain evaluation, scope-subset proofs, inter-agent decisions (extends R25) | A child's out-of-parent-scope action is denied naming the chain link | P2 |
| **R40** | **Break-glass elevation with auto-revert** — time-boxed, fully audited posture elevation | Elevation expires without manual action; every decision in the window carries `break_glass_id` | P2 |
| **R41** | **Dual-control approvals** — quorum (default 2) of distinct approvers for the irreversible class | A single approval does not release a dual-control ask | P2 |
| **R42** | **NL policy drafting** (`agentpolicy draft`) — authoring-time candidate generation, advisory only | A draft compiles, passes generated tests + lint, and waits for human review; no ML in the decision path | P2 |
| **R43** | **Policy backtest & PR decision-diff** — replay recorded agentwatch history against a candidate policy; attach the flip set to the PR | Exact flip set over fixture history; read-only, watermarked `backtest`, states coverage + limits ([PRD 23](23-enterprise-adoption-and-governance-hardening.md)) | P1 |
| **R44** | **Narrow-only policy layering** — org baseline → project overlay → session consent; children may only restrict | A widening overlay fails `agentpolicy check` at PR time; the floor holds under layer fuzz | P1 |
| **R45** | **Action-space coverage report** — taxonomy × rules × fleet inventory | Exercised-but-uncovered verbs named loudly; `gap:unexplained` = 0 | P1 |
| **R46** | **Self-attack pack** — shipped pack attacking agentpolicy's own decision surface, run every release | A seeded miss blocks the release; the result is published, misses included | P1 |
| **R47** | **Allow-justification** — every decision names its matched rule, allows included (v0.2.0) | An allowed prod write names the permitting rule + policy version in the decision and audit entry | P1 |

## Feature catalog (v0.1.0)

| # | Feature | Requirement | Origin |
|---|---|---|---|
| F1 | Cedar policy loader + validator (strict; line/column errors) | R2, R7 | new (Cedar) |
| F2 | Action normalizer (MCP / LangGraph / Python / HTTP / dispatcher → canonical action) | R24 | predecessor: dispatcher-bypass safety |
| F3 | Cedar evaluator (deterministic core) + OPA/Rego peer backend | R2 | predecessor: dual authoring backend |
| F4 | Five-outcome decision shaper (`allow`/`deny`/`ask`/`rate-limit`/`redact`) | R1 | predecessor 4-state (extended to 5) |
| F5 | Contextual scoring dimensions + 13-domain action taxonomy | R15 | predecessor: risk dimensions + taxonomy |
| F6 | Posture presets + `agentpolicy init --posture` scaffold | R16 | predecessor: posture presets + scaffold |
| F7 | `explain-decision` artifact (clause, factors, criticality, suggested change) | R5 | predecessor: explainability |
| F8 | Reason codes + SIEM-ready failure taxonomy | R8 | predecessor: failure-mode reason codes |
| F9 | Rule packs (Replit rule, secret-in-output, MCP allowlist) + pack format | R3 | predecessor: policy-pack format |
| F10 | Ask-gate broker (`ask_id`, action-identity binding, expiry, timeout=deny) | R18 | predecessor: escalation round-trip |
| F11 | Redact-and-allow (secret/PII output scrub) + redaction receipts | R20 | predecessor: output inspection |
| F12 | Budget/session store (files, requests, spend, calls) + consent scope | R9, R23 | predecessor: session-state family |
| F13 | Rate/burst limiter (per session/agent) | R23 | predecessor: rate limits |
| F14 | Argument-level semantic validators (regex/range/enum/path/URL) | R19 | predecessor: argument validation |
| F15 | Tool-name normalization + adversarial normalization suite | R24, R26 | predecessor: adversarial normalization |
| F16 | Audit log (JSONL/SQLite/Postgres) with policy version per entry | R6, R7 | predecessor: audit log |
| F17 | Tamper-evident hash chain over the decision log | R7 | predecessor: tamper-evident audit |
| F18 | Event emitter — decisions in the agentwatch security-event schema | R6 | agentwatch schema (new) |
| F19 | Delivery surfaces — library, CLI (`evaluate`/`explain`/`audit`/`check`/`init`/`lint`), MCP server (`evaluate`/`explain`), HTTP PDP | R28 | predecessor: multi-surface delivery |
| F20 | Adapter registry (harness hooks, MCP client wrapper, LangGraph, PydanticAI, OpenAI SDK, CrewAI) | R28 | predecessor: framework adapters |
| F21 | CI regression suite (golden decision fixtures, deterministic drift) | R22 | predecessor: policy regression suite |
| F22 | Shadow/dry-run + counterfactual calibration report | R30 | predecessor: shadow mode + score calibration |
| F23 | Policy lint (unused/shadowed/over-permissive) | R12 | new |
| F24 | Policy `diff`/report (kept vs overridden vs gaps) | R16 | predecessor: policy diff/report |
| F25 | AuthZEN Authorization API 1.0 binding (`/access/v1/evaluation`) | R27 | new (AuthZEN) |
| F26 | Evidence artifact (action + clause + policy version + event ref), offline-verifiable | R5, R6 | agentwatch evidence-bundle pattern |
| F27 | Compliance tagger (OWASP ASI/LLM, MITRE ATLAS) on every rule pack | R32 | predecessor: OWASP mapping |
| F28 | `agentpolicy check` (policy validation, never operate broken) | R2, R8 | predecessor: policy check |
| F29 | Demo reference agent (fs/shell/http/db/git) demonstrating all five outcomes | R1 | predecessor: demo agent |
| F30 | Freeze-window condition + `freeze` context flag + freeze-aware posture switching | R33 | new — the Replit lesson ([PRD 22](22-policy-intelligence-and-governance.md)) |
| F31 | Declarative data-class derivation table (globs/tags/schema) with conflict resolution | R34 | new — unblocks adoption |
| F32 | Enrollment ledger + probation posture + classification flow | R35 | new — policy side of shadow-agent discovery |
| F33 | Approval-analytics report (`agentpolicy report approvals`) with rubber-stamp detection | R36 | new — the HITL honesty layer |
| F34 | Break-glass elevation + auto-revert timer + audit | R40 | new — enterprise pattern |
| F35 | Quorum approvals on the irreversible class | R41 | new — high-security pattern |
| F36 | Delegation-chain evaluation + scope-subset proof + inter-agent decisions | R39 | new — ASI07/ASI08 |
| F37 | `permitted_alternatives[]` + agent-facing replan text (operator split) | R37 | new — denials that replan |
| F38 | `agentpolicy draft` — NL → candidate Cedar + generated tests (authoring-time only) | R42 | new — adoption, boundary-locked |
| F39 | Argument-side secret/PII detection + redaction receipts | R38 | predecessor output-inspection, extended to args |
| F40 | Backtest engine + PR decision-diff (`agentpolicy backtest --history <window> --candidate <policy> --ci`) | R43 | new — [PRD 23](23-enterprise-adoption-and-governance-hardening.md) |
| F41 | Layered policy composition (org → project → session) with the narrow-only invariant at load | R44 | new — the AWS SCP pattern |
| F42 | Coverage report (`agentpolicy report coverage`) — four quadrants, `gap:unexplained` = 0 | R45 | new — agentwatch's own discipline, applied to user policy |
| F43 | Shipped `self-attack` pack + release-cadence CI job | R46 | new — the agentdrill evasion-pack pattern, turned inward |
| F44 | `matched_rule` on all outcomes + allow-justification + allow patterns in analytics | R47 | new — completes the R5 symmetry |

## P1/P2 feature additions

- **R9/F12 budgets** — see [PRD 18](18-blast-radius-budgets.md).
- **R10 exfil-sink + R11 step-up + R29 packs** — see [PRD 16](16-rule-packs.md).
- **R17 session state** — cumulative risk, consent boundaries, replay.
- **R21 tool hiding, R25/R39 child delegation + multi-agent governance** — capability minimization.
- **R13 OPA→Cedar migration, R14 marketplace, R31 fleet sync** — post-v0.1.0.
- **R33–R42 policy intelligence & governance** (freeze windows, data-class derivation, enrollment + probation,
  approval analytics, break-glass, dual-control, nearest-permissible-action, NL drafting, secrets-in-args) —
  full definitions, semantics, and tests in [PRD 22](22-policy-intelligence-and-governance.md).

## Compatibility (harness-agnostic by construction)

> **Non-negotiable:** agentpolicy is agentic-harness-agnostic or explicitly harness-compatible. As a **PDP
> service**, it is harness-agnostic *by construction* — it works for every harness that has any enforcement
> point at all, because it sits behind the enforcer, not inside the harness.

| Tier | Harness / ecosystem | v0.1.0 requirement |
|---|---|---|
| 1 — Coding agents | Claude Code · Cursor · GitHub Copilot · Codex CLI · Gemini CLI | Works day one via any enforcer/hook; exercised through agentgate/agentseatbelt |
| 2 — Frameworks | LangGraph · CrewAI · OpenAI Agents SDK · AutoGen · LlamaIndex · PydanticAI · smolagents | Library + adapter surface; ≥3 adapters by v0.3.0 |
| 3 — Protocol / enterprise | Generic MCP clients · enterprise platforms | MCP-server surface + AuthZEN interop; enterprise via standards |

Full matrix: [PRD 19](19-harness-compatibility.md).

## Explicit non-requirements

- **No ML/classifier in any decision path** — determinism is a product requirement, not a style choice.
- **No console/UI beyond CLI** in v1 — policies are text; review lives in git.
- **No enforcement** — agentpolicy composes the enforcers; it never becomes one.
- **No self-hosted PDP-service hardening story** in v1 — local-first first.
- **No full IAM/IdP** — agentpolicy consumes identity, it does not issue it.

## Standards it must meet

Cedar (primary); OPA/Rego adapter; **AuthZEN Authorization API 1.0** (PDP↔PEP); OTel/agentwatch
security-event schema; every shipped rule pack tagged to OWASP LLM Top-10, OWASP Agentic Top-10 (ASI), and
MITRE ATLAS in a published coverage matrix. See [PRD 20](20-standards-and-claims.md).

## Fit in the ecosystem

The **brain**: every enforcer (agentgate, agentseatbelt, agentkernel, agentkeys issuance) calls it; policyweave
compiles its artifacts outward; agentdrill treats rule packs as test subjects; agentcomply maps its decisions
to controls; agentinbox answers its asks; agentwatch records its decisions; agenthalt reacts to its budget
exhaustion. Dependency position: *agentpolicy ⟵ every enforcer* — it ships early and everything depends on it.

## Success metrics (outcome-level)

- **Adoption friction:** `pip install` → first correct `evaluate()` < 5 min (< 2 min with `init`).
- **Correctness:** 100% on the acceptance matrix (tool × env × action × data class).
- **Explanation usefulness:** reviewers can re-explain any deny in one paragraph; deny reasons are actionable
  (a CI test).
- **Shadow conversion:** % of monitor-mode users who switch to enforce after seeing a "would have blocked X"
  report — the conviction funnel (with agentdiff).
- **Rule packs:** each blocks its named incident replay with zero false positives in CI.
- **Community:** packs contributed (ecosystem health).
