#!/usr/bin/env bash
# Run one field-test case. Usage:
#   run-case.sh CASE-ID [--keep]
#
# Sources cases/steps/<CASE-ID>.sh, which runs its assertions and calls
# ft_finalize (which sets FT_CASE_STATUS=pass only if every assertion held AND at
# least one grounded check backs the pass). There is no skip: a case that does
# not pass is a failed case (or `declared` for a P/F|D case).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ID="${1:-}"
KEEP="${2:-}"
if [[ -z "$ID" ]]; then
  echo "usage: run-case.sh CASE-ID [--keep]" >&2
  exit 2
fi

# Derive FT_RUN_ID from the registry BEFORE sourcing lib.sh (lib.sh refuses an
# unset FT_RUN_ID so a stray "all" results dir can never be created).
REGISTRY="$HERE/cases/registry.json"
_reg() { python3 - "$REGISTRY" "$ID" "$1" <<'PY'
import json, sys
try:
    registry = json.load(open(sys.argv[1], encoding="utf-8"))
except (OSError, ValueError):
    registry = []
match = next((c for c in registry if c.get("id") == sys.argv[2]), {})
print(match.get(sys.argv[3], ""))
PY
}

if [[ -z "${FT_RUN_ID:-}" ]]; then
  export FT_RUN_ID="$(_reg suite)"
  [[ -n "$FT_RUN_ID" ]] || export FT_RUN_ID="standalone"
fi

# shellcheck source=lib.sh
source "$HERE/lib.sh"
export STACK_ON_NO_DOCKER=fail
if [[ "$KEEP" == "--keep" ]]; then export STACK_KEEP=1; fi

STEP="$HERE/cases/steps/$ID.sh"
if [[ ! -f "$STEP" ]]; then
  echo "unknown case $ID (no steps at $STEP)" >&2
  exit 2
fi

REQUIRES="$(_reg requires)"
CLASS="$(_reg class)"
export FT_CASE_CLASS="${CLASS:-P/F}"
FT_CASE_LLM="$(_reg llm)"
if [[ "${FT_CASE_LLM:-no}" == "yes" || "${FT_CASE_LLM:-}" == "1" || "${FT_CASE_LLM:-}" == "true" ]]; then
  export FT_CASE_LLM=1
else
  export FT_CASE_LLM=0
fi
if [[ "$FT_CASE_LLM" == "1" || "$REQUIRES" == *llm* ]]; then
  export FT_WITH_LLM=1
fi

# Unsupported (N/A) cases are retired and must never run.
if [[ "$(_reg unsupported)" == "True" ]]; then
  echo "case $ID is marked unsupported (N/A); not run." >&2
  exit 0
fi

trap ft_teardown_on_exit EXIT
ft_case_begin "$ID"

if [[ "$REQUIRES" == *docker* ]] && ! ft_require_docker; then
  # No Docker: a P/F|D case resolves to `declared` (the plan permits it); a hard
  # P/F case fails (never a silent skip).
  if [[ "$FT_CASE_CLASS" == "P/F|D" ]]; then
    ft_declare "Docker unavailable on this host" "PRD 19 harness / Docker leg"
    ft_finalize
    ft_case_end "$ID" "$FT_CASE_STATUS"
    exit 0
  fi
  printf '{"name":"docker-available","ok":false}\n' >> "$FT_CASE_DIR/assertions.ndjson"
  ft_case_end "$ID" "fail"
  exit 1
fi

# Run the step without errexit so a single failed assertion does not abort before
# the verdict is written; ft_finalize decides pass/fail.
set +e
# shellcheck source=/dev/null
source "$STEP"
step_rc=$?
set -e
if [[ "$step_rc" -ne 0 ]]; then FT_ASSERT_FAILED=1; fi
ft_finalize
ft_case_end "$ID" "$FT_CASE_STATUS"

[[ "$FT_CASE_STATUS" == "pass" || "$FT_CASE_STATUS" == "declared" ]] || exit 1
