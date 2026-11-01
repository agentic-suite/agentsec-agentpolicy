#!/usr/bin/env bash
# Field-test helpers for agentpolicy — a thin layer over scripts/stack_lib.sh.
#
# Reuses the repo's stack lifecycle primitive (stack_up / stack_verify /
# stack_teardown_on_exit) and adds per-case result capture. Results are written
# to field-test/<FT_VERSION>/results/<run-id>/ (see
# docs/field-test/v0.1.0/FIELD_TEST_PLAN.md).
#
# Source from a runner:
#   source "$(dirname "$0")/lib.sh"
#   trap ft_teardown_on_exit EXIT
#   ft_case_begin "$ID"
#   ... steps + ft_assert / ft_pytest / ft_cmd ...
#   ft_finalize
#   ft_case_end "$ID" "$FT_CASE_STATUS"
#
# No skips: every case runs and is pass/fail (or `declared` for a P/F|D case
# whose environment is genuinely unavailable — never a silent pass).
set -euo pipefail

FT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"      # scripts/fieldtest
REPO_ROOT="$(cd "$FT_DIR/../.." && pwd)"                    # repo root
export REPO_ROOT
# Load the field-test env file if present (LLM endpoint/model, STACK_*, FT_TAG).
if [[ -f "$FT_DIR/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$FT_DIR/.env"
  set +a
fi
# Results are version-scoped: field-test/<FT_VERSION>/results/<run-id>/.
FT_VERSION="${FT_VERSION:-v0.1.0}"
# FREEZE GUARD: a version listed in FT_FROZEN_VERSIONS must never be written by a
# later run (protects a published report's results forever). Empty by default.
for _frozen in ${FT_FROZEN_VERSIONS:-}; do
  if [[ "${FT_VERSION}" == "${_frozen}" && "${FT_ALLOW_FROZEN_WRITE:-0}" != "1" ]]; then
    echo "FATAL: refusing to write to field-test/${_frozen} (frozen). Set FT_VERSION to a later version." >&2
    echo "       (override only with FT_ALLOW_FROZEN_WRITE=1, and only to regenerate that report)" >&2
    exit 3
  fi
done
RESULTS_ROOT="${FT_RESULTS_ROOT:-$REPO_ROOT/field-test/$FT_VERSION/results}"
# FT_RUN_ID MUST be set by the runner (run-suite.sh sets it to the suite;
# run-case.sh derives it from the registry). No default — a stray "all" results
# dir silently duplicates evidence and must never be created.
if [[ -z "${FT_RUN_ID:-}" ]]; then
  echo "FATAL: FT_RUN_ID is not set — refusing to write to a default results dir." >&2
  echo "       Run via run-suite.sh (suite dir) or run-case.sh (derives the suite)." >&2
  exit 3
fi
FT_RUN_DIR="$RESULTS_ROOT/$FT_RUN_ID"

# shellcheck source=../stack_lib.sh
source "$REPO_ROOT/scripts/stack_lib.sh"

# Prefer the repo venv's python so host-native pytest cases work out of the box.
if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
  FT_PY="${AGENTPOLICY_PYTHON:-$REPO_ROOT/.venv/bin/python}"
else
  FT_PY="${AGENTPOLICY_PYTHON:-python3}"
fi
export FT_PY

# The field-test compose overlay. agentpolicy has a base compose (the server), but
# the field-test overlay is standalone: the agentpolicy CLI/SDK (SUT). No LLM
# container — the LLM is the host oMLX server (see FT_LLM_HOST_URL / FT_LLM_BASE_URL).
# --project-directory pins relative build contexts / mounts to the repo root.
STACK_COMPOSE=(docker compose --project-directory "$REPO_ROOT" -f "$FT_DIR/docker-compose.fieldtest.yml")
FT_SUT_SERVICE="agentpolicy"
FT_SERVICES=(agentpolicy)
STACK_SERVICES=(agentpolicy)
# The LLM is the local oMLX server on the host (OpenAI-compatible), reached from
# the container via host.docker.internal. Variables are namespaced FT_LLM_* so the
# ambient environment (e.g. a coding agent's OPENAI_*/LLM_* vars) can never leak
# into a field-test LLM call.
FT_LLM_HOST_URL="${FT_LLM_HOST_URL:-http://127.0.0.1:8000}"
FT_LLM_BASE_URL="${FT_LLM_BASE_URL:-http://host.docker.internal:8000/v1}"
FT_LLM_MODEL="${FT_LLM_MODEL:-Qwen3-4B-Instruct-2507-4bit}"
export FT_LLM_HOST_URL FT_LLM_BASE_URL FT_LLM_MODEL

FT_CASE_DIR=""
FT_CASE_STATUS="fail"
FT_ASSERT_FAILED=0
FT_ASSERT_TOTAL=0
FT_ASSERT_GROUNDED=0
FT_LLM_CAPTURED=0
# Declare class: FT_CASE_CLASS is "P/F" or "P/F|D" (from the registry).
FT_CASE_CLASS="${FT_CASE_CLASS:-P/F}"
FT_CASE_DECLARED=0
FT_DECLARE_LIMITATION=""
FT_DECLARE_GATE=""

# --- run directory -----------------------------------------------------------
ft_run_init() {
  mkdir -p "$FT_RUN_DIR"
  if [[ ! -f "$FT_RUN_DIR/env.json" ]]; then
    {
      printf '{"run_id":"%s","version":"%s","docker":"%s","compose":"%s","os":"%s","arch":"%s","python":"%s","llm_base_url":"%s","llm_model":"%s"}\n' \
        "$FT_RUN_ID" \
        "$FT_VERSION" \
        "$(docker --version 2>/dev/null || echo unknown)" \
        "$(docker compose version --short 2>/dev/null || echo unknown)" \
        "$(uname -s 2>/dev/null || echo unknown)" \
        "$(uname -m 2>/dev/null || echo unknown)" \
        "$("$FT_PY" --version 2>/dev/null | tr ' ' '-' || echo unknown)" \
        "${FT_LLM_BASE_URL}" \
        "${FT_LLM_MODEL}"
    } > "$FT_RUN_DIR/env.json"
  fi
}

# --- setup log (preserved) ---------------------------------------------------
FT_SETUP_DIR="${FT_SETUP_DIR:-$RESULTS_ROOT/_setup}"
FT_SETUP_LOG="${FT_SETUP_LOG:-$FT_SETUP_DIR/${FT_RUN_ID}-stack-up.log}"

_ft_log() {
  mkdir -p "$(dirname "$FT_SETUP_LOG")"
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$FT_SETUP_LOG"
}

# --- case lifecycle ----------------------------------------------------------
ft_case_begin() {
  local id="$1"
  ft_run_init
  FT_CASE_DIR="$FT_RUN_DIR/cases/$id"
  export FT_CASE_DIR
  FT_LLM_DIR="$FT_CASE_DIR/artifacts/llm"
  mkdir -p "$FT_CASE_DIR/artifacts" "$FT_LLM_DIR"
  : > "$FT_CASE_DIR/commands.log"
  : > "$FT_CASE_DIR/stdout.log"
  : > "$FT_CASE_DIR/stderr.log"
  : > "$FT_CASE_DIR/assertions.ndjson"
  FT_CASE_STATUS="fail"
  FT_ASSERT_FAILED=0
  FT_ASSERT_TOTAL=0
  FT_ASSERT_GROUNDED=0
  FT_LLM_CAPTURED=0
  FT_STACK_BOOTED=0
  FT_CASE_DECLARED=0
  FT_DECLARE_LIMITATION=""
  FT_DECLARE_GATE=""
  echo "== case $id =="
}

# Resolve to `declared` for a P/F|D case whose environment is genuinely
# unavailable. Requires a named limitation + the plan/gate item that permits "or
# declared". A `declared` outcome for a hard gate is invalid and fails the case.
ft_declare() {
  local limitation="$1" gate="${2:-}"
  if [[ "$FT_CASE_CLASS" != "P/F|D" ]]; then
    echo "  DECLARE-INVALID $limitation (case class is $FT_CASE_CLASS, not P/F|D)" >&2
    FT_ASSERT_FAILED=1
    return 1
  fi
  FT_CASE_DECLARED=1
  FT_DECLARE_LIMITATION="$limitation"
  FT_DECLARE_GATE="$gate"
  printf '{"name":"declared","ok":true,"limitation":"%s","release_gate_item":"%s"}\n' \
    "$limitation" "$gate" >> "$FT_CASE_DIR/assertions.ndjson"
  echo "  DECLARED $limitation"
}

ft_record() {
  [[ -n "${FT_CASE_DIR:-}" ]] || return 0
  printf '+ %s\n' "$*" >> "$FT_CASE_DIR/commands.log"
}

_ft_json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  printf '%s' "$s"
}

# Weak-assertion catalogue — the same shapes gen_cases.py / check_grounding.py
# reject. An assertion that proves only *plumbing* is NOT a grounded check and
# cannot, on its own, justify a PASS. Deep verification: every PASS must rest on
# >=1 grounded assertion (see ft_finalize / check_grounding.py).
_ft_weak_reasons() {
  local cmd="$1" reasons=""
  [[ -z "${cmd// }" ]] && reasons="$reasons empty-command"
  grep -qE "^(:|true)$" <<<"$cmd" && reasons="$reasons bare-true"
  grep -qE "python3? +-c +['\"]import " <<<"$cmd" && reasons="$reasons import-only"
  grep -qE "python3? +-m +[A-Za-z_.]+ *$" <<<"$cmd" && reasons="$reasons module-import-only"
  grep -qF "|| true" <<<"$cmd" && reasons="$reasons cannot-fail"
  grep -qF "json.tool" <<<"$cmd" && reasons="$reasons json.tool"
  if grep -qE "\btest +-[fsn]\b" <<<"$cmd" && [[ "$cmd" != *grep* && "$cmd" != *"&&"* ]]; then
    reasons="$reasons existence-only"
  fi
  if grep -qE "python3 +/ft/scripts/[^ ]+\.py" <<<"$cmd" && [[ "$cmd" != *grep* && "$cmd" != *"&&"* ]]; then
    reasons="$reasons driver-only"
  fi
  # A `pytest` selection is grounded only through the run_pytest.py driver (which
  # fails on skip / no-tests). A bare `pytest` exit-0 is plumbing.
  if grep -qE "(^| )pytest " <<<"$cmd" && [[ "$cmd" != *run_pytest.py* ]]; then
    reasons="$reasons bare-pytest"
  fi
  printf '%s' "$reasons"
}

# ft_assert runs a command whose exit code IS the check. It records the *command*
# and a grounding verdict so a weak assertion can never be mistaken for a
# grounded one.
ft_assert() {
  local name="$1"; shift
  local cmd="$*"
  local weak; weak="$(_ft_weak_reasons "$cmd")"
  local grounded="true"; [[ -n "$weak" ]] && grounded="false"
  if "$@" >> "$FT_CASE_DIR/stdout.log" 2>> "$FT_CASE_DIR/stderr.log"; then
    if [[ "$grounded" == "true" ]]; then FT_ASSERT_GROUNDED=$((FT_ASSERT_GROUNDED + 1)); fi
    printf '{"name":"%s","ok":true,"grounded":%s,"cmd":"%s"}\n' \
      "$name" "$grounded" "$(_ft_json_escape "$cmd")" >> "$FT_CASE_DIR/assertions.ndjson"
    echo "  PASS $name${weak:+ (WEAK:${weak# })}"
    return 0
  fi
  FT_ASSERT_FAILED=1
  printf '{"name":"%s","ok":false,"grounded":%s,"cmd":"%s"}\n' \
    "$name" "$grounded" "$(_ft_json_escape "$cmd")" >> "$FT_CASE_DIR/assertions.ndjson"
  echo "  FAIL $name" >&2
  return 1
}

# ft_fail / ft_pass record an assertion without running a command.
ft_fail() {
  local name="$1"
  FT_ASSERT_FAILED=1
  printf '{"name":"%s","ok":false}\n' "$name" >> "$FT_CASE_DIR/assertions.ndjson"
  echo "  FAIL $name" >&2
}

ft_pass() {
  local name="$1"
  printf '{"name":"%s","ok":true}\n' "$name" >> "$FT_CASE_DIR/assertions.ndjson"
  echo "  PASS $name"
}

# Host-native grounded pytest: skip = failure, no-tests = failure.
ft_pytest() {
  local name="$1"; shift
  ft_assert "$name" "$FT_PY" "$FT_DIR/run_pytest.py" "$@"
}

# Host-native agentpolicy CLI, captured as a grounded assertion. Resolves the
# console script (venv, then PATH) and falls back to `python -m agentpolicy.cli`.
FT_CLI="${AGENTPOLICY_CLI:-$REPO_ROOT/.venv/bin/agentpolicy}"
ft_cmd() {
  local name="$1"; shift
  if [[ -x "$FT_CLI" ]]; then
    ft_assert "$name" "$FT_CLI" "$@"
  else
    ft_assert "$name" "$FT_PY" -m agentpolicy.cli "$@"
  fi
}

ft_capture() {
  local src="$1" dest="$2"
  mkdir -p "$FT_CASE_DIR/artifacts/$dest"
  cp -R "$src"/. "$FT_CASE_DIR/artifacts/$dest/" 2>/dev/null || true
}

ft_case_end() {
  local id="$1" status="${2:-$FT_CASE_STATUS}"
  FT_CASE_STATUS="$status"
  # Leak gate: results are committed to git, so a case must never persist an
  # artifact carrying an unmasked secret. A leak fails the case.
  if grep -rqiIE 'sk-[A-Za-z0-9]{16,}|Bearer +[A-Za-z0-9._-]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}' \
        "$FT_CASE_DIR/artifacts" 2>/dev/null; then
    FT_ASSERT_FAILED=1
    printf '{"name":"no-secret-leak","ok":false,"grounded":true,"cmd":"scan artifacts for secrets"}\n' \
      >> "$FT_CASE_DIR/assertions.ndjson"
    echo "  FAIL no-secret-leak (unmasked secret in case artifacts)" >&2
    FT_CASE_STATUS="fail"
  else
    printf '{"name":"no-secret-leak","ok":true,"grounded":true,"cmd":"scan artifacts for secrets"}\n' \
      >> "$FT_CASE_DIR/assertions.ndjson"
    echo "  PASS no-secret-leak"
  fi
  {
    printf '{\n'
    printf '  "id": "%s",\n' "$id"
    printf '  "status": "%s",\n' "$status"
    printf '  "class": "%s",\n' "$FT_CASE_CLASS"
    printf '  "declared": %s,\n' "$([[ "$FT_CASE_DECLARED" -eq 1 ]] && echo true || echo false)"
    printf '  "grounded": %s,\n' "$([[ "${FT_ASSERT_GROUNDED:-0}" -ge 1 ]] && echo true || echo false)"
    printf '  "assertions_total": %s,\n' "${FT_ASSERT_TOTAL:-0}"
    printf '  "assertions_grounded": %s,\n' "${FT_ASSERT_GROUNDED:-0}"
    printf '  "llm_captured": %s,\n' "$([[ "${FT_LLM_CAPTURED:-0}" -eq 1 ]] && echo true || echo false)"
    if [[ "$FT_CASE_DECLARED" -eq 1 ]]; then
      printf '  "limitation": "%s",\n' "$FT_DECLARE_LIMITATION"
      printf '  "release_gate_item": "%s",\n' "$FT_DECLARE_GATE"
    fi
    printf '  "run_id": "%s",\n' "$FT_RUN_ID"
    printf '  "assertions": ['
    if [[ -s "$FT_CASE_DIR/assertions.ndjson" ]]; then
      paste -sd, "$FT_CASE_DIR/assertions.ndjson"
    fi
    printf ']\n}\n'
  } > "$FT_CASE_DIR/verdict.json"
  echo "== case $id: $status =="
}

ft_finalize() {
  # No skip: pass only if every assertion held. DEEP VERIFICATION: a PASS must
  # additionally rest on >=1 *grounded* assertion, and an LLM-requiring case must
  # have captured its request/response pairs. A declared P/F|D case is a distinct
  # terminal state, not a pass.
  local total=0
  if [[ -s "$FT_CASE_DIR/assertions.ndjson" ]]; then
    total=$(wc -l < "$FT_CASE_DIR/assertions.ndjson" | tr -d ' ')
  fi
  FT_ASSERT_TOTAL="$total"
  if [[ "$FT_ASSERT_FAILED" -ne 0 ]]; then
    FT_CASE_STATUS="fail"
  elif [[ "$FT_CASE_DECLARED" -eq 1 ]]; then
    FT_CASE_STATUS="declared"
  elif [[ "$total" -eq 0 ]]; then
    FT_CASE_STATUS="fail"
    echo "  FAIL no-assertions (a pass must be backed by >=1 assertion)" >&2
  elif [[ "${FT_STRICT_GROUNDING:-1}" == "1" && "$FT_ASSERT_GROUNDED" -eq 0 ]]; then
    FT_CASE_STATUS="fail"
    echo "  FAIL ungrounded (no grounded assertion; every assertion is plumbing)" >&2
  elif [[ "${FT_CASE_LLM:-0}" == "1" && "$FT_LLM_CAPTURED" != "1" ]]; then
    FT_CASE_STATUS="fail"
    echo "  FAIL no-llm-capture (LLM case with no captured request/response pair)" >&2
  else
    FT_CASE_STATUS="pass"
  fi
}

# Case-exit trap. In a shared-stack run the stack stays up across cases; the
# top-level runner tears it down once, at the end. A standalone case honors
# STACK_KEEP. Host-native cases never boot the stack, so teardown is a no-op.
ft_teardown_on_exit() {
  local code=$?
  if [[ "${FT_SHARED_STACK:-0}" == "1" ]]; then
    exit "$code"
  fi
  # Only a case that actually booted the Docker stack tears it down. Host-native
  # cases never boot it, so teardown is a no-op.
  if [[ "${FT_STACK_BOOTED:-0}" != "1" ]]; then
    exit "$code"
  fi
  if [[ "${STACK_KEEP:-}" == "1" ]]; then
    echo "==> STACK_KEEP=1 set; leaving the stack running"
    exit "$code"
  fi
  stack_teardown
  exit "$code"
}

# --- docker SUT lifecycle (only the docker-required cases) -------------------
FT_SUT_HOME=/data/agentpolicy

ft_require_docker() {
  if ! docker info >/dev/null 2>&1; then
    echo "FAIL: Docker is unavailable; field test cannot run." >&2
    return 3
  fi
}

# Confirm the stack is genuinely ONLINE (running + healthy + SUT answers).
ft_wait_ready() {
  local timeout="${STACK_TIMEOUT:-180}"
  local deadline=$((SECONDS + timeout))
  _ft_log "waiting for stack readiness (timeout ${timeout}s)"
  while :; do
    local all_ok=1 svc cid status health
    for svc in "${FT_SERVICES[@]}"; do
      cid="$("${STACK_COMPOSE[@]}" ps -q "$svc" 2>/dev/null)"
      if [[ -z "$cid" ]]; then _ft_log "  $svc: no container yet"; all_ok=0; continue; fi
      status="$(docker inspect --format '{{.State.Status}}' "$cid" 2>/dev/null)"
      health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$cid" 2>/dev/null)"
      _ft_log "  $svc: status=$status health=$health"
      [[ "$status" == "running" ]] || all_ok=0
      [[ "$health" == "healthy" || "$health" == "none" ]] || all_ok=0
    done
    [[ "$all_ok" -eq 1 ]] && break
    if (( SECONDS >= deadline )); then
      _ft_log "FAIL: stack not running+healthy within ${timeout}s"
      "${STACK_COMPOSE[@]}" ps >>"$FT_SETUP_LOG" 2>&1 || true
      return 1
    fi
    sleep 2
  done
  _ft_log "services running + healthy"
  while :; do
    if "${STACK_COMPOSE[@]}" exec -T "$FT_SUT_SERVICE" agentpolicy --version >>"$FT_SETUP_LOG" 2>&1; then
      _ft_log "SUT answers: agentpolicy --version OK"
      break
    fi
    if (( SECONDS >= deadline )); then
      _ft_log "FAIL: SUT did not answer within ${timeout}s"
      return 1
    fi
    sleep 2
  done
  if [[ "${FT_WITH_LLM:-0}" == "1" ]]; then
    while :; do
      if _ft_llm_reachable; then
        _ft_log "oMLX LLM endpoint responds (host ${FT_LLM_HOST_URL})"
        break
      fi
      if (( SECONDS >= deadline )); then
        _ft_log "FAIL: oMLX endpoint ${FT_LLM_HOST_URL} did not respond within ${timeout}s"
        return 1
      fi
      sleep 2
    done
  fi
  _ft_log "stack READY"
  return 0
}

ft_up_sut() {
  FT_STACK_BOOTED=1
  ft_record "compose up (full stack)"
  if "${STACK_COMPOSE[@]}" up -d --build "${FT_SERVICES[@]}" \
      >> "$FT_CASE_DIR/stdout.log" 2>> "$FT_CASE_DIR/stderr.log"; then
    ft_pass "stack-up"
  else
    ft_fail "stack-up"
  fi
  if ft_wait_ready; then ft_pass "stack-ready"; else ft_fail "stack-ready"; fi
}

ft_exec() {
  local service="$1"; shift
  ft_record "compose exec $service $*"
  local rc=0
  "${STACK_COMPOSE[@]}" exec -T "$service" "$@" \
    >> "$FT_CASE_DIR/stdout.log" 2>> "$FT_CASE_DIR/stderr.log" || rc=$?
  return "$rc"
}

ft_sut() { ft_exec "$FT_SUT_SERVICE" "$@"; }

ft_assert_sut() {
  local name="$1"; shift
  ft_assert "$name" ft_sut bash -lc "$*"
}

# --- LLM backend — the host oMLX server (OpenAI-compatible) ------------------
_ft_llm_reachable() {
  curl -sf --max-time 5 "${FT_LLM_HOST_URL%/}/v1/models" >/dev/null 2>&1 \
    || curl -sf --max-time 5 "${FT_LLM_BASE_URL%/}/v1/models" >/dev/null 2>&1
}

# NOTE (2026-11-01): the Gemini CLI Tier-1 case (FT-T1-GEMINI) was removed — the
# gemma router is classifier-only and the main loop needs sunset Google OAuth;
# Cursor (GUI IDE) was removed likewise. Neither is claimed as supported at v0.1.0
# (plan §7.7, PRD 19).

ft_llm_up() {
  export FT_WITH_LLM=1
  ft_record "require oMLX endpoint ${FT_LLM_HOST_URL}"
  if _ft_llm_reachable; then ft_pass "llm-endpoint-reachable"; else ft_fail "llm-endpoint-reachable"; fi
}

ft_assert_llm_capture() {
  local name="${1:-llm-capture}"
  local req resp real
  req=$(find "$FT_LLM_DIR" -name '*-request.json' 2>/dev/null | wc -l | tr -d ' ')
  resp=$(find "$FT_LLM_DIR" -name '*-response.json' 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$req" -ge 1 && "$resp" -ge 1 ]]; then
    FT_LLM_CAPTURED=1
    FT_ASSERT_GROUNDED=$((FT_ASSERT_GROUNDED + 1))
    printf '{"name":"%s","ok":true,"grounded":true,"cmd":"capture: %s request(s) + %s response(s)"}\n' \
      "$name" "$req" "$resp" >> "$FT_CASE_DIR/assertions.ndjson"
    echo "  PASS $name ($req request(s), $resp response(s))"
    return 0
  fi
  FT_ASSERT_FAILED=1
  printf '{"name":"%s","ok":false,"grounded":true,"cmd":"capture: %s request(s) + %s response(s)"}\n' \
    "$name" "$req" "$resp" >> "$FT_CASE_DIR/assertions.ndjson"
  echo "  FAIL $name (no LLM request/response pair captured)" >&2
  return 1
}
