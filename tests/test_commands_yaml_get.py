import pytest

@pytest.fixture
def input_files(tmp_path_factory):
    """Creates a sample YAML_FILE for CLI tests."""
    good_yaml_file_name = "good.test.yaml"
    imparsible_yaml_file_name = "imparsible.test.yaml"
    badsyntax_yaml_file_name = "badsyntax.test.yaml"
    badcmp_yaml_file_name = "bad-composition.test.yaml"
    good_yaml_file = tmp_path_factory.mktemp("test_files") / good_yaml_file_name
    imparsible_yaml_file = tmp_path_factory.mktemp("test_files") / imparsible_yaml_file_name
    badsyntax_yaml_file = tmp_path_factory.mktemp("test_files") / badsyntax_yaml_file_name
    badcmp_yaml_file = tmp_path_factory.mktemp("test_files") / badcmp_yaml_file_name

    good_yaml_content = """---
    aliases:
      - &plainScalar Plain scalar string
    """

    imparsible_yaml_content = '''{"json": "is YAML", "but_bad_json": "isn't anything!"'''

    badsyntax_yaml_content = """---
    # This YAML content contains a critical syntax error
    & bad_anchor: is bad
    """

    badcmp_yaml_content = """---
    # This YAML file is improperly composed
    this is a parsing error: *no such capability
    """

    with open(good_yaml_file, 'w') as fhnd:
        fhnd.write(good_yaml_content)
    with open(imparsible_yaml_file, 'w') as fhnd:
        fhnd.write(imparsible_yaml_content)
    with open(badsyntax_yaml_file, 'w') as fhnd:
        fhnd.write(badsyntax_yaml_content)
    with open(badcmp_yaml_file, 'w') as fhnd:
        fhnd.write(badcmp_yaml_content)

    return [good_yaml_file, imparsible_yaml_file, badsyntax_yaml_file, badcmp_yaml_file]

class Test_yaml_get():
    """Tests for the yaml-get command-line interface."""

    def test_no_options(self, script_runner):
        result = script_runner.run("yaml-get")
        assert not result.success, result.stderr
        assert "the following arguments are required: -p/--query, YAML_FILE" in result.stderr

    def test_no_input_file(self, script_runner):
        result = script_runner.run("yaml-get", "--query='/test'")
        assert not result.success, result.stderr
        assert "the following arguments are required: YAML_FILE" in result.stderr

    def test_bad_input_file(self, script_runner):
        result = script_runner.run("yaml-get", "--query='/test'", "no-such-file")
        assert not result.success, result.stderr
        assert "YAML_FILE not found:" in result.stderr

    def test_no_query(self, script_runner, input_files):
        result = script_runner.run("yaml-get", input_files[0])
        assert not result.success, result.stderr
        assert "the following arguments are required: -p/--query" in result.stderr

    def test_bad_privatekey(self, script_runner, input_files):
        result = script_runner.run("yaml-get", "--query=aliases", "--privatekey=no-such-file", input_files[0])
        assert not result.success, result.stderr
        assert "EYAML private key is not a readable file" in result.stderr

    def test_bad_publickey(self, script_runner, input_files):
        result = script_runner.run("yaml-get", "--query=aliases", "--publickey=no-such-file", input_files[0])
        assert not result.success, result.stderr
        assert "EYAML public key is not a readable file" in result.stderr

    def test_yaml_parsing_error(self, script_runner, input_files):
        result = script_runner.run("yaml-get", "--query=/", input_files[1])
        assert not result.success, result.stderr
        assert "YAML parsing error" in result.stderr

    def test_yaml_syntax_error(self, script_runner, input_files):
        result = script_runner.run("yaml-get", "--query=/", input_files[2])
        assert not result.success, result.stderr
        assert "YAML syntax error" in result.stderr

    def test_yaml_composition_error(self, script_runner, input_files):
        result = script_runner.run("yaml-get", "--query=/", input_files[3])
        assert not result.success, result.stderr
        assert "YAML composition error" in result.stderr

    def test_query_anchor(self, script_runner, input_files):
        result = script_runner.run("yaml-get", "--query=aliases[&plainScalar]", input_files[0])
        assert result.success, result.stderr
        assert "Plain scalar string" in result.stdout
