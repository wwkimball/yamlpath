import pytest

from tests.conftest import create_temp_yaml_file, requireseyaml, old_eyaml_keys


class Test_commands_yaml_diff():
    """Tests for the yaml-diff command-line tool."""
    command = "yaml-diff"

    ###
    # Simple Hash comparisons
    ###
    lhs_hash_content = """---
key: value
hash:
  with:
    multiple: child
    key_value: pairs
  and:
    complex: structure
    with:
      several: levels
lhs_exclusive: value
"""

    rhs_hash_content = """---
key: changed value
hash:
  with:
    multiple: children
    key_value: pairs
  and:
    complex:
      more: complex
    with:
      several_nested: levels
  including:
    additional: structure
rhs_exclusive: value
"""

    ###
    # Simple Array comparisons
    ###
    lhs_array_content = """---
- alpha
- mu
- psi
- beta
- delta
- chi
- delta
- gamma
- alpha
- theta
"""

    rhs_array_content = """---
- zeta
- mu
- psi
- alpha
- gamma
- gamma
- phi
- beta
- chi
"""

    diff_array_defaults = """c [0]
< "alpha"
---
> "zeta"

c [3]
< "beta"
---
> "alpha"

c [4]
< "delta"
---
> "gamma"

c [5]
< "chi"
---
> "gamma"

c [6]
< "delta"
---
> "phi"

c [7]
< "gamma"
---
> "beta"

c [8]
< "alpha"
---
> "chi"

d [9]
< "theta"
"""


    ###
    # Simple Array-of-Hashes comparisons
    ###
    lhs_aoh_content = """---
- step: 0
  action: INITIALIZE
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
- step: 9
  action: CLEANUP
"""

    rhs_aoh_content = """---
- step: 0
  action: INITIALIZE
- step: 3
  action: quit
  status: 0
- step: 2
  action: print
  message: A tout %args[0]!
- step: 1
  action: input
  args:
    - le monde
- step: 9
  action: CLEANUP
"""

    diff_hash_defaults = """d hash.and.complex
< "structure"

c key
< "value"
---
> "changed value"

a rhs_exclusive
> "value"

d lhs_exclusive
< "value"

c hash.with.multiple
< "child"
---
> "children"

a hash.and.complex.more
> "complex"

d hash.and.with.several
< "levels"

a hash.and.with.several_nested
> "levels"

a hash.including
> {"additional": "structure"}
"""

    diff_aoh_deep = """c [3].args[0]
< "world"
---
> "le monde"

c [2].message
< "Hello, %args[0]!"
---
> "A tout %args[0]!"
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

    def test_cannot_quiet_sameness(self, script_runner):
        result = script_runner.run(self.command, "--quiet", "--same", "any-file.yaml", "any-other-file.json")
        assert not result.success, result.stderr
        assert "The --quiet|-q option suppresses all output, including" in result.stderr

    def test_missing_config_file(self, script_runner):
        result = script_runner.run(self.command, "--config=/does/not/exist/on/most/systems.ini", "any-file.yaml", "any-other-file.json")
        assert not result.success, result.stderr
        assert "INI style configuration file is not readable" in result.stderr

    def test_missing_private_key(self, script_runner):
        result = script_runner.run(self.command, "--privatekey=/does/not/exist/on/most/systems.key", "any-file.yaml", "any-other-file.json")
        assert not result.success, result.stderr
        assert "EYAML private key is not a readable file" in result.stderr

    def test_missing_public_key(self, script_runner):
        result = script_runner.run(self.command, "--publickey=/does/not/exist/on/most/systems.key", "any-file.yaml", "any-other-file.json")
        assert not result.success, result.stderr
        assert "EYAML public key is not a readable file" in result.stderr

    def test_bad_eyaml_value(self, script_runner, tmp_path_factory):
        content = """---
        aliases:
          - &encryptedScalar >
            ENC[PKCS7,MIIx...broken-on-purpose...==]
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--eyaml=/does/not/exist-on-most/systems",
            yaml_file,
            yaml_file
        )
        assert not result.success, result.stderr
        assert "No accessible eyaml command" in result.stderr

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

    def test_no_diff_two_aoh_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_aoh_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_aoh_content)

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

    def test_no_aoh_diff_lhs_from_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_aoh_content)

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
            , input=self.lhs_aoh_content
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

    def test_no_aoh_diff_rhs_from_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_aoh_content)

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
            , input=self.rhs_aoh_content
            , universal_newlines=True
        )
        assert 0 == result.returncode, result.stderr
        assert "" == result.stdout

    def test_quiet_diff_two_hash_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_hash_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_hash_content)

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--quiet"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
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
        assert self.diff_hash_defaults == result.stdout

    def test_default_diff_two_aoh_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_aoh_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_aoh_content)
        stdout_content = """c [1]
< {"step": 1, "action": "input", "args": ["world"]}
---
> {"step": 3, "action": "quit", "status": 0}

c [2]
< {"step": 2, "action": "print", "message": "Hello, %args[0]!"}
---
> {"step": 2, "action": "print", "message": "A tout %args[0]!"}

c [3]
< {"step": 3, "action": "quit", "status": 0}
---
> {"step": 1, "action": "input", "args": ["le monde"]}
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
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_position_diff_two_aoh_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_aoh_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_aoh_content)
        stdout_content = """c [1]
< {"step": 1, "action": "input", "args": ["world"]}
---
> {"step": 3, "action": "quit", "status": 0}

c [2]
< {"step": 2, "action": "print", "message": "Hello, %args[0]!"}
---
> {"step": 2, "action": "print", "message": "A tout %args[0]!"}

c [3]
< {"step": 3, "action": "quit", "status": 0}
---
> {"step": 1, "action": "input", "args": ["le monde"]}
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--aoh=position"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_key_diff_two_aoh_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_aoh_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_aoh_content)
        stdout_content = """c [1]
< {"step": 1, "action": "input", "args": ["world"]}
---
> {"step": 1, "action": "input", "args": ["le monde"]}

c [2]
< {"step": 2, "action": "print", "message": "Hello, %args[0]!"}
---
> {"step": 2, "action": "print", "message": "A tout %args[0]!"}
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--aoh=key"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_dpos_diff_two_aoh_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_aoh_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_aoh_content)
        stdout_content = """c [1].step
< 1
---
> 3

a [1].status
> 0

c [1].action
< "input"
---
> "quit"

d [1].args
< ["world"]

c [2].message
< "Hello, %args[0]!"
---
> "A tout %args[0]!"

c [3].step
< 3
---
> 1

c [3].action
< "quit"
---
> "input"

d [3].status
< 0

