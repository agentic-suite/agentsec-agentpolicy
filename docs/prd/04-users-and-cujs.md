# PRD 04 — Users and Critical User Journeys

**BLUF:** agentpolicy serves the platform/security engineer running agent workloads (**P1 Maya**, **P2 Ravi**)
and the ecosystem builder/embedder (**P5 Alex**) who needs a decision service to call. The v0.1.0 journeys:
evaluate one action, wire it into a harness/enforcer, understand *why*, adopt in shadow mode, extend with a
rule pack, prove compliance, gate a policy PR, customize the posture, handle failure modes, run the ask
round-trip, resist adversarial bypass, cap the blast radius, block an exfil chain, ask from anywhere, redact a
secret, compile one policy to every harness, lint the policy, rate-limit a runaway, step up on scope
escalation, and verify a decision offline.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## Users

| Persona | Who | What they need from agentpolicy |
|---|---|---|
| **P1 Maya — platform/security lead** | Owns safe defaults for AI tooling across a fleet; chooses posture; defends decisions in review | A posture preset that isn't a blank slate; budgets; a decision log a reviewer can read; fleet-coherent policy |
| **P2 Ravi — security/platform engineer** | Runs agent workloads; owns the deployed enforcement stack | One place to ask *"is this allowed?"*; an explanation for every deny; a CI gate that catches an un-blocking policy change |
| **P5 Alex — ecosystem builder / embedder** | Builds on agentic-suite; ships enforcers/harnesses that must call a PDP | A stable PDP contract (library/CLI/MCP/HTTP/AuthZEN), rule packs to reuse, portable Cedar |
| **Non-security engineer** | Writes their first policy | A language they can read and test; a scaffold with sane defaults; an explain that says what to change |

## Users this is *not* for

- Teams that want a **detection product** or an injection classifier — agentpolicy is deterministic policy
  ([PRD 14](14-non-goals.md)).
- Anyone who wants an **enforcement engine** — agentpolicy composes the enforcers; it owns none.
- Anyone who wants a **sandbox / runtime isolation** — that's agentseatbelt/agentkernel; agentpolicy governs
  the decision, not the runtime.
- Anyone who wants a **full IAM / IdP** — agentpolicy consumes identity, it does not issue it.

## User problems

1. **Flat allow-lists are a reachability control, not an authorization decision.** The same tool is harmless in
   staging and dangerous in production; the same read is fine on public docs and risky on customer data.
2. **"Ask me every time" causes permission fatigue** → users auto-grant durable approvals that silently
   authorize privilege escalation.
3. **Policy logic is scattered** across prompts, wrappers, app code, and undocumented conventions — untested,
   unaudited, no explanations.
4. **Policy changes are unverified** — a rule edit can silently un-block a known attack.
5. **Denials with no reason get bypassed** — black-box decisions destroy trust and adoption.

## Critical user journeys (v0.1.0)

### CUJ-1 — Evaluate one action ("15 lines to a decision")
Ravi runs a small snippet and sees all **five** outcomes returned correctly with readable explanations.

**Acceptance criteria (P0):**

| Scenario | Expected decision | Expected explanation |
|---|---|---|
| Read logs in staging, internal data | `allow` | "Read-only in staging: low risk." |
| Write deploy in production, internal data | `ask` | "Write in production: human approval required." |
| Delete in production, restricted data | `deny` | "Delete in production on restricted data: blocked by clause …" |
| 40th external send this session | `rate-limit` | "Session send budget exhausted (40/40): throttled." |
| Tool output containing an API key, allow path | `redact` | "Allowed with redaction: 1 secret scrubbed from output." |
| Unknown tool name, any context | `deny` | "Unknown tool: default deny." |
| Engine unreachable / malformed policy | `deny` | "Policy unavailable: fail-closed." |

All within ~15 lines of Python, no service, no network call in the hot path.

### CUJ-2 — Wire agentpolicy into a harness or enforcer
Alex hooks agentpolicy into Claude Code (via hooks), Cursor, the MCP proxy (agentgate), or a framework tool
node, and gets safe-by-default without breaking the agent loop.

