if [[ -d "$REPO_ROOT/tests/field/agents/vendor" ]] && _ft_llm_reachable; then
  ft_llm_up
  export AGENTPOLICY_FIELD_LLM_DIR="$FT_LLM_DIR"
  ft_assert "matrix-adk" "$FT_PY" "$REPO_ROOT/scripts/run_field_agents.py" adk --plan B --llm-out "$FT_LLM_DIR"
  ft_assert_llm_capture "adk-captured"
else
  ft_declare "no vendored framework repo / oMLX endpoint on the box; covered by the CI deterministic matrix + agent-build smoke" "PRD 19 Tier-2"
fi
ft_finalize
