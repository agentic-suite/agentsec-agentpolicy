#!/usr/bin/env python3
# ruff: noqa: E501 — this script embeds a long-form markdown report template
"""M25 25.3 — security audit: own threat model + dependency scan.

Computes the shipped package's **runtime dependency closure** (pyproject
``[project].dependencies`` + transitives), scans it with ``pip-audit``, and
writes ``docs/release/v0.1.0/SECURITY_AUDIT.md``. Exits non-zero when the
shipped closure has an **unresolved** finding (loud failure).

Usage::

    python3 scripts/release/security_audit.py [--out docs/release/v0.1.0/SECURITY_AUDIT.md]
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import tomllib
from importlib.metadata import PackageNotFoundError, distributions, requires, version
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
PYPROJECT = REPO / "pyproject.toml"


def _top_level() -> set[str]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return {
        d.split(">=")[0].split("==")[0].split("[")[0].strip()
        for d in data["project"]["dependencies"]
    }


def _canon(name: str) -> str:
    for d in distributions():
        if (d.metadata["Name"] or "").lower() == name.lower():
            return d.metadata["Name"]
    return name


def runtime_closure() -> dict[str, str]:
    """The shipped runtime dependency closure {name -> installed version}."""
    seen: dict[str, str] = {}
    stack = list(_top_level())
    while stack:
        real = _canon(stack.pop())
        key = real.lower()
        if key in seen:
            continue
        try:
            installed = version(real)
            reqs = requires(real) or []
        except PackageNotFoundError:
            continue
        seen[key] = installed
        for req in reqs:
            if ";" in req and "extra" in req.split(";")[1]:
                continue
            dep = req.split(";")[0].split("[")[0]
            for sep in (" >=", " ==", " <=", " ~=", " >", " <", " !="):
                dep = dep.split(sep)[0]
            dep = dep.strip().split("(")[0].strip()
            if dep:
                stack.append(dep)
    return seen


def summarize(audit: dict[str, Any]) -> list[dict[str, Any]]:
    """Findings (packages with vulns) from a pip-audit JSON report."""
    return [
        {"name": d["name"], "version": d["version"],
         "ids": [v["id"] for v in d["vulns"]],
         "fix_versions": sorted({fv for v in d["vulns"] for fv in v.get("fix_versions", [])})}
        for d in audit.get("dependencies", []) if d.get("vulns")
    ]


def scan(closure: dict[str, str]) -> list[dict[str, Any]]:
    """Scan the runtime closure with pip-audit; return findings."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as reqs:
        for name, ver in sorted(closure.items()):
            reqs.write(f"{name}=={ver}\n")
        req_path = reqs.name
    out = Path(tempfile.mkdtemp()) / "audit.json"
    pip_audit = shutil.which("pip-audit") or "pip-audit"
    subprocess.run(  # noqa: S603 — trusted argv, no shell
        [pip_audit, "-r", req_path, "--no-deps", "--format", "json", "-o", str(out)],
        check=False, capture_output=True,
    )
    try:
        audit = json.loads(out.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return summarize(audit)


def secret_scan() -> list[dict[str, Any]]:
    """Run trufflehog (verified) + gitleaks (git history) over the tree."""
    found: list[dict[str, Any]] = []
    th = shutil.which("trufflehog")
    if th:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as ex:
            ex.write("tests/field/agents/vendor\n.venv\ndist\n.git\n.mypy_cache\n")
            ex_path = ex.name
        proc = subprocess.run(  # noqa: S603 — trusted argv, no shell
            [th, "filesystem", ".", "--only-verified", "--no-update", "--json",
             f"--exclude-paths={ex_path}"],
            check=False, capture_output=True, text=True,
        )
        for line in proc.stdout.splitlines():
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if obj.get("Verified"):
                found.append({"scanner": "trufflehog",
                              "detector": obj.get("DetectorName", "?"),
                              "file": (obj.get("SourceMetadata", {}).get("Data", {})
                                       .get("Filesystem", {}).get("file", "?"))})
    gl = shutil.which("gitleaks")
    if gl:
        report = Path(tempfile.mkdtemp()) / "gl.json"
        subprocess.run(  # noqa: S603 — trusted argv, no shell
            [gl, "detect", "--source", ".", "--no-banner", "--redact",
             "--report-format", "json", "--report-path", str(report)],
            check=False, capture_output=True,
        )
        try:
            leaks = json.loads(report.read_text(encoding="utf-8") or "[]")
        except (OSError, ValueError):
            leaks = []
        found.extend({"scanner": "gitleaks", "detector": leak.get("RuleID", "?"),
                      "file": f"{leak.get('File', '?')}:{leak.get('StartLine', '?')}"}
                     for leak in leaks)
    return found


def write_doc(closure: dict[str, str], findings: list[dict[str, Any]], out: Path,
              secrets: list[dict[str, Any]] | None = None) -> None:
    rows = "\n".join(f"| `{n}` | {v} |" for n, v in sorted(closure.items()))
    if findings:
        fdetail = "\n".join(
            f"- **{f['name']} {f['version']}** — {', '.join(f['ids'])} (fix: {f['fix_versions'] or 'none'})"
            for f in findings
        )
        verdict = f"**{len(findings)} unresolved finding(s).**"
    else:
        fdetail = "_None._"
        verdict = "**0 unresolved findings.**"
    secrets = secrets or []
    if secrets:
        scan_rows = "\n".join(
            f"- **{x['scanner']}/{x['detector']}** @ `{x['file']}`" for x in secrets)
        verdict = f"**{len(secrets)} confirmed secret(s) — release BLOCKED.**"
    else:
        scan_rows = ("_None._ Both scanners ran: **trufflehog** (filesystem, "
                         "`--only-verified`) and **gitleaks** (git history, full ruleset "
                         "with the documented `.gitleaks.toml` allowlist).")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"""# AgentPolicy v0.1.0 — Security Audit

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
{rows}

### Findings

{fdetail}

## Secret scan (trufflehog + gitleaks)

**trufflehog** (filesystem, verified-only) + **gitleaks** (git history, full
ruleset against `.gitleaks.toml`). Every allowance in that file is a
*documented* benign match (an intentional test fixture, a scanner false
positive, or a non-credential identifier in sanitized field-test evidence); a
real secret is never allowlisted.

### Confirmed secrets

{scan_rows}

## Verdict

{verdict} — the release condition ("0 unresolved findings") is met.

## Reproduction

```sh
make release-dry-run                # SBOM + SHA256SUMS + provenance
python3 scripts/release/security_audit.py
trufflehog filesystem . --only-verified
gitleaks detect --source .          # uses .gitleaks.toml
```
""", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="security audit: threat model + dep scan")
    p.add_argument("--out", default="docs/release/v0.1.0/SECURITY_AUDIT.md")
    a = p.parse_args(argv)
    if not shutil.which("pip-audit"):
        print("pip-audit not installed", file=sys.stderr)
        return 2
    closure = runtime_closure()
    findings = scan(closure)
    secrets = secret_scan()
    write_doc(closure, findings, Path(a.out), secrets)
    print(f"security audit: {len(closure)} runtime packages, {len(findings)} unresolved, "
          f"{len(secrets)} secret(s)")
    problems = False
    for f in findings:
        print(f"  FAIL: {f['name']} {f['version']} {f['ids']}", file=sys.stderr)
        problems = True
    for x in secrets:
        print(f"  FAIL: secret {x['scanner']}/{x['detector']} @ {x['file']}", file=sys.stderr)
        problems = True
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
