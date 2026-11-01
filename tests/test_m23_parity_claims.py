"""M23 — parity/absorption ledger, standards/claims linter, deferred-optional.

WBS M23: ``23.5`` parity · ``23.6`` standards/claims · ``23.7`` deferred-optional.
PRD 10 / R32 / R13 / R14 / R31.
"""

from __future__ import annotations

from agentpolicy.claims import CLAIMS, Claim, lint_claims
from agentpolicy.deferred import DEFERRED, deferred_gate, deferred_report
from agentpolicy.parity import PARITY_LEDGER, parity_gate, parity_report


class TestParityLedger:
    def test_gate_is_green_no_silent_drops(self) -> None:
        assert parity_gate() == []

    def test_every_capability_is_present_and_classified(self) -> None:
        assert len(PARITY_LEDGER) >= 12
        for entry in PARITY_LEDGER:
            assert entry.status in {"delivered", "delegated", "waived"}
            if entry.status == "waived":
                assert entry.reason

    def test_report_counts(self) -> None:
        report = parity_report()
        assert report["total"] == len(PARITY_LEDGER)
        assert sum(report["by_status"].values()) == len(PARITY_LEDGER)


class TestClaimsLinter:
    def test_shipped_claims_lint_clean(self) -> None:
        assert lint_claims() == []
        assert CLAIMS

    def test_claim_on_an_unknown_control_is_flagged(self) -> None:
        finding = lint_claims([Claim("we invented a control", "OWASP-ASI", "ASI999")])
        assert finding and "ASI999" in finding[0]

    def test_claim_on_an_uncovered_control_is_flagged(self) -> None:
        matrix = {
            "frameworks": {
                "X": {
                    "controls": [
                        {"id": "C1", "covered": False, "framework": "X", "title": "t",
                         "domains": []},
                    ]
                }
            }
        }
        finding = lint_claims([Claim("we cover C1", "X", "C1")], matrix=matrix)
        assert finding and "C1" in finding[0]


class TestDeferredOptional:
    def test_every_item_is_implemented_or_waived_with_a_reason(self) -> None:
        assert deferred_gate() == []
        for item in DEFERRED:
            assert item.status in {"implemented", "waived"}
            if item.status == "waived":
                assert item.reason

    def test_report_lists_the_reqs(self) -> None:
        report = deferred_report()
        assert {"R13", "R14", "R31"} <= set(report["reqs"])
