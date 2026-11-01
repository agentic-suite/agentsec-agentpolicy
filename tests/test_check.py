"""Tests for the ``agentpolicy check`` CLI.

``agentpolicy check`` reads a policy file and validates it against the schema.
A clean file exits 0 and prints the version/posture; a broken one **fails
closed** with exit code 2 and the first error with its line/column location
(WBS M1 1.3 — invalid config fails closed, exit 2).
"""

from pathlib import Path

from agentpolicy.cli import main


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "agentpolicy.yaml"
    path.write_text(text)
    return path


class TestCheckCli:
    def test_clean_policy_exits_zero(self, tmp_path):
        out = write(tmp_path, 'version: "1.0.0"')
        assert main(["check", str(out)]) == 0

    def test_missing_file_fails_closed_exit_two(self):
        assert main(["check", "/nope/x.yaml"]) == 2

    def test_bad_yaml_fails_closed_exit_two(self, tmp_path, capsys):
        out = write(tmp_path, "version: [1, 2\n")
        rc = main(["check", str(out)])
        captured = capsys.readouterr()
        assert rc == 2
        assert "invalid policy:" in captured.err

    def test_schema_violation_fails_closed_exit_two(self, tmp_path, capsys):
        out = write(tmp_path, 'version: "1.0.0"\nposture: paranoid\n')
        rc = main(["check", str(out)])
        captured = capsys.readouterr()
        assert rc == 2
        assert "invalid policy:" in captured.err

    def test_default_path_checks_cwd(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        rc = main(["check"])
        captured = capsys.readouterr()
        assert rc == 2
        assert "invalid policy:" in captured.err or "no such" in captured.err
