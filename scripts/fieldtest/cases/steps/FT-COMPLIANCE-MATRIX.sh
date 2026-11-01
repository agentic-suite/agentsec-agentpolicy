ft_pytest "compliance" tests/test_m23_parity_claims.py
ft_cmd "claims-gate" compliance claims
ft_finalize
