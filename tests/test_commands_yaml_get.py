import pytest

from tests.conftest import create_temp_yaml_file


class Test_yaml_get():
    """Tests for the yaml-get command-line interface."""
    command = "yaml-get"

    def test_no_options(self, script_runner):
        result = script_runner.run(self.command, "--nostdin")
        assert not result.success, result.stderr
        assert "the following arguments are required: -p/--query" in result.stderr

    def test_no_input_file(self, script_runner):
        result = script_runner.run(self.command, "--nostdin", "--query='/test'")
        assert not result.success, result.stderr
        assert "YAML_FILE must be set or be read from STDIN" in result.stderr

    def test_bad_input_file(self, script_runner):
        result = script_runner.run(self.command, "--query='/test'", "no-such-file")
        assert not result.success, result.stderr
        assert "File not found:" in result.stderr

    def test_no_query(self, script_runner, tmp_path_factory):
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, yaml_file)
        assert not result.success, result.stderr
        assert "the following arguments are required: -p/--query" in result.stderr

    def test_bad_privatekey(self, script_runner, tmp_path_factory):
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, "--query=aliases", "--privatekey=no-such-file", yaml_file)
        assert not result.success, result.stderr
        assert "EYAML private key is not a readable file" in result.stderr

    def test_bad_publickey(self, script_runner, tmp_path_factory):
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, "--query=aliases", "--publickey=no-such-file", yaml_file)
        assert not result.success, result.stderr
        assert "EYAML public key is not a readable file" in result.stderr

    def test_yaml_parsing_error(self, script_runner, imparsible_yaml_file):
        result = script_runner.run(self.command, "--query=/", imparsible_yaml_file)
        assert not result.success, result.stderr
        assert "YAML parsing error" in result.stderr

    def test_yaml_syntax_error(self, script_runner, badsyntax_yaml_file):
        result = script_runner.run(self.command, "--query=/", badsyntax_yaml_file)
        assert not result.success, result.stderr
        assert "YAML syntax error" in result.stderr

    def test_yaml_composition_error(self, script_runner, badcmp_yaml_file):
        result = script_runner.run(self.command, "--query=/", badcmp_yaml_file)
        assert not result.success, result.stderr
        assert "YAML composition error" in result.stderr

    def test_bad_yaml_path(self, script_runner, tmp_path_factory):
        content = """---
        aliases:
          - &plainScalar Plain scalar string
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, "--query=aliases[1]", yaml_file)
        assert not result.success, result.stderr
        assert "Required YAML Path does not match any nodes" in result.stderr

    def test_bad_eyaml_value(self, script_runner, tmp_path_factory):
        content = """---
        aliases:
          - &encryptedScalar >
            ENC[PKCS7,MIIx...broken-on-purpose...==]
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--query=aliases[&encryptedScalar]",
            "--eyaml=/does/not/exist-on-most/systems",
            yaml_file
        )
        assert not result.success, result.stderr
        assert "No accessible eyaml command" in result.stderr

    def test_recursive_yaml_anchor(self, script_runner, tmp_path_factory):
        content = """--- &recursive_this
hash:
  recursive_key: *recursive_this
"""
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(
            self.command,
            "--query=/hash",
            yaml_file
        )
        assert not result.success, result.stderr
        assert "contains an infinitely recursing" in result.stderr

    def test_query_anchor(self, script_runner, tmp_path_factory):
        content = """---
        aliases:
          - &plainScalar Plain scalar string
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, "--query=aliases[&plainScalar]", yaml_file)
        assert result.success, result.stderr
        assert "Plain scalar string" in result.stdout

    def test_query_list(self, script_runner, tmp_path_factory):
        content = """---
        aliases:
          - &plainScalar Plain scalar string
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, "--query=aliases", yaml_file)
        assert result.success, result.stderr
        assert '["Plain scalar string"]' in result.stdout

    def test_query_doc_from_stdin(
        self, script_runner, tmp_path_factory
    ):
        import subprocess

        yaml_file = """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
"""

        result = subprocess.run(
            [self.command
            , "--query=/hash/lhs_exclusive"
            , "-"]
            , stdout=subprocess.PIPE
            , input=yaml_file
            , universal_newlines=True
        )

        assert 0 == result.returncode, result.stderr
        assert "LHS exclusive\n" == result.stdout

    def test_get_every_data_type(self, script_runner, tmp_path_factory):
        # Contributed by https://github.com/AndydeCleyre
        content = """---
intthing: 6
floatthing: 6.8
yesthing: yes
nothing: no
truething: true
falsething: false
nullthing: null
nothingthing:
emptystring: ""
nullstring: "null"
        """

        # Note that true nulls are translated as "\x00" (hexadecimal NULL
        # control-characters).
        results = ["6", "6.8", "yes", "no", "True", "False", "\x00", "\x00", "", "null"]

        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, "--query=*", yaml_file)
        assert result.success, result.stderr

        match_index = 0
        for line in result.stdout.splitlines():
            assert line == results[match_index]
            match_index += 1

    def test_get_only_aoh_nodes_without_named_child(self, script_runner, tmp_path_factory):
        content = """---
items:
  - - alpha
    - bravo
    - charlie
  - - alpha
    - charlie
    - delta
  - - alpha
    - bravo
    - delta
  - - bravo
    - charlie
    - delta
"""
        results = [
            "alpha",
            "charlie",
            "delta"
        ]

        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, "--query=/items/*[!has_child(bravo)]*", yaml_file)
        assert result.success, result.stderr

        match_index = 0
        for line in result.stdout.splitlines():
            assert line == results[match_index]
            match_index += 1

    def test_get_only_aoh_nodes_with_named_child(self, script_runner, tmp_path_factory):
        content = """---
products:
  - name: something
    price: 0.99
    weight: 0.75
    recalled: false
  - name: other
    price: 9.99
    weight: 2.25
    dimensions:
      width: 1
      height: 1
      depth: 1
  - name: moar
    weight: 100
    dimensions:
      width: 100
      height: 100
      depth: 100
  - name: less
    price: 5
    dimensions:
      width: 5
      height: 5
  - name: bad
    price: 0
    weight: 4
    dimensions:
      width: 13
      height: 4
      depth: 7
    recalled: true
"""
        results = [
            "something",
            "bad",
        ]

        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, "--query=/products[has_child(recalled)]/name", yaml_file)
        assert result.success, result.stderr

        match_index = 0
        for line in result.stdout.splitlines():
            assert line == results[match_index]
            match_index += 1

    @pytest.mark.parametrize("query,output", [
        ("/items/*[!has_child(bravo)][2][parent(0)]", ['delta']),
        ("/items/*[!has_child(bravo)][2][parent()]", ['["alpha", "charlie", "delta"]']),
        ("/items/*[!has_child(bravo)][2][parent(2)]", ['[["alpha", "bravo", "charlie"], ["alpha", "charlie", "delta"], ["alpha", "bravo", "delta"], ["bravo", "charlie", "delta"]]']),
    ])
    def test_get_parent_nodes(self, script_runner, tmp_path_factory, query, output):
        content = """---
items:
  - - alpha
    - bravo
    - charlie
  - - alpha
    - charlie
    - delta
  - - alpha
    - bravo
    - delta
  - - bravo
    - charlie
    - delta
"""

        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, "--query={}".format(query), yaml_file)
        assert result.success, result.stderr

        match_index = 0
        for line in result.stdout.splitlines():
            assert line == output[match_index]
            match_index += 1

    @pytest.mark.parametrize("query,output", [
        ("svcs.*[name()]", ['coolserver', 'logsender']),
        ("svcs.*[enabled=false][parent()][name()]", ['logsender']),
        ("svcs[name()]", ['svcs']),
        ("indexes[.^Item][name()]", ['0', '1', '3']),
    ])
    def test_get_node_names(self, script_runner, tmp_path_factory, query, output):
        # Contributed by https://github.com/AndydeCleyre
        content = """---
svcs:
  coolserver:
    enabled: true
    exec: ./coolserver.py
  logsender:
    enabled: false
    exec: remote_syslog -D
indexes:
  - Item 1
  - Item 2
  - Disabled 3
  - Item 4
"""

        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        result = script_runner.run(self.command, "--query={}".format(query), yaml_file)
        assert result.success, result.stderr

        match_index = 0
        for line in result.stdout.splitlines():
            assert line == output[match_index]
            match_index += 1
