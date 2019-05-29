import pytest

@pytest.fixture
def yaml_file_f(tmp_path_factory):
    """Creates a sample YAML_FILE for CLI tests."""
    file_name = "test.yaml"
    yaml_file = tmp_path_factory.mktemp("test_files") / file_name

    file_content = """---
    aliases:
      - &plainScalar Plain scalar string
    """

    with open(yaml_file, 'w') as fhnd:
        fhnd.write(file_content)

    return yaml_file

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

    def test_no_query(self, script_runner, yaml_file_f):
        result = script_runner.run("yaml-get", yaml_file_f)
        assert not result.success, result.stderr
        assert "the following arguments are required: -p/--query" in result.stderr

    def test_query_anchor(self, script_runner, yaml_file_f):
        result = script_runner.run("yaml-get", "--query=aliases[&plainScalar]", yaml_file_f)
        assert result.success, result.stderr
        assert "Plain scalar string" in result.stdout
