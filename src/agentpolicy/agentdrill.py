"""agentdrill — the incident-replay gate (WBS M11 ``11.2``, CUJ-7 / R22).

Every launch pack is **incident-anchored** (``metadata.yaml: incident_ref``) and
ships the incident's **replay** (``tests.yaml``). A change that un-blocks a named
incident — a fixture whose expected outcome was a block but now allows — is
rejected before it can ship.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from agentpolicy.pack_format import run_pack_dir

#: Outcomes that stop, gate, or scrub a call — the "blocked" evidence.
BLOCKED: frozenset[str] = frozenset({"deny", "ask", "rate-limit", "redact"})


@dataclass(frozen=True)
class DrillResult:
    """One replayed incident fixture."""

    pack: str
    name: str
    expected: str
    got: str

    @property
    def passed(self) -> bool:
        """Whether the replay still produces the expected outcome."""
        return self.expected == self.got

    @property
    def unblocked(self) -> bool:
        """Whether a block was weakened to an allow (the regression)."""
        return self.expected in BLOCKED and self.got == "allow"

    def to_dict(self) -> dict[str, str | bool]:
        """JSON-friendly representation."""
        return {
            "pack": self.pack, "name": self.name, "expected": self.expected,
            "got": self.got, "passed": self.passed, "unblocked": self.unblocked,
        }


def drill_pack(pack_dir: str | Path) -> list[DrillResult]:
    """Replay a pack's incident fixtures through its evaluator."""
    pack = Path(pack_dir)
    results = run_pack_dir(pack)
    return [
        DrillResult(pack=pack.name, name=r.name, expected=r.expected, got=r.got)
        for r in results
    ]


def gate(pack_dirs: Iterable[str | Path]) -> tuple[DrillResult, ...]:
    """The fixtures whose incident block was un-blocked (empty == gate passes)."""
    unblocked: list[DrillResult] = []
    for pack_dir in pack_dirs:
        unblocked.extend(r for r in drill_pack(pack_dir) if r.unblocked)
    return tuple(unblocked)


__all__ = ["BLOCKED", "DrillResult", "drill_pack", "gate"]
