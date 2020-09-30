import pytest

from tests.conftest import create_temp_yaml_file


class Test_commands_yaml_merge():
    """Tests for the yaml-merge command-line tool."""
    command = "yaml-merge"

    def test_no_options(self, script_runner):
        result = script_runner.run(self.command)
        assert not result.success, result.stderr
        assert "the following arguments are required: YAML_FILE" in result.stderr

    def test_missing_input_file_arg(self, script_runner):
        result = script_runner.run(self.command, "no-file.yaml")
        assert not result.success, result.stderr
        assert "There must be at least two YAML_FILEs" in result.stderr

    def test_missing_config_file(self, script_runner):
        result = script_runner.run(
            self.command
            , "--config=no-file.ini"
            , "lhs-file.yaml"
            , "rhs-file.yaml")
        assert not result.success, result.stderr
        assert "INI style configuration file is not readable" in result.stderr

    def test_output_file_exists(self, script_runner, tmp_path_factory):
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
key: value
""")
        output_file = create_temp_yaml_file(tmp_path_factory, merged_yaml)

        result = script_runner.run(
            self.command
            , "--output={}".format(output_file)
            , "lhs-file.yaml"
            , "rhs-file.yaml")
        assert not result.success, result.stderr
        assert "Output file already exists" in result.stderr

    def test_missing_prime_input_file(self, script_runner):
        result = script_runner.run(
            self.command
            , "no-file.yaml"
            , "-")
        assert not result.success, result.stderr
        assert "The first input file" in result.stderr

    def test_missing_rhs_input_file(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")

        result = script_runner.run(
            self.command
            , lhs_file
            , "no-such-file.yaml")
        assert not result.success, result.stderr
        assert "Not a file" in result.stderr

    def test_empty_rhs_input_file(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, "")

        result = script_runner.run(
            self.command
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr

    def test_merge_two_happy_files_to_stdout(
        self, script_runner, tmp_path, tmp_path_factory
    ):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
""")
        merged_yaml_content = """---
hash:
  lhs_exclusive: LHS exclusive
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , lhs_file
            , rhs_file)
        assert result.success, result.stderr
        assert merged_yaml_content == result.stdout

    def test_merge_two_happy_files_to_file(self, script_runner, tmp_path, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
""")
        merged_yaml_content = """---
hash:
  lhs_exclusive: LHS exclusive
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
"""

        output_dir = tmp_path / "test_merge_two_files"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Output File:  {}".format(output_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--output={}".format(output_file)
            , lhs_file
            , rhs_file)
        assert result.success, result.stderr

        with open(output_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert merged_yaml_content == filedat

    def test_bad_rhs_input_file(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
- one
- two
""")

        result = script_runner.run(
            self.command
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr

    def test_merge_from_stdin_to_stdout(
        self, script_runner, tmp_path_factory
    ):
        import subprocess

        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")
        rhs_content = ("{hash: {rhs_exclusive: RHS exclusive"
                       ", merge_target: RHS override value}}")
        merged_yaml_content = """---
hash:
  lhs_exclusive: LHS exclusive
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
"""

        result = subprocess.run(
            [self.command
            , lhs_file
            , "-"]
            , stdout=subprocess.PIPE
            , input=rhs_content
            , universal_newlines=True
        )

        # DEBUG
        # print("Expected:")
        # print(merged_yaml_content)
        # print("Got:")
        # print(result.stdout)

        assert 0 == result.returncode, result.stderr
        assert merged_yaml_content == result.stdout

    def test_bad_mergeat_yamlpath(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
new_key: New value
""")

        result = script_runner.run(
            self.command
            , "--mergeat=/[.~='']"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert "Unexpected use of ~ operator" in result.stderr
