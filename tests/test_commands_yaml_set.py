import pytest

from tests.conftest import create_temp_yaml_file, requireseyaml, old_eyaml_keys


class Test_yaml_set():
    """Tests for the yaml-set command-line interface."""
    command = "yaml-set"

    def test_no_options(self, script_runner):
        result = script_runner.run(self.command)
        assert not result.success, result.stderr
        assert "the following arguments are required: -g/--change" in result.stderr

    def test_no_input_file(self, script_runner):
        result = script_runner.run(self.command, "--nostdin", "--change='/test'")
        assert not result.success, result.stderr
        assert "There must be a YAML_FILE or STDIN document" in result.stderr

    def test_no_input_param(self, script_runner):
        result = script_runner.run(self.command, "--change='/test'", "no-such-file")
        assert not result.success, result.stderr
        assert "Exactly one of the following must be set:" in result.stderr

    def test_bad_yaml_file(self, script_runner):
        result = script_runner.run(self.command, "--change='/test'", "--random=1", "no-such-file")
        assert not result.success, result.stderr
        assert "File not found:" in result.stderr

    def test_identical_saveto_change_error(self, script_runner):
        result = script_runner.run(self.command, "--change='/test'", "--random=1", "--saveto='/test'", "no-such-file")
        assert not result.success, result.stderr
        assert "Impossible to save the old value to the same YAML Path as the new value!" in result.stderr

    def test_insufficient_randomness(self, script_runner):
        result = script_runner.run(self.command, "--change='/test'", "--random=1", "--random-from=A", "no-such-file")
        assert not result.success, result.stderr
        assert "The pool of random CHARS must have at least 2 characters" in result.stderr

    def test_bad_privatekey(self, script_runner):
        result = script_runner.run(self.command, "--change='/test'", "--random=1", "--privatekey=no-such-file", "no-such-file")
        assert not result.success, result.stderr
        assert "EYAML private key is not a readable file" in result.stderr

    def test_bad_publickey(self, script_runner):
        result = script_runner.run(self.command, "--change='/test'", "--random=1", "--publickey=no-such-file", "no-such-file")
        assert not result.success, result.stderr
        assert "EYAML public key is not a readable file" in result.stderr

    def test_no_dual_stdin(self, script_runner):
        result = script_runner.run(self.command, "--change='/test'", "--stdin", "-")
        assert not result.success, result.stderr
        assert "Impossible to read both document and replacement value from STDIN" in result.stderr

    def test_no_backup_stdin(self, script_runner):
        result = script_runner.run(
            self.command, "--change='/test'", "--backup", "-")
        assert not result.success, result.stderr
        assert "applies only when reading from a file" in result.stderr

    def test_bad_data_type_optional(self, script_runner, tmp_path_factory):
        yaml_file = create_temp_yaml_file(tmp_path_factory, """---
boolean: false
""")
        result = script_runner.run(
            self.command, "--change=/boolean", "--value=NOT_BOOLEAN",
            "--format=boolean", yaml_file)
        assert not result.success, result.stderr
        assert "Impossible to write 'NOT_BOOLEAN' as boolean." in result.stderr

    def test_bad_data_type_mandatory(self, script_runner, tmp_path_factory):
        yaml_file = create_temp_yaml_file(tmp_path_factory, """---
boolean: false
""")
        result = script_runner.run(
            self.command, "--change=/boolean", "--value=NOT_BOOLEAN",
            "--format=boolean", "--mustexist", yaml_file)
        assert not result.success, result.stderr
        assert "Impossible to write 'NOT_BOOLEAN' as boolean." in result.stderr

    def test_input_by_value(self, script_runner, tmp_path_factory):
        import re

        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--change=/key", "--value=abc", yaml_file)
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

    @requireseyaml
    def test_missing_key(self, script_runner, tmp_path_factory, old_eyaml_keys):
        content = """---
        encrypted: ENC[PKCS7,MIIx...blahblahblah...==]
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--change=encrypted",
            "--random=1",
            "--check=n/a",
            "--privatekey={}".format(old_eyaml_keys[0]),
            yaml_file
        )
        assert not result.success, result.stderr
        assert "Neither or both private and public EYAML keys must be set" in result.stderr

        result = script_runner.run(
            self.command,
            "--change=encrypted",
            "--random=1",
            "--check=n/a",
            "--publickey={}".format(old_eyaml_keys[1]),
            yaml_file
        )
        assert not result.success, result.stderr
        assert "Neither or both private and public EYAML keys must be set" in result.stderr

    @requireseyaml
    def test_bad_decryption(self, script_runner, tmp_path_factory, old_eyaml_keys):
        content = """---
        encrypted: ENC[PKCS7,MIIx...broken-on-purpose...==]
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--change=encrypted",
            "--random=1",
            "--check=n/a",
            "--privatekey={}".format(old_eyaml_keys[0]),
            "--publickey={}".format(old_eyaml_keys[1]),
            yaml_file
        )
        assert not result.success, result.stderr
        assert "Unable to decrypt value!" in result.stderr

    def test_bad_value_check(self, script_runner, tmp_path_factory):
        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--change=key",
            "--random=1",
            "--check=abc",
            yaml_file
        )
        assert not result.success, result.stderr
        assert "does not match the check value" in result.stderr

    def test_cannot_save_multiple_matches(self, script_runner, tmp_path_factory):
        content = """---
        key1: value1
        key2: value2
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--change=/[.^key]",
            "--random=1",
            "--saveto=/backup",
            yaml_file
        )
        assert not result.success, result.stderr
        assert "It is impossible to meaningly save more than one" in result.stderr

    def test_save_old_plain_value(self, script_runner, tmp_path_factory):
        import re

        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--change=key",
            "--value=new",
            "--saveto=backup",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert re.findall(r"^backup:\s+value$", filedat, re.M), filedat

    def test_save_old_crypt_value(self, script_runner, tmp_path_factory):
        import re

        content = """---
        encrypted: >
          ENC[PKCS7,MIIB...]
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--change=encrypted",
            "--value=now_plaintext",
            "--saveto=backup",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert re.findall(r"^backup:\s+>$", filedat, re.M), filedat

    def test_broken_change(self, script_runner, tmp_path_factory):
        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--change=[0]",
            "--random=1",
            yaml_file
        )
        assert not result.success, result.stderr
        assert "Cannot add" in result.stderr

    def test_broken_saveto(self, script_runner, tmp_path_factory):
        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--change=key",
            "--random=1",
            "--saveto=[2]",
            yaml_file
        )
        assert not result.success, result.stderr
        assert "Cannot add" in result.stderr

    @requireseyaml
    def test_bad_decryption(self, script_runner, tmp_path_factory, old_eyaml_keys):
        content = """---
        encrypted: ENC[PKCS7,MIIx...broken-on-purpose...==]
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--change=encrypted",
            "--random=1",
            "--check=n/a",
            "--privatekey={}".format(old_eyaml_keys[0]),
            "--publickey={}".format(old_eyaml_keys[1]),
            yaml_file
        )
        assert not result.success, result.stderr
        assert "Unable to decrypt value!" in result.stderr

    @requireseyaml
    def test_good_encryption(self, script_runner, tmp_path_factory, old_eyaml_keys):
        import re

        content = """---
        key: >
          old
          multiline
          value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--change=key",
            "--value=now_encrypted",
            "--eyamlcrypt",
            "--privatekey={}".format(old_eyaml_keys[0]),
            "--publickey={}".format(old_eyaml_keys[1]),
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert re.findall(r"\nkey:\s+>\n\s{2}ENC\[.+\n", filedat), filedat

    @requireseyaml
    def test_bad_crypt_path(self, script_runner, tmp_path_factory, old_eyaml_keys):
        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--change=[0]",
            "--random=1",
            "--eyamlcrypt",
            "--privatekey={}".format(old_eyaml_keys[0]),
            "--publickey={}".format(old_eyaml_keys[1]),
            yaml_file
        )
        assert not result.success, result.stderr
        assert "Cannot add" in result.stderr

    def test_bad_eyaml_command(self, script_runner, tmp_path_factory):
        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--change=key",
            "--random=1",
            "--eyamlcrypt",
            "--eyaml=/does/not/exist/on-most/systems",
            yaml_file
        )
        assert not result.success, result.stderr
        assert "The eyaml binary is not executable" in result.stderr

    def test_backup_file(self, script_runner, tmp_path_factory):
        import os

        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        backup_file = yaml_file + ".bak"
        result = script_runner.run(
            self.command,
            "--change=key",
            "--random=1",
            "--backup",
            yaml_file
        )
        assert result.success, result.stderr
        assert os.path.isfile(backup_file)

        with open(backup_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == content

    def test_replace_backup_file(self, script_runner, tmp_path_factory):
        import os

        content = """---
        key: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        backup_file = yaml_file + ".bak"
        with open(backup_file, 'w') as fhnd:
            fhnd.write(content + "\nkey2: value2")

        result = script_runner.run(
            self.command,
            "--change=key",
            "--random=1",
            "--backup",
            yaml_file
        )
        assert result.success, result.stderr
        assert os.path.isfile(backup_file)

        with open(backup_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == content

    def test_nonref_changes(self, script_runner, tmp_path_factory):
        yamlin = """---
somestring:
  string:
    someotherstring: true
otherstring:
  default:
    config:
      deploy:
        me: true
"""
        yamlout = """---
somestring:
  string:
    someotherstring: true
otherstring:
  default:
    config:
      deploy:
        me: set_value
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=otherstring.default.config.deploy.me",
            "--value=set_value",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == yamlout

    @pytest.mark.xfail(strict=True, reason="https://sourceforge.net/p/ruamel-yaml/tickets/351/")
    def test_commented_aliased_parent_hash(self, script_runner, tmp_path_factory):
        yamlin = """---
aliases:
  - &key_alias hash

*key_alias :
  # Comment
  key: value
"""
        yamlout = """---
aliases:
  - &key_alias hash

*key_alias :
  # Comment
  key: new value
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=/hash/key",
            "--value=new value",
            "--backup",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == yamlout

    def test_set_value_in_empty_file(
        self, script_runner, tmp_path_factory
    ):
        yaml_file = create_temp_yaml_file(tmp_path_factory, "")
        result_content = """---
some:
  key:
    to: nowhere
"""

        result = script_runner.run(
            self.command
            , "--change=some.key.to"
            , "--value=nowhere"
            , yaml_file)
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == result_content

    def test_set_value_in_json_file(
        self, script_runner, tmp_path_factory
    ):
        yaml_file = create_temp_yaml_file(tmp_path_factory, '{"key": "value"}')
        result_content = '{"key": "changed"}'

        result = script_runner.run(
            self.command
            , "--change=key"
            , "--value=changed"
            , yaml_file)
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == result_content

    def test_stdin_to_stdout_yaml(self, script_runner):
        import subprocess

        stdin_content = """---
hash:
  sub_hash:
    key1: value 1.1
    key2: value 2.1
  another_sub_hash:
    key1: value 1.2
    key2: value 2.2
array:
  - element 1
  - element 2
"""

        stdout_content = """---
hash:
  sub_hash:
    key1: CHANGE EVERYTHING!
    key2: CHANGE EVERYTHING!
  another_sub_hash:
    key1: CHANGE EVERYTHING!
    key2: CHANGE EVERYTHING!
array:
  - CHANGE EVERYTHING!
  - CHANGE EVERYTHING!
"""

        result = subprocess.run(
            [self.command
            , "--change=**"
            , "--value=CHANGE EVERYTHING!"
            , "-"]
            , stdout=subprocess.PIPE
            , input=stdin_content
            , universal_newlines=True
        )

        # DEBUG
        # print("Expected:")
        # print(merged_yaml_content)
        # print("Got:")
        # print(result.stdout)

        assert 0 == result.returncode, result.stderr
        assert stdout_content == result.stdout

    def test_stdin_to_stdout_json(self, script_runner):
        import subprocess

        stdin_content = """{"hash": {"sub_hash": {"key1": "value 1.1", "key2": "value 2.1"}, "another_sub_hash": {"key1": "value 1.2", "key2": "value 2.2"}}, "array": ["element 1", "element 2"]}"""

        stdout_content = """{"hash": {"sub_hash": {"key1": "CHANGE EVERYTHING!", "key2": "CHANGE EVERYTHING!"}, "another_sub_hash": {"key1": "CHANGE EVERYTHING!", "key2": "CHANGE EVERYTHING!"}}, "array": ["CHANGE EVERYTHING!", "CHANGE EVERYTHING!"]}"""

        result = subprocess.run(
            [self.command
            , "--change=**"
            , "--value=CHANGE EVERYTHING!"]
            , stdout=subprocess.PIPE
            , input=stdin_content
            , universal_newlines=True
        )

        # DEBUG
        # print("Expected:")
        # print(merged_yaml_content)
        # print("Got:")
        # print(result.stdout)

        assert 0 == result.returncode, result.stderr
        assert stdout_content == result.stdout

    def test_delete_key(self, script_runner, tmp_path_factory):
        yamlin = """---
array:
  - 0
  - 1
  - 2
  - 3

array_of_arrays:
  - - 0.0
    - 0.1
    - 0.2
  - - 1.0
    - 1.1
    - 1.2
  - - 2.0
    - 2.1
    - 2.2
  - - 3.0
    - 3.1
    - 3.2

array_of_hashes:
  - id: 0
    name: zero
  - id: 1
    name: one
  - id: 2
    name: two
  - id: 3
    name: three
"""
        yamlout = """---
array_of_arrays:
  -   - 0.0
      - 0.1
      - 0.2
  -   - 1.0
      - 1.1
      - 1.2
  -   - 2.0
      - 2.1
      - 2.2
  -   - 3.0
      - 3.1
      - 3.2

array_of_hashes:
  - id: 0
    name: zero
  - id: 1
    name: one
  - id: 2
    name: two
  - id: 3
    name: three
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=/array",
            "--delete",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == yamlout

    def test_delete_from_collectors(self, script_runner, tmp_path_factory):
        yamlin = """---
array:
  - 0
  - 1
  - 2
  - 3

array_of_arrays:
  - - 0.0
    - 0.1
    - 0.2
  - - 1.0
    - 1.1
    - 1.2
  - - 2.0
    - 2.1
    - 2.2
  - - 3.0
    - 3.1
    - 3.2

array_of_hashes:
  - id: 0
    name: zero
  - id: 1
    name: one
  - id: 2
    name: two
  - id: 3
    name: three
"""
        yamlout = """---
array:
  - 1
  - 2
  - 3

array_of_arrays:
  -   - 0.0
      - 0.1
      - 0.2
  - []
  -   - 2.0
      - 2.1
      - 2.2
  -   - 3.0
      - 3.1
      - 3.2

array_of_hashes:
  - id: 0
    name: zero
  - id: 1
    name: one
  - id: 3
    name: three
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=(/array[0])+(/array_of_arrays[1])+(/array_of_hashes[2])",
            "--delete",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == yamlout

    def test_delete_from_nested_collectors(self, script_runner, tmp_path_factory):
        yamlin = """---
array:
  - 0
  - 1
  - 2
  - 3

array_of_arrays:
  - - 0.0
    - 0.1
    - 0.2
  - - 1.0
    - 1.1
    - 1.2
  - - 2.0
    - 2.1
    - 2.2
  - - 3.0
    - 3.1
    - 3.2

array_of_hashes:
  - id: 0
    name: zero
  - id: 1
    name: one
  - id: 2
    name: two
  - id: 3
    name: three
"""
        yamlout = """---
array:
  - 1
  - 2
  - 3

array_of_arrays:
  -   - 0.0
      - 0.1
      - 0.2
  - []
  -   - 2.0
      - 2.1
      - 2.2
  -   - 3.0
      - 3.1
      - 3.2

array_of_hashes:
  - id: 0
    name: zero
  - id: 1
    name: one
  - id: 3
    name: three
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=((/array[0])+(/array_of_arrays[1])+(/array_of_hashes[2]))",
            "--delete",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == yamlout

    def test_delete_from_too_too_nested_collectors(self, script_runner, tmp_path_factory):
        yamlin = """---
array:
  - 0
  - 1
  - 2
  - 3

array_of_arrays:
  - - 0.0
    - 0.1
    - 0.2
  - - 1.0
    - 1.1
    - 1.2
  - - 2.0
    - 2.1
    - 2.2
  - - 3.0
    - 3.1
    - 3.2

array_of_hashes:
  - id: 0
    name: zero
  - id: 1
    name: one
  - id: 2
    name: two
  - id: 3
    name: three
"""
        yamlout = """---
array:
  - 1
  - 2
  - 3

array_of_arrays:
  -   - 0.0
      - 0.1
      - 0.2
  - []
  -   - 2.0
      - 2.1
      - 2.2
  -   - 3.0
      - 3.1
      - 3.2

array_of_hashes:
  - id: 0
    name: zero
  - id: 1
    name: one
  - id: 3
    name: three
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=(((/array[0])+(/array_of_arrays[1])+(/array_of_hashes[2])))",
            "--delete",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == yamlout

    def test_refuse_delete_document(self, script_runner, tmp_path_factory):
        content = """---
key: value
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--change=/",
            "--delete",
            yaml_file
        )
        assert not result.success, result.stderr
        assert "Refusing to delete" in result.stderr

    def test_rename_anchor_explicit(self, script_runner, tmp_path_factory):
        yamlin = """---
aliases:
  - &old_anchor Some string
key: *old_anchor
"""
        yamlout = """---
aliases:
  - &new_anchor Some string
key: *new_anchor
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=aliases[&old_anchor]",
            "--aliasof=aliases[&old_anchor]",
            "--anchor=new_anchor",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == yamlout

    def test_rename_anchor_implicit(self, script_runner, tmp_path_factory):
        yamlin = """---