a [3].args
> ["le monde"]
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--aoh=dpos"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_deep_diff_two_aoh_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_aoh_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_aoh_content)

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--aoh=deep"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert self.diff_aoh_deep == result.stdout

    def test_value_diff_two_aoh_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_aoh_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_aoh_content)
        stdout_content = """d [1]
< {"step": 1, "action": "input", "args": ["world"]}

c [2]
< {"step": 2, "action": "print", "message": "Hello, %args[0]!"}
---
> {"step": 2, "action": "print", "message": "A tout %args[0]!"}

a [3]
> {"step": 1, "action": "input", "args": ["le monde"]}
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--aoh=value"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

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
        assert self.diff_hash_defaults == result.stdout

    def test_simple_aoh_diff_lhs_from_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_aoh_content)

        result = subprocess.run(
            [self.command
            , "--aoh=deep"
            , "-"
            , rhs_file
            ]
            , stdout=subprocess.PIPE
            , input=self.lhs_aoh_content
            , universal_newlines=True
        )
        assert 1 == result.returncode, result.stderr
        assert self.diff_aoh_deep == result.stdout

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
        assert self.diff_hash_defaults == result.stdout

    def test_simple_aoh_diff_rhs_from_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_aoh_content)

        result = subprocess.run(
            [self.command
            , "--aoh=deep"
            , lhs_file
            , "-"
            ]
            , stdout=subprocess.PIPE
            , input=self.rhs_aoh_content
            , universal_newlines=True
        )
        assert 1 == result.returncode, result.stderr
        assert self.diff_aoh_deep == result.stdout

    def test_simple_diff_hash_from_nothing_via_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_hash_content)
        stdout_content = """a key
> "changed value"

a rhs_exclusive
> "value"

a hash
> {"with": {"multiple": "children", "key_value": "pairs"}, "and": {"complex": {"more": "complex"}, "with": {"several_nested": "levels"}}, "including": {"additional": "structure"}}
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

    def test_simple_diff_aoh_from_nothing_via_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_aoh_content)
        stdout_content = """a [0]
> {"step": 0, "action": "INITIALIZE"}

a [1]
> {"step": 3, "action": "quit", "status": 0}

a [2]
> {"step": 2, "action": "print", "message": "A tout %args[0]!"}

a [3]
> {"step": 1, "action": "input", "args": ["le monde"]}

a [4]
> {"step": 9, "action": "CLEANUP"}
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
< "This is a general text file."

a key
> "changed value"

a rhs_exclusive
> "value"

a hash
> {"with": {"multiple": "children", "key_value": "pairs"}, "and": {"complex": {"more": "complex"}, "with": {"several_nested": "levels"}}, "including": {"additional": "structure"}}
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

    def test_simple_diff_aoh_from_text_via_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_aoh_content)
        stdout_content = """d -
< "This is a general text file."

a [0]
> {"step": 0, "action": "INITIALIZE"}

a [1]
> {"step": 3, "action": "quit", "status": 0}

a [2]
> {"step": 2, "action": "print", "message": "A tout %args[0]!"}

a [3]
> {"step": 1, "action": "input", "args": ["le monde"]}

a [4]
> {"step": 9, "action": "CLEANUP"}
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
< "value"

d lhs_exclusive
< "value"

d hash
< {"with": {"multiple": "child", "key_value": "pairs"}, "and": {"complex": "structure", "with": {"several": "levels"}}}
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

    def test_simple_diff_aoh_into_nothing_via_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_aoh_content)
        stdout_content = """d [0]
< {"step": 0, "action": "INITIALIZE"}

d [1]
< {"step": 1, "action": "input", "args": ["world"]}

d [2]
< {"step": 2, "action": "print", "message": "Hello, %args[0]!"}

d [3]
< {"step": 3, "action": "quit", "status": 0}

d [4]
< {"step": 9, "action": "CLEANUP"}
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
> "This is a general text file."

d key
< "value"

d lhs_exclusive
< "value"

d hash
< {"with": {"multiple": "child", "key_value": "pairs"}, "and": {"complex": "structure", "with": {"several": "levels"}}}
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

    def test_simple_diff_aoh_into_text_via_stdin(self, script_runner, tmp_path_factory):
        import subprocess
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_aoh_content)
        stdout_content = """a -
> "This is a general text file."

d [0]
< {"step": 0, "action": "INITIALIZE"}

d [1]
< {"step": 1, "action": "input", "args": ["world"]}

d [2]
< {"step": 2, "action": "print", "message": "Hello, %args[0]!"}

d [3]
< {"step": 3, "action": "quit", "status": 0}

d [4]
< {"step": 9, "action": "CLEANUP"}
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
        stdout_content = """s hash.with.key_value
= "pairs"
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--onlysame"
            , "--aoh=deep"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_onlysame_deep_diff_two_aoh_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_aoh_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_aoh_content)
        stdout_content = """s [0].step
= 0

s [0].action
= "INITIALIZE"

s [3].step
= 1

s [3].action
= "input"

s [2].step
= 2

s [2].action
= "print"

s [1].step
= 3

s [1].action
= "quit"

s [1].status
= 0

s [4].step
= 9

s [4].action
= "CLEANUP"
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--onlysame"
            , "--aoh=deep"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_diff_two_aliased_hash_files(self, script_runner, tmp_path_factory):
        """
        Test Anchors, their Aliases, and YAML Merge Operators.

        Also demonstrate that the yaml-diff tool is a FUNCTIONAL comparison of
        two data files, NOT a textual comparison.  In other words, yaml-diff is
        only interested in how the data is represented to YAML/JSON parsers,
        NOT how the YAML/JSON file is constructed.  Immaterial elements like
        comments, white-space, and demarcation symbols are deliberately ignored
        because none of these have any impact on what data YAML/JSON parsers
        actually percieve to be within the files at run-time.

        Users who need a TEXTUAL (non-functional) comparison of two YAML/JSON
        files should use the GNU `diff` command-line tool rather than this
        yaml-diff command-line tool.
        """
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &string_value This is a reusable string value.
  - &int_value 5280
some_values: &some_values
  aliased_int: *int_value
  original_float: 3.14159265358
more_values: &more_values
  aliased_string: *string_value
  original_string: This is another reusable string except its in a reusable parent Hash.
collector_hash:
  <<: [ *some_values, *more_values ]
  concrete_string: This is a non-reusable concrete string.
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
# Reusable aliases
aliases:
  - &string_value This is a CHANGED reusable string value.
  - &aliased_int_value 5280

# Reusable numbers reusing one number
some_values: &some_values
  aliased_int: *aliased_int_value
  original_float: 3.14

# Reusable strings reusing one string
more_values: &more_values
  aliased_string: *string_value
  original_string: "This is another reusable string except its in a reusable parent Hash."

