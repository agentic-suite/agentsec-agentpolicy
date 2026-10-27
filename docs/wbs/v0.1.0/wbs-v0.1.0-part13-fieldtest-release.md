# WBS v0.1.0 — Part 13: Field Tests & Release Readiness (M24–M25, last)

**BLUF:** **M24 runs the field tests** — every CUJ-1..CUJ-33 executed end to end in real agent loops across
frameworks, with an honest published report. **M25 closes release readiness** and **tags `v0.1.0`** (mirrors
agentdrill M31/M32).

> Standard exit criteria + closure apply to every milestone — see the [index](wbs-v0.1.0-index.md).

---

## Milestone M24 — Field tests (last)

**Goal:** drive **real agents** through the CUJ matrix — decisions asserted per scenario across every supported
framework — and publish the honest field-test report. A field-test miss on a P0 CUJ blocks the release.

**CUJ:** **all CUJ-1..CUJ-33** (executed end to end) · **Requirements:** every R, verified in a live loop.

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 24.D0 | **Design docs first** | Field-test plan: scenario matrix, frameworks, harness (Docker), pass/fail criteria, report format | docs | reviewed before code | #255 | — | — |
| 24.1 | Field-test harness | Docker harness driving a demo enforcer + the system-under-test; captures request/response pairs | harness | reproducible locally | #256 | — | — |
| 24.2 | Scenario matrix | safe/staging→allow · prod-write→ask · blocked→deny · budget→rate-limit · secret→redact · unknown→fail-closed · deny→replan · ask round-trip | suite | every outcome exercised | #257 | CUJ-1..CUJ-33 | all |
| 24.3 | Framework coverage | ≥2 Tier-1 harnesses + ≥3 framework adapters exercised in their native loops | suite | adapters exercised end to end | #258 | CUJ-2, CUJ-14 | R28 |
| 24.4 | Adversarial + self-attack | The adversarial sub-matrix and the self-attack pack in the field run | suite | every attempt blocks | #259 | CUJ-11, CUJ-32 | R26, R46 |
| 24.5 | Field-test report | `docs/field-test/v0.1.0/FIELD_TEST_REPORT.md`: scenarios × frameworks × expected/actual; misses named | report | published; empty not-tested list | #260 | all | all |
| 24.6 | Fix loop | Every harness defect found → fixed with a regression test | code + tests | 0 open product defects | #261 | all | all |
| 24.T | Tests | The full suite green after fixes | tests | coverage ≥ 95% | #262 | — | — |
| 24.C | Coverage gate | coverage ≥ 95% | report | ≥ 95% | #263 | — | — |
| 24.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #264 | — | — |
| 24.CR | Code review | Findings in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #265 | — | — |
| 24.D | Docs | Field-test plan + report; CI docs | docs | updated + linked | #266 | — | — |
| 24.CI | Commit & push | On the feature branch | git | pushed | — | — | — |
| 24.W | Update WBS | Checkpoint in the index Progress | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] Every **CUJ-1..CUJ-33** executed end to end; the report is published, misses included, not-tested list empty
- [ ] A field-test miss on a P0 CUJ blocks the release; all harness defects fixed with regressions

---

## Milestone M25 — Release readiness (last; tags `v0.1.0`)

**Goal:** tag and release `v0.1.0` — release tooling, first-run evidence, security audit, compliance matrix,
versioning policy, release notes, signed artifacts — and **make the predecessor private (never deleted)**.

**CUJ:** — (release) · **Requirements:** [PRD 07](../../prd/07-success-metrics.md) release gate, PRD 09 roadmap,
[PRD 19](../../prd/19-harness-compatibility.md), [PRD 20](../../prd/20-standards-and-claims.md).

**Work items**

| # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req |
|---|---|---|---|---|---|---|---|
| 25.D0 | **Design docs first** | Release plan: versioning policy, artifact set, evidence, tag/release steps | docs | reviewed before code | #267 | — | — |
| 25.1 | Release tooling | `make release-dry-run`: build + CycloneDX SBOM + `SHA256SUMS` + SLSA provenance; independent verification | tooling | dry-run green | #268 | — | — |
| 25.2 | First-run evidence | `pip install` → first correct decision < 5 min (< 2 min with `init`); recorded | evidence | documented | #269 | — | R2 |
| 25.3 | Security audit | Own-threat-model + dependency scan; 0 unresolved findings | audit | clean | #270 | — | PRD 06 |
| 25.4 | Compliance & standards matrix | OWASP ASI/LLM + ATLAS + NIST/ISO/EU coverage, explicit gaps; claims linter green | matrix | published | #271 | — | R32 |
| 25.5 | Versioning policy + release notes | Normative versioning policy; release notes; compatibility matrix (harness × enforcer) | docs | published | #272 | — | — |
| 25.6 | Docs audit | Full docs audit; ADRs accepted; links green | docs | green | #273 | — | — |
| 25.7 | Tag + release | Annotated tag `v0.1.0`; GitHub Release (wheel/sdist/SBOM/checksums/provenance); PyPI `agentsec-agentpolicy==0.1.0` install-verified, hashes match | release | released | #274 | — | — |
| 25.8 | Predecessor **made private** | Retain `agent-tooltrust` private; never delete | ops | private, retained | #275 | — | PRD 10 |
| 25.T | Tests | Full suite green on the release commit | tests | coverage ≥ 95% | #276 | — | — |
| 25.C | Coverage gate | coverage ≥ 95% on the release commit | report | ≥ 95% | #277 | — | — |
| 25.L | Lint & type gate | `ruff` zero; `mypy --strict` clean | CI | zero violations | #278 | — | — |
| 25.CR | Code review | Final review in [codereview-log.md](codereview-log.md), resolved | log | no open findings | #279 | — | — |
| 25.D | Docs | Release notes, README status → shipped, CHANGELOG | docs | updated + linked | #280 | — | — |
| 25.CI | Commit & push | Release commit on `main` | git | pushed | — | — | — |
| 25.W | Update WBS | Final checkpoint: **M0–M25 complete, v0.1.0 released** | WBS | recorded | — | — | — |

**Exit criteria**

- [ ] Design docs first · all tests pass · coverage ≥ 95% · lint strict clean · docs updated · committed+pushed
- [ ] Release tooling green; first-run evidence recorded; security audit clean; compliance matrix published
- [ ] **`v0.1.0` tagged + released** (GitHub + PyPI, install-verified, hashes match)
- [ ] **Predecessor repository retained and made private (not deleted)**

---

Part 13 green ⇒ **agentpolicy v0.1.0 is released.** Back to the [index](wbs-v0.1.0-index.md).