**Acceptance criteria (P0):** a denied call returns a structured, model-consumable rejection the agent can
replan around; an `ask` pauses the loop; every decision (allow and deny alike) emits an audit entry; the
integration is exercised in the field-test matrix ([PRD 19](19-harness-compatibility.md)).

### CUJ-3 — Understand *why* an action was risky ("explainable, not black-box")
As a reviewer, when a request was escalated or denied, Ravi reads the explanation, identifies the one factor
that drove the decision within 10 seconds, and knows what to change — without reading engine code.

**Acceptance criteria (P0):** the decision carries `decision`, `criticality`, `reason_code`, `explanation`,
and `factors[]` (`{dimension, value, contribution}`); **actionability test:** a human given only the
explanation text and the original action can name the one change (approve, move to staging, lower data class)
that would flip the outcome — without docs. `agentpolicy explain '<action-json>'` prints the full breakdown;
no "denied with no reason" entries. See [PRD 17](17-explain-decision-and-evidence.md).

### CUJ-4 — Adopt incrementally with shadow mode ("trust before you enforce")
Maya deploys agentpolicy in **observe-only** mode first, watches the decisions against a real workload, tunes
the policy, and only then flips enforce — without changing a line of agent code.

**Acceptance criteria (P0):** `evaluate(..., dry_run=True)` returns the decision, logs it, but returns `allow`
to the caller; after N days `agentpolicy audit query --dry-run` shows what *would have* been blocked/escalated;
the shadow→enforced diff is one filter; the calibration report shows false-block/miss rates.

### CUJ-5 — Extend agentpolicy without touching the engine ("one pack, one PR")
As a tool-platform author, Alex defines a new rule pack (or risk function) using a documented schema, validates
it, and the engine scores it — no engine changes.

**Acceptance criteria (P1):** a `rulepack` maps native tool names → canonical actions + typed Cedar rules +
`tests` with expected decisions; `agentpolicy pack validate && agentpolicy pack test` passes with no engine
change; contribution is one file + one test file → one PR; one page of docs is the only reference needed.

### CUJ-6 — Prove compliance ("show me the decision log")
As a compliance reviewer, given a `session_id`, Maya reconstructs the full chain of decisions, exports it, and
traces every `ask` back to its human approver.

**Acceptance criteria (P0):** `agentpolicy audit show --session <id>` prints every decision (timestamp, action,
env, data_class, decision, reason_code, explanation, policy_version, approver); exportable as JSON/CSV;
every `ask` has a linked approval record (who, when, what, expiry); a multi-step chain is reconstructable in
under 5 minutes.

### CUJ-7 — Gate a policy PR in CI
A contributor edits a Cedar policy; CI replays the **golden decision fixtures** and the agentdrill incident
replays.

**Acceptance criteria (P0):** a change that flips a golden `deny` to `allow` fails the build with the exact
clause + fixture; a change that un-blocks a named incident replay is rejected; deterministic (no flakiness).

### CUJ-8 — Customize the risk posture to my org ("not a blank slate")
Maya chooses a **posture preset** (`strict`/`balanced`/`permissive`), then incrementally overrides: her
environments, data classifications, tool categories, thresholds — without touching engine code.

**Acceptance criteria (P0):** `agentpolicy init --posture <name>` generates a commented, pre-populated Cedar
policy (override *down* from a sane default, never build from zero); custom environments/data classes score
the same call differently; `agentpolicy test` confirms overrides don't accidentally permit a dangerous action;
`agentpolicy diff` shows kept vs overridden vs gaps; policy loads from `AGENTPOLICY_PATH` and is PR-reviewable.

### CUJ-9 — Degraded and failure modes ("what happens when it breaks")
As an operator, Ravi knows exactly what happens in every failure condition, and every scenario is safe by
default.

**Acceptance criteria (P0):**

