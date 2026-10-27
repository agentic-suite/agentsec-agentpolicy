# PRD 13 — Non-Functional Requirements

**BLUF:** agentpolicy's non-functionals are dominated by **determinism** (same input + policy ⇒ same decision)
and **fail-closed safety** (no path silently allows). It must be **fast** (sub-100 ms p99 inline), **portable**
(harness-agnostic, local-first), **safe to run untrusted packs**, **auditable** (tamper-evident), and cheap
enough to gate every policy PR.

**Status:** Draft — v0.1.0 (2026-10-26) · **Owner:** @deghosal-2026 · **Parent:** agentic-suite #209 · PRD #211

## Determinism (primary)

- **Same input + same policy ⇒ same decision**, always. The decision path contains **no ML, no randomness, no
  network**.
- **Pinned policy:** every decision records `policy_version` + policy hash; a changed hash is a declared,
  reviewed change.
- **Replayable:** a decision (action + policy version + context + session state) can be re-evaluated offline to
  the same result — the basis of the offline evidence artifact (CUJ-20).
- **Documented semantics:** how each outcome is derived (rule match, budget, ask class, redaction) is published;
  no proprietary scoring.
- Verified by an automated determinism test (re-run ⇒ identical decision unless a pin changed).

## Fail-closed safety (primary)

- **Any exception, unknown input, or disabled engine → `deny`** (configurable to `ask`, never to `allow` by
  default).
- Every failure path has a **distinct `reason_code`** a SIEM can alert on (`engine_unavailable`,
  `policy_unavailable`, `opa_backend_unavailable`, `evaluation_timeout`, `unknown_action`, `audit_sink_error`).
- **Audit is a side effect, not a gating dependency** — a sink failure never changes the decision.
- The fail-closed contract is itself a CI test over a fuzzed input space.

## Performance

- **p99 < 100 ms** per decision inline (local, warm); p50/p95/p99 published per release.
- **No network in the hot path**; the OPA/Rego backend and any LLM advisor are off the critical path.
- Cold start budgeted (policy load + entity build) and measured; a decision cache for repeated identical calls.
- Parallel evaluation for batched (`evaluations[]`) AuthZEN requests.

## Reliability & failure modes

- A malformed policy **refuses to load** (`agentpolicy check` reports line/column); the engine never operates
  with a broken policy.
- Exit codes are always propagated (0 allow-ish, non-zero on deny/error), `--ci` or not.
- Budget/session store failures degrade to fail-closed, never to unlimited.

## Portability

- **Harness-agnostic by construction** — a PDP behind the enforcer; the same decision for every harness.
- **Local-first** (no service required for core function); **CI-second**; optional HTTP/AuthZEN service.
- Python 3.10+ core; CLI wrapper; MCP server; no runtime dependency on a proprietary backend.

## Security

- Untrusted rule packs: schema validation, trust levels (`built-in`/`local`/`external`), sandbox (env
  stripping, FS isolation, optional Docker `--network none`), audit trail, secret sanitization (PRD 06).
- Strict identifier validation (`^[a-zA-Z0-9_-]+$`) before any path use.
- Signed packs + provenance on release; tamper-evident decision log (hash chain).
- No secrets in decisions or logs; outputs redacted with receipts.

## Auditability

- Append-only decision log with policy version per entry; JSONL/SQLite/Postgres sinks; export/query.
- **Tamper-evident**: a hash chain over the log; a verification command proves unedited history. The chain head
  is **anchored at every rotation** (signed local anchor, optionally remote-timestamped) so a
  truncate-and-rebuild attack is detectable, not just in-segment edits.
- **Retention & rotation**: configurable retention (default: 90 days hot, then archive); each archived segment
  commits to the prior segment's head hash and verification walks segments in order — rotation never breaks the
  chain, and a missing segment is a loud finding, never a quiet gap.
- Decisions emitted in the agentwatch schema so they join the ecosystem's telemetry.

## Cost

- Deterministic evaluation is free; no per-call API cost on the default path.
- The optional LLM advisor is off by default and budgeted (`--max-cost`) when on.

## Observability & self-check

- `agentpolicy doctor` — environment/policy/backend sanity.
- `agentpolicy check --strict [--migrate]` — policy validation before a run.
- A shareable decision summary (outcome + criticality + reason code + policy version).
- Metrics: decisions by outcome, ask latency, budget exhaustion, lint findings.

## Documentation

- Every published decision documents its policy version and pins so an external party can re-derive it offline
  (CUJ-20). The explain artifact is the unit of documentation.