aliases:
  - &old_anchor Some string
key: *old_anchor
"""
        yamlout = """---
aliases:
  - &new_anchor Some string
key: *new_anchor
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=aliases[&old_anchor]",
            "--anchor=new_anchor",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == yamlout

    def test_auto_anchor(self, script_runner, tmp_path_factory):
        yamlin = """---
some_key: its value
a_hash:
  a_key: A value
"""
        yamlout = """---
some_key: &some_key its value
a_hash:
  a_key: *some_key
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=a_hash.a_key",
            "--aliasof=some_key",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == yamlout

    def test_too_many_nodes_to_alias(self, script_runner, tmp_path_factory):
        yamlin = """---
aliases:
  - &valid_anchor Has validity
  - &another_valid_anchor Also has validity
hash:
  concete_key: Concrete value
  aliased_key: *valid_anchor
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=hash.new_key",
            "--aliasof=aliases.*",
            yaml_file
        )
        assert not result.success, result.stderr
        assert "impossible to Alias more than one Anchor at a time" in result.stderr

    def test_auto_anchor_conflicted(self, script_runner, tmp_path_factory):
        yamlin = """---
a_key: &name_taken Conflicting anchored value
another_key: its value
a_hash:
  a_key: A value
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=a_hash.a_key",
            "--aliasof=another_key",
            "--anchor=name_taken",
            yaml_file
        )
        assert not result.success, result.stderr
        assert "Anchor names must be unique within YAML documents" in result.stderr

    def test_auto_anchor_deconflicted(self, script_runner, tmp_path_factory):
        yamlin = """---
