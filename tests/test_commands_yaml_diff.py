import pytest

from tests.conftest import create_temp_yaml_file


class Test_commands_yaml_diff():
    """Tests for the yaml-diff command-line tool."""
    command = "yaml-diff"

    lhs_hash_content = """---
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

    lhs_array_content = """---
- step: 1
  action: input
  args:
    - world
- step: 2
  action: print
  message: Hello, %args[0]!
- step: 3
  action: quit
  status: 0
"""

    rhs_hash_content = """---
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

    rhs_array_content = """---
- step: 1
  action: input
  args:
    - le monde
- step: 2
  action: print
  message: A tout %args[0]!
"""

    standard_hash_diff = """c key
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

    standard_array_diff = """c [0].args[0]
< world
---
> le monde

c [1].message
< Hello, %args[0]!
---
> A tout %args[0]!

d [2]
< {"step": 3, "action": "quit", "status": 0}
"""

    def test_no_options(self, script_runner):
        result = script_runner.run(self.command)
        assert not result.success, result.stderr
        assert "the following arguments are required: YAML_FILE" in result.stderr

    def test_too_many_pseudo_files(self, script_runner):
        result = script_runner.run(self.command, "-", "-")
        assert not result.success, result.stderr
        assert "Only one YAML_FILE may be the - pseudo-file" in result.stderr

    def test_missing_first_input_file_arg(self, script_runner):
        result = script_runner.run(self.command, "no-file.yaml", "no-file.yaml")
        assert not result.success, result.stderr
        assert "File not found" in result.stderr

    def test_missing_second_input_file_arg(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_hash_content)
        result = script_runner.run(self.command, lhs_file, "no-file.yaml")
        assert not result.success, result.stderr
        assert "File not found" in result.stderr

    def test_no_diff_two_hash_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_hash_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_hash_content)

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
        assert "" == result.stdout

    def test_no_diff_two_array_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_array_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_array_content)

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
        assert "" == result.stdout

    def test_no_hash_diff_lhs_from_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_hash_content)

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
            , input=self.lhs_hash_content
            , universal_newlines=True
        )
        assert 0 == result.returncode, result.stderr
        assert "" == result.stdout

    def test_no_array_diff_lhs_from_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_array_content)

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
            , input=self.lhs_array_content
            , universal_newlines=True
        )
        assert 0 == result.returncode, result.stderr
        assert "" == result.stdout

    def test_no_hash_diff_rhs_from_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_hash_content)

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
            , input=self.rhs_hash_content
            , universal_newlines=True
        )
        assert 0 == result.returncode, result.stderr
        assert "" == result.stdout

    def test_no_array_diff_rhs_from_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_array_content)

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
            , input=self.rhs_array_content
            , universal_newlines=True
        )
        assert 0 == result.returncode, result.stderr
        assert "" == result.stdout

    def test_simple_diff_two_hash_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_hash_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_hash_content)

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert self.standard_hash_diff == result.stdout

    def test_simple_diff_two_array_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_array_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_array_content)

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert self.standard_array_diff == result.stdout

    def test_simple_hash_diff_lhs_from_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_hash_content)

        result = subprocess.run(
            [self.command
            , "-"
            , rhs_file
            ]
            , stdout=subprocess.PIPE
            , input=self.lhs_hash_content
            , universal_newlines=True
        )
        assert 1 == result.returncode, result.stderr
        assert self.standard_hash_diff == result.stdout

    def test_simple_array_diff_lhs_from_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_array_content)

        result = subprocess.run(
            [self.command
            , "-"
            , rhs_file
            ]
            , stdout=subprocess.PIPE
            , input=self.lhs_array_content
            , universal_newlines=True
        )
        assert 1 == result.returncode, result.stderr
        assert self.standard_array_diff == result.stdout

    def test_simple_hash_diff_rhs_from_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_hash_content)

        result = subprocess.run(
            [self.command
            , lhs_file
            , "-"
            ]
            , stdout=subprocess.PIPE
            , input=self.rhs_hash_content
            , universal_newlines=True
        )
        assert 1 == result.returncode, result.stderr
        assert self.standard_hash_diff == result.stdout

    def test_simple_array_diff_rhs_from_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_array_content)

        result = subprocess.run(
            [self.command
            , lhs_file
            , "-"
            ]
            , stdout=subprocess.PIPE
            , input=self.rhs_array_content
            , universal_newlines=True
        )
        assert 1 == result.returncode, result.stderr
        assert self.standard_array_diff == result.stdout

    def test_simple_diff_hash_from_nothing_via_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_hash_content)
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

    def test_simple_diff_array_from_nothing_via_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_array_content)
        stdout_content = """a [0]
> {"step": 1, "action": "input", "args": ["le monde"]}

a [1]
> {"step": 2, "action": "print", "message": "A tout %args[0]!"}
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

    def test_simple_diff_hash_from_text_via_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_hash_content)
        stdout_content = """d -
< This is a general text file.

a key
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
            , input="This is a general text file."
            , universal_newlines=True
        )
        assert 1 == result.returncode, result.stderr
        assert stdout_content == result.stdout

    def test_simple_diff_array_from_text_via_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_array_content)
        stdout_content = """d -
< This is a general text file.

a [0]
> {"step": 1, "action": "input", "args": ["le monde"]}

a [1]
> {"step": 2, "action": "print", "message": "A tout %args[0]!"}
"""

        result = subprocess.run(
            [self.command
            , "-"
            , rhs_file
            ]
            , stdout=subprocess.PIPE
            , input="This is a general text file."
            , universal_newlines=True
        )
        assert 1 == result.returncode, result.stderr
        assert stdout_content == result.stdout

    def test_simple_diff_hash_into_nothing_via_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_hash_content)
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

    def test_simple_diff_array_into_nothing_via_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_array_content)
        stdout_content = """d [0]
< {"step": 1, "action": "input", "args": ["world"]}

d [1]
< {"step": 2, "action": "print", "message": "Hello, %args[0]!"}

d [2]
< {"step": 3, "action": "quit", "status": 0}
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




    def test_simple_diff_hash_into_text_via_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_hash_content)
        stdout_content = """a -
> This is a general text file.

d key
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
            , input="This is a general text file."
            , universal_newlines=True
        )
        assert 1 == result.returncode, result.stderr
        assert stdout_content == result.stdout

    def test_simple_diff_array_into_text_via_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_array_content)
        stdout_content = """a -
> This is a general text file.

d [0]
< {"step": 1, "action": "input", "args": ["world"]}

d [1]
< {"step": 2, "action": "print", "message": "Hello, %args[0]!"}

d [2]
< {"step": 3, "action": "quit", "status": 0}
"""

        result = subprocess.run(
            [self.command
            , lhs_file
            , "-"
            ]
            , stdout=subprocess.PIPE
            , input="This is a general text file."
            , universal_newlines=True
        )
        assert 1 == result.returncode, result.stderr
        assert stdout_content == result.stdout


    def test_onlysame_diff_two_hash_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_hash_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_hash_content)
        stdout_content = """s array[0]
= 1

s aoh[0].id
= 0

s aoh[0].name
= zero

s aoh[1].id
= 1
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--onlysame"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_onlysame_diff_two_array_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_array_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_array_content)
        stdout_content = """s [0].step
= 1

s [0].action
= input

s [1].step
= 2

s [1].action
= print
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--onlysame"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert stdout_content == result.stdout
