#!/usr/bin/env python3
"""WBS → GitHub: create agentpolicy v0.1.0 milestones + one issue per WBS work item.

Reads the work-item tables in `docs/wbs/v0.1.0/wbs-v0.1.0-part*.md`, creates a
GitHub milestone per WBS milestone, and one detailed issue per work item (agentdrill
body template). Idempotent: an existing milestone is reused; an existing issue
(matched by title) is skipped. Records the item→issue map to
`docs/wbs/v0.1.0/.issue-map.json` and, with `--write-wbs`, stamps the issue number
back into each part file's `Issue` column.

Usage:
    python scripts/wbs_issues.py                 # create everything
    python scripts/wbs_issues.py --write-wbs     # also stamp issue #s into the WBS
    python scripts/wbs_issues.py --milestones 0,1  # limit to M0,M1
"""
import argparse
import json
import os
import re
import subprocess
import sys

REPO = "agentic-suite/agentsec-agentpolicy"
BRANCH = "main"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WBS = os.path.join(ROOT, "docs/wbs/v0.1.0")

# Per-milestone metadata reused across the milestone's issues.
MILESTONES = {
    0: dict(name="Port the predecessor codebase", part="wbs-v0.1.0-part1-port-foundation.md",
            why="Make agentpolicy **self-contained** by absorbing the entire predecessor policy-engine codebase before any new work — later milestones re-point it from a bespoke Python risk scorer to a Cedar PDP.",
            what="A bulk port of the predecessor tree with a renamed namespace and a green ported suite.",
            how="Bulk-move the repo tree, rename the namespace, preserve git history, adapt packaging, get the ported suite green, record provenance.",
            data="None new (ported tree).", security="MIT attribution carried; the source repository is retained and made **private, never deleted**.",
            edge="Ported tests may assume predecessor names/paths.", prds=[10, 3], deps="—"),
    1: dict(name="Foundation & identity", part="wbs-v0.1.0-part1-port-foundation.md",
            why="Establish identity, CLI, config, and the CI quality gate every later milestone depends on.",
            what="The `agentpolicy` CLI surface, fail-closed configuration, the policy loader + `check`, and the CI quality gate.",
            how="Rebrand build config; wire the CLI + reserved exit codes; add fail-closed config; CI quality gate; `doctor`; policy loader + `check`.",
            data="Config model; loaded policy files.", security="Fail-closed on invalid config; never persist secrets.",
            edge="A malformed policy must refuse to load (never operate broken).", prds=[2, 11, 13], deps="M0"),
    2: dict(name="Cedar decision core (five outcomes)", part="wbs-v0.1.0-part2-decision-core-normalization.md",
            why="The decision core is the product: a deterministic Cedar PDP that returns one of five outcomes for every agent action.",
            what="A deterministic Cedar evaluator + decision shaper returning `allow`/`deny`/`ask`/`rate-limit`/`redact`, with the mandatory human-gate class and the inline latency budget.",
            how="Build the Cedar evaluator; the five-outcome shaper; the mandatory human-gate class; the decision model; measure the sub-100 ms p99 budget.",
            data="`Decision`/`Factor`/`Explanation` (PRD 15).", security="No ML/network in the path; fail-closed.",
            edge="Unknown action → deny; gate-class default change requires a logged amendment.", prds=[5, 15, 13], deps="M1"),
    3: dict(name="Action normalization, taxonomy & contextual model", part="wbs-v0.1.0-part2-decision-core-normalization.md",
            why="Every enforcer speaks a different shape; one canonical action + a contextual model is what makes a decision portable and correct.",
            what="A canonical action normalizer, the 13-domain taxonomy, the contextual decision model, and dispatcher/obfuscation safety.",
            how="Normalize every surface to one canonical action; fold tool names; parse coarse dispatcher input; ship the taxonomy; decide from the contextual dimensions.",
            data="Canonical action shape; taxonomy module.", security="Closes dispatcher-bypass and tool-name obfuscation as P0.",
            edge="Unicode/case/whitespace variants; `bash: git push --force` smuggling.", prds=[5, 4], deps="M2"),
    4: dict(name="Rule packs, pack tooling & policy backends", part="wbs-v0.1.0-part3-packs-explain.md",
            why="Shipped rules must stop the incidents that actually happened — and packs must be reusable, reviewable artifacts.",
            what="A versioned pack format, the three launch packs (destructive-commands/Replit, secret-in-output, mcp-allowlist), `pack validate`/`pack test`, and the OPA/Rego peer backend.",
            how="Define the pack format + loader; ship each launch pack anchored to its incident; wire `pack validate`/`pack test`; add the Rego backend.",
            data="Pack format + schema; Rego backend.", security="Untrusted packs validated strictly; path-safe ids.",
            edge="Malformed pack → `ConfigError`; Rego backend fails independently.", prds=[16, 5, 20], deps="M2, M3"),
    5: dict(name="Explain-decision, reason codes & event schema", part="wbs-v0.1.0-part3-packs-explain.md",
            why="A decision without an explanation gets bypassed; a decision the ecosystem cannot read is half a decision.",
            what="The explain-decision contract (matched rule, factors, criticality, suggested change), the reason-code registry, and decisions emitted in the agentwatch security-event schema.",
            how="Build the explain artifact + reason codes; the actionability test; `agentpolicy explain`; the event emitter.",
            data="Explain artifact; `agentwatch.security_event.v1` (`policy.decision`).", security="No policy internals leak to the agent; operator/agent split.",
            edge="A deny with no matched rule is a bug.", prds=[17, 5, 20], deps="M2, M3"),
    6: dict(name="Audit, policy versioning & tamper evidence", part="wbs-v0.1.0-part4-audit-ask.md",
            why="The decision log is forensic evidence — it must be tamper-evident and answer 'which policy governed this?'.",
            what="An append-only hash-chained audit log with the policy version/hash on every entry, review-flagging, and an offline-verifiable evidence artifact.",
            how="Build the audit log + sinks; `audit query`/`show`; the hash chain + rotation anchor; policy versioning + the review flag; the offline evidence artifact.",
            data="Audit entries; evidence artifact.", security="Tamper-evident chain; a truncated/rebuilt log is detectable.",
            edge="Rotation never breaks the chain; a missing segment is a loud finding.", prds=[7, 17, 13], deps="M5"),
    7: dict(name="Ask round-trip, redaction & secrets-in-args", part="wbs-v0.1.0-part4-audit-ask.md",
            why="Irreversible actions need a reliable human gate, and secrets must not leave through output **or arguments**.",
            what="The ask-gate round-trip (action-identity bound, expiring, timeout=deny), redact-and-allow with receipts, and secrets-in-arguments handling.",
            how="Build the ask broker + approve/deny CLI; redact-and-allow; argument-side secret detection + receipts.",
            data="Ask/Approval; redaction receipts.", security="Action-identity binding prevents replay; raw secrets never persisted.",
            edge="Replay with different args; expiry; timeout=deny.", prds=[4, 17, 5], deps="M2, M5"),
    8: dict(name="Delivery surfaces & adapters", part="wbs-v0.1.0-part5-surfaces-postures.md",
            why="One decision service must be callable from every harness/enforcer — library, CLI, MCP, HTTP.",
            what="The delivery surfaces (library, CLI, MCP server, HTTP) and a validated adapter registry.",
            how="Expose the same engine through each surface; build the adapter registry; wire a reference enforcer integration.",
            data="Adapter manifests.", security="Uniform decision semantics across surfaces.",
            edge="Unknown adapter → `ConfigError`; a denied call must be model-consumable.", prds=[19, 2, 5], deps="M2, M5"),
    9: dict(name="Posture presets, init, diff & lint", part="wbs-v0.1.0-part5-surfaces-postures.md",
            why="Adoption starts with a sane default, not a blank file — and policy must be lintable and portable.",
            what="Posture presets (strict/balanced/permissive) + `init`, policy `diff`, rule-pack lint, and the policyweave export surface.",
            how="Ship the presets + `init`; `diff`; lint (unused/shadowed/over-permissive/conflict/secrets); export for policyweave.",
            data="Preset policies; lint report.", security="Overrides must not accidentally permit a dangerous action.",
            edge="Never a blank slate; lint findings are CI-failable.", prds=[5, 20, 16], deps="M4, M5"),
    10: dict(name="Shadow mode, calibration & canary", part="wbs-v0.1.0-part6-shadow-ci.md",
             why="Trust before you enforce — shadow mode + calibration are the adoption funnel.",
             what="Shadow/dry-run mode, the calibration report (false-block/miss rates), and canary rollout.",
             how="Implement `dry_run`; `audit query --dry-run`; the calibration report; percentage-based canary rollout.",
             data="Shadow decisions; calibration report.", security="Shadow decisions never reach the agent.",
             edge="Canary selection must be deterministic.", prds=[5, 7], deps="M6"),
    11: dict(name="CI regression suite & fail-closed hardening", part="wbs-v0.1.0-part6-shadow-ci.md",
             why="A policy change must not silently un-block a known attack; every failure path must deny.",
             what="Golden decision fixtures, the agentdrill replay gate, the fail-closed fuzz suite, and coverage/evidence export.",
             how="Ship the golden suite + replay gate; fuzz the input space asserting fail-closed; export the standards coverage matrix.",
             data="Golden fixtures; coverage matrix.", security="0 failure modes silently allow.",
             edge="A golden deny→allow flip fails the build.", prds=[7, 12, 13], deps="M4, M6"),
    12: dict(name="Session state, blast-radius budgets & rate limits", part="wbs-v0.1.0-part7-budgets-exfil.md",
             why="Per-call rules decide *what*; budgets decide *how much* — the novel class nobody ships.",
             what="Session/context state, cumulative blast-radius budgets, and rate/burst limits with `retry_after`.",
             how="Build the session store; cumulative budgets (files/requests/spend/calls); rate/burst limits; the agenthalt trigger.",
             data="SessionState; budget state in every decision.", security="Cumulative counting defeats split evasion.",
             edge="Exhaustion → `rate-limit`/halt with a reason; budget reset/inherit semantics.", prds=[18, 5, 13], deps="M6"),
    13: dict(name="Exfil-sink, argument validation & tool hiding", part="wbs-v0.1.0-part7-budgets-exfil.md",
             why="Data-flow and argument semantics are where real exfil and misuse happen.",
             what="The exfil-sink rule class (taint-lite, no ML), argument-level validators, and discovery-time tool hiding.",
             how="Ship the exfil-sink pack; argument validators (regex/range/enum/path/URL); tool hiding.",
             data="Exfil-sink pack; validators.", security="Blocks outputs carrying secrets/PII from reaching external sinks.",
             edge="The rule names source + sink.", prds=[16, 5], deps="M3, M7"),
    14: dict(name="Step-up, AuthZEN interop & adversarial suite", part="wbs-v0.1.0-part8-stepup-freeze.md",
             why="The PDP must be interop-standard and provably un-trickable.",
             what="Scope-escalation/step-up, the AuthZEN Authorization API 1.0 binding, and the adversarial resilience suite.",
             how="Build the step-up rules; the AuthZEN `/access/v1/evaluation` binding + MCP ask path; the adversarial sub-matrix.",
             data="AuthZEN binding; step-up requests.", security="Every bypass attempt blocks + logs a distinct reason.",
             edge="AuthZEN conformance; the swap test.", prds=[20, 4], deps="M5, M8"),
    15: dict(name="Freeze windows & data-class derivation", part="wbs-v0.1.0-part8-stepup-freeze.md",
             why="The Replit incident happened during a declared code freeze — the policy must be able to express it; and data classes must be derivable.",
             what="Change-freeze/maintenance windows and declarative data-class derivation.",
             how="Build freeze declaration + audit + the `code-freeze` pack; the data-class derivation table.",
             data="Freeze artifacts; data-class derivation.", security="A declared freeze the policy enforces, not a prompt.",
             edge="Overlapping freezes → strictest wins; a data-class conflict fails loudly.", prds=[22, 16], deps="M9, M10"),
    16: dict(name="Enrollment/probation & approval analytics", part="wbs-v0.1.0-part9-enrollment-alternatives.md",
             why="First-seen agents need a safe posture, and human gates that are always approved are theater.",
             what="Agent enrollment + probation posture, and the approval-analytics report (rubber-stamp detection).",
             how="Build the enrollment ledger + probation; the approval-analytics report.",
             data="Enrollment ledger; analytics report.", security="No shadow IdP — classify, never issue identity.",
             edge="First-seen write → `ask` + `agent_probation`; always-approved gate flagged.", prds=[22, 7], deps="M9, M12"),
    17: dict(name="Nearest-permissible-action & multi-agent governance", part="wbs-v0.1.0-part9-enrollment-alternatives.md",
             why="Denials that offer a true alternative get adopted; delegation must not leak scope.",
             what="`permitted_alternatives[]` on decisions, delegation-chain evaluation, scope-subset proofs, and inter-agent decisions.",
             how="Generate verified-permissible alternatives (agent/operator split); delegation chains + scope-subset; inter-agent decisions; the delegation pack.",
             data="Alternatives; delegation chain.", security="Alternatives are evaluated-true; no policy internals leak.",
             edge="Out-of-scope child denied, chain link named.", prds=[22, 5], deps="M5, M12"),
    18: dict(name="Break-glass & dual-control", part="wbs-v0.1.0-part10-breakglass-drafting.md",
             why="Incidents need time-boxed elevation, and the irreversible class may need two humans.",
             what="Break-glass elevation with auto-revert, and dual-control (quorum) approvals.",
             how="Build break-glass (reason, TTL, auto-revert, audit); dual-control quorum; the composition guard.",
             data="Break-glass windows; quorum approvals.", security="Elevation widens scope ceilings only, never the human-gate class.",
             edge="Expiry reverts automatically; same-principal second approval rejected.", prds=[22, 7], deps="M7, M16"),
    19: dict(name="NL policy drafting", part="wbs-v0.1.0-part10-breakglass-drafting.md",
             why="Cedar's learning curve is the adoption bar; a sentence-to-rule draft lowers it — without touching the decision path.",
             what="`agentpolicy draft` — NL → candidate Cedar rule, advisory only, gated on generated tests + human review.",
             how="Build the draft command (model call outside runtime); generate `tests.yaml`; the human-review gate + boundary lock.",
             data="Draft artifacts; generated tests.", security="The decision path contains no ML (boundary-lock test).",
             edge="An over-permissive draft is caught by lint; drafts are never auto-pinned.", prds=[22, 11], deps="M9"),
    20: dict(name="Policy backtest & PR decision-diff", part="wbs-v0.1.0-part11-backtest-layering.md",
             why="Policy changes are the scariest moment of adoption — prove what a change would have done to real history.",
             what="A backtest engine replaying recorded history against a candidate policy, with the flip set attached to the PR (read-only, advisory).",
             how="Build `backtest`; the PR decision-diff; the advisory watermark + golden-gate exclusion.",
             data="Flip set; backtest watermark.", security="Read-only; emits no fleet events.",
             edge="Thin history window is stated; never auto-merges.", prds=[23, 7], deps="M6, M11"),
    21: dict(name="Narrow-only layering & action-space coverage report", part="wbs-v0.1.0-part11-backtest-layering.md",
             why="A central team must guarantee a floor while teams tighten locally; and the silent quadrant is where incidents hide.",
             what="Narrow-only policy layering (org → project → session) and the action-space coverage report.",
             how="Build layered composition + the narrow-only invariant at load; the coverage report (four quadrants).",
             data="Layers; coverage report.", security="A widening overlay fails at `check`; `gap:unexplained` = 0.",
             edge="Overlay fuzz must never widen the floor.", prds=[23, 16], deps="M9"),
    22: dict(name="Self-attack pack & allow-justification", part="wbs-v0.1.0-part12-selfattack-hardening.md",
             why="A decision service that never drills itself is asking to be trusted on faith; and allows must be as traceable as denies.",
             what="A shipped self-attack pack (run every release) and allow-justification (`matched_rule` on every outcome).",
             how="Ship the self-attack pack; the release-cadence CI job; allow-justification + allow-side analytics.",
             data="Self-attack pack; matched_rule on all outcomes.", security="A seeded miss blocks the release; misses published.",
             edge="The pack is dogfoodable by third parties.", prds=[6, 23, 17], deps="M14, M20"),
    23: dict(name="NFRs, hardening, parity closure & deferred-optional", part="wbs-v0.1.0-part12-selfattack-hardening.md",
             why="Meet the non-functionals, harden against the own-threat-model, and close the parity ledger.",
             what="Performance/portability/fail-closed hardening, the untrusted-pack sandbox, cost controls, the parity/absorption ledger, the standards/compliance export, and the deferred-optional items.",
             how="Meet perf budgets; fault-inject every path; sandbox untrusted packs; cost governor; close the parity ledger; regenerate the compliance matrix; land or waive the deferred-optional items.",
             data="Parity ledger; compliance matrix.", security="Fail-closed on tamper; untrusted packs sandboxed.",
             edge="Deferred-optional items are implemented or explicitly waived with reason.", prds=[13, 20, 10], deps="M4, M14, M22"),
    24: dict(name="Field tests", part="wbs-v0.1.0-part13-fieldtest-release.md",
             why="The plan is only credible if it runs in real agent loops — every CUJ executed end to end.",
             what="A Docker field-test harness driving a demo enforcer + the system-under-test, exercising every CUJ-1..33 across frameworks, with an honest published report.",
             how="Build the harness; the scenario matrix; framework coverage; the adversarial + self-attack runs; publish the report; fix every harness defect with a regression.",
             data="Field-test report; captured request/response pairs.", security="An honest report — misses named, not-tested list empty.",
             edge="A P0 CUJ miss blocks the release.", prds=[4, 7, 19], deps="M0–M23"),
    25: dict(name="Release readiness", part="wbs-v0.1.0-part13-fieldtest-release.md",
             why="Ship it: signed artifacts, evidence, audit, and the tag.",
             what="Release tooling (SBOM, SHA256SUMS, SLSA provenance), first-run evidence, security audit, the compliance/standards matrix, release notes, the tag + PyPI publish, and making the predecessor private.",
             how="Build release tooling; record first-run evidence; security audit; publish the compliance matrix + release notes; tag `v0.1.0` + release + PyPI; make the predecessor private.",
             data="SBOM; provenance; release notes.", security="Signed artifacts; 0 unresolved findings.",
             edge="Hashes must match `SHA256SUMS`; the predecessor is retained private, never deleted.", prds=[7, 9, 20], deps="M24"),
}


