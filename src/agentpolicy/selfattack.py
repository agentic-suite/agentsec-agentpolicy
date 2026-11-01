"""The self-attack gate (WBS M22 ``22.1`` / ``22.2``, CUJ-32 / R46).

Replays the shipped ``self-attack`` pack — which attacks agentpolicy's **own**
decision surface — as a **normal pack**. A fixture whose expected outcome was a
block but which is no longer blocked is a **miss**, and **a miss blocks the
release**. The result is published with the release notes, misses included.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from agentpolicy.pack_format import run_pack_dir

#: Outcomes that stop, gate, or scrub a call — the "blocked" evidence.
BLOCKED: frozenset[str] = frozenset({"deny", "ask", "rate-limit", "redact"})

#: The default shipped pack.
DEFAULT_PACK = "packs/self-attack"


@dataclass(frozen=True)
class SelfAttackResult:
    """One replayed self-attack fixture."""

    pack: str
    name: str
    expected: str
    got: str

    @property
    def passed(self) -> bool:
        """Whether the replay produced the expected outcome."""
        return self.expected == self.got

    @property
    def missed(self) -> bool:
        """Whether an attack that should have been blocked got through."""
        return self.expected in BLOCKED and self.got not in BLOCKED

    def to_dict(self) -> dict[str, str | bool]:
        """JSON-friendly representation."""
        return {
            "pack": self.pack, "name": self.name, "expected": self.expected,
            "got": self.got, "passed": self.passed, "missed": self.missed,
        }


def self_attack_pack(pack_dir: str | Path) -> list[SelfAttackResult]:
    """Replay the self-attack pack's fixtures through its evaluator."""
    pack = Path(pack_dir)
    return [
        SelfAttackResult(pack=pack.name, name=r.name, expected=r.expected, got=r.got)
        for r in run_pack_dir(pack)
    ]


def gate(pack_dirs: Iterable[str | Path]) -> tuple[SelfAttackResult, ...]:
    """The fixtures that failed to block (empty == the gate passes)."""
    misses: list[SelfAttackResult] = []
    for pack_dir in pack_dirs:
        misses.extend(r for r in self_attack_pack(pack_dir) if not r.passed)
    return tuple(misses)


__all__ = ["BLOCKED", "DEFAULT_PACK", "SelfAttackResult", "gate", "self_attack_pack"]