silly_key: &some_key Conflicting anchored value
another_silly_key: &some_key001 Yet another conflict
some_key: its value
a_hash:
  a_key: A value
"""
        yamlout = """---
silly_key: &some_key Conflicting anchored value
another_silly_key: &some_key001 Yet another conflict
some_key: &some_key002 its value
a_hash:
  a_key: *some_key002
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=a_hash.a_key",
            "--aliasof=some_key",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == yamlout

    def test_reuse_anchor(self, script_runner, tmp_path_factory):
        yamlin = """---
some_key: &has_anchor its value
a_hash:
  a_key: A value
"""
        yamlout = """---
some_key: &has_anchor its value
a_hash:
  a_key: *has_anchor
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=a_hash.a_key",
            "--aliasof=some_key",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == yamlout

    def test_assign_docroot_tag(self, script_runner, tmp_path_factory):
        yamlin = """---
key: value
"""
        yamlout = """--- !something
key: value
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=/",
            "--tag=!something",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == yamlout

    def test_assign_anchorless_tag(self, script_runner, tmp_path_factory):
        yamlin = """---
key: value
"""
        yamlout = """---
key: !something value
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=key",
            "--tag=!something",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == yamlout

    def test_assign_original_anchored_tag(self, script_runner, tmp_path_factory):
        yamlin = """---