def run(args):
    return subprocess.run(args, capture_output=True, text=True)


def gh_json(args):
    r = run(["gh"] + args)
    if r.returncode != 0:
        raise SystemExit(f"gh failed: {args}\n{r.stderr}")
    return json.loads(r.stdout or "null")


def parse_part(path):
    """Yield dicts: ms,item,task,desc,deliverable,acceptance,issue,cuj,req."""
    items, ms = [], None
    for line in open(path):
        h = re.match(r"^## Milestone M(\d+) — ", line)
        if h:
            ms = int(h.group(1))
            continue
        if ms is not None and re.match(r"^\|\s*[0-9]+\.[0-9A-Za-z]+\s*\|", line):
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            # # | Task | Description | Deliverable | Acceptance | Issue | CUJ | Req
            if len(c) >= 8:
                items.append(dict(ms=ms, item=c[0], task=c[1], desc=c[2], deliverable=c[3],
                                  acceptance=c[4], issue=c[5], cuj=c[6], req=c[7]))
    return items


def strip_md(s):
    return re.sub(r"`(.+?)`", r"\1", re.sub(r"\*\*(.+?)\*\*", r"\1", s)).strip()


def part_files():
    fs = [f for f in os.listdir(WBS) if re.match(r"wbs-v0.1.0-part\d+-.*\.md$", f)]
    return sorted(fs, key=lambda f: int(re.search(r"part(\d+)", f).group(1)))


