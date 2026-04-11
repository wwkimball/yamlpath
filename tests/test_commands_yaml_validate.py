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
