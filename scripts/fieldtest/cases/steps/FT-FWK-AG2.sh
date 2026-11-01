if [[ -d "$REPO_ROOT/tests/field/agents/vendor" ]] && _ft_llm_reachable; then
  ft_llm_up
  ft_assert "matrix-autogen" "$FT_PY" "$REPO_ROOT/scripts/run_field_agents.py" autogen --plan B
else
  ft_declare "no vendored framework repo / oMLX endpoint on the box; covered by the CI deterministic matrix + agent-build smoke" "PRD 19 Tier-2"
fi
ft_finalize
