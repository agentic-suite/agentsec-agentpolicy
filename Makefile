.PHONY: setup test cov lint typecheck fmt \
        docker-build docker-up docker-down docker-test docker-smoke docker-sse \
        self-attack fieldtest fieldtest-verify fieldtest-suite fieldtest-case \
        fieldtest-check fieldtest-scan fieldtest-report

# --- developer setup & quality gates (WBS M1) -------------------------------

setup:  ## install the package (editable) + dev tooling into the active venv
	uv pip install -e .
	uv pip install pytest pytest-cov hypothesis ruff mypy types-PyYAML

test:  ## run the ported suite (default config; `field` excluded)
	pytest --tb=short

cov:  ## run the suite with coverage (gate: fail_under = 95)
	pytest --cov=agentpolicy --cov-report=term-missing

lint:  ## ruff, zero violations
	ruff check .

typecheck:  ## mypy strict
	mypy --strict src/

fmt:  ## auto-fix lint where possible, then re-check
	ruff check --fix .
	ruff check .

# --- docker ----------------------------------------------------------------

docker-build:
	docker build -t agentpolicy:latest .

docker-up:
	docker compose up --detach --wait

docker-down:
	docker compose down

docker-smoke:
	uv run pytest tests/test_docker_smoke.py -v

docker-sse:
	uv run pytest tests/test_sse_integration.py -v

docker-test: docker-smoke docker-sse

# --- release cadence (M22) --------------------------------------------------

self-attack:  ## self-attack pack gate — a miss blocks the release
	agentpolicy self-attack check --pack packs/self-attack

# --- field test (M24) -------------------------------------------------------

fieldtest-verify:  ## verify the verifier: the grounding gate catches shallow passes
	python3 scripts/fieldtest/verify_harness.py

fieldtest:  ## run the whole field-test case set (host suites + declared docker/llm legs)
	bash scripts/fieldtest/run-all.sh

fieldtest-suite:  ## run one suite: make fieldtest-suite SUITE=s1-outcomes
	bash scripts/fieldtest/run-suite.sh $(SUITE)

fieldtest-case:  ## run one case: make fieldtest-case CASE=FT-DEC-ASK
	bash scripts/fieldtest/run-case.sh $(CASE)

fieldtest-check:  ## deep-verification gate: every PASS must be grounded
	python3 scripts/fieldtest/check_grounding.py --strict

fieldtest-scan:  ## leak gate over the (committed) results
	python3 scripts/fieldtest/scan_results.py

fieldtest-report:  ## write a GENERATED draft (FIELD_TEST_REPORT.generated.md) — never the canonical report
	python3 scripts/fieldtest/build_report.py
	@echo "NOTE: FIELD_TEST_REPORT.md is HAND-MAINTAINED — update it by hand, not from the draft."

release-dry-run:  ## build wheel+sdist + CycloneDX SBOM + SHA256SUMS + SLSA provenance, then verify
	python3 scripts/release/release_tooling.py --dist dist --build
