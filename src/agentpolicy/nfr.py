"""Non-functional targets (WBS M23 ``23.1``, R8).

The sub-100 ms p99 budget, Python 3.10+, macOS/Linux portability, and
local-first operation. The Cedar evaluator's latency is separately covered by
``tests/test_cedar_latency.py``; this module measures the **engine** path.
"""

from __future__ import annotations

import platform
import statistics
import sys
import time
from collections.abc import Callable
from typing import Any

#: The minimum supported Python.
MIN_PYTHON: tuple[int, int] = (3, 10)
#: The supported platforms (local-first: a developer laptop or a Linux server).
PORTABLE_PLATFORMS: frozenset[str] = frozenset({"darwin", "linux"})
#: The sub-100 ms p99 budget (PRD 13 / R8).
P99_BUDGET_MS = 100.0


def p99_ms(
    fn: Callable[[], Any], *, samples: int = 300, warmup: int = 50
) -> float:
    """Measure the 99th-percentile latency (ms) of *fn* over *samples* calls."""
    for _ in range(warmup):
        fn()
    timings: list[float] = []
    for _ in range(samples):
        start = time.perf_counter()
        fn()
        timings.append((time.perf_counter() - start) * 1000.0)
    return statistics.quantiles(timings, n=100)[98]


def supported_python(version_info: Any = None) -> bool:
    """Whether the running interpreter (or *version_info*) is Python 3.10+."""
    version = version_info if version_info is not None else sys.version_info
    return tuple(version[:2]) >= MIN_PYTHON


def is_portable_platform(system: str | None = None) -> bool:
    """Whether *system* (default: the current platform) is macOS or Linux."""
    return (system or platform.system()).lower() in PORTABLE_PLATFORMS


def local_first() -> bool:
    """Whether the engine decides in-process with no network or external service."""
    from agentpolicy.engine.engine import Engine
    from agentpolicy.policy.models import default_policy

    decision = Engine(default_policy("balanced")).evaluate(
        tool_name="query_logs", action="read", environment="staging",
        data_class="internal", agent_id="nfr-check",
    )
    return decision.decision in {"allow", "audit", "escalate", "deny"}


__all__ = [
    "MIN_PYTHON",
    "P99_BUDGET_MS",
    "PORTABLE_PLATFORMS",
    "is_portable_platform",
    "local_first",
    "p99_ms",
    "supported_python",
]