# Bring it all together
collector_hash:
  <<: [ *some_values, *more_values ]
  concrete_string: 'This is a non-reusable concrete string.'
""")
        stdout_content = """c aliases[0]
< "This is a reusable string value."
---
> "This is a CHANGED reusable string value."

c some_values.original_float
< 3.14159265358
---
> 3.14

c more_values.aliased_string
< "This is a reusable string value."
---
> "This is a CHANGED reusable string value."

c collector_hash.original_float
< 3.14159265358
---
> 3.14

c collector_hash.aliased_string
< "This is a reusable string value."
---
> "This is a CHANGED reusable string value."
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
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_simple_diff_two_hash_files_fslash(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_hash_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_hash_content)
        stdout_content = """d /hash/and/complex
< "structure"

c /key
< "value"
---
> "changed value"

a /rhs_exclusive
> "value"

d /lhs_exclusive
< "value"

c /hash/with/multiple
< "child"
---
> "children"

a /hash/and/complex/more
> "complex"

d /hash/and/with/several
< "levels"

a /hash/and/with/several_nested
> "levels"

a /hash/including
> {"additional": "structure"}
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--pathsep=/"
            , "--aoh=deep"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    @requireseyaml
    def test_diff_eyaml_allowed(self, script_runner, tmp_path_factory, old_eyaml_keys):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
same_secret_same_crypt: >-
  ENC[PKCS7,MIIBygYJKoZIhvcNAQcDoIIBuzCCAbcCAQAxggEhMIIBHQIBADAFMAACAQEw
  DQYJKoZIhvcNAQEBBQAEggEAP5tXc8gPp1p5945Ih/i/k/OqvoDrWi/F05/V
  EhlgUwXgNer0Y5C7G/FE4Gt5nasoolbPQTMVuq+CW8qQ6wsnVrB60SCDvy5q
  9k7WGHyQU5n6UR00/RLhctStGe6nN/zIsoYLQyyY/+xJaHAwahB/GkzFPk9S
  F2Zu+fsxj1X38XVuGFC+Nx89ODXnNYBxRuElUK9qHuC5rCRyPBWEM9brv6Am
  7+PCig9WZSxXUkDyX6hG2Mzm/ndKgqonhCEBOp3CrDrmFdWCdmx81Qe1dLRl
  mSonHjWYyFugtrRz6YV7Ni1cicEZoKUFT/XXqntX1BS97M9Ms8AZODrDxB66
  rpZ41jCBjAYJKoZIhvcNAQcBMB0GCWCGSAFlAwQBKgQQBHXHyWGQNDL6l7tA
  9Rf784BgLbcaRZMscSjL/ym69YQXRJPzo3nCBSVOCUrVtU0pGFpkSUvdYRmr
  ZVlZ5jcv9xiU+ktGJZhjzzVcSHYMf9LkwtCiHYRYzVgDX/S24/NSVF5NEeTz
  MvIW862oA8UFtodj]
same_secret_different_crypt: >-
  ENC[PKCS7,MIIBygYJKoZIhvcNAQcDoIIBuzCCAbcCAQAxggEhMIIBHQIBADAFMAACAQEw
  DQYJKoZIhvcNAQEBBQAEggEAYUDg4y4+LXY0IdEDYFgxfxRJ3dfkOPwTSLxl
  A91x5IQlgQYQpXkgkFEeJj3EXdYwt9K6prtFywokVQoOaWgXWWV+Tf0lF5P0
  0sw4LH7MgaszKPpiOHxx9hTmexEIusF+tzvQBOD1zHfDdkZQ0v9R3JLHckub
  rg/XOLJXzkkyKEoKIFScBT115aedGY60baMtvD1Md9rxi97xCmj6BroatMlM
  Cm266oFnijrQN9Xsb5ZTnGiPMA9hC2y6X+oJeMaG0S6G64EnTwnjAQytWE6a
  JM1/YXVKIoE2c/E44/m74kuyO70RwACV9QknSqoLuUbYpcbU4FHU/xICiWAG
  CaTz9zCBjAYJKoZIhvcNAQcBMB0GCWCGSAFlAwQBKgQQ9kFVNmG9heK0WyWU
  R1kfyIBgCIJzi+XnQMS9w85Mbq6BaNPpJrU7ZaoHQ6c3Ps9sgJStVDQNmrbL
  WAP8fEC6S7V07rA7hp4YomvAJRJjDIK7M2AzXDNzupuAh4crF905AR4TF+Jd
  nNuWarGVGx1Bv+6h]
different_secrets: >-
  ENC[PKCS7,MIIBmQYJKoZIhvcNAQcDoIIBijCCAYYCAQAxggEhMIIBHQIBADAFMAACAQEw
  DQYJKoZIhvcNAQEBBQAEggEAJRw+urxm+Pyt0Xys5UpJUIaZhA0Tt1JuVsLG
  9jiHb9aua+2bBr/kAN8D/+dowOJlVkG6LZ4Uzn+NZboO8Q2JpQeV9CJTqayJ
  eZnRx02298qSrWOogSQUoS/or0+QWGLeQqJMiNuUx6IHskyWVsROamTmK9p2
  gAgL5bAXzD2+1MHIRMrf8ascVmTOV4/JMckWznCseM+uJ7PkR12044mWhuvk
  aJUjaXFXIEYhA4+jjKWdlOTWJAFkjhKE6HAHqaNZVlcf8X1WuoX4f1iPP53z
  mATu0eDx8D5XwQnygUMrPWrlCyoIqRIcwU6f5iv+HT1EWEvSI5+i7bByx0hk
  apUR+TBcBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBCgVC5h5pznSfACl7+Q
  ff+mgDBAZPMofXWfguD6OgcXu0/QMz90QHAN4bu+CHHZLZ+8X3qSgKHszijK
  eEeStAMoq50=]
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
same_secret_same_crypt: >-
  ENC[PKCS7,MIIBygYJKoZIhvcNAQcDoIIBuzCCAbcCAQAxggEhMIIBHQIBADAFMAACAQEw
  DQYJKoZIhvcNAQEBBQAEggEAP5tXc8gPp1p5945Ih/i/k/OqvoDrWi/F05/V
  EhlgUwXgNer0Y5C7G/FE4Gt5nasoolbPQTMVuq+CW8qQ6wsnVrB60SCDvy5q
  9k7WGHyQU5n6UR00/RLhctStGe6nN/zIsoYLQyyY/+xJaHAwahB/GkzFPk9S
  F2Zu+fsxj1X38XVuGFC+Nx89ODXnNYBxRuElUK9qHuC5rCRyPBWEM9brv6Am
  7+PCig9WZSxXUkDyX6hG2Mzm/ndKgqonhCEBOp3CrDrmFdWCdmx81Qe1dLRl
  mSonHjWYyFugtrRz6YV7Ni1cicEZoKUFT/XXqntX1BS97M9Ms8AZODrDxB66
  rpZ41jCBjAYJKoZIhvcNAQcBMB0GCWCGSAFlAwQBKgQQBHXHyWGQNDL6l7tA
  9Rf784BgLbcaRZMscSjL/ym69YQXRJPzo3nCBSVOCUrVtU0pGFpkSUvdYRmr
  ZVlZ5jcv9xiU+ktGJZhjzzVcSHYMf9LkwtCiHYRYzVgDX/S24/NSVF5NEeTz
  MvIW862oA8UFtodj]
same_secret_different_crypt: >-
  ENC[PKCS7,MIIBygYJKoZIhvcNAQcDoIIBuzCCAbcCAQAxggEhMIIBHQIBADAFMAACAQEw
  DQYJKoZIhvcNAQEBBQAEggEAV/S/jxC79aiKR1UnPxcrPo7bLpSpsoUqJfdQ
  znMp0LJrqacIcrq+jFRLqFUv2dDcTRnReP5CZy4HEJw73710Ngb+sJLQeCE9
  f8qYvjKAlWyrw0Strpwe5BQT4g7ph5GX3lOqjCBJbqRPE9XfhI9DPljkUzBB
  IQ8zVZz/zy5TbBCRZm7RKPjbczTMaHRRQb0fEKnK7tTdHIucNRQh0AZ9ZGuJ
  8TchxlBhgtwjKU0NxbpQyi/hVyv7Dw8/wSq3Wp5nFYJj1uFxYES0sw6QAsM+
  1LzY2hg+RCzL3gxU724gH0xRCv346tKoyqzVxtO+knLVh/m8HulrXJABKn0/
  ZJrBezCBjAYJKoZIhvcNAQcBMB0GCWCGSAFlAwQBKgQQMvmLomzj48fPsA1H
  DVQiaoBgctgTfmmKEaEoCYJqd4WXpJeb96viMyTXRaa8Pt0rl22mbt92qMUk
  witfhD7lzteg1k2tunXQx8w37vx60kqY3aEXV8crQb1TQdBUuZIks1RnLFur
  14/eAgRAn37NhJli]
different_secrets: >-
  ENC[PKCS7,MIIBmQYJKoZIhvcNAQcDoIIBijCCAYYCAQAxggEhMIIBHQIBADAFMAACAQEw
  DQYJKoZIhvcNAQEBBQAEggEAm9Sw3jUCLMOKU0wpQgu7kW4yO/MvoLbQpWMB
  KKFEssxhJ0Kqc5Q+2cTAk6vo5K7GopVYr5iCaaoxLmCJq3ke1XBR6O182q/2
  vcvgqTVq3OaaMR3qji1edJQd6NJuqpuV+tIf6RCktt5+9wlIXLxujnaYxmr1
  vrEMXnb0R6PWunXsTAlDDrCVMC6iXIvbhsP2GF8zhhuTkCXp1LTDuvj3aSso
  iloELuCdCGO7iFTXPuPy4nrgXjlaVnGftoDmVukDP8PUzyEBT1a9ZXUjrswS
  sXzCsTnEGIpPlIe84Nvk43osbVw2sOgwod7Uko7KmdXVFAh8l15BoW5E9uRw
  y2XahTBcBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBAIA2FJ1Fo38jwnbHs8
  V8GOgDAaCmR9jyjK/0f0V2WnRF+nPS21sNoB0qONn1V0GwAQbu0yk7QS5y8q
  4OTZEGxziGU=]
""")
        stdout_content = """c different_secrets
< "ENC[PKCS7,MIIBmQYJKoZIhvcNAQcDoIIBijCCAYYCAQAxggEhMIIBHQIBADAFMAACAQEwDQYJKoZIhvcNAQEBBQAEggEAJRw+urxm+Pyt0Xys5UpJUIaZhA0Tt1JuVsLG9jiHb9aua+2bBr/kAN8D/+dowOJlVkG6LZ4Uzn+NZboO8Q2JpQeV9CJTqayJeZnRx02298qSrWOogSQUoS/or0+QWGLeQqJMiNuUx6IHskyWVsROamTmK9p2gAgL5bAXzD2+1MHIRMrf8ascVmTOV4/JMckWznCseM+uJ7PkR12044mWhuvkaJUjaXFXIEYhA4+jjKWdlOTWJAFkjhKE6HAHqaNZVlcf8X1WuoX4f1iPP53zmATu0eDx8D5XwQnygUMrPWrlCyoIqRIcwU6f5iv+HT1EWEvSI5+i7bByx0hkapUR+TBcBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBCgVC5h5pznSfACl7+Qff+mgDBAZPMofXWfguD6OgcXu0/QMz90QHAN4bu+CHHZLZ+8X3qSgKHszijKeEeStAMoq50=]"
---
> "ENC[PKCS7,MIIBmQYJKoZIhvcNAQcDoIIBijCCAYYCAQAxggEhMIIBHQIBADAFMAACAQEwDQYJKoZIhvcNAQEBBQAEggEAm9Sw3jUCLMOKU0wpQgu7kW4yO/MvoLbQpWMBKKFEssxhJ0Kqc5Q+2cTAk6vo5K7GopVYr5iCaaoxLmCJq3ke1XBR6O182q/2vcvgqTVq3OaaMR3qji1edJQd6NJuqpuV+tIf6RCktt5+9wlIXLxujnaYxmr1vrEMXnb0R6PWunXsTAlDDrCVMC6iXIvbhsP2GF8zhhuTkCXp1LTDuvj3aSsoiloELuCdCGO7iFTXPuPy4nrgXjlaVnGftoDmVukDP8PUzyEBT1a9ZXUjrswSsXzCsTnEGIpPlIe84Nvk43osbVw2sOgwod7Uko7KmdXVFAh8l15BoW5E9uRwy2XahTBcBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBAIA2FJ1Fo38jwnbHs8V8GOgDAaCmR9jyjK/0f0V2WnRF+nPS21sNoB0qONn1V0GwAQbu0yk7QS5y8q4OTZEGxziGU=]"
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--privatekey={}".format(old_eyaml_keys[0])
            , "--publickey={}".format(old_eyaml_keys[1])
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_diff_eyaml_disallowed(self, script_runner, tmp_path_factory, old_eyaml_keys):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
same_secret_same_crypt: >
  ENC[PKCS7,MIIBygYJKoZIhvcNAQcDoIIBuzCCAbcCAQAxggEhMIIBHQIBADAFMAACAQEw
  DQYJKoZIhvcNAQEBBQAEggEAP5tXc8gPp1p5945Ih/i/k/OqvoDrWi/F05/V
  EhlgUwXgNer0Y5C7G/FE4Gt5nasoolbPQTMVuq+CW8qQ6wsnVrB60SCDvy5q
  9k7WGHyQU5n6UR00/RLhctStGe6nN/zIsoYLQyyY/+xJaHAwahB/GkzFPk9S
  F2Zu+fsxj1X38XVuGFC+Nx89ODXnNYBxRuElUK9qHuC5rCRyPBWEM9brv6Am
  7+PCig9WZSxXUkDyX6hG2Mzm/ndKgqonhCEBOp3CrDrmFdWCdmx81Qe1dLRl
  mSonHjWYyFugtrRz6YV7Ni1cicEZoKUFT/XXqntX1BS97M9Ms8AZODrDxB66
  rpZ41jCBjAYJKoZIhvcNAQcBMB0GCWCGSAFlAwQBKgQQBHXHyWGQNDL6l7tA
  9Rf784BgLbcaRZMscSjL/ym69YQXRJPzo3nCBSVOCUrVtU0pGFpkSUvdYRmr
  ZVlZ5jcv9xiU+ktGJZhjzzVcSHYMf9LkwtCiHYRYzVgDX/S24/NSVF5NEeTz
  MvIW862oA8UFtodj]
same_secret_different_crypt: >
  ENC[PKCS7,MIIBygYJKoZIhvcNAQcDoIIBuzCCAbcCAQAxggEhMIIBHQIBADAFMAACAQEw
  DQYJKoZIhvcNAQEBBQAEggEAYUDg4y4+LXY0IdEDYFgxfxRJ3dfkOPwTSLxl
  A91x5IQlgQYQpXkgkFEeJj3EXdYwt9K6prtFywokVQoOaWgXWWV+Tf0lF5P0
  0sw4LH7MgaszKPpiOHxx9hTmexEIusF+tzvQBOD1zHfDdkZQ0v9R3JLHckub
  rg/XOLJXzkkyKEoKIFScBT115aedGY60baMtvD1Md9rxi97xCmj6BroatMlM
  Cm266oFnijrQN9Xsb5ZTnGiPMA9hC2y6X+oJeMaG0S6G64EnTwnjAQytWE6a
  JM1/YXVKIoE2c/E44/m74kuyO70RwACV9QknSqoLuUbYpcbU4FHU/xICiWAG
  CaTz9zCBjAYJKoZIhvcNAQcBMB0GCWCGSAFlAwQBKgQQ9kFVNmG9heK0WyWU
  R1kfyIBgCIJzi+XnQMS9w85Mbq6BaNPpJrU7ZaoHQ6c3Ps9sgJStVDQNmrbL
  WAP8fEC6S7V07rA7hp4YomvAJRJjDIK7M2AzXDNzupuAh4crF905AR4TF+Jd
  nNuWarGVGx1Bv+6h]
different_secrets: >
  ENC[PKCS7,MIIBmQYJKoZIhvcNAQcDoIIBijCCAYYCAQAxggEhMIIBHQIBADAFMAACAQEw
  DQYJKoZIhvcNAQEBBQAEggEAJRw+urxm+Pyt0Xys5UpJUIaZhA0Tt1JuVsLG
  9jiHb9aua+2bBr/kAN8D/+dowOJlVkG6LZ4Uzn+NZboO8Q2JpQeV9CJTqayJ
  eZnRx02298qSrWOogSQUoS/or0+QWGLeQqJMiNuUx6IHskyWVsROamTmK9p2
  gAgL5bAXzD2+1MHIRMrf8ascVmTOV4/JMckWznCseM+uJ7PkR12044mWhuvk
  aJUjaXFXIEYhA4+jjKWdlOTWJAFkjhKE6HAHqaNZVlcf8X1WuoX4f1iPP53z
  mATu0eDx8D5XwQnygUMrPWrlCyoIqRIcwU6f5iv+HT1EWEvSI5+i7bByx0hk
  apUR+TBcBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBCgVC5h5pznSfACl7+Q
  ff+mgDBAZPMofXWfguD6OgcXu0/QMz90QHAN4bu+CHHZLZ+8X3qSgKHszijK
  eEeStAMoq50=]
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
same_secret_same_crypt: >
  ENC[PKCS7,MIIBygYJKoZIhvcNAQcDoIIBuzCCAbcCAQAxggEhMIIBHQIBADAFMAACAQEw
  DQYJKoZIhvcNAQEBBQAEggEAP5tXc8gPp1p5945Ih/i/k/OqvoDrWi/F05/V
  EhlgUwXgNer0Y5C7G/FE4Gt5nasoolbPQTMVuq+CW8qQ6wsnVrB60SCDvy5q
  9k7WGHyQU5n6UR00/RLhctStGe6nN/zIsoYLQyyY/+xJaHAwahB/GkzFPk9S
  F2Zu+fsxj1X38XVuGFC+Nx89ODXnNYBxRuElUK9qHuC5rCRyPBWEM9brv6Am
  7+PCig9WZSxXUkDyX6hG2Mzm/ndKgqonhCEBOp3CrDrmFdWCdmx81Qe1dLRl
  mSonHjWYyFugtrRz6YV7Ni1cicEZoKUFT/XXqntX1BS97M9Ms8AZODrDxB66
  rpZ41jCBjAYJKoZIhvcNAQcBMB0GCWCGSAFlAwQBKgQQBHXHyWGQNDL6l7tA
  9Rf784BgLbcaRZMscSjL/ym69YQXRJPzo3nCBSVOCUrVtU0pGFpkSUvdYRmr
  ZVlZ5jcv9xiU+ktGJZhjzzVcSHYMf9LkwtCiHYRYzVgDX/S24/NSVF5NEeTz
  MvIW862oA8UFtodj]
same_secret_different_crypt: >
  ENC[PKCS7,MIIBygYJKoZIhvcNAQcDoIIBuzCCAbcCAQAxggEhMIIBHQIBADAFMAACAQEw
  DQYJKoZIhvcNAQEBBQAEggEAV/S/jxC79aiKR1UnPxcrPo7bLpSpsoUqJfdQ
  znMp0LJrqacIcrq+jFRLqFUv2dDcTRnReP5CZy4HEJw73710Ngb+sJLQeCE9
  f8qYvjKAlWyrw0Strpwe5BQT4g7ph5GX3lOqjCBJbqRPE9XfhI9DPljkUzBB
  IQ8zVZz/zy5TbBCRZm7RKPjbczTMaHRRQb0fEKnK7tTdHIucNRQh0AZ9ZGuJ
  8TchxlBhgtwjKU0NxbpQyi/hVyv7Dw8/wSq3Wp5nFYJj1uFxYES0sw6QAsM+
  1LzY2hg+RCzL3gxU724gH0xRCv346tKoyqzVxtO+knLVh/m8HulrXJABKn0/
  ZJrBezCBjAYJKoZIhvcNAQcBMB0GCWCGSAFlAwQBKgQQMvmLomzj48fPsA1H
  DVQiaoBgctgTfmmKEaEoCYJqd4WXpJeb96viMyTXRaa8Pt0rl22mbt92qMUk
  witfhD7lzteg1k2tunXQx8w37vx60kqY3aEXV8crQb1TQdBUuZIks1RnLFur
  14/eAgRAn37NhJli]
different_secrets: >
  ENC[PKCS7,MIIBmQYJKoZIhvcNAQcDoIIBijCCAYYCAQAxggEhMIIBHQIBADAFMAACAQEw
  DQYJKoZIhvcNAQEBBQAEggEAm9Sw3jUCLMOKU0wpQgu7kW4yO/MvoLbQpWMB
  KKFEssxhJ0Kqc5Q+2cTAk6vo5K7GopVYr5iCaaoxLmCJq3ke1XBR6O182q/2
  vcvgqTVq3OaaMR3qji1edJQd6NJuqpuV+tIf6RCktt5+9wlIXLxujnaYxmr1
  vrEMXnb0R6PWunXsTAlDDrCVMC6iXIvbhsP2GF8zhhuTkCXp1LTDuvj3aSso
  iloELuCdCGO7iFTXPuPy4nrgXjlaVnGftoDmVukDP8PUzyEBT1a9ZXUjrswS
  sXzCsTnEGIpPlIe84Nvk43osbVw2sOgwod7Uko7KmdXVFAh8l15BoW5E9uRw
  y2XahTBcBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBAIA2FJ1Fo38jwnbHs8
  V8GOgDAaCmR9jyjK/0f0V2WnRF+nPS21sNoB0qONn1V0GwAQbu0yk7QS5y8q
  4OTZEGxziGU=]
""")
        stdout_content = """c same_secret_different_crypt
< "ENC[PKCS7,MIIBygYJKoZIhvcNAQcDoIIBuzCCAbcCAQAxggEhMIIBHQIBADAFMAACAQEw DQYJKoZIhvcNAQEBBQAEggEAYUDg4y4+LXY0IdEDYFgxfxRJ3dfkOPwTSLxl A91x5IQlgQYQpXkgkFEeJj3EXdYwt9K6prtFywokVQoOaWgXWWV+Tf0lF5P0 0sw4LH7MgaszKPpiOHxx9hTmexEIusF+tzvQBOD1zHfDdkZQ0v9R3JLHckub rg/XOLJXzkkyKEoKIFScBT115aedGY60baMtvD1Md9rxi97xCmj6BroatMlM Cm266oFnijrQN9Xsb5ZTnGiPMA9hC2y6X+oJeMaG0S6G64EnTwnjAQytWE6a JM1/YXVKIoE2c/E44/m74kuyO70RwACV9QknSqoLuUbYpcbU4FHU/xICiWAG CaTz9zCBjAYJKoZIhvcNAQcBMB0GCWCGSAFlAwQBKgQQ9kFVNmG9heK0WyWU R1kfyIBgCIJzi+XnQMS9w85Mbq6BaNPpJrU7ZaoHQ6c3Ps9sgJStVDQNmrbL WAP8fEC6S7V07rA7hp4YomvAJRJjDIK7M2AzXDNzupuAh4crF905AR4TF+Jd nNuWarGVGx1Bv+6h]"
---
> "ENC[PKCS7,MIIBygYJKoZIhvcNAQcDoIIBuzCCAbcCAQAxggEhMIIBHQIBADAFMAACAQEw DQYJKoZIhvcNAQEBBQAEggEAV/S/jxC79aiKR1UnPxcrPo7bLpSpsoUqJfdQ znMp0LJrqacIcrq+jFRLqFUv2dDcTRnReP5CZy4HEJw73710Ngb+sJLQeCE9 f8qYvjKAlWyrw0Strpwe5BQT4g7ph5GX3lOqjCBJbqRPE9XfhI9DPljkUzBB IQ8zVZz/zy5TbBCRZm7RKPjbczTMaHRRQb0fEKnK7tTdHIucNRQh0AZ9ZGuJ 8TchxlBhgtwjKU0NxbpQyi/hVyv7Dw8/wSq3Wp5nFYJj1uFxYES0sw6QAsM+ 1LzY2hg+RCzL3gxU724gH0xRCv346tKoyqzVxtO+knLVh/m8HulrXJABKn0/ ZJrBezCBjAYJKoZIhvcNAQcBMB0GCWCGSAFlAwQBKgQQMvmLomzj48fPsA1H DVQiaoBgctgTfmmKEaEoCYJqd4WXpJeb96viMyTXRaa8Pt0rl22mbt92qMUk witfhD7lzteg1k2tunXQx8w37vx60kqY3aEXV8crQb1TQdBUuZIks1RnLFur 14/eAgRAn37NhJli]"

c different_secrets
< "ENC[PKCS7,MIIBmQYJKoZIhvcNAQcDoIIBijCCAYYCAQAxggEhMIIBHQIBADAFMAACAQEw DQYJKoZIhvcNAQEBBQAEggEAJRw+urxm+Pyt0Xys5UpJUIaZhA0Tt1JuVsLG 9jiHb9aua+2bBr/kAN8D/+dowOJlVkG6LZ4Uzn+NZboO8Q2JpQeV9CJTqayJ eZnRx02298qSrWOogSQUoS/or0+QWGLeQqJMiNuUx6IHskyWVsROamTmK9p2 gAgL5bAXzD2+1MHIRMrf8ascVmTOV4/JMckWznCseM+uJ7PkR12044mWhuvk aJUjaXFXIEYhA4+jjKWdlOTWJAFkjhKE6HAHqaNZVlcf8X1WuoX4f1iPP53z mATu0eDx8D5XwQnygUMrPWrlCyoIqRIcwU6f5iv+HT1EWEvSI5+i7bByx0hk apUR+TBcBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBCgVC5h5pznSfACl7+Q ff+mgDBAZPMofXWfguD6OgcXu0/QMz90QHAN4bu+CHHZLZ+8X3qSgKHszijK eEeStAMoq50=]"
---
> "ENC[PKCS7,MIIBmQYJKoZIhvcNAQcDoIIBijCCAYYCAQAxggEhMIIBHQIBADAFMAACAQEw DQYJKoZIhvcNAQEBBQAEggEAm9Sw3jUCLMOKU0wpQgu7kW4yO/MvoLbQpWMB KKFEssxhJ0Kqc5Q+2cTAk6vo5K7GopVYr5iCaaoxLmCJq3ke1XBR6O182q/2 vcvgqTVq3OaaMR3qji1edJQd6NJuqpuV+tIf6RCktt5+9wlIXLxujnaYxmr1 vrEMXnb0R6PWunXsTAlDDrCVMC6iXIvbhsP2GF8zhhuTkCXp1LTDuvj3aSso iloELuCdCGO7iFTXPuPy4nrgXjlaVnGftoDmVukDP8PUzyEBT1a9ZXUjrswS sXzCsTnEGIpPlIe84Nvk43osbVw2sOgwod7Uko7KmdXVFAh8l15BoW5E9uRw y2XahTBcBgkqhkiG9w0BBwEwHQYJYIZIAWUDBAEqBBAIA2FJ1Fo38jwnbHs8 V8GOgDAaCmR9jyjK/0f0V2WnRF+nPS21sNoB0qONn1V0GwAQbu0yk7QS5y8q 4OTZEGxziGU=]"
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--ignore-eyaml-values"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_diff_two_multiline_string_hash_files(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
folded_string: >
  This is
  one really long
  string.  It
  is presented in
  YAML "folded"
  format.  This will
  cause all of the
  new-line characters
  to be replaced with
  single spaces
  when this value
  is read by a
  YAML parser.

literal_string: |
  This is another
  really long string.
  It is presented in
  YAML "literal"
  format.  When a
  YAML parser reads
  this value, all of
  these new-line
  characters will be
  preserved.
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
folded_string: >
  This CHANGED
  one really long
  string.  It
  is presented in
  YAML "folded"
  format.  This will
  cause all of the
  new-line characters
  to be replaced with
  single spaces
  when this value
  is read by a
  YAML parser.

literal_string: |
  This is another
  really long CHANGED string.
  It is presented in
  YAML "literal"
  format.  When a
  YAML parser reads
  this value, all of
  these new-line
  characters will be
  preserved.
""")
        stdout_content = r"""c folded_string
< "This is one really long string.  It is presented in YAML \"folded\" format.  This will cause all of the new-line characters to be replaced with single spaces when this value is read by a YAML parser."
---
> "This CHANGED one really long string.  It is presented in YAML \"folded\" format.  This will cause all of the new-line characters to be replaced with single spaces when this value is read by a YAML parser."

c literal_string
< "This is another
< really long string.
< It is presented in
< YAML \"literal\"
< format.  When a
< YAML parser reads
< this value, all of
< these new-line
< characters will be
< preserved."
---
> "This is another
> really long CHANGED string.
> It is presented in
> YAML \"literal\"
> format.  When a
> YAML parser reads
> this value, all of
> these new-line
> characters will be
> preserved."
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
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_diff_two_multiline_string_hash_files_verbosely(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
folded_string: >
  This is
  one really long
  string.  It
  is presented in
  YAML "folded"
  format.  This will
  cause all of the
  new-line characters
  to be replaced with
  single spaces
  when this value
  is read by a
  YAML parser.

literal_string: |
  This is another
  really long string.
  It is presented in
  YAML "literal"
  format.  When a
  YAML parser reads
  this value, all of
  these new-line
  characters will be
  preserved.
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
folded_string: >
  This CHANGED
  one really long
  string.  It
  is presented in
  YAML "folded"
  format.  This will
  cause all of the
  new-line characters
  to be replaced with
  single spaces
  when this value
  is read by a
  YAML parser.

literal_string: |
  This is another
  really long CHANGED string.
  It is presented in
  YAML "literal"
  format.  When a
  YAML parser reads
  this value, all of
  these new-line
  characters will be
  preserved.
""")
        stdout_content = r"""c1.0.0.1.0.0 folded_string
< "This is one really long string.  It is presented in YAML \"folded\" format.  This will cause all of the new-line characters to be replaced with single spaces when this value is read by a YAML parser."
---
> "This CHANGED one really long string.  It is presented in YAML \"folded\" format.  This will cause all of the new-line characters to be replaced with single spaces when this value is read by a YAML parser."

c1.0.1.1.0.1 literal_string
< "This is another
< really long string.
< It is presented in
< YAML \"literal\"
< format.  When a
< YAML parser reads
< this value, all of
< these new-line
< characters will be
< preserved."
---
> "This is another
> really long CHANGED string.
> It is presented in
> YAML \"literal\"
> format.  When a
> YAML parser reads
> this value, all of
> these new-line
> characters will be
> preserved."
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--verbose"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_diff_array_by_default(self, script_runner, tmp_path_factory):
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
        assert self.diff_array_defaults == result.stdout

    def test_diff_array_by_position(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_array_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_array_content)

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--arrays=position"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert self.diff_array_defaults == result.stdout

    def test_diff_array_by_value(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, self.lhs_array_content)
        rhs_file = create_temp_yaml_file(tmp_path_factory, self.rhs_array_content)
        stdout_content = """a [0]