def prd_link(n):
    fs = [f for f in os.listdir(os.path.join(ROOT, "docs/prd")) if f.startswith(f"{n:02d}-")]
    p = f"docs/prd/{fs[0]}" if fs else f"docs/prd/{n:02d}-*.md"
    return f"[PRD {n:02d}](https://github.com/{REPO}/blob/{BRANCH}/{p})"


def build_body(ms, it):
    m = MILESTONES[ms]
    title = strip_md(it["task"])
    refs = " · ".join(prd_link(n) for n in m["prds"])
    cuj = f"**CUJs:** {it['cuj']} · **Requirements:** {it['req']}\n\n" if it["cuj"] not in ("—", "-", "") else ""
    return f"""# M{ms} {it['item']} — {title}

> `[0.1.0 M{ms}]` — owning milestone: **M{ms} {m['name']}**. Source item: `{m['part']}` `{it['item']}`.

**Why.** {m['why']} _This item:_ {title} — it produces the **{it['deliverable']}** deliverable and unblocks later items.

**Behavior / What.** {m['what']} This item delivers **{it['deliverable']}**: {it['desc']}

**How.**
{m['how']}

Steps:
1. Read the linked PRD/design sections above before writing code.
2. Implement "{title}": {it['desc']}
3. Wire it into **{it['deliverable']}** and expose it through the documented surface (CLI/library/MCP/HTTP) within this milestone.
4. Handle failure modes **loudly** — invalid input, unknown references, and partial state must never pass silently.
5. Keep it **deterministic** (no ML/network in any decision path) and evidence-bound where results are produced.
6. Update docs as you go (this milestone's `.D` item).

**Data & schema impact.** {m['data']}

**Security & privacy.** {m['security']}

**Edge cases.** {m['edge']}

**Testing.**
- Test-first (RED → GREEN): write a failing test asserting _{strip_md(it['acceptance']) or 'the behaviour above'}_, run it (**RED**), implement, run it (**GREEN**).
- Minimum cases: unit + integration + (where relevant) fault-injection tests for the new paths.
- Happy path **and** at least one failure path; determinism where applicable; no regression in earlier items of this milestone.

**Risks & mitigations.** Scope creep beyond this item — keep the diff to the linked WBS item.

## Acceptance criteria
- [ ] {strip_md(it['acceptance']) or 'The item behaves as specified above'}
- [ ] Wired into **{it['deliverable']}**; reachable from the documented surface
- [ ] Failure modes handled loudly (invalid input / unknown reference / partial state)
- [ ] All tests pass; every new code path has a test
- [ ] Code coverage ≥ 95% on touched modules
- [ ] `ruff` zero violations; `mypy --strict` clean
- [ ] Code review recorded in `docs/wbs/v0.1.0/codereview-log.md`; all findings resolved
- [ ] Design/reference docs updated and linked from the WBS

{cuj}## Dependencies
{m['deps']}

## References
- WBS: `docs/wbs/v0.1.0/{m['part']}` · index: `docs/wbs/v0.1.0/wbs-v0.1.0-index.md`
- {refs}

## Definition of done
Implemented + tests passing + committed + pushed + this issue closed (or commented with status), with a
checkpoint recorded in the WBS index. Commits are conventional and DCO-signed.

<!-- wbs:{it['item']} -->
"""


