ft_pytest "self-attack-tests" tests/test_m22_selfattack.py
ft_cmd "self-attack-gate" self-attack check --pack packs/self-attack
ft_finalize
