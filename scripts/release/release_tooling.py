#!/usr/bin/env python3
"""M25 25.1 — release tooling: build a verifiable release set.

From a dist directory this produces the release artifacts that make v0.1.0
auditable — a **CycloneDX SBOM**, a **``SHA256SUMS``** manifest, and an
**in-toto / SLSA provenance** statement — and then **independently verifies**
them. Verification recomputes every hash and refuses to pass when an artifact
was tampered with or a manifest is missing (loud failure, never a silent pass).

Usage::

    python3 scripts/release/release_tooling.py --dist dist            # manifest+verify
    python3 scripts/release/release_tooling.py --dist dist --build    # build first
    python3 scripts/release/release_tooling.py --dist dist --verify-only

Stdlib only — no external SBOM/provenance toolchain is required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from importlib.metadata import distributions
from pathlib import Path

#: Release artifact globs (build outputs) that the manifest covers.
_ARTIFACT_GLOBS = ("*.whl", "*.tar.gz", "*.zip")
_MANIFEST_NAMES = ("SHA256SUMS", "provenance.intoto.jsonl")
_SBOM_NAME = "sbom.cdx.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _artifacts(dist: Path) -> list[Path]:
    """The files the manifest covers: build outputs + the SBOM itself."""
    files: list[Path] = []
    for pattern in _ARTIFACT_GLOBS:
        files.extend(sorted(dist.glob(pattern)))
    sbom = dist / _SBOM_NAME
    if sbom.is_file():
        files.append(sbom)
    return files


def _components(dist: Path) -> list[dict[str, object]]:
    """CycloneDX components: the release artifacts + the installed packages."""
    comps: list[dict[str, object]] = []
    for art in _artifacts(dist):
        comps.append({
            "type": "file",
            "name": art.name,
            "version": "0.1.0",
            "hashes": [{"alg": "SHA-256", "content": _sha256(art)}],
        })
    seen: set[str] = set()
    for d in sorted(distributions(), key=lambda x: (x.metadata["Name"] or "").lower()):
        name = d.metadata["Name"]
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        comps.append({
            "type": "library",
            "name": name,
            "version": d.version,
            "purl": f"pkg:pypi/{name.lower().replace('_', '-')}@{d.version}",
        })
    return comps


def _sbom(dist: Path) -> dict[str, object]:
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "name": "agentsec-agentpolicy",
                "version": "0.1.0",
            },
        },
        "components": _components(dist),
    }


def _provenance(dist: Path) -> dict[str, object]:
    subjects = [
        {"name": a.name, "digest": {"sha256": _sha256(a)}}
        for a in _artifacts(dist)
    ]
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": subjects,
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "https://agentpolicy/release@v1",
                "externalParameters": {"dist": dist.name, "package": "agentsec-agentpolicy"},
            },
            "runDetails": {"builder": {"id": "make release-dry-run"}},
        },
    }


def write_manifest(dist: Path) -> None:
    """Write the SBOM, ``SHA256SUMS``, and provenance into *dist*."""
    dist.mkdir(parents=True, exist_ok=True)
    (dist / _SBOM_NAME).write_text(json.dumps(_sbom(dist), indent=2) + "\n", encoding="utf-8")
    # SHA256SUMS covers every artifact + the SBOM (not the manifest files)
    lines = [f"{_sha256(a)}  {a.name}" for a in _artifacts(dist)]
    (dist / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (dist / "provenance.intoto.jsonl").write_text(
        json.dumps(_provenance(dist), indent=2) + "\n", encoding="utf-8")


def verify(dist: Path) -> list[str]:
    """Independently verify the release set. Returns problems ([] == green)."""
    problems: list[str] = []
    sums_path = dist / "SHA256SUMS"
    if not sums_path.is_file():
        return [f"missing manifest: {sums_path}"]
    listed: dict[str, str] = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, _, name = line.partition("  ")
        listed[name] = digest
    # every artifact must be present and hash-match
    for art in _artifacts(dist):
        if art.name not in listed:
            problems.append(f"artifact not in SHA256SUMS: {art.name}")
        elif _sha256(art) != listed[art.name]:
            problems.append(f"hash mismatch (tampered?): {art.name}")
    for name in listed:
        if not (dist / name).is_file():
            problems.append(f"listed artifact missing: {name}")
    # SBOM must be valid CycloneDX
    sbom_path = dist / _SBOM_NAME
    if not sbom_path.is_file():
        problems.append(f"missing SBOM: {sbom_path}")
    else:
        try:
            if json.loads(sbom_path.read_text())["bomFormat"] != "CycloneDX":
                problems.append("SBOM is not CycloneDX")
        except (OSError, ValueError, KeyError) as exc:
            problems.append(f"SBOM unreadable: {exc}")
    # provenance must reference every artifact with a sha256
    prov_path = dist / "provenance.intoto.jsonl"
    if not prov_path.is_file():
        problems.append(f"missing provenance: {prov_path}")
    else:
        try:
            prov = json.loads(prov_path.read_text())
            subjects = {s["name"]: s["digest"]["sha256"] for s in prov["subject"]}
            for art in _artifacts(dist):
                if subjects.get(art.name) != _sha256(art):
                    problems.append(f"provenance hash mismatch: {art.name}")
        except (OSError, ValueError, KeyError) as exc:
            problems.append(f"provenance unreadable: {exc}")
    return problems


def build(dist: Path) -> None:
    """Build the wheel + sdist into *dist* (requires `build`)."""
    dist.mkdir(parents=True, exist_ok=True)
    subprocess.run(  # noqa: S603 — trusted argv, no shell
        [sys.executable, "-m", "build", "--outdir", str(dist)], check=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="release manifest + verification")
    p.add_argument("--dist", default="dist", help="dist directory (default: dist)")
    p.add_argument("--build", action="store_true", help="build wheel+sdist first")
    p.add_argument("--verify-only", action="store_true", help="only verify")
    a = p.parse_args(argv)
    dist = Path(a.dist)
    if a.build:
        build(dist)
    if not a.verify_only:
        write_manifest(dist)
        print(f"wrote SBOM + SHA256SUMS + provenance into {dist}")
    problems = verify(dist)
    if problems:
        for prob in problems:
            print(f"  FAIL: {prob}", file=sys.stderr)
        print("release dry-run FAILED", file=sys.stderr)
        return 1
    print("release dry-run: OK (hashes match SHA256SUMS; SBOM + provenance verified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
