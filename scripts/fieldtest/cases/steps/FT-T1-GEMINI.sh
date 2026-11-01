if command -v gemini >/dev/null 2>&1 && _ft_gemini_local_ok; then
  ft_llm_up
else
  ft_declare "Gemini CLI present but its model backend is Google-hosted only (no local-Gemini endpoint on the box); MCP/agentgate surface covered at the lower layer" "PRD 19 Tier-1"
fi
ft_cmd "t1-gemini-evaluate-parity" bash -c 'DEC=$("$FT_PY" "$REPO_ROOT/scripts/fieldtest/t1_evaluate.py" --tool execute_shell --action delete --env production --data restricted --agent gemini-t1 --policy "$REPO_ROOT/scripts/fieldtest/t1_policy.yaml") 2>/dev/null || true; test "$(printf "%s" "$DEC" | "$FT_PY" -c "import json,sys;print(json.load(sys.stdin)[\"decision\"])" 2>/dev/null)" = deny && echo PARITY-OK'
ft_finalize