aliases:
  - &anchored_scalar This (scalar) string is Anchored.
key: *anchored_scalar
"""
        yamlout = """---
aliases:
  - &anchored_scalar !some_tag This (scalar) string is Anchored.
key: *anchored_scalar
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=aliases[&anchored_scalar]",
            "--tag=!some_tag",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == yamlout

    def test_assign_original_aliased_tag(self, script_runner, tmp_path_factory):
        yamlin = """---
aliases:
  - &anchored_scalar This (scalar) string is Anchored.
key: *anchored_scalar
"""
        yamlout = """---
aliases:
  - &anchored_scalar !some_tag This (scalar) string is Anchored.
key: *anchored_scalar
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=key",
            "--tag=some_tag",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == yamlout

    def test_assign_null(self, script_runner, tmp_path_factory):
        yamlin = """---
ingress_key: Preceding value
concrete_key: Old value
egress_key: Following value
"""
        yamlout = """---
ingress_key: Preceding value
concrete_key:
egress_key: Following value
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, yamlin)
        result = script_runner.run(
            self.command,
            "--change=concrete_key",
            "--null",
            yaml_file
        )
        assert result.success, result.stderr

        with open(yaml_file, 'r') as fhnd:
            filedat = fhnd.read()
        assert filedat == yamlout
