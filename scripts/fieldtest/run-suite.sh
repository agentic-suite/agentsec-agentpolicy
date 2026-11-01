#!/usr/bin/env bash
# Run one field-test suite: every case whose registry `suite` matches.
# Usage:
#   run-suite.sh SUITE              # e.g. s1-outcomes
#   run-suite.sh SUITE FT-DEC-ASK   # only these cases within the suite
#
# Results land under field-test/<FT_VERSION>/results/<SUITE>/. There is no skip:
# a case that cannot run is recorded as a failure. P/F|D cases may resolve to
# `declared`.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUITE="${1:-}"
shift || true
if [[ -z "$SUITE" ]]; then
  {
    echo "usage: run-suite.sh SUITE [CASE...]"
    echo "suites: s0-regression s1-outcomes s2-explain s3-packs s4-policy s5-shadow"
    echo "        s6-budgets s7-data s8-ask s9-surfaces s10-adversarial s11-freeze"
    echo "        s12-enroll s13-multiagent s14-draft s15-backtest s16-frameworks"
    echo "        s17-nfr s18-tier1"
  } >&2
  exit 2
fi

export FT_VERSION="${FT_VERSION:-v0.1.0}"
export FT_RUN_ID="$SUITE"
export STACK_KEEP=0
export FT_SHARED_STACK=1
# shellcheck source=lib.sh
source "$HERE/lib.sh"
export STACK_ON_NO_DOCKER=fail

ids=("$@")
if [[ ${#ids[@]} -eq 0 ]]; then
  while IFS= read -r id; do
    [[ -n "$id" ]] && ids+=("$id")
  done < <(python3 - "$HERE/cases/registry.json" "$SUITE" <<'PY'
import json, sys
try:
    registry = json.load(open(sys.argv[1], encoding="utf-8"))
except (OSError, ValueError):
    registry = []
for case in registry:
    if case.get("suite") == sys.argv[2] and not case.get("unsupported"):
        print(case["id"])
PY
)
fi

if [[ ${#ids[@]} -eq 0 ]]; then
  echo "run-suite: no cases found for suite '$SUITE'" >&2
  exit 2
fi

echo "==> suite $SUITE: ${#ids[@]} case(s) -> $FT_RUN_DIR"

rc=0
for id in "${ids[@]}"; do
  echo
  echo "################ $id ################"
  if ! bash "$HERE/run-case.sh" "$id"; then
    rc=1
  fi
done

echo
echo "==> Aggregating results into $FT_RUN_DIR"
python3 "$HERE/collect-results.py" "$FT_RUN_DIR" --expect "${ids[@]}" || true

# Deep verification is part of the run, not a separate step: every PASS must be
# grounded (re-derived from disk) and the committed evidence must be leak-free.
echo
echo "==> deep verification (grounding re-derivation + leak scan)"
if ! python3 "$HERE/check_grounding.py" "$RESULTS_ROOT" > "$FT_RUN_DIR/.grounding.log" 2>&1; then
  tail -5 "$FT_RUN_DIR/.grounding.log"
  echo "!! deep-verification FAILED (a PASS is not grounded)" >&2
  rc=1
else
  tail -2 "$FT_RUN_DIR/.grounding.log"
fi
if ! python3 "$HERE/scan_results.py" "$RESULTS_ROOT" --quiet; then
  echo "!! leak scan FAILED (unmasked secret in results)" >&2
  rc=1
else
  echo "leak scan: clean"
fi
exit "$rc"
