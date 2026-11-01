"""CI gates — ``goldens``, ``drill``, ``compliance`` (WBS M11).

* ``agentpolicy goldens check`` — replay golden fixtures; a deny→allow flip (vs a
  committed baseline) fails the build.
* ``agentpolicy drill check`` — replay the incident packs; an un-blocked incident
  replay fails the build.
* ``agentpolicy compliance export`` — emit the standards coverage matrix.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agentpolicy import agentdrill, claims, compliance, goldens, selfattack
from agentpolicy.cli.errors import CliError

_DEFAULT_FIXTURES = "tests/fixtures/acceptance_matrix.yaml"
_DEFAULT_PACKS = "packs"


def add_parser(subparsers: Any) -> None:
    """Register the ``goldens``, ``drill``, and ``compliance`` subcommands."""
    goldens_parser = subparsers.add_parser("goldens", help="golden decision regression gate")
    goldens_sub = goldens_parser.add_subparsers(
        dest="goldens_command", required=True, metavar="SUBCOMMAND"
    )
    gcheck = goldens_sub.add_parser("check", help="replay goldens vs a committed baseline")
    gcheck.add_argument("--fixtures", default=_DEFAULT_FIXTURES)
    gcheck.add_argument("--baseline", default=None, help="committed baseline JSON")
    gcheck.add_argument("--json", action="store_true")
    gcheck.set_defaults(func=_run_goldens_check)

    drill_parser = subparsers.add_parser("drill", help="incident-replay gate")
    drill_sub = drill_parser.add_subparsers(
        dest="drill_command", required=True, metavar="SUBCOMMAND"
    )
    dcheck = drill_sub.add_parser("check", help="replay the incident packs")
    dcheck.add_argument("--packs-dir", default=_DEFAULT_PACKS)
    dcheck.add_argument("--json", action="store_true")
    dcheck.set_defaults(func=_run_drill_check)

    compliance_parser = subparsers.add_parser("compliance", help="standards coverage export")
    compliance_sub = compliance_parser.add_subparsers(
        dest="compliance_command", required=True, metavar="SUBCOMMAND"
    )
    export = compliance_sub.add_parser("export", help="emit the coverage matrix")
    export.add_argument("--json", action="store_true")
    export.add_argument("-o", "--output", default=None)
    export.set_defaults(func=_run_compliance_export)

    claims_check = compliance_sub.add_parser(
        "claims", help="lint published claims against the coverage matrix"
    )
    claims_check.add_argument("--json", action="store_true")
    claims_check.set_defaults(func=_run_claims_check)

    self_attack = subparsers.add_parser(
        "self-attack", help="self-attack pack gate (a miss blocks the release)"
    )
    sa_sub = self_attack.add_subparsers(
        dest="self_attack_command", required=True, metavar="SUBCOMMAND"
    )
    sa_check = sa_sub.add_parser("check", help="replay the self-attack pack")
    sa_check.add_argument("--pack", default=selfattack.DEFAULT_PACK)
    sa_check.add_argument("--json", action="store_true")
    sa_check.set_defaults(func=_run_self_attack_check)


def _run_goldens_check(args: argparse.Namespace) -> int:
    try:
        cases = goldens.load_cases(args.fixtures)
    except OSError as exc:
        raise CliError(f"cannot read fixtures: {exc}") from exc
    if args.baseline:
        try:
            baseline = goldens.load_baseline(args.baseline)
        except OSError as exc:
            raise CliError(f"cannot read baseline: {exc}") from exc
        result = goldens.detect_flips(baseline, cases)
        if args.json:
            print(json.dumps([f.to_dict() for f in result.findings], indent=2))
        else:
            for finding in result.findings:
                print(f"  {finding.kind}: {finding.name} {finding.baseline} -> {finding.current}")
            if result.passed:
                print(f"goldens: {len(cases)} cases, no flips")
        return 0 if result.passed else 1
    baseline = goldens.capture(cases)
    print(goldens.dump_baseline(baseline))
    return 0


def _run_drill_check(args: argparse.Namespace) -> int:
    packs_dir = Path(args.packs_dir)
    pack_dirs = [d for d in sorted(packs_dir.iterdir()) if (d / "rules.cedar").exists()] if (
        packs_dir.exists()
    ) else []
    unblocked = agentdrill.gate(pack_dirs)
    if args.json:
        print(json.dumps([r.to_dict() for r in unblocked], indent=2))
    elif unblocked:
        for result in unblocked:
            print(f"  UNBLOCKED {result.pack}/{result.name}: {result.expected} -> {result.got}")
    else:
        print(f"drill: {len(pack_dirs)} incident pack(s) still block their replays")
    return 0 if not unblocked else 1


def _run_claims_check(args: argparse.Namespace) -> int:
    findings = claims.lint_claims()
    if args.json:
        print(json.dumps(findings, indent=2))
    elif findings:
        for finding in findings:
            print(f"  CLAIM: {finding}")
    else:
        print("claims: every published claim maps to a covered control")
    return 0 if not findings else 1


def _run_self_attack_check(args: argparse.Namespace) -> int:
    results = selfattack.self_attack_pack(args.pack)
    misses = [r for r in results if not r.passed]
    if args.json:
        print(json.dumps([r.to_dict() for r in misses], indent=2))
    elif misses:
        for miss in misses:
            print(f"  MISS {miss.pack}/{miss.name}: {miss.expected} -> {miss.got}")
    else:
        print(f"self-attack: {len(results)} case(s), no misses")
    return 0 if not misses else 1


def _run_compliance_export(args: argparse.Namespace) -> int:
    matrix = compliance.export_matrix()
    if args.output:
        Path(args.output).write_text(json.dumps(matrix, indent=2, sort_keys=True), encoding="utf-8")
        print(f"wrote {args.output}")
        return 0
    print(json.dumps(matrix, indent=2, sort_keys=True))
    return 0
