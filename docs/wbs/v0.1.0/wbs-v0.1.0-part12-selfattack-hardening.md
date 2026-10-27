# WBS v0.1.0 — Part 12: Self-Attack, Allow-Justification & Hardening (M22–M23)

**BLUF:** M22 ships the **self-attack pack and allow-justification** — agentpolicy drilled against itself, and
"who authorized this?" answerable for allows (CUJ-32, CUJ-33). M23 closes the **NFRs, security hardening, the
parity/absorption gate, and the deferred-optional items**.

> Standard exit criteria + closure apply to every milestone — see the [index](wbs-v0.1.0-index.md).

---

## Milestone M22 — Self-attack pack & allow-justification

**Goal:** a shipped pack that attacks agentpolicy's **own** decision surface, run every release (a hit blocks the
release); and every outcome — **allows included** — names its matched rule.

**CUJ:** **CUJ-32**, **CUJ-33** · **Requirements:** R46, R47.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 22.D0 | **Design docs first** | Self-attack pack design (surfaces: tamper/bypass/replay/budget-split/audit-truncation/event-forgery) + allow-justification design | docs | reviewed before code | #233 | — | — |
| 22.1 | `self-attack` pack | Attacks agentpolicy's own surface; runs as a normal pack (dogfoodable) | pack | a seeded miss blocks the release | #234 | CUJ-32 | R46 |
| 22.2 | Release-cadence CI job | The pack runs every release; misses published | CI job | cadence enforced | #235 | CUJ-32 | R46 |
| 22.3 | Allow-justification | `matched_rule` on **every** outcome; allow-side patterns in analytics | engine | an allow names its permitting rule + version | #236 | CUJ-33 | R47 |
| 22.T | Tests | Self-attack pack (seeded miss blocks); allow names rule + version | tests | coverage ≥ 95% | #237 | CUJ-32, CUJ-33 | R46, R47 |
| 22.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #238 | — | — |
| 22.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #239 | — | — |
| 22.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #240 | — | — |
| 22.D | Docs | Self-attack reference + allow-justification note + security baseline update | docs | updated + linked | #241 | — | — |
| 22.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 22.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] A tamper/replay/bypass/forgery attempt that gets through blocks the release; published with misses
      (**CUJ-32**)
- [ ] An allowed action names the permitting rule + policy version (**CUJ-33**)

---

## Milestone M23 — NFRs, hardening, parity closure & deferred-optional

**Goal:** meet the non-functionals, harden against the own-threat-model, close the predecessor parity ledger, and
land the deferred-optional items (OPA→Cedar migration, pack marketplace, fleet sync).

**CUJ:** — (cross-cutting) · **Requirements:** R8/R13 (performance, sandbox, portability, cost), R32, R13, R14,
R31 (deferred-optional).

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 23.D0 | **Design docs first** | Hardening design + parity/gap-closure reference + deferred-optional plan | docs | reviewed before code | #242 | — | — |
| 23.1 | Performance + portability | Sub-100 ms p99 budget; macOS/Linux; Python 3.10+; local-first | engine | budgets met | #243 | — | R8 |
| 23.2 | Fail-closed fault injection | Inject failures across every path; assert deny + reason; case failure never aborts | suite | no silent allow | #244 | — | R8 |
| 23.3 | Untrusted-pack sandbox | Env stripping, FS isolation, optional `--network none`, trust levels, audit | sandbox | external packs confined | #245 | — | R6 (PRD 06) |
| 23.4 | Cost controls | `--max-cost` budget governor; abort + report | engine | run aborts over ceiling | #246 | — | R8 |
| 23.5 | Parity / absorption ledger | Every predecessor capability delivered/delegated/waived; parity gate green | reference | no silent drops | #247 | — | PRD 10 |
| 23.6 | Standards/compliance export | Regenerate the OWASP ASI/LLM + ATLAS + NIST/ISO/EU coverage matrix; claims linter | export | matrix + linter in CI | #248 | — | R32 |
| 23.7 | Deferred-optional (may be waived) | OPA→Cedar migration assistant (R13); pack marketplace (R14); fleet sync (R31) | optional | implemented or explicitly waived with reason | #249 | — | R13/R14/R31 |
| 23.T | Tests | Perf budgets, fault injection, sandbox, cost, parity gate, compliance export | tests | coverage ≥ 95% | #250 | — | — |
| 23.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #251 | — | — |
| 23.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #252 | — | — |
| 23.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #253 | — | — |
| 23.D | Docs | Hardening reference + parity reference + standards/claims reference | docs | updated + linked | #254 | — | — |
| 23.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 23.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] NFRs met; fail-closed on tamper; untrusted packs sandboxed
- [ ] Parity ledger green (no silent drops); compliance matrix regenerated
- [ ] Deferred-optional items implemented or explicitly waived with reason

---

Part 12 green ⇒ the feature set is complete, hardened, and parity-closed; proceed to
[Part 13 (M24–M25)](wbs-v0.1.0-part13-fieldtest-release.md).
