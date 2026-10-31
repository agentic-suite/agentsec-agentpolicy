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

from agentpolicy import agentdrill, compliance, goldens
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


def _run_compliance_export(args: argparse.Namespace) -> int:
    matrix = compliance.export_matrix()
    if args.output:
        Path(args.output).write_text(json.dumps(matrix, indent=2, sort_keys=True), encoding="utf-8")
        print(f"wrote {args.output}")
        return 0
    print(json.dumps(matrix, indent=2, sort_keys=True))
    return 0
