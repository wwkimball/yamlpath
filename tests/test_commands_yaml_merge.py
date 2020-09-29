import pytest

from tests.conftest import create_temp_yaml_file


class Test_commands_yaml_merge():
    """Tests for the yaml-merge command-line tool."""
    command = "yaml-merge"

    def test_no_options(self, script_runner):
        result = script_runner.run(self.command)
        assert not result.success, result.stderr
        assert "the following arguments are required: YAML_FILE" in result.stderr
