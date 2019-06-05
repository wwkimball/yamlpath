import pytest

from tests.conftest import create_temp_yaml_file


class Test_yaml_paths():
    """Tests the yaml-paths command-line interface."""
    command = "yaml-paths"

    def test_no_options(self, script_runner):
        result = script_runner.run(self.command)
        assert not result.success, result.stderr
        assert "the following arguments are required: -s/--search, YAML_FILE" in result.stderr

    def test_no_input_file(self, script_runner):
        result = script_runner.run(self.command, "--search=%abc")
        assert not result.success, result.stderr
        assert "the following arguments are required: YAML_FILE" in result.stderr

    def test_bad_input_file(self, script_runner):
        result = script_runner.run(self.command, "--search=%abc", "no-such-file")
        assert not result.success, result.stderr
        assert "File not found:" in result.stderr

    def test_no_query(self, script_runner, tmp_path_factory):
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, yaml_file)
        assert not result.success, result.stderr
        assert "the following arguments are required: -s/--search" in result.stderr

    def test_yaml_parsing_error(self, script_runner, imparsible_yaml_file):
        result = script_runner.run(
            self.command, "--search=%abc", imparsible_yaml_file
        )
        assert not result.success, result.stderr
        assert "YAML parsing error" in result.stderr

    def test_yaml_syntax_error(self, script_runner, badsyntax_yaml_file):
        result = script_runner.run(
            self.command, "--search=%abc", badsyntax_yaml_file
        )
        assert not result.success, result.stderr
        assert "YAML syntax error" in result.stderr

    def test_yaml_composition_error(self, script_runner, badcmp_yaml_file):
        result = script_runner.run(
            self.command, "--search=%abc", badcmp_yaml_file
        )
        assert not result.success, result.stderr
        assert "YAML composition error" in result.stderr

    def test_bad_privatekey(self, script_runner, tmp_path_factory):
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--search=%abc", "--privatekey=no-such-file", yaml_file
        )
        assert not result.success, result.stderr
        assert "EYAML private key is not a readable file" in result.stderr

    def test_bad_publickey(self, script_runner, tmp_path_factory):
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--search=%abc", "--publickey=no-such-file", yaml_file
        )
        assert not result.success, result.stderr
        assert "EYAML public key is not a readable file" in result.stderr

    def test_simple_array_result(self, script_runner, tmp_path_factory):
        content = """---
        - element 1
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--search", "^element", yaml_file
        )
        assert result.success, result.stderr
        assert "/[0]\n" == result.stdout

    def test_nonrepeating_value_anchored_array(self, script_runner, tmp_path_factory):
        content = """---
        aliases:
          - &anchor1 element 1

        array:
          - *anchor1
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--search", "^element", yaml_file
        )
        assert result.success, result.stderr
        assert "/aliases[&anchor1]\n" == result.stdout

    def test_nonrepeating_anchor_name_in_array(self, script_runner, tmp_path_factory):
        content = """---
        aliases:
          - &anchor1 element 1

        array:
          - *anchor1
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--anchors", "--search", "^anchor", yaml_file
        )
        assert result.success, result.stderr
        assert "/aliases[&anchor1]\n" == result.stdout

    def test_nonrepeating_subarray(self, script_runner, tmp_path_factory):
        content = """---
        array:
          -
            - subvalue
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--search", "=subvalue", yaml_file
        )
        assert result.success, result.stderr
        assert "/array[0][0]\n" == result.stdout

    def test_simple_hash_result(self, script_runner, tmp_path_factory):
        content = """---
        parent:
          child: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--search", "=value", yaml_file
        )
        assert result.success, result.stderr
        assert "/parent/child\n" == result.stdout

    def test_hash_merge_anchor(self, script_runner, tmp_path_factory):
        content = """---
        anchored_hash: &anchoredHash
          key: value
        more_hash:
          <<: *anchoredHash
          more: values
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--keynames", "--anchors",
            "--search", "^anchored", yaml_file
        )
        assert result.success, result.stderr
        assert "/anchored_hash\n" == result.stdout

    def test_anchored_hash_value(self, script_runner, tmp_path_factory):
        content = """---
        hash:
          key: &anchoredValue anchored_value
          more: *anchoredValue
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--anchors",
            "--search", "^anchored", yaml_file
        )
        assert result.success, result.stderr
        assert "/hash/key\n" == result.stdout

    def test_duplicate_hash_value_anchor(self, script_runner, tmp_path_factory):
        content = """---
        aliases:
          - &anchor element 1
        hash:
          child1: *anchor
          subhash:
            subchild1: *anchor
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--duplicates",
            "--search", "^element", yaml_file
        )
        assert result.success, result.stderr
        assert "/aliases[&anchor]\n/hash/child1\n/hash/subhash/subchild1\n" == result.stdout

    # FIXME: This should work...
    @pytest.mark.xfail
    def test_simple_hash_anchor(self, script_runner, tmp_path_factory):
        content = """---
        parent: &anchored
          child: value
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--anchors", "--search", "=anchored", yaml_file
        )
        assert result.success, result.stderr
        assert "/parent\n" == result.stdout

    # FIXME: This should also work...
    @pytest.mark.xfail
    def test_hash_anchored_key(self, script_runner, tmp_path_factory):
        content = """---
        anchorKeys:
          &keyOne aliasOne: 11A1
          &keyTwo aliasTwo: 22B2
          &recursiveAnchorKey subjectKey: *recursiveAnchorKey

        hash:
          *keyOne :
            subval: 1.1
          *keyTwo :
            subval: 2.2
          *recursiveAnchorKey :
            subval: 3.3
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--onlykeynames",
            "--search", "=aliasOne", yaml_file
        )
        assert result.success, result.stderr
        assert "/anchorKeys/aliasOne\n" == result.stdout

    def test_hash_nonduplicate_anchor_name_search(self, script_runner, tmp_path_factory):
        content = """---
        anchorKeys:
          &keyOne aliasOne: 11A1
          &keyTwo aliasTwo: 22B2
          &recursiveAnchorKey subjectKey: *recursiveAnchorKey

        hash:
          *keyOne :
            subval: 1.1
          *keyTwo :
            subval: 2.2
          *recursiveAnchorKey :
            subval: 3.3
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--anchors", "--keynames",
            "--search", "=recursiveAnchorKey", yaml_file
        )
        assert result.success, result.stderr
        assert "/anchorKeys/subjectKey\n" == result.stdout

    def test_hash_duplicate_anchor_name_search(self, script_runner, tmp_path_factory):
        content = """---
        anchorKeys:
          &keyOne aliasOne: 11A1
          &keyTwo aliasTwo: 22B2
          &recursiveAnchorKey subjectKey: *recursiveAnchorKey

        hash:
          *keyOne :
            subval: 1.1
          *keyTwo :
            subval: 2.2
          *recursiveAnchorKey :
            subval: 3.3
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--pathsep=/", "--anchors", "--keynames",
            "--duplicates", "--search", "=recursiveAnchorKey", yaml_file
        )
        assert result.success, result.stderr
        assert "/anchorKeys/subjectKey\n/hash/subjectKey\n" == result.stdout

    def test_empty_search_expression(self, script_runner, tmp_path_factory):
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--search=", yaml_file
        )
        assert not result.success, result.stderr
        assert "" in result.stdout

    def test_bad_expression(self, script_runner, tmp_path_factory):
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command, "--search=abc", yaml_file
        )
        assert not result.success, result.stderr
        assert "Invalid search expression" in result.stderr
