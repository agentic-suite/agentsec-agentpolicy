# AgentPolicy v0.1.0 — Security Audit

> M25 25.3 (issue #270). Scope: the **shipped package's** runtime dependency
> closure + an own threat model of the decision point. No ML/network in any
> decision path.

## Own threat model (the decision point)

AgentPolicy is a deterministic policy decision point (PDP) that every agent
tool call passes through. Its own threat model, by asset:

| Threat | Surface | Control |
|---|---|---|
| **Silent allow on error** (the worst outcome) | every stage of NORMALIZE→SCORE→DECIDE→EXPLAIN→AUDIT | **fail-closed**: any stage failure closes to `deny`; never an exception surfacing |
| **Policy tampering / unaudited change** | `agentpolicy.yaml`, git | policies are git-reviewed; provenance + hash-chained audit; `audit` chain tamper-evident |
| **Secret leakage in evidence** | args, receipts, release artifacts, SBOM | arg-validate + redact obligations; the field-test leak gate (`scan_results.py`) must be clean; SBOM/manifests carry no secrets |
| **Crafted-input bypass** (obfuscation / unicode / nonstring) | the normalizer + scorer | normalization + fail-closed on malformed input; adversarial sub-matrix proven with **0 crafted allows** |
| **Supply-chain compromise** | third-party packages | **dependency scan** below; SBOM (CycloneDX) + SLSA provenance in the release set |
| **Privilege escalation / scope creep** | multi-agent delegation | scope + step-up rules; delegation audited |
| **Availability / DoS** | runaway budgets | budget + halt controls |

## Dependency scan (shipped runtime closure)

Scanned with **`pip-audit`** against the advisory DB — the exact closure a
consumer gets from `pip install agentsec-agentpolicy`:

| Package | Version |
|---|---|
| `cedarpy` | 4.12.2 |
| `cryptography` | 50.0.2 |
| `opentelemetry-api` | 1.45.2 |
| `opentelemetry-sdk` | 1.45.2 |
| `pydantic` | 2.12.5 |
| `pyyaml` | 6.0.3 |
| `starlette` | 1.10.0 |
| `watchfiles` | 1.3.0 |

### Findings

_None._

## Secret scan (trufflehog + gitleaks)

**trufflehog** (filesystem, verified-only) + **gitleaks** (git history, full
ruleset against `.gitleaks.toml`). Every allowance in that file is a
*documented* benign match (an intentional test fixture, a scanner false
positive, or a non-credential identifier in sanitized field-test evidence); a
real secret is never allowlisted.

### Confirmed secrets

_None._ Both scanners ran: **trufflehog** (filesystem, `--only-verified`) and **gitleaks** (git history, full ruleset with the documented `.gitleaks.toml` allowlist).

## Verdict

**0 unresolved findings.** — the release condition ("0 unresolved findings") is met.

## Reproduction

```sh
make release-dry-run                # SBOM + SHA256SUMS + provenance
python3 scripts/release/security_audit.py
trufflehog filesystem . --only-verified
gitleaks detect --source .          # uses .gitleaks.toml
```
