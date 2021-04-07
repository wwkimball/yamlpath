import pytest

from tests.conftest import create_temp_yaml_file


class Test_commands_yaml_validate():
    """Tests for the yaml-validate command-line tool."""
    command = "yaml-validate"

    def test_no_arguments(self, script_runner):
        result = script_runner.run(self.command, "--nostdin")
        assert not result.success, result.stderr
        assert "There must be at least one YAML_FILE" in result.stderr

    def test_too_many_pseudofiles(self, script_runner):
        result = script_runner.run(
            self.command
            , '-'
            , '-')
        assert not result.success, result.stderr
        assert "Only one YAML_FILE may be the - pseudo-file" in result.stderr

    def test_valid_singledoc(self, script_runner, tmp_path_factory):
        yaml_file = create_temp_yaml_file(tmp_path_factory, """---
this:
  single-document:
    is: valid
""")
        result = script_runner.run(
            self.command
            , "--nostdin"
            , yaml_file)
        assert result.success, result.stderr

    def test_invalid_singledoc(self, script_runner, tmp_path_factory):
        yaml_file = create_temp_yaml_file(tmp_path_factory, "{[}")
        result = script_runner.run(
            self.command
            , "--nostdin"
            , yaml_file)
        assert not result.success, result.stderr
        assert "  * YAML parsing error in" in result.stdout

    def test_valid_stdin_explicit(self, script_runner, tmp_path_factory):
        import subprocess
        stdin_content = "{this: {is: valid}}"
        result = subprocess.run(
            [self.command
            , "-"]
            , stdout=subprocess.PIPE
            , input=stdin_content
            , universal_newlines=True
        )
        assert 0 == result.returncode, result.stderr

    def test_valid_stdin_implicit(self, script_runner, tmp_path_factory):
        import subprocess
        stdin_content = "{this: {is: valid}}"
        result = subprocess.run(
            [self.command]
            , stdout=subprocess.PIPE
            , input=stdin_content
            , universal_newlines=True
        )
        assert 0 == result.returncode, result.stderr

    def test_invalid_stdin_explicit(self, script_runner, tmp_path_factory):
        import subprocess
        stdin_content = "{this: {is not: valid}]"
        result = subprocess.run(
            [self.command
            , "-"]
            , stdout=subprocess.PIPE
            , input=stdin_content
            , universal_newlines=True
        )
        assert 2 == result.returncode, result.stderr
        assert "  * YAML parsing error in" in result.stdout

    def test_invalid_stdin_implicit(self, script_runner, tmp_path_factory):
        import subprocess
        stdin_content = "{this: {is not: valid}]"
        result = subprocess.run(
            [self.command]
            , stdout=subprocess.PIPE
            , input=stdin_content
            , universal_newlines=True
        )
        assert 2 == result.returncode, result.stderr
        assert "  * YAML parsing error in" in result.stdout