| Failure | Behavior | Why |
|---|---|---|
| Policy engine process crashes / import fails | every `evaluate()` → `deny`, `reason_code=engine_unavailable` | Fail-closed: no authorization → no execution |
| Malformed Cedar policy | engine refuses to load; `agentpolicy check` reports line/column; all calls deny | Never operate with a broken policy |
| OPA backend unreachable (Rego path) | Rego-path calls → `deny`, `opa_backend_unavailable`; native Cedar path unaffected | Dual backend fails independently |
| Evaluation exceeds timeout | `deny`, `evaluation_timeout` | Safety over latency |
| Unknown tool / unparseable action | `deny`, `unknown_action` | No implicit allow |
| Audit sink failure (disk full, Postgres down) | decision stands; write failure logged to stderr; engine continues | Audit is a side effect, not a gating dependency |

No failure mode silently allows. Every reason is a distinct `reason_code` a SIEM can alert on.

### CUJ-10 — Ask round-trip ("human says yes or no, agent continues")
When an action is `ask`, a human approves or denies it; the agent resumes where it left off; the approval is
audited with an expiry.

**Acceptance criteria (P0):** agent calls tool → engine returns `ask` + `ask_id` + reason → agent pauses; human
reviews (CLI `agentpolicy approve <id>` or via agentinbox) → on approve, the engine records an approval bound
to `ask_id` + **action identity** (tool+args hash) so it cannot be replayed for a different call; on deny the
agent gets the reason and replans; approval is time-bounded (default 5 min); an expired approval = deny; a
timeout with no answer = **deny**.

### CUJ-11 — Adversarial resilience ("you can't trick the engine")
As a security reviewer, Ravi attempts to bypass agentpolicy — prompt injection, tool-name obfuscation, OPA
policy tampering, argument smuggling, approval replay, flooding — and every attempt is blocked, logged, and
never silently allowed.

**Acceptance criteria (P0/P1):**

| Attack vector | Expected defense |
|---|---|
| Prompt injection instructing a blocked tool | engine evaluates the *action*, not the prompt; deny stands |
| Tool-name obfuscation (`"deploy_service "`, Unicode lookalikes, case variants) | normalization before matching; unknown normalized name → deny |
| Argument smuggling via dispatcher (`bash: "git push --force"`) | dispatcher input parsed to canonical `(tool, action)` and evaluated against the same policy |
| OPA/Cedar policy tampering | policy version recorded in every decision; hash mismatch detection; tamper → fail-closed |
| Approval replay (reuse an ask token with different args) | approval bound to action identity; replay fails |
| Flooding (rapid calls hoping one slips) | per-session rate/burst limits; every call independently evaluated — no "slip through" path |

Every blocked attempt logs a distinct `reason_code`; the adversarial sub-matrix is part of the field test.

### CUJ-12 — Budget the blast radius (P1 Maya)
Maya caps a session: *"10 files modified, 20 external requests, $5 spent."* When the session exhausts a budget,
the next action is `rate-limit`/halt with a reason, and agenthalt can freeze the run.

**Acceptance criteria (P1):** cumulative counters per session; exhaustion → `rate-limit` (soft) or halt
trigger (hard); the budget state is in every decision; budgets are versioned policy, reviewable in git. See
[PRD 18](18-blast-radius-budgets.md).

### CUJ-13 — Block an exfil chain (P0/P1)
Ravi writes an **exfil-sink** rule: tool outputs carrying secrets/PII must not flow to external-sink tools.

**Acceptance criteria (P1):** the rule blocks the documented exfil chain (taint-lite, no ML); the decision names
the source and the sink; `redact` is offered where a scrub is safe; the pack has a named incident replay.

### CUJ-14 — Ask the gate from anywhere (P5 Alex)
Alex calls agentpolicy over HTTP (**AuthZEN Authorization API 1.0**) or via the MCP server, from a non-Python
host or another PDP.

**Acceptance criteria (P1):** `POST /access/v1/evaluation` returns a conformant AuthZEN decision; the MCP
server exposes `evaluate`/`explain`; a non-Python caller gets the same decision as the in-process path.

### CUJ-15 — Redact-and-allow a secret (P0)
An allowed call returns output containing an API key; agentpolicy returns `redact` with the scrubbed output and
a redaction receipt.

**Acceptance criteria (P0):** the secret is removed before it reaches the model; the decision is `redact`, not
`allow`; the receipt records class/count/location; the raw value is never persisted. *(Extended, R38: the same
holds for a secret pasted into tool-call **arguments** — scrubbed or blocked before the call leaves.)*

