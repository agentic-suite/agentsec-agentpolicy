ft_pytest "drill-tests" tests/test_m11_ci.py
ft_cmd "drill-gate" drill check
ft_finalize
