"""``agentpolicy diff`` — kept vs overridden vs gaps (WBS M9 ``9.3``).

Compares a loaded policy against its posture default and classifies every entry:
**kept** (equal to the default), **overridden** (changed), or a **gap** (present
in the default, absent from the overlay). ``--json`` emits the structured diff
for CI.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from agentpolicy.cli.errors import CliError
from agentpolicy.errors import PolicyParseError
from agentpolicy.policy.loader import load_policy
from agentpolicy.policy.models import Policy, default_policy
from agentpolicy.policy.postures import available_postures


def add_parser(subparsers: Any) -> None:
    """Register the ``agentpolicy diff`` subcommand parser.

    Args:
        subparsers: The ``add_subparsers()`` action from the parent parser.
    """
    parser = subparsers.add_parser(
        "diff",
        help="compare policy against the default posture preset",
        description="Compare a policy file against its posture default; show kept/overridden/gaps.",
    )
    parser.add_argument(
        "policy",
        nargs="?",
        default="agentpolicy.yaml",
        help="policy file to check (default: ./agentpolicy.yaml)",
    )
    parser.add_argument(
        "--posture",
        choices=available_postures(),
        default=None,
        help="override posture inference (default: from file's posture field)",
    )
    parser.add_argument("--json", action="store_true", help="emit the structured diff as JSON")
    parser.set_defaults(func=_run)


def _diff_map(base: dict[str, Any], org: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return ``(kept_keys, overridden)`` for a name→value mapping."""
    kept: dict[str, Any] = {}
    overridden: dict[str, Any] = {}
    for key in sorted(set(base) | set(org)):
        if base.get(key) == org.get(key):
            kept[key] = base.get(key)
        else:
            overridden[key] = {"base": base.get(key), "policy": org.get(key)}
    return kept, overridden


def structured_diff(base: Policy, org: Policy) -> dict[str, Any]:
    """Classify a policy against its posture default."""
    env_kept, env_over = _diff_map(base.environments, org.environments)
    dc_kept, dc_over = _diff_map(base.data_classes, org.data_classes)
    rw_kept, rw_over = _diff_map(base.risk_weights, org.risk_weights)
    base_rules = {repr(r) for r in base.rules}
    org_rules = {repr(r) for r in org.rules}
    return {
        "posture": org.posture,
        "kept": {
            "environments": sorted(env_kept),
            "data_classes": sorted(dc_kept),
            "risk_weights": sorted(rw_kept),
            "rules": len(base_rules & org_rules),
        },
        "overridden": {
            "environments": env_over,
            "data_classes": dc_over,
            "risk_weights": rw_over,
            "rules_added": len(org_rules - base_rules),
            "rules_removed": len(base_rules - org_rules),
        },
        "gaps": {
            "environments": sorted(set(base.environments) - set(org.environments)),
            "data_classes": sorted(set(base.data_classes) - set(org.data_classes)),
            "rules_removed": sorted(base_rules - org_rules),
        },
    }


def _run(args: argparse.Namespace) -> int:
    try:
        org = load_policy(args.policy)
    except PolicyParseError as exc:
        raise CliError(f"cannot load policy: {exc}") from exc
    posture = args.posture if args.posture else org.posture
    base = default_policy(posture)
    diff = structured_diff(base, org)

    if args.json:
        print(json.dumps(diff, indent=2, sort_keys=True))
        return 0 if org == base else 1

    print(f"--- base (posture {posture})")
    print(f"+++ policy ({args.policy})")
    for env_name in sorted(set(base.environments) | set(org.environments)):
        if base.environments.get(env_name) != org.environments.get(env_name):
            print(
                f"  environment {env_name}: "
                f"{base.environments.get(env_name, '-')} -> "
                f"{org.environments.get(env_name, '-')}"
            )
    for dc_name in sorted(set(base.data_classes) | set(org.data_classes)):
        if base.data_classes.get(dc_name) != org.data_classes.get(dc_name):
            print(
                f"  data_class: {dc_name}: "
                f"{base.data_classes.get(dc_name, '-')} -> "
                f"{org.data_classes.get(dc_name, '-')}"
            )
    for dim in sorted(set(base.risk_weights) | set(org.risk_weights)):
        if base.risk_weights.get(dim) != org.risk_weights.get(dim):
            print(
                f"  risk_weight {dim}: "
                f"{base.risk_weights.get(dim, '-')} -> "
                f"{org.risk_weights.get(dim, '-')}"
            )
    if org.rules != base.rules:
        print(f"  rules: {len(base.rules)} -> {len(org.rules)} rules")
    print(f"  kept: {len(diff['kept']['environments'])} env, "
          f"{len(diff['kept']['data_classes'])} data class, "
          f"{diff['kept']['rules']} rule(s)")
    gaps = diff["gaps"]
    print(f"  gaps: {len(gaps['environments'])} env, {len(gaps['data_classes'])} data class, "
          f"{len(gaps['rules_removed'])} rule(s) removed")
    return 0 if org == base else 1
