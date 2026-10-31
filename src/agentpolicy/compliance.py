"""Standards coverage / evidence export (WBS M11 ``11.4``).

Walks the shipped rule packs and reports which **OWASP ASI / LLM** and **ATLAS**
controls the current policy set covers — a **computed** matrix (not a hardcoded
number) that agentcomply/agentwatch consume. See
``docs/reference/ci-regression.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentpolicy.pack_format import load_manifest

#: The repo's shipped packs directory (…/src/agentpolicy/compliance.py → repo root).
DEFAULT_PACKS_DIR = Path(__file__).resolve().parents[2] / "packs"

#: The export schema id.
SCHEMA = "agentcomply.coverage.v1"


@dataclass(frozen=True)
class Control:
    """One standards control and the policy domains that cover it."""

    framework: str
    control_id: str
    title: str
    domains: tuple[str, ...]

    def to_dict(self, *, covered: bool) -> dict[str, Any]:
        """JSON-friendly representation with the computed coverage."""
        return {
            "framework": self.framework,
            "id": self.control_id,
            "title": self.title,
            "covered": covered,
            "domains": list(self.domains),
        }


#: The curated control set (a representative OWASP ASI/LLM + ATLAS mapping).
CONTROLS: tuple[Control, ...] = (
    Control("OWASP-ASI", "ASI01", "Agent goal hijack", ("shell", "http", "mcp")),
    Control("OWASP-ASI", "ASI02", "Tool misuse", ("db", "shell", "cloud", "git")),
    Control("OWASP-ASI", "ASI03", "Privilege compromise", ("cloud", "secrets")),
    Control("OWASP-ASI", "ASI04", "Supply-chain tampering", ("mcp", "git")),
    Control("OWASP-ASI", "ASI05", "Unexpected code execution", ("shell", "db")),
    Control("OWASP-LLM", "LLM01", "Prompt injection", ("http", "secrets")),
    Control("OWASP-LLM", "LLM02", "Insecure output handling", ("secrets", "db")),
    Control("OWASP-LLM", "LLM06", "Sensitive information disclosure", ("secrets", "db")),
    Control("OWASP-LLM", "LLM07", "Insecure plugin design", ("mcp",)),
    Control("ATLAS", "AML.T0051", "LLM prompt injection", ("http", "secrets")),
    Control("ATLAS", "AML.T0054", "LLM jailbreak", ("shell", "mcp")),
    Control("ATLAS", "AML.T0012", "Exfiltration via tool", ("secrets", "http", "db")),
)


def _domains_of(pack_dir: Path) -> tuple[str, ...]:
    """The domains of one pack, or ``()`` when it cannot be loaded."""
    try:
        return load_manifest(pack_dir).domains
    except Exception:
        return ()


def shipped_domains(packs_dir: str | Path | None = None) -> set[str]:
    """The set of policy domains covered by the shipped packs."""
    directory = Path(packs_dir) if packs_dir is not None else DEFAULT_PACKS_DIR
    domains: set[str] = set()
    if not directory.exists():
        return domains
    for child in sorted(directory.iterdir()):
        if not child.is_dir() or not (child / "metadata.yaml").exists():
            continue
        domains.update(_domains_of(child))
    return domains


def coverage_matrix(packs_dir: str | Path | None = None) -> dict[str, Any]:
    """Compute the standards coverage matrix from the shipped packs."""
    covered_domains = shipped_domains(packs_dir)
    frameworks: dict[str, dict[str, Any]] = {}
    for control in CONTROLS:
        covered = bool(covered_domains & set(control.domains))
        bucket = frameworks.setdefault(
            control.framework, {"covered": 0, "total": 0, "controls": []}
        )
        bucket["controls"].append(control.to_dict(covered=covered))
        bucket["total"] += 1
        bucket["covered"] += int(covered)
    return {"covered_domains": sorted(covered_domains), "frameworks": frameworks}


def export_matrix(
    *, target: str = "agentcomply", packs_dir: str | Path | None = None
) -> dict[str, Any]:
    """Build the agentcomply-facing coverage artifact."""
    matrix = coverage_matrix(packs_dir)
    matrix["schema"] = SCHEMA
    matrix["target"] = target
    matrix["generated_from"] = "shipped packs (metadata.yaml domains)"
    return matrix


__all__ = [
    "CONTROLS",
    "DEFAULT_PACKS_DIR",
    "SCHEMA",
    "Control",
    "coverage_matrix",
    "export_matrix",
    "shipped_domains",
]
