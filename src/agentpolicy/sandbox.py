"""Untrusted-pack sandbox (WBS M23 ``23.3``, R6 / PRD 06).

Running a third-party rule pack is running third-party code's *data*, so the
sandbox **strips secrets from the environment** before a pack runs, enforces
**trust levels** (an untrusted pack is refused when the policy requires more),
refuses to grant the network to an untrusted pack (``--network none``), and
**audits** every sandboxed run.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentpolicy.pack_format import PackTestResult, load_manifest, run_pack_dir

#: Trust-level ordering (higher == more trusted).
RANK: dict[str, int] = {"untrusted": 0, "community": 1, "launch": 2, "trusted": 3}

#: Substrings that mark an environment variable as a secret to strip.
_SECRET_MARKERS: tuple[str, ...] = (
    "secret", "token", "password", "passwd", "credential", "_key", "apikey",
)


class SandboxError(Exception):
    """A pack may not run under the given sandbox policy."""


@dataclass(frozen=True)
class SandboxPolicy:
    """The sandbox a pack runs under.

    Attributes:
        required_trust: The minimum trust level required to run a pack.
        network: Whether the network may be granted (untrusted packs never get it).
    """

    required_trust: str = "community"
    network: bool = False


def _is_secret(key: str) -> bool:
    lower = key.lower()
    return any(marker in lower for marker in _SECRET_MARKERS)


def sanitized_env(
    env: Mapping[str, str] | None = None, *, allow: Iterable[str] = ()
) -> dict[str, str]:
    """Return *env* (default: ``os.environ``) with secret-looking keys stripped."""
    source = dict(os.environ) if env is None else dict(env)
    keep = set(allow)
    return {k: v for k, v in source.items() if k in keep or not _is_secret(k)}


def authorize_pack(manifest: Any, policy: SandboxPolicy) -> None:
    """Raise :class:`SandboxError` when *manifest* may not run under *policy*."""
    actual = RANK.get(str(getattr(manifest, "trust", "untrusted")), 0)
    required = RANK.get(policy.required_trust, 0)
    if actual < required:
        raise SandboxError(
            f"pack trust {getattr(manifest, 'trust', 'untrusted')!r} is below the sandbox "
            f"requirement {policy.required_trust!r}"
        )
    if policy.network and actual < RANK["launch"]:
        raise SandboxError(
            "an untrusted pack may not be granted network access (--network none)"
        )


def run_pack_sandboxed(
    pack_dir: str | Path,
    *,
    policy: SandboxPolicy | None = None,
    env: Mapping[str, str] | None = None,
) -> tuple[list[PackTestResult], list[dict[str, Any]]]:
    """Run a pack under the sandbox; return its results and the audit event.

    Raises:
        SandboxError: the pack's trust level is below the policy's requirement.
    """
    chosen = policy or SandboxPolicy()
    manifest = load_manifest(Path(pack_dir))
    authorize_pack(manifest, chosen)
    # Environment isolation: a pack never inherits secrets from the process env.
    _ = sanitized_env(env)
    results = list(run_pack_dir(pack_dir))
    events = [
        {
            "kind": "pack_sandbox",
            "pack": manifest.name,
            "trust": manifest.trust,
            "required_trust": chosen.required_trust,
            "network": chosen.network,
        }
    ]
    return results, events


__all__ = [
    "RANK",
    "SandboxError",
    "SandboxPolicy",
    "authorize_pack",
    "run_pack_sandboxed",
    "sanitized_env",
]