> "zeta"

a [5]
> "gamma"

c [6]
< "delta"
---
> "phi"

d [4]
< "delta"

d [8]
< "alpha"

d [9]
< "theta"
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--arrays=value"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_diff_add_array_element(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
- 0
- 1
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
- 0
- 1
- 2
""")
        stdout_content = """a [2]
> 2
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
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_diff_add_aoh_element_default(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
- id: 0
  name: zero
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
- id: 0
  name: zero
- id: 1
  name: uno
""")
        stdout_content = """a [1]
> {"id": 1, "name": "uno"}
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
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_diff_add_aoh_element_key(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
- id: 1
  name: uno
- id: 0
  name: zero
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
- id: 0
  name: zero
- id: 2
  name: dos
- id: 1
  name: uno
""")
        stdout_content = """a [1]
> {"id": 2, "name": "dos"}
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--aoh=key"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_diff_delete_aoh_element_default(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
- id: 0
  name: zero
- id: 1
  name: uno
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
- id: 0
  name: zero
""")
        stdout_content = """d [1]
< {"id": 1, "name": "uno"}
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
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_diff_delete_aoh_element_key(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
- id: 0
  name: zero
- id: 1
  name: uno
- id: 2
  name: dos
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
- id: 1
  name: uno
- id: 0
  name: zero
""")
        stdout_content = """d [2]
< {"id": 2, "name": "dos"}
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--aoh=key"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_diff_unkeyed_aoh_elements(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
- id: 1
  name: uno
- id: 0
  name: zero
- name: tres
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
- id: 0
  name: zero
- name: dos
- id: 1
  name: uno
""")
        stdout_content = """a [1]
> {"name": "dos"}

d [2]
< {"name": "tres"}
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--aoh=key"
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_diff_custom_aoh_keyed_elements(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
products:
  - product: doodad
    sku: 0-000-0001-0
    availability:
      start:
        date: 2020-10-10
        time: 08:00
      stop:
        date: 2020-10-29
        time: 17:00
    dimensions:
      width: 5
      height: 5
      depth: 5
      weight: 10
  - product: dumdow
    sku: 0-000-0002-0
    availability:
      start:
        date: 2020-10-23
        time: 08:00
      stop:
        date: 2020-11-23
        time: 17:00
    dimensions:
      width: 3
      height: 3
      depth: 3
      weight: 27
  - product: doohickey
    sku: 0-000-0003-0
    availability:
      start:
        date: 2020-08-01
        time: 10:00
      stop:
        date: 2020-09-25
        time: 10:00
    dimensions:
      width: 1
      height: 2
      depth: 3
      weight: 4
  - product: widget
    sku: 0-000-0004-0
    availability:
      start:
        date: 2020-01-01
        time: 12:00
      stop:
        date: 2020-01-01
        time: 16:00
    dimensions:
      width: 9
      height: 10
      depth: 1
      weight: 4
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
products:
  - sku: 0-000-0001-0
    availability:
      start:
        date: 2020-10-10
        time: 08:00
      stop:
        date: 2020-10-29
        time: 17:00
    dimensions:
      width: 5
      height: 5
      depth: 5
      weight: 10
  - sku: 0-000-0002-0
    availability:
      start:
        date: 2020-10-23
        time: 08:00
      stop:
        date: 2020-11-23
        time: 17:00
    dimensions:
      width: 4
      height: 3
      depth: 3
      weight: 27
  - dimensions:
      width: 9
      height: 10
      depth: 1
      weight: 4
    sku: 0-000-0004-0
    availability:
      start:
        date: 2020-01-01
        time: 12:00
      stop:
        date: 2020-01-01
        time: 16:00
  - product: doohickey
    availability:
      stop:
        date: 2020-09-25
        time: 10:00
      start:
        date: 2020-08-01
        time: 10:00
    dimensions:
      weight: 4
      width: 1
      depth: 3
      height: 2
""")
        config_file = create_temp_yaml_file(tmp_path_factory, """[rules]
/products = key

[keys]
/products[product=doohickey] = product
""")
        stdout_content = """c products[0]
< {"product": "doodad", "sku": "0-000-0001-0", "availability": {"start": {"date": "2020-10-10", "time": "08:00"}, "stop": {"date": "2020-10-29", "time": "17:00"}}, "dimensions": {"width": 5, "height": 5, "depth": 5, "weight": 10}}
---
> {"sku": "0-000-0001-0", "availability": {"start": {"date": "2020-10-10", "time": "08:00"}, "stop": {"date": "2020-10-29", "time": "17:00"}}, "dimensions": {"width": 5, "height": 5, "depth": 5, "weight": 10}}

c products[1]
< {"product": "dumdow", "sku": "0-000-0002-0", "availability": {"start": {"date": "2020-10-23", "time": "08:00"}, "stop": {"date": "2020-11-23", "time": "17:00"}}, "dimensions": {"width": 3, "height": 3, "depth": 3, "weight": 27}}
---
> {"sku": "0-000-0002-0", "availability": {"start": {"date": "2020-10-23", "time": "08:00"}, "stop": {"date": "2020-11-23", "time": "17:00"}}, "dimensions": {"width": 4, "height": 3, "depth": 3, "weight": 27}}

c products[2]
< {"product": "doohickey", "sku": "0-000-0003-0", "availability": {"start": {"date": "2020-08-01", "time": "10:00"}, "stop": {"date": "2020-09-25", "time": "10:00"}}, "dimensions": {"width": 1, "height": 2, "depth": 3, "weight": 4}}
---
> {"product": "doohickey", "availability": {"stop": {"date": "2020-09-25", "time": "10:00"}, "start": {"date": "2020-08-01", "time": "10:00"}}, "dimensions": {"weight": 4, "width": 1, "depth": 3, "height": 2}}

c products[3]
< {"product": "widget", "sku": "0-000-0004-0", "availability": {"start": {"date": "2020-01-01", "time": "12:00"}, "stop": {"date": "2020-01-01", "time": "16:00"}}, "dimensions": {"width": 9, "height": 10, "depth": 1, "weight": 4}}
---
> {"dimensions": {"width": 9, "height": 10, "depth": 1, "weight": 4}, "sku": "0-000-0004-0", "availability": {"start": {"date": "2020-01-01", "time": "12:00"}, "stop": {"date": "2020-01-01", "time": "16:00"}}}
"""

        # DEBUG
        # print("LHS File:  {}".format(lhs_file))
        # print("RHS File:  {}".format(rhs_file))
        # print("Expected Output:")
        # print(merged_yaml_content)

        result = script_runner.run(
            self.command
            , "--config={}".format(config_file)
            , lhs_file
            , rhs_file)
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

    def test_comprehensive_tag_diffs(self, script_runner, tmp_path_factory):
        lhs_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &one One
  - &two !tag_two Two
  - &three !tag_three Three

hash_one:
  key_one: *one
  key_two: *two
  key_three: *three
  *one : *two
  *two : *one
  *three : *three

hash_two:
  key_one: *one
  key_two: *two
  *one : *two
  *two : *one
  *three : *three
""")
        rhs_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &one !tag_one One
  - &two Two
  - &three !tag_tres Three

hash_one:
  key_one: *one
  key_two: *two
  key_three: *three
  *one : *two
  *two : *one
  *three : *three

hash_two: !example
  key_one: *one
  key_two: *two
  *one : *two
  *two : *one
  *three : *three
""")
        stdout_content = """c aliases[0]
< "One"
---
> !tag_one "One"

c aliases[1]
< !tag_two "Two"
---
> "Two"

c aliases[2]
< !tag_three "Three"
---
> !tag_tres "Three"

c hash_one.key_one
< "One"
---
> !tag_one "One"

a hash_one.One !tag_one
> "Two"

a hash_one.Two
> !tag_one "One"

a hash_one.Three !tag_tres
> !tag_tres "Three"

c hash_one.key_two
< !tag_two "Two"
---
> "Two"

c hash_one.key_three
< !tag_three "Three"
---
> !tag_tres "Three"

d hash_one.One
< !tag_two "Two"

d hash_one.Two !tag_two
< "One"

d hash_one.Three !tag_three
< !tag_three "Three"

a hash_two !example
> {"key_one": "One", "key_two": "Two", "One": "Two", "Two": "One", "Three": "Three"}

d hash_two
< {"key_one": "One", "key_two": "Two", "One": "Two", "Two": "One", "Three": "Three"}
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
        assert not result.success, result.stderr
        assert stdout_content == result.stdout

