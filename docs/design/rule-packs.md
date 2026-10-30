# Rule Packs — Design (M4, v0.1.0)

**BLUF:** M4 ships a versioned, **incident-anchored** rule-pack format with the three launch packs
(**destructive-commands / the "Replit rule"**, **secret-in-output**, **mcp-allowlist**), `pack validate` /
`pack test` determinism, and OPA/Rego as a peer backend. Cedar is the pack language. This is the design of
record (`4.D0`); it delivers **CUJ-5**.

> Status: **Done** — branch `feat-0.1.0`. Format + loader: `src/agentpolicy/pack_format.py`.

---

## 1. Pack format (`4.1`)

```
packs/<name>/
  metadata.yaml     # name, version, description, incident_ref, min_agentpolicy, license, trust, domains
  rules.cedar       # Cedar rules appended to the base policy
  tests.yaml        # golden fixtures (incident replays), evaluated deterministically
  validators.yaml   # (optional) argument validators — M13
```

* **Strict + path-safe:** the manifest `name` must be a slug (`^[a-z0-9][a-z0-9-]{0,63}$`) and must match its
  directory. A malformed pack raises `PackFormatError`; the CLI surfaces it as **`ConfigError` (exit 2)** —
  fail-closed. `rules.cedar` is parsed at load (a syntax error is rejected).
* A pack's **policy set** is `BASE_POLICY + rules.cedar`, evaluated by the Cedar decision core
  ([cedar-decision-core](cedar-decision-core.md)).

## 2. The three launch packs (`4.2`–`4.4`)

| Pack | `incident_ref` | What it blocks/does |
|---|---|---|
| **destructive-commands** (the "Replit rule") | `incident-register#6` | `forbid`s destructive/irreversible verbs in production → `deny` |
| **secret-in-output** | `incident-register#9` | sensitive reads are permitted but the shaper **`redact`s** secrets/PII from the result |
| **mcp-allowlist** | `incident-register#11` | default-denies a call whose MCP server is not allowlisted (shadow-tool defence) |

Each ships `tests.yaml` **incident replays**; `pack test` runs them deterministically, and every fixture must
match:

```console
$ agentpolicy pack test packs/destructive-commands
PASS replit-prod-db-delete: expected=deny got=deny
...
4/4 passed
```

## 3. `pack validate` / `pack test` (`4.5`)

`agentpolicy pack validate <dir>` and `pack test <dir>` auto-detect the pack format:

* **Cedar pack** (has `rules.cedar`) → `pack_format.validate_pack_dir` / `run_pack_dir` (base + pack rules).
* **legacy catalog pack** (has `tools.yaml`) → the ported `policy.pack` validator/tester.

`pack test` is **deterministic** — the same pack + fixtures yield the same outcomes.

## 4. OPA/Rego peer backend (`4.6`)

`agentpolicy/policy/opa.py` evaluates a Rego policy with the **same decision contract**, independently: an
unreachable/erroring OPA raises `OpaUnavailableError` with reason `deny_opa_backend_down` (a **deny**), so a
backend outage never silently allows.

## 5. WBS M4 item mapping

| Item | Where |
|---|---|
| 4.D0 | this document |
| 4.1 pack format + loader | `pack_format.py` (§1) |
| 4.2 destructive-commands | `packs/destructive-commands/` (§2) |
| 4.3 secret-in-output | `packs/secret-in-output/` (§2) |
| 4.4 mcp-allowlist | `packs/mcp-allowlist/` (§2) |
| 4.5 `pack validate` / `pack test` | `cli/pack.py` (§3) |
| 4.6 OPA/Rego peer backend | `policy/opa.py` (§4) |
| 4.T/4.C/4.L/4.CR/4.D | `tests/test_m4_packs.py` · gates · [codereview-log](../wbs/v0.1.0/codereview-log.md) · [packs reference](../reference/packs.md) |
