# Versioning Policy (normative)

> This document is **normative** for the AgentPolicy (`agentsec-agentpolicy`)
> project. It defines how versions are assigned, what a bump promises, and how
> the release is cut. M25 25.5 (issue #272). See also
> [`release-notes-v0.1.0.md`](release-notes-v0.1.0.md) and
> [`docs/release/v0.1.0/RELEASE_PLAN.md`](../release/v0.1.0/RELEASE_PLAN.md).

## 1. Scheme

AgentPolicy uses **Semantic Versioning** (`MAJOR.MINOR.PATCH`).

- The package version is the single source of truth in `pyproject.toml`
  `[project].version`.
- The git tag is `v<version>` (annotated). The release tooling fails if the tag
  and `pyproject.toml` disagree.

## 2. What a bump promises

| Change | Bump |
|---|---|
| Breaking API/policy/CLI change | `MAJOR` |
| New backward-compatible feature | `MINOR` |
| Backward-compatible bug fix | `PATCH` |

### Pre-1.0

While `MAJOR == 0`, the API is not yet frozen: a **`MINOR` bump MAY carry
breaking changes** (they are called out prominently in the release notes), and a
**`PATCH` bump MUST be backward-compatible**. `v0.1.0` is the first release of
the `0.x` line.

## 3. Deprecation

A public surface is deprecated by **announcing it one `MINOR` before removal**,
recorded in the release notes and (where applicable) emitting a runtime
deprecation warning. Surfaces are **never removed silently in a `PATCH`**.

## 4. Compatibility matrix (harness × enforcer)

Every release publishes the compatibility matrix of **harnesses** (how the PDP is
reached) × **enforcers** (where the decision is enforced). A cell is only marked
supported when it is **field-tested** — an untested surface is named as *not
supported*, never claimed (see [`release-notes-v0.1.0.md`](release-notes-v0.1.0.md)).

## 5. Release cut

1. Freeze `pyproject.toml` version; ensure the field-test report, security audit,
   and compliance matrix are current.
2. `make release-dry-run` → wheel + sdist + SBOM + `SHA256SUMS` + provenance,
   verified.
3. Annotated tag `v<version>` on the release commit.
4. GitHub Release + PyPI publish; install-verify with hashes matching
   `SHA256SUMS`.
5. Flip `README` status to shipped; update `CHANGELOG.md` and the release notes.

## 6. Compatibility of release artifacts

- `SHA256SUMS` is authoritative: a consumer MUST verify hashes before install.
- Wheel/sdist are built from the tagged commit; no post-hash edits.
