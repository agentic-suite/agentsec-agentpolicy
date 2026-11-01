# Field-test fixtures (read-only at runtime).

Version-tagged, secret-scanned inputs used by the Docker-required and CLI cases.
The harness binds this directory at `/ft/fixtures` inside the field-test
container (see `docker-compose.fieldtest.yml`).

Host-native cases read fixtures from the repo (`tests/field/`, `packs/`,
`tests/fixtures/`) directly; this directory exists for container parity and any
fixtures that must ship with the harness rather than the suite.
