# agentpolicy field-test image — the system under test (CLI + SDK + dev deps).
#
# Builds from the repo root so it can install the package:
#   docker compose -f scripts/fieldtest/docker-compose.fieldtest.yml build agentpolicy
FROM python:3.13-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# git/curl/procps/ca-certificates for the field agent matrix + readiness helpers.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl procps ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /work

# Install agentpolicy (CLI + SDK) with dev tooling (pytest) and the framework
# adapters the matrix drives.
COPY pyproject.toml README.md /work/
COPY src /work/src
RUN uv pip install --system --no-cache-dir ".[dev]"

# Field-test definitions + harness helpers. `tests/field/` and `scripts/fieldtest/`
# are bind-mounted at runtime (see docker-compose.fieldtest.yml), so the image
# only carries the shipped packs.
COPY packs /work/packs

RUN mkdir -p /data/agentpolicy/.agentpolicy

CMD ["sleep", "infinity"]
