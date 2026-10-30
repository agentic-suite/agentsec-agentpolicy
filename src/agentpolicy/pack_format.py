"""The rule-pack format (WBS M4 ``4.1``).

A **rule pack** is a directory shipping an incident-anchored rule set:

```
packs/<name>/
  metadata.yaml     # name, version, description, incident_ref, license, trust, domains
  rules.cedar       # Cedar rules appended to the base policy
  tests.yaml        # golden fixtures (incident replays), evaluated deterministically
  validators.yaml   # (optional) argument validators — M13
```

The format is **strict** and **path-safe**: the manifest ``name`` must be a
slug matching the directory, or the pack is rejected (``PackFormatError``),
which the CLI surfaces as ``ConfigError`` (fail-closed).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from agentpolicy.canonical import canonicalize
from agentpolicy.cedar import CedarEvaluator
from agentpolicy.cedar.policy import BASE_POLICY

METADATA_FILE = "metadata.yaml"
RULES_FILE = "rules.cedar"
TESTS_FILE = "tests.yaml"

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


class PackFormatError(Exception):
    """A malformed rule pack (bad manifest, unsafe id, or unreadable file)."""


@dataclass(frozen=True)
class PackManifest:
    """A pack's ``metadata.yaml``."""

    name: str
    version: str
    description: str
    incident_ref: str = ""
    min_agentpolicy: str = "0.1.0"
    license: str = "Apache-2.0"
    trust: str = "community"
    domains: tuple[str, ...] = ()


@dataclass(frozen=True)
class PackTestResult:
    """The outcome of one golden fixture in a pack's replay."""

    name: str
    expected: str
    got: str
    passed: bool


@dataclass(frozen=True)
class Pack:
    """A loaded rule pack."""

    path: Path
    manifest: PackManifest
    rules_cedar: str
    fixtures: tuple[dict[str, Any], ...]

    def policies(self) -> str:
        """The Cedar policy set: the base policy + this pack's rules."""
        return BASE_POLICY + "\n" + self.rules_cedar

    def evaluator(self) -> CedarEvaluator:
        """A Cedar evaluator over the base policy + this pack."""
        return CedarEvaluator(self.policies())


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PackFormatError(f"cannot read {path.name}: {exc}") from exc


def load_manifest(pack_dir: Path) -> PackManifest:
    """Load and validate a pack's ``metadata.yaml``."""
    meta_path = pack_dir / METADATA_FILE
    if not meta_path.is_file():
        raise PackFormatError(f"missing {METADATA_FILE} in {pack_dir}")
    try:
        raw = yaml.safe_load(_read_text(meta_path)) or {}
    except yaml.YAMLError as exc:
        raise PackFormatError(f"invalid {METADATA_FILE}: {exc}") from exc
    if not isinstance(raw, dict):
        raise PackFormatError(f"{METADATA_FILE} must be a mapping")
    name = str(raw.get("name", "")).strip()
    if not _NAME_RE.match(name):
        raise PackFormatError(
            f"unsafe pack name {name!r}: expected a slug like 'destructive-commands'"
        )
    if pack_dir.name != name:
        raise PackFormatError(f"pack name {name!r} does not match its directory {pack_dir.name!r}")
    domains = raw.get("domains") or []
    if not isinstance(domains, list):
        raise PackFormatError("domains must be a list")
    return PackManifest(
        name=name,
        version=str(raw.get("version", "0.1.0")),
        description=str(raw.get("description", "")),
        incident_ref=str(raw.get("incident_ref", "")),
        min_agentpolicy=str(raw.get("min_agentpolicy", "0.1.0")),
        license=str(raw.get("license", "Apache-2.0")),
        trust=str(raw.get("trust", "community")),
        domains=tuple(str(d) for d in domains),
    )


def load_pack(target: str | Path) -> Pack:
    """Load a pack directory (manifest + rules + fixtures), or raise ``PackFormatError``."""
    pack_dir = Path(target)
    if not pack_dir.is_dir():
        raise PackFormatError(f"not a pack directory: {pack_dir}")
    manifest = load_manifest(pack_dir)
    rules_path = pack_dir / RULES_FILE
    rules = _read_text(rules_path) if rules_path.is_file() else ""
    tests_path = pack_dir / TESTS_FILE
    fixtures: tuple[dict[str, Any], ...] = ()
    if tests_path.is_file():
        try:
            doc = yaml.safe_load(_read_text(tests_path)) or {}
        except yaml.YAMLError as exc:
            raise PackFormatError(f"invalid {TESTS_FILE}: {exc}") from exc
        if not isinstance(doc, dict) or not isinstance(doc.get("fixtures", []), list):
            raise PackFormatError(f"{TESTS_FILE} must contain a 'fixtures' list")
        fixtures = tuple(doc.get("fixtures", []))
    # The rules must parse (fail fast on a malformed Cedar pack).
    CedarEvaluator(BASE_POLICY + "\n" + rules)
    return Pack(path=pack_dir, manifest=manifest, rules_cedar=rules, fixtures=fixtures)


def validate_pack_dir(target: str | Path) -> list[str]:
    """Validate a pack; return a (possibly empty) list of human-readable errors."""
    try:
        load_pack(target)
    except PackFormatError as exc:
        return [str(exc)]
    return []


def run_pack_dir(target: str | Path) -> list[PackTestResult]:
    """Replay a pack's golden fixtures deterministically through the Cedar core.

    Raises ``PackFormatError`` on a malformed pack. An empty ``tests.yaml``
    yields no results.
    """
    pack = load_pack(target)
    evaluator = pack.evaluator()
    results: list[PackTestResult] = []
    for fixture in pack.fixtures:
        if not isinstance(fixture, dict):
            raise PackFormatError("each fixture must be a mapping")
        extra = fixture.get("context") if isinstance(fixture.get("context"), dict) else None
        call = canonicalize(
            tool=str(fixture.get("tool", "")),
            action=str(fixture.get("action", "read")),
            environment=str(fixture.get("environment", "staging")),
            data_class=str(fixture.get("data_class", "internal")),
            agent_id=str(fixture.get("agent_id", "pack-tester")),
            agent_class=str(fixture.get("agent_class", "general")),
        )
        decision = evaluator.evaluate(
            call, budget_exhausted=bool(fixture.get("budget_exhausted", False)), extra_context=extra
        )
        expected = str(fixture.get("expect", fixture.get("expected", "allow")))
        results.append(
            PackTestResult(
                name=str(fixture.get("name", fixture.get("tool", "fixture"))),
                expected=expected,
                got=decision.decision,
                passed=decision.decision == expected,
            )
        )
    return results