def milestone_title(ms):
    return f"0.1.0 — M{ms} {MILESTONES[ms]['name']}"


def ensure_milestone(ms):
    """Return (number, title) for the milestone, creating it if absent. Match by title."""
    title = milestone_title(ms)
    for m in gh_json(["api", f"repos/{REPO}/milestones?state=all&per_page=100"]):
        if m["title"] == title:
            return m["number"], title
    r = run(["gh", "api", f"repos/{REPO}/milestones", "-f", f"title={title}",
             "-f", "state=open", "-f", f"description=agentpolicy v0.1.0 — {MILESTONES[ms]['name']} (WBS M{ms})."])
    if r.returncode != 0:
        raise SystemExit(f"milestone create failed: {r.stderr}")
    return json.loads(r.stdout)["number"], title


def existing_issue_numbers():
    out = {}
    r = run(["gh", "issue", "list", "-R", REPO, "--state", "all", "--limit", "1000",
             "--json", "number,title"])
    if r.returncode == 0:
        for i in json.loads(r.stdout):
            out[i["title"]] = i["number"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-wbs", action="store_true", help="stamp issue #s into the part files")
    ap.add_argument("--milestones", default="", help="comma list, e.g. 0,1")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    only = {int(x) for x in args.milestones.split(",") if x.strip()} if args.milestones else None
    items = []
    for p in part_files():
        items += parse_part(os.path.join(WBS, p))
    by_ms = {}
    for it in items:
        by_ms.setdefault(it["ms"], []).append(it)
    print(f"parsed {len(items)} work items across {len(part_files())} part files")

    known = existing_issue_numbers()
    mapping = {}
    if os.path.exists(os.path.join(WBS, ".issue-map.json")):
        mapping = json.load(open(os.path.join(WBS, ".issue-map.json")))

    run(["gh", "label", "create", "0.1.0", "-R", REPO, "-c", "1d76db", "-d", "v0.1.0 scope", "--force"])
    run(["gh", "label", "create", "wbs", "-R", REPO, "-c", "5319e7", "-d", "work-breakdown item", "--force"])

    for ms in sorted(by_ms):
        if only and ms not in only:
            continue
        num, title = ensure_milestone(ms)
        print(f"milestone M{ms} -> #{num} ({title})")
        for it in by_ms[ms]:
            if it["item"].endswith(".CI") or it["item"].endswith(".W"):
                continue  # process steps (git + WBS checkpoint); not tracked as issues
            ititle = f"[0.1.0 M{ms}] {it['item']} {strip_md(it['task'])}"
            if ititle in known:
                print(f"  = {it['item']} already #{known[ititle]}")
                mapping[it["item"]] = known[ititle]
                continue
            if args.dry_run:
                print(f"  + {it['item']} (dry-run)")
                continue
            body = build_body(ms, it)
            r = run(["gh", "issue", "create", "-R", REPO, "--milestone", title,
                     "--title", ititle, "--body", body, "--label", "0.1.0", "--label", "wbs"])
            if r.returncode != 0:
                print(f"  ✗ {it['item']}: {r.stderr.strip()[:120]}")
                continue
            inum = int(r.stdout.strip().splitlines()[-1].rstrip("/").split("/")[-1])
            mapping[it["item"]] = inum
            print(f"  ✓ {it['item']} -> #{inum}")

    if not args.dry_run:
        json.dump(mapping, open(os.path.join(WBS, ".issue-map.json"), "w"), indent=2, sort_keys=True)
        print(f"map: {len(mapping)} items -> docs/wbs/v0.1.0/.issue-map.json")

    if args.write_wbs and not args.dry_run:
        for p in part_files():
            path = os.path.join(WBS, p)
            lines = open(path).read().splitlines()
            out = []
            for line in lines:
                mm = re.match(r"^\|\s*([0-9]+\.[0-9A-Za-z]+)\s*\|", line)
                if mm and mm.group(1) in mapping:
                    cells = line.split("|")
                    if len(cells) >= 8:
                        cells[6] = f" #{mapping[mm.group(1)]} "
                        line = "|".join(cells)
                out.append(line)
            open(path, "w").write("\n".join(out) + "\n")
        print("WBS part files stamped with issue numbers")


if __name__ == "__main__":
    main()
