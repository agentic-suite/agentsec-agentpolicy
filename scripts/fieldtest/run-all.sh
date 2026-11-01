#!/usr/bin/env bash
# Run every field-test suite (s0..s18) and collect results.
# Results land under field-test/<FT_VERSION>/results/<suite>/.
#
#   run-all.sh              # all suites
#   run-all.sh s1-outcomes  # just these suites
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export FT_VERSION="${FT_VERSION:-v0.1.0}"
export STACK_KEEP=0
export FT_SHARED_STACK=1
# shellcheck source=lib.sh
source "$HERE/lib.sh"
export STACK_ON_NO_DOCKER=fail

ALL=(s0-regression s1-outcomes s2-explain s3-packs s4-policy s5-shadow
     s6-budgets s7-data s8-ask s9-surfaces s10-adversarial s11-freeze
     s12-enroll s13-multiagent s14-draft s15-backtest s16-frameworks
     s17-nfr s18-tier1)

suites=("$@")
if [[ ${#suites[@]} -eq 0 ]]; then
  suites=("${ALL[@]}")
fi

echo "==> field-test run: ${#suites[@]} suite(s); STACK_KEEP=$STACK_KEEP"

# Verify the verifier FIRST: if the grounding gate cannot catch a shallow pass,
# the whole run's green is worthless.
if ! python3 "$HERE/verify_harness.py"; then
  echo "!! verify-harness FAILED — the grounding gate is too weak; aborting." >&2
  exit 1
fi

rc=0
for s in "${suites[@]}"; do
  echo
  echo "############## suite $s ##############"
  if ! bash "$HERE/run-suite.sh" "$s"; then
    echo "!! suite $s had failures" >&2
    rc=1
  fi
done

# End-of-run deep verification across every suite: every PASS grounded
# (re-derived from disk), and the evidence leak-free. Part of the run.
echo
echo "==> end-of-run deep verification"
if ! python3 "$HERE/check_grounding.py" "$RESULTS_ROOT" --strict > "$RESULTS_ROOT/.grounding.log" 2>&1; then
  tail -6 "$RESULTS_ROOT/.grounding.log"
  echo "!! end-of-run deep-verification FAILED" >&2
  rc=1
else
  tail -2 "$RESULTS_ROOT/.grounding.log"
fi
if ! python3 "$HERE/scan_results.py" "$RESULTS_ROOT" --quiet; then
  echo "!! leak scan FAILED" >&2
  rc=1
else
  echo "leak scan: clean"
fi

echo
echo "==> run complete (rc=$rc). Results under field-test/$FT_VERSION/results/"
exit "$rc"
