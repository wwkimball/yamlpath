import pytest

from tests.conftest import create_temp_yaml_file


class Test_commands_yaml_diff():
    """Tests for the yaml-diff command-line tool."""
    command = "yaml-diff"

    lhs_content = """---
key: value
array:
  - 1
  - 2
  - 3
aoh:
  - id: 0
    name: zero
  - id: 1
    name: one
  - id: 2
    name: two
lhs_exclusive:
  - node
"""

    rhs_content = """---
key: different value
array:
  - 1
  - 3
  - 4 (new)
  - 5 (new)
aoh:
  - id: 0
    name: zero
    extra_field: is an extra field (new)
  - id: 1
    name: different one
  - id: 3 (new)
    name: three (new)
  - id: 4 (new)
    name: four (new)
rhs_exclusive:
  with:
    structure: true
"""

    standard_diff = """c key
< value
---
> different value

c array[1]
< 2
---
> 3

c array[2]
< 3
---
> 4 (new)

a array[3]
> 5 (new)

a aoh[0].extra_field
> is an extra field (new)

c aoh[1].name
< one
---
> different one

c aoh[2].id
< 2
---
> 3 (new)

c aoh[2].name
< two
---
> three (new)

d lhs_exclusive
< ["node"]

a aoh[3]
> {"id": "4 (new)", "name": "four (new)"}

a rhs_exclusive
> {"with": {"structure": true}}
"""

    def test_no_options(self, script_runner):
        result = script_runner.run(self.command, "--nostdin")
        assert not result.success, result.stderr
        assert "the following arguments are required: YAML_FILE" in result.stderr

    def test_missing_input_file_arg(self, script_runner):
        result = script_runner.run(self.command, "--nostdin", "no-file.yaml", "no-file.yaml")
        assert not result.success, result.stderr
        assert "File not found" in result.stderr

    def test_no_diff_two_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_content)

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--nostdin"
            , lhs_file
            , rhs_file)
        assert result.success, result.stderr
        assert "" == result.stdout

    def test_no_diff_lhs_from_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_content)

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = subprocess.run(
            [self.command
            , "-"
            , rhs_file
            ]
            , stdout=subprocess.PIPE
            , input=self.lhs_content
            , universal_newlines=True
        )
        assert 0 == result.returncode, result.stderr
        assert "" == result.stdout

    def test_no_diff_rhs_from_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_content)

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = subprocess.run(
            [self.command
            , lhs_file
            , "-"
            ]
            , stdout=subprocess.PIPE
            , input=self.rhs_content
            , universal_newlines=True
        )
        assert 0 == result.returncode, result.stderr
        assert "" == result.stdout

    def test_simple_diff_two_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_content)

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--nostdin"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert self.standard_diff == result.stdout

    def test_simple_diff_lhs_from_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_content)

        result = subprocess.run(
            [self.command
            , "-"
            , rhs_file
            ]
            , stdout=subprocess.PIPE
            , input=self.lhs_content
            , universal_newlines=True
        )
        assert 1 == result.returncode, result.stderr
        assert self.standard_diff == result.stdout

    def test_simple_diff_rhs_from_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_content)

        result = subprocess.run(
            [self.command
            , lhs_file
            , "-"
            ]
            , stdout=subprocess.PIPE
            , input=self.rhs_content
            , universal_newlines=True
        )
        assert 1 == result.returncode, result.stderr
        assert self.standard_diff == result.stdout

    def test_simple_diff_from_nothing_via_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_content)
        stdout_content = """a key
> different value

a array
> [1, 3, "4 (new)", "5 (new)"]

a aoh
> [{"id": 0, "name": "zero", "extra_field": "is an extra field (new)"}, {"id": 1, "name": "different one"}, {"id": "3 (new)", "name": "three (new)"}, {"id": "4 (new)", "name": "four (new)"}]

a rhs_exclusive
> {"with": {"structure": true}}
"""

        result = subprocess.run(
            [self.command
            , "-"
            , rhs_file
            ]
            , stdout=subprocess.PIPE
            , input=""
            , universal_newlines=True
        )
        assert 1 == result.returncode, result.stderr
        assert stdout_content == result.stdout

    def test_simple_diff_into_nothing_via_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_content)
        stdout_content = """d key
< value

d array
< [1, 2, 3]

d aoh
< [{"id": 0, "name": "zero"}, {"id": 1, "name": "one"}, {"id": 2, "name": "two"}]

d lhs_exclusive
< ["node"]
"""

        result = subprocess.run(
            [self.command
            , lhs_file
            , "-"
            ]
            , stdout=subprocess.PIPE
            , input=""
            , universal_newlines=True
        )
        assert 1 == result.returncode, result.stderr
        assert stdout_content == result.stdout