### CUJ-16 — Compile one policy to every harness (P5 Alex)
Alex writes one Cedar policy and **policyweave** compiles it into Claude Code rules, Cursor `permissions.json`,
and Codex/Gemini configs.

**Acceptance criteria (v0.1.0):** agentpolicy is the Cedar source of truth and exposes the policy + compiled
artifacts for policyweave; drift between the source and a harness format is flagged.

### CUJ-17 — Lint the policy (P1 Maya)
Maya runs `agentpolicy lint` before merging and catches an over-permissive rule, an unused rule, and a shadowed
rule.

**Acceptance criteria (P1):** the lint reports unused/shadowed/over-permissive rules with locations; CI can
fail on lint findings; the report is deterministic.

### CUJ-18 — Rate-limit a runaway agent (P0/P1)
An agent loops on external sends; agentpolicy returns `rate-limit` after the per-session ceiling.

**Acceptance criteria (P0):** per-session op-count and burst ceilings; the throttled call names the budget; the
agent sees a structured reason it can handle; the audit shows the throttle.

### CUJ-19 — Step-up on scope escalation (P1)
A tool responds 403 "insufficient scope"; agentpolicy maps the authorization-challenge event to a step-up rule
and requests narrower-scope re-issuance (with agentkeys).

**Acceptance criteria (P1):** the step-up rule reacts to the challenge event; the response requests narrower
scope (AuthZEN step-up context); the loop is least-privilege by construction.

### CUJ-20 — Verify a decision offline (public/auditor)
A reviewer downloads a decision's **evidence artifact** (action + matched clause + policy version + event ref)
and verifies it on another machine.

**Acceptance criteria (P0/P1):** the explain artifact + audit entry + agentwatch event ref let a third party
re-derive the decision offline without installing agentpolicy; the artifact is hash-bound to the policy version.

### CUJ-21 — Declare a change freeze (P1 Maya)
A release freeze is declared for the production environment; during the window, every prod write asks a human
— even actions the balanced posture would allow.

**Acceptance criteria (P1):** `agentpolicy freeze declare --env production --until <ts>` (or a git-declared
freeze) flips the posture for the window; decisions inside the window carry `freeze_id`; the freeze on/off
events are audited. The Replit lesson: *"I told the agent not to touch it" is not a control — a declared freeze
the policy enforces is.* ([PRD 22](22-policy-intelligence-and-governance.md) R33/R34.)

### CUJ-22 — Enroll an unknown agent safely (P1 Maya)
A new agent appears in the fleet. It is not denied outright — it runs in **probation** (read + audit + ask on
writes) until Maya classifies it.

**Acceptance criteria (P1):** the first-seen agent's first write returns `ask` with `reason_code=agent_probation`;
classification is a logged event feeding the agentwatch inventory; probation ends only on classification
(R35). See [PRD 22](22-policy-intelligence-and-governance.md).

### CUJ-23 — Find the rubber-stamp gates (P1 Maya)
Maya opens the approval-analytics report and sees which human gates are theater (approved 100% of the time) and
which deny reasons dominate shadow mode.

**Acceptance criteria (P1):** `agentpolicy report approvals` lists gates by approval rate, approval latency, and
shadow→enforce delta; an always-approved gate is flagged with a recommendation (demote to allow+audit or
tighten); the report is computed from the ask/approval records (R36).

### CUJ-24 — Get a denial I can act on (P1 Ravi / the agent)
A denied call returns not just the reason but `permitted_alternatives[]` — verified-permissible variants the
agent can replan to immediately.

**Acceptance criteria (P1):** every alternative is **evaluated-true** against the policy before being returned
(the PDP never suggests something it would deny); the agent-facing text is a curated template with no policy
internals; the operator explanation stays full-fidelity (R37).

### CUJ-25 — Break glass, without breaking trust (P2 Ravi)
An incident needs elevated scope *now*. Ravi triggers a time-boxed break-glass window with a logged reason; it
reverts automatically at expiry.

**Acceptance criteria (P2):** elevation requires a reason; every decision in the window carries `break_glass_id`;
reversion happens without manual action and is a logged event; dual-control class actions still require the
quorum inside the window (R40/R41).

