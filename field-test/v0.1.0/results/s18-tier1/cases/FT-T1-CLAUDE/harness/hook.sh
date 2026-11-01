#!/usr/bin/env bash
set -euo pipefail
FT_H="$(cd "$(dirname "$0")" && pwd)"
FT_PY="/Users/deghosal/Desktop/code/github/agentic-suite/agentpolicy/.venv/bin/python"
INPUT="$(cat)"
CMD="$(printf '%s' "$INPUT" | "$FT_PY" -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))')"
case "$CMD" in
  *"rm -rf"*|*"rm -r"*)    ACTION=delete; ENV=production; DATA=restricted ;;
  *"cat "*|*"grep "*|*"ls "*) ACTION=read;  ENV=staging;    DATA=internal ;;
  *">>"*|*"echo "*|*"tee "*)  ACTION=write; ENV=production; DATA=internal ;;
  *)                      ACTION=read;  ENV=staging;    DATA=internal ;;
esac
DEC_JSON="$("$FT_PY" "/Users/deghosal/Desktop/code/github/agentic-suite/agentpolicy/scripts/fieldtest/t1_evaluate.py" --tool execute_shell --action "$ACTION" --env "$ENV" --data "$DATA" --agent claude-code-t1 --session ft-t1-claude --policy "$FT_H/agentpolicy.yaml" 2>/dev/null || true)"
DEC="$(printf '%s' "$DEC_JSON" | "$FT_PY" -c 'import json,sys; print(json.load(sys.stdin).get("decision","deny"))' 2>/dev/null || echo deny)"
REASON="$(printf '%s' "$DEC_JSON" | "$FT_PY" -c 'import json,sys; d=json.load(sys.stdin); print(d.get("explanation","policy decision"))' 2>/dev/null || echo "policy decision")"
printf '%s\n' "$DEC_JSON" >> "$FT_H/audit.ndjson"
case "$DEC" in
  allow)     PD=allow ;;
  escalate)  PD=ask ;;
  *)         PD=deny ;;
esac
printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"%s","permissionDecisionReason":"agentpolicy: %s"}}\n' "$PD" "$REASON"
