"""The reason-code registry (WBS M5 ``5.2``).

The **single source of truth** for the machine-readable ``reason_code``
vocabulary the decision path emits. A code is stable (never re-used for a
different situation) and SIEM-alertable where marked. The Cedar shaper imports
these constants — no inline string literals — so the code in the decision path,
the audit trail, the emitted event, and the docs cannot drift.

See ``docs/reference/reason-codes.md`` and PRD 17 for the contract.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- the emitted codes (v0.1.0 Cedar path) ---------------------------------

#: allow — within the allow band.
ALLOW_LOW_RISK = "allow_low_risk"
#: an explicit rule decided the outcome (allow-justification is v0.2.0).
POLICY_MATCH = "policy_match"
#: deny — no permit matched (default-deny posture).
DEFAULT_DENY = "default_deny"
#: deny — the destructive/irreversible class.
IRREVERSIBLE_ACTION = "irreversible_action"
#: ask — the mandatory human gate.
HUMAN_GATE_REQUIRED = "human_gate_required"
#: deny — an ask expired / timed out (M7 ask broker).
HUMAN_GATE_TIMEOUT = "human_gate_timeout"
#: allow — an ask was approved by a human (M7).
ALLOW_ASK_APPROVED = "allow_ask_approved"
#: deny — an ask was denied by a human (M7).
DENY_ASK_DENIED = "deny_ask_denied"
#: deny — the ask is still pending (replay) (M7).
DENY_ASK_PENDING = "deny_ask_pending"
#: deny — the ask id is unknown (M7).
DENY_ASK_UNKNOWN = "deny_ask_unknown"
#: deny — an approval was reused for a different action identity (M7).
DENY_ACTION_IDENTITY_MISMATCH = "deny_action_identity_mismatch"
#: ask — a write by an agent in enrollment probation (M16).
AGENT_PROBATION = "agent_probation"
#: rate-limit — the session budget is exhausted.
BUDGET_EXHAUSTED = "budget_exhausted"
#: rate-limit — a burst/op-count limit was hit (M12).
RATE_LIMITED = "rate_limited"
#: redact — secret/PII content scrubbed from the result.
SECRET_DETECTED = "secret_detected"  # noqa: S105 - a reason code, not a password

# --- the failure taxonomy (wired by their owning milestones) ----------------

#: deny — the action could not be canonicalized.
UNKNOWN_ACTION = "unknown_action"
#: deny — the PDP could not evaluate.
ENGINE_UNAVAILABLE = "engine_unavailable"
#: deny — the policy is missing or malformed.
POLICY_UNAVAILABLE = "policy_unavailable"
#: deny — the Rego peer backend was unreachable (M4).
OPA_BACKEND_UNAVAILABLE = "opa_backend_unavailable"
#: deny — evaluation exceeded its time budget.
EVALUATION_TIMEOUT = "evaluation_timeout"
#: the audit write failed (the decision still stands).
AUDIT_SINK_ERROR = "audit_sink_error"


@dataclass(frozen=True)
class ReasonCode:
    """One registry entry.

    Attributes:
        code: The stable machine-readable code.
        meaning: One human sentence a SIEM analyst can read.
        alertable: Whether a SIEM should alert on this code individually.
        outcome: The decision outcome the code belongs to, or ``None`` when the
            code is a failure-taxonomy code not tied to one outcome.
    """

    code: str
    meaning: str
    alertable: bool
    outcome: str | None

    def to_dict(self) -> dict[str, object]:
        """JSON-friendly representation."""
        return {
            "code": self.code,
            "meaning": self.meaning,
            "alertable": self.alertable,
            "outcome": self.outcome,
        }


#: The closed registry, keyed by code. Insertion order is the doc order.
REASON_CODES: dict[str, ReasonCode] = {
    rc.code: rc
    for rc in (
        ReasonCode(ALLOW_LOW_RISK, "The action is within the allow band.", False, "allow"),
        ReasonCode(POLICY_MATCH, "An explicit rule decided the outcome.", False, None),
        ReasonCode(DEFAULT_DENY, "No permit matched (default-deny posture).", True, "deny"),
        ReasonCode(IRREVERSIBLE_ACTION, "A destructive/irreversible action.", True, "deny"),
        ReasonCode(HUMAN_GATE_REQUIRED, "A human decision is required.", True, "ask"),
        ReasonCode(HUMAN_GATE_TIMEOUT, "An ask expired without a decision.", True, "deny"),
        ReasonCode(ALLOW_ASK_APPROVED, "An ask was approved by a human.", False, "allow"),
        ReasonCode(DENY_ASK_DENIED, "An ask was denied by a human.", True, "deny"),
        ReasonCode(DENY_ASK_PENDING, "The ask is still pending (no approval).", True, "deny"),
        ReasonCode(DENY_ASK_UNKNOWN, "The ask id is unknown.", True, "deny"),
        ReasonCode(
            DENY_ACTION_IDENTITY_MISMATCH,
            "An approval was reused for a different action identity.",
            True,
            "deny",
        ),
        ReasonCode(AGENT_PROBATION, "A write by an agent in enrollment probation.", True, "ask"),
        ReasonCode(BUDGET_EXHAUSTED, "The session budget is exhausted.", True, "rate-limit"),
        ReasonCode(RATE_LIMITED, "A burst/op-count limit was hit.", False, "rate-limit"),
        ReasonCode(
            SECRET_DETECTED, "Sensitive content was scrubbed from the result.", True, "redact"
        ),
        ReasonCode(UNKNOWN_ACTION, "The action could not be canonicalized.", True, "deny"),
        ReasonCode(ENGINE_UNAVAILABLE, "The PDP could not evaluate the action.", True, "deny"),
        ReasonCode(POLICY_UNAVAILABLE, "The policy is missing or malformed.", True, "deny"),
        ReasonCode(OPA_BACKEND_UNAVAILABLE, "The Rego peer backend was unreachable.", True, "deny"),
        ReasonCode(EVALUATION_TIMEOUT, "Evaluation exceeded its time budget.", True, "deny"),
        ReasonCode(AUDIT_SINK_ERROR, "The audit write failed.", True, None),
    )
}

CODES: frozenset[str] = frozenset(REASON_CODES)


def is_known(code: str) -> bool:
    """Whether *code* is in the registry."""
    return code in REASON_CODES


def require(code: str) -> ReasonCode:
    """Return the registry entry for *code*, or raise.

    Raises:
        KeyError: *code* is not a registered reason code. An unregistered code
            is a programmer error, surfaced loudly — never silently emitted.
    """
    try:
        return REASON_CODES[code]
    except KeyError as exc:  # pragma: no cover - defensive, exercised by tests
        raise KeyError(f"unknown reason_code {code!r}; register it in reason_codes.py") from exc


def meaning(code: str) -> str:
    """The human meaning of *code* (empty string for an unknown code)."""
    entry = REASON_CODES.get(code)
    return entry.meaning if entry is not None else ""


def alertable_codes() -> frozenset[str]:
    """The codes a SIEM should alert on individually."""
    return frozenset(code for code, rc in REASON_CODES.items() if rc.alertable)


__all__ = [
    "AGENT_PROBATION",
    "ALLOW_ASK_APPROVED",
    "ALLOW_LOW_RISK",
    "AUDIT_SINK_ERROR",
    "BUDGET_EXHAUSTED",
    "CODES",
    "DEFAULT_DENY",
    "DENY_ACTION_IDENTITY_MISMATCH",
    "DENY_ASK_DENIED",
    "DENY_ASK_PENDING",
    "DENY_ASK_UNKNOWN",
    "ENGINE_UNAVAILABLE",
    "EVALUATION_TIMEOUT",
    "HUMAN_GATE_REQUIRED",
    "HUMAN_GATE_TIMEOUT",
    "IRREVERSIBLE_ACTION",
    "OPA_BACKEND_UNAVAILABLE",
    "POLICY_MATCH",
    "POLICY_UNAVAILABLE",
    "RATE_LIMITED",
    "REASON_CODES",
    "SECRET_DETECTED",
    "UNKNOWN_ACTION",
    "ReasonCode",
    "alertable_codes",
    "is_known",
    "meaning",
    "require",
]
