"""The exfil-sink rule class (WBS M13 ``13.1``, CUJ-13 / R10).

A **taint-lite** guard with no ML: a call that sends **sensitive** data
(``restricted`` / ``customer_pii``) to an **external-sink** tool (an ``http`` /
``email`` / ``notify`` domain) is an exfiltration chain, and is denied with a
reason that **names the source and the sink**. The rule is deterministic —
same call, same verdict.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentpolicy.types import NormalizedCall

#: Tool domains that move data *out* of the trust boundary.
EXFIL_SINK_DOMAINS: frozenset[str] = frozenset({"http", "email", "notify"})

#: Verbs that push data outward.
OUTBOUND_VERBS: frozenset[str] = frozenset(
    {"send", "post", "put", "write", "publish", "push", "upload", "forward"}
)

#: Data classes that must not leave.
SENSITIVE_DATA_CLASSES: frozenset[str] = frozenset({"restricted", "customer_pii"})


def exfil_violation(call: NormalizedCall) -> str | None:
    """Return a source→sink description when *call* is an exfil chain, else ``None``."""
    if (
        call.tool_category in EXFIL_SINK_DOMAINS
        and call.data_class in SENSITIVE_DATA_CLASSES
        and call.action in OUTBOUND_VERBS
    ):
        return (
            f"exfil-sink: sensitive {call.data_class} data flowing to external "
            f"sink {call.tool!r} ({call.tool_category})"
        )
    return None


__all__ = [
    "EXFIL_SINK_DOMAINS",
    "OUTBOUND_VERBS",
    "SENSITIVE_DATA_CLASSES",
    "exfil_violation",
]