### CUJ-26 — Require two humans for the irreversible class (P2 Maya)
The payment-destruction rule requires **two distinct approvers**. One approval releases nothing.

**Acceptance criteria (P2):** a dual-control `ask` records both approvers; a second approval by the same
principal does not release; expiry still applies; the quorum is audited (R41).

### CUJ-27 — Draft a policy from a sentence (P2 non-security engineer)
"I want a human asked before any production write." → `agentpolicy draft` returns a candidate Cedar rule with
generated tests — which compiles, passes `pack test` + lint, and waits for human review.

**Acceptance criteria (P2):** the draft is advisory — never auto-pinned; it must pass its generated tests and
lint before review; the runtime path is untouched (no ML in any decision path) (R42).

### CUJ-28 — Delegate to a child agent without leaking scope (P2 Alex)
A parent agent delegates a task; the child's permitted scope is provably a **subset** of the parent's — and an
agent-to-agent request is decided like any other action.

**Acceptance criteria (P2):** a child's out-of-parent-scope action is denied naming the chain link
(`delegation_chain`); scope-subset is proven, not assumed; inter-agent requests evaluate through the same
deterministic engine (R39, extends R25).

### CUJ-29 — Backtest a policy change against real history (P1 Ravi)
Ravi opens a policy PR; CI replays a window of recorded agentwatch history against the candidate policy and
attaches the **decision-diff** to the PR.

**Acceptance criteria (P1):** the flip set (newly-denied/asked/allowed) is exact and reproducible; the backtest
runs read-only (no re-execution, no fleet events, watermarked `backtest`); the report states its coverage window
and limits and is advisory — never auto-merge (R43, [PRD 23](23-enterprise-adoption-and-governance-hardening.md)).

### CUJ-30 — Guarantee the floor (P1 Maya)
The central team owns the org baseline; project overlays and session consent may only **restrict**.

**Acceptance criteria (P1):** a widening overlay fails `agentpolicy check` **at PR time**, naming the rule; no
overlay/consent combination can widen the floor (fuzz-tested); teams can still tighten locally (R44).

### CUJ-31 — See the uncovered action space (P1 Maya)
Before a compliance review, Maya runs the coverage report: which verbs does the fleet exercise that **no rule
mentions**?

**Acceptance criteria (P1):** the report names the exercised-but-uncovered quadrant loudly, the dead rules,
and the declared out-of-scope set; `gap:unexplained` is zero (R45).

### CUJ-32 — Verify agentpolicy against itself (public / P5 Alex)
Every release, the shipped **self-attack pack** runs against the deployed PDP.

**Acceptance criteria (P1):** a tamper/replay/bypass/forgery attempt that gets through blocks the release; the
result publishes with the release notes, misses included; a third party can run the same pack against their own
deployment (R46).

### CUJ-33 — Justify an allow (auditor)
"Who authorized this production write?" must be answerable for **allows**, not just denies.

**Acceptance criteria (P1):** an allowed action's decision and audit entry name the permitting rule, the policy
version, and (if consent-scoped) the consent; always-permitted patterns surface in the analytics report (R47).

## Later journeys (not v0.1.0)

- **Fleet-coherent policy** — one policy synced to N PDP nodes with drift detection (R31).
- **Policy-pack marketplace** — community packs with verified badges (R14).
- **Child-agent delegation** — a delegated agent's scope must be a subset of its parent's (R25).
- **Cross-PDP interop** — swap agentpolicy for another AuthZEN PDP and keep the ecosystem working (R27).

## Success criteria for v0.1.0 users

CUJ-1..CUJ-11 and CUJ-15/18/20 pass on a clean machine; a non-security engineer writes a first useful Cedar
policy in an afternoon (CUJ-8); every deny is explainable and actionable (CUJ-3); a policy PR that un-blocks a
known attack is rejected by CI (CUJ-7); no failure mode silently allows (CUJ-9); and every decision is emitted
in the agentwatch schema (CUJ-6).

CUJ-21..CUJ-28 (the [PRD 22](22-policy-intelligence-and-governance.md) additions) are **v0.2.0/v0.3.0** journeys
— they do not gate the v0.1.0 release.
