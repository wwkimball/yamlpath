import pytest

from tests.conftest import create_temp_yaml_file


class Test_yaml_set():
    """Tests for the yaml-set command-line interface."""
    command = "yaml-set"

    def test_no_options(self, script_runner):
        result = script_runner.run(self.command)
        assert not result.success, result.stderr
        assert "the following arguments are required: -g/--change, YAML_FILE" in result.stderr

    def test_no_input_file(self, script_runner):
        result = script_runner.run(self.command, "--change='/test'")
        assert not result.success, result.stderr
        assert "the following arguments are required: YAML_FILE" in result.stderr

    def test_no_input_param(self, script_runner):
        result = script_runner.run(self.command, "--change='/test'", "no-such-file")
        assert not result.success, result.stderr
        assert "Exactly one of the following must be set:" in result.stderr

    def test_bad_yaml_file(self, script_runner):
        result = script_runner.run(self.command, "--change='/test'", "--random=1", "no-such-file")
        assert not result.success, result.stderr
        assert "YAML_FILE not found:" in result.stderr

    def test_identical_saveto_change_error(self, script_runner):
        result = script_runner.run(self.command, "--change='/test'", "--random=1", "--saveto='/test'", "no-such-file")
        assert not result.success, result.stderr
        assert "Impossible to save the old value to the same YAML Path as the new value!" in result.stderr

    def test_bad_privatekey(self, script_runner):
        result = script_runner.run(self.command, "--change='/test'", "--random=1", "--privatekey=no-such-file", "no-such-file")
        assert not result.success, result.stderr
        assert "EYAML private key is not a readable file" in result.stderr

    def test_bad_publickey(self, script_runner):
        result = script_runner.run(self.command, "--change='/test'", "--random=1", "--publickey=no-such-file", "no-such-file")
        assert not result.success, result.stderr
        assert "EYAML public key is not a readable file" in result.stderr

    def test_input_by_value(self, script_runner, tmp_path_factory):
        import re

        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, "--change=/key", "--value=abc", yaml_file)
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert re.findall(r"^key:\s+abc$", filedat, re.M), filedat

    def test_input_by_stdin(self, tmp_path_factory):
        import re
        import subprocess

        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = subprocess.run(
            [self.command,
            "--change=/key",
            "--stdin",
            yaml_file],
            stdout=subprocess.PIPE,
            input="abc".encode(),
        )
        assert 0 == result.returncode, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert re.findall(r"^key:\s+abc$", filedat, re.M), filedat

    def test_input_by_file(self, script_runner, tmp_path_factory):
        import re

        content = """---
        key: value
        """
        input_file = create_temp_yaml_file(tmp_path_factory, "abc\n")
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--change=/key",
            "--file={}".format(input_file),
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert re.findall(r"^key:\s+abc$", filedat, re.M), filedat

    def test_input_by_random(self, script_runner, tmp_path_factory):
        import re

        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--change=/key",
            "--random=50",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert re.findall(r"^key:\s+[A-Za-z0-9]{50}$", filedat, re.M), filedat

    def test_yaml_parsing_error(self, script_runner, imparsible_yaml_file):
        result = script_runner.run(self.command, "--change=/", "--random=1", imparsible_yaml_file)
        assert not result.success, result.stderr
        assert "YAML parsing error" in result.stderr

    def test_yaml_syntax_error(self, script_runner, badsyntax_yaml_file):
        result = script_runner.run(self.command, "--change=/", "--random=1", badsyntax_yaml_file)
        assert not result.success, result.stderr
        assert "YAML syntax error" in result.stderr

    def test_yaml_composition_error(self, script_runner, badcmp_yaml_file):
        result = script_runner.run(self.command, "--change=/", "--random=1", badcmp_yaml_file)
        assert not result.success, result.stderr
        assert "YAML composition error" in result.stderr

    def test_bad_yaml_path(self, script_runner, tmp_path_factory):
        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)

        # Explicit --mustexist
        result = script_runner.run(self.command, "--change=key2", "--random=1", "--mustexist", yaml_file)
        assert not result.success, result.stderr
        assert "Required YAML Path does not match any nodes" in result.stderr

        # Implicit --mustexist via --saveto
        result = script_runner.run(self.command, "--change=key3", "--random=1", "--saveto=save_here", yaml_file)
        assert not result.success, result.stderr
        assert "Required YAML Path does not match any nodes" in result.stderr

    def test_checked_replace(self, script_runner, tmp_path_factory):
        import re

        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--change=/key",
            "--value=abc",
            "--check=value",
            yaml_file
        )
        assert result.success, result.stderr
