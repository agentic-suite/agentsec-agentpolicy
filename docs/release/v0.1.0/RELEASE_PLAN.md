# AgentPolicy v0.1.0 — Release Plan

> **M25 25.D0 — reviewed before code.** This is the design for *how* v0.1.0 is
> shipped: the versioning policy, the artifact set, the evidence, and the exact
> tag/release steps. Later M25 items implement exactly this plan; nothing ships
> that isn't named here.
>
> Owning milestone: **M25 Release readiness** · WBS
> `docs/wbs/v0.1.0/wbs-v0.1.0-part13-fieldtest-release.md` `25.D0` (issue #267).
> Package: **`agentsec-agentpolicy`** · Version: **`0.1.0`** · Tag: **`v0.1.0`**.

---

## 1. Versioning policy

- **Scheme:** semantic versioning (`MAJOR.MINOR.PATCH`). The Python package
  version is `agentsec-agentpolicy==0.1.0`; the git tag is `v0.1.0` (annotated,
  with a release message).
- **Normative source:** `pyproject.toml` `[project].version` is the single
  source of truth. The tag MUST equal `v<version>`; the release tooling fails if
  they disagree.
- **Pre-1.0 stability:** while `MAJOR == 0`, a `MINOR` bump MAY carry breaking
  changes; a `PATCH` bump MUST be backward-compatible. Every breaking change is
  called out in the release notes.
- **Compatibility matrix:** the shipped (harness × enforcer) matrix is published
  alongside the notes (§5 of the release notes; PRD 19). A harness/enforcer is
  only listed as supported when it is field-tested — v0.1.0 lists what the M24
  field test proved and names what it did not.
- **Deprecation:** a deprecated surface is announced one `MINOR` before removal
  and recorded in the release notes; nothing is removed silently in a `PATCH`.

## 2. Artifact set

Every release produces, from the release commit, an immutable, verifiable set:

| Artifact | Produced by | What it proves |
|---|---|---|
| **wheel** (`*.whl`) + **sdist** (`*.tar.gz`) | `python -m build` (via `make release-dry-run`) | the installable distribution |
| **CycloneDX SBOM** (`sbom.cdx.json`) | the release tooling | the full dependency inventory |
| **`SHA256SUMS`** | the release tooling | a checksum for every shipped artifact |
| **SLSA provenance** (`provenance.intoto.jsonl`) | the release tooling | how/where the artifact was built |
| **release notes** | `docs/reference/release-notes-v0.1.0.md` | human-readable change set |

- **`make release-dry-run`** builds the wheel + sdist, the CycloneDX **SBOM**,
  the **`SHA256SUMS`**, and the **SLSA provenance**, then **independently
  verifies** them (M25 25.1 / #268). The dry run is the gate: it must be green
  before the tag.
- No artifact is hand-edited after it is hashed.

## 3. Evidence

The release cites, and does not restate, the evidence produced by prior
milestones:

- **Field-test report** — `docs/field-test/v0.1.0/FIELD_TEST_REPORT.md`
  (97/97 field units PASS; not-tested list empty; every PASS deep-verified
  grounded). This is the release's headline evidence.
- **Security audit** — M25 25.3 / #270 (own threat model + dependency scan;
  **0 unresolved findings**).
- **Compliance & standards matrix** — M25 25.4 / #271 (OWASP ASI/LLM + ATLAS +
  NIST/ISO/EU coverage with explicit gaps; claims linter green).
- **First-run evidence** — M25 25.2 / #269 (`pip install` → first correct
  decision < 5 min, < 2 min with `init`; recorded).
- **Gates on the release commit** — 25.T suite green · 25.C coverage ≥ 95% ·
  25.L `ruff` zero + `mypy --strict` clean · 25.CR review log clean.

## 4. Security & privacy

- **Signed / verifiable artifacts:** every artifact carries a `SHA256SUMS`
  entry and SLSA provenance; consumers verify hashes before install.
- **Zero unresolved findings** is a release condition (25.3). A finding is
  either fixed or explicitly waived with a written reason — never silently
  dropped.
- **Secrets:** no release artifact, log, or SBOM contains an unmasked secret;
  the field-test leak gate (`scan_results.py`) must be clean.
- **Predecessor:** the predecessor project **`agent-tooltrust` is retained
  private and never deleted** (25.8 / #275, PRD 10). The release neither moves,
  renames, nor removes it.

## 5. Tag & release steps

Run from the release commit on `main`, after every gate above is green:

1. **Freeze** — confirm `pyproject.toml` version `0.1.0` and that the field-test
   report, security audit, and compliance matrix are published and current.
2. **Dry run** — `make release-dry-run` → wheel + sdist + **SBOM** +
   **`SHA256SUMS`** + **provenance**, independently verified. Green.
3. **Tag** — annotated tag **`v0.1.0`** on the release commit; the tag message
   summarises the release and links the notes.
4. **GitHub Release** — attach the wheel, sdist, CycloneDX **SBOM**,
   **`SHA256SUMS`**, and SLSA **provenance**; body links the release notes.
5. **Publish** — upload to PyPI as **`agentsec-agentpolicy==0.1.0`**; install in
   a clean venv and run a first decision.
6. **Verify** — the downloaded artifacts' hashes MUST match **`SHA256SUMS`**;
   the PyPI install MUST succeed and reproduce the first-run evidence. A hash
   mismatch blocks the release.
7. **Retain** — confirm **`agent-tooltrust`** remains **private** (never
   deleted); record the checkpoint in the WBS index.
8. **Announce** — flip README status to *shipped*, publish the CHANGELOG /
   release notes (25.D / #280).

## 6. Out of scope

- Any change to the decision engine or policy surface (that was M1–M23).
- New field-test cases (M24 is closed; a re-run only re-produces evidence).
- Deleting or un-privating the predecessor.

## 7. Definition of done (for 25.D0)

This plan is reviewed before any release code: `make release-dry-run` (#268),
the evidence items (#269–#271), the notes/matrix (#272), the docs audit (#273),
and the tag/release (#274) all implement the sections above. The plan is linked
from the WBS and the release-notes index.
