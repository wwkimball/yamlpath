import pytest

from tests.conftest import create_temp_markdown_file, create_temp_yaml_file


class Test_commands_yaml_validate():
    """Tests for the yaml-validate command-line tool."""
    command = "yaml-validate"

    def test_no_arguments(self, script_runner):
        result = script_runner.run([self.command, "--nostdin"])
        assert not result.success, result.stderr
        assert "There must be at least one YAML_FILE" in result.stderr

    def test_too_many_pseudofiles(self, script_runner):
        result = script_runner.run([
            self.command
            , '-'
            , '-'])
        assert not result.success, result.stderr
        assert "Only one YAML_FILE may be the - pseudo-file" in result.stderr

    def test_valid_singledoc(self, script_runner, tmp_path_factory):
        yaml_file = create_temp_yaml_file(tmp_path_factory, """---
this:
  single-document:
    is: valid
""")
        result = script_runner.run([
            self.command
            , "--nostdin"
            , yaml_file])
        assert result.success, result.stderr

    def test_invalid_singledoc(self, script_runner, tmp_path_factory):
        yaml_file = create_temp_yaml_file(tmp_path_factory, "{[}")
        result = script_runner.run([
            self.command
            , "--nostdin"
            , yaml_file])
        assert not result.success, result.stderr
        assert "  * YAML parsing error in" in result.stdout

    def test_valid_markdown_frontmatter(self, script_runner, tmp_path_factory):
        markdown_file = create_temp_markdown_file(
            tmp_path_factory,
            "---\ntitle: okay\n---\n# Body\n")
        result = script_runner.run([
            self.command,
            "--nostdin",
            markdown_file,
        ])
        assert result.success, result.stderr

    def test_invalid_markdown_frontmatter_reports_spec_violation(
        self, script_runner, tmp_path_factory
    ):
        markdown_file = create_temp_markdown_file(
            tmp_path_factory,
            "+++\ntitle = 'bad'\n+++\n# Body\n")
        result = script_runner.run([
            self.command,
            "--nostdin",
            markdown_file,
        ])
        assert not result.success, result.stderr
        assert "is invalid due to:" in result.stdout
        assert "TOML frontmatter ('+++') is not supported" in result.stdout

    def test_frontmatter_flag_missing_opener_reports_violation(
        self, script_runner, tmp_path_factory
    ):
        markdown_file = create_temp_markdown_file(
            tmp_path_factory,
            "# Missing metadata\n")
        result = script_runner.run([
            self.command,
            "--nostdin",
            "--frontmatter",
            markdown_file,
        ])
        assert not result.success, result.stderr
        assert "is invalid due to:" in result.stdout
        assert "expected a frontmatter opener" in result.stdout

    def test_frontmatter_and_json_multi_doc_are_mutually_exclusive(
        self, script_runner, tmp_path_factory
    ):
        yaml_file = create_temp_yaml_file(tmp_path_factory, "---\nkey: value\n")
        result = script_runner.run([
            self.command,
            "--nostdin",
            "--frontmatter",
            "--json-multi-doc",
            yaml_file,
        ])
        assert not result.success, result.stderr
        assert "cannot be used together" in result.stderr

    def test_valid_stdin_explicit(self, script_runner, tmp_path_factory):
        import subprocess
        stdin_content = "{this: {is: valid}}"
        result = subprocess.run(
            [self.command
            , "-"]
            , stdout=subprocess.PIPE
            , input=stdin_content
            , universal_newlines=True
        )
        assert 0 == result.returncode, result.stderr

    def test_valid_stdin_implicit(self, script_runner, tmp_path_factory):
        import subprocess
        stdin_content = "{this: {is: valid}}"
        result = subprocess.run(
            [self.command]
            , stdout=subprocess.PIPE
            , input=stdin_content
            , universal_newlines=True
        )
        assert 0 == result.returncode, result.stderr

    def test_invalid_stdin_explicit(self, script_runner, tmp_path_factory):
        import subprocess
        stdin_content = "{this: {is not: valid}]"
        result = subprocess.run(
            [self.command
            , "-"]
            , stdout=subprocess.PIPE
            , input=stdin_content
            , universal_newlines=True
        )
        assert 2 == result.returncode, result.stderr
        assert "  * YAML parsing error in" in result.stdout

    def test_invalid_stdin_implicit(self, script_runner, tmp_path_factory):
        import subprocess
        stdin_content = "{this: {is not: valid}]"
        result = subprocess.run(
            [self.command]
            , stdout=subprocess.PIPE
            , input=stdin_content
            , universal_newlines=True
        )
        assert 2 == result.returncode, result.stderr
        assert "  * YAML parsing error in" in result.stdout

    def test_valid_json_multi_doc_stdin_explicit(self, script_runner, tmp_path_factory):
        import subprocess
        import sys
        stdin_content = '{"id":"test1"}\n{"id":"test2"}'
        result = subprocess.run(
            [sys.executable, "-m", "yamlpath.commands.yaml_validate",
             "--json-multi-doc", "-", "-v"]
            , stdout=subprocess.PIPE
            , input=stdin_content
            , universal_newlines=True
        )
        assert 0 == result.returncode, result.stderr
        assert "STDIN/0 is valid." in result.stdout
        assert "STDIN/1 is valid." in result.stdout

    def test_valid_json_multi_doc_file(self, script_runner, tmp_path_factory):
        json_file = create_temp_yaml_file(
            tmp_path_factory,
            '{"id":"test1"}\n{"id":"test2"}\n')
        result = script_runner.run([
            self.command,
            "--nostdin",
            "-j",
            "-v",
            json_file,
        ])
        assert result.success, result.stderr
        assert "/0 is valid." in result.stdout
        assert "/1 is valid." in result.stdout

    def test_invalid_json_multi_doc_stdin_explicit(self, script_runner, tmp_path_factory):
        import subprocess
        import sys
        stdin_content = '{"id":"test1"}\n{"id":oops}'
        result = subprocess.run(
            [sys.executable, "-m", "yamlpath.commands.yaml_validate",
             "--json-multi-doc", "-"]
            , stdout=subprocess.PIPE
            , input=stdin_content
            , universal_newlines=True
        )
        assert 2 == result.returncode, result.stderr
        assert "JSON parsing error" in result.stdout

    def test_json_multi_doc_flag_is_harmless_for_single_doc_json(
        self, tmp_path_factory
    ):
        import subprocess
        import sys

        json_file = create_temp_yaml_file(
            tmp_path_factory,
            '{"id":"test1"}\n')

        base_result = subprocess.run(
            [sys.executable, "-m", "yamlpath.commands.yaml_validate",
             "--nostdin", json_file],
            capture_output=True, text=True
        )
        flag_result = subprocess.run(
            [sys.executable, "-m", "yamlpath.commands.yaml_validate",
             "--nostdin", "--json-multi-doc", json_file],
            capture_output=True, text=True
        )

        assert base_result.returncode == 0, base_result.stderr
        assert flag_result.returncode == 0, flag_result.stderr
        assert base_result.stdout == flag_result.stdout
        assert base_result.stderr == flag_result.stderr
