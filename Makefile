.PHONY: setup test cov lint typecheck fmt \
        docker-build docker-up docker-down docker-test docker-smoke docker-sse

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
