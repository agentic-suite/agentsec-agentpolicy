"""M23 — performance + portability NFRs (R8).

WBS M23: ``23.1`` performance + portability. The sub-100 ms p99 budget on the
**engine** path, Python 3.10+, macOS/Linux, local-first.
"""

from __future__ import annotations

from agentpolicy.engine.engine import Engine
from agentpolicy.nfr import is_portable_platform, local_first, p99_ms, supported_python
from agentpolicy.policy.models import default_policy


def _evaluate(engine: Engine) -> None:
    engine.evaluate(
        tool_name="query_logs", action="read", environment="staging",
        data_class="internal", agent_id="debug-bot",
    )


def test_engine_p99_under_100ms() -> None:
    engine = Engine(default_policy("balanced"))
    p99 = p99_ms(lambda: _evaluate(engine))
    assert p99 < 100.0, f"engine p99 was {p99:.2f} ms (budget 100 ms)"


def test_supported_python() -> None:
    assert supported_python((3, 10, 0))
    assert supported_python((3, 13, 0))
    assert not supported_python((3, 9, 0))


def test_portable_platforms() -> None:
    assert is_portable_platform("darwin")
    assert is_portable_platform("linux")
    assert not is_portable_platform("win32")


def test_local_first() -> None:
    assert local_first() is True
