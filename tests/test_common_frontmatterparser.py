import pytest

from io import StringIO

from yamlpath.common.frontmatterparser import FrontmatterParser
from yamlpath.exceptions import FrontmatterException


class DummyParser:
    """Minimal parser stub for FrontmatterParser tests."""

    def __init__(self):
        """Initialize this class instance."""
        self.last_load = None
        self.last_load_all = None
        self.dump_payload = "---\n...\n"
        self.dump_calls = []

    def load(self, source):
        """Capture and return the source value."""
        self.last_load = source
        return source

    def load_all(self, source):
        """Capture and return one value for iterable callers."""
        self.last_load_all = source
        return [source]

    def dump(self, data, stream):
        """Write configured serialized YAML output."""
        self.dump_calls.append(data)
        stream.write(self.dump_payload)


class FailingJSONReloadParser(DummyParser):
    """Parser that fails only when asked to re-load YAML dump text."""

    def load(self, source):
        """Raise when conversion back into JSON is requested."""
        if isinstance(source, str) and source.startswith("title:"):
            raise ValueError("cannot parse generated YAML")
        return super().load(source)


class Test_common_frontmatterparser:
    """Tests for the FrontmatterParser helper class."""

    def test_load_and_load_all_reject_when_unmatched_marker(self):
        parser = DummyParser()
        frontmatter = FrontmatterParser(parser)
        markdown = "---\nkey: value\n"

        with pytest.raises(FrontmatterException):
            frontmatter.load(markdown)
        with pytest.raises(FrontmatterException):
            list(frontmatter.load_all(markdown))

    def test_strip_yaml_markers_removes_trailing_document_end(self):
        serialized = "---\nkey: value\n...\n"
        stripped = FrontmatterParser._strip_yaml_markers(serialized)
        assert stripped == "key: value\n"

    def test_dump_delegates_without_frontmatter_sections(self):
        parser = DummyParser()
        frontmatter = FrontmatterParser(parser)
        stream = StringIO()

        frontmatter.dump({"k": "v"}, stream)

        assert stream.getvalue() == "---\n...\n"
        assert parser.dump_calls == [{"k": "v"}]

    def test_dump_appends_newline_when_replacing_frontmatter(self):
        parser = DummyParser()
        frontmatter = FrontmatterParser(parser)
        markdown = "---\ntitle: old\n---\nBody\n"
        parser.dump_payload = "---\n...\n"

        frontmatter.load(markdown)
        stream = StringIO()
        frontmatter.dump({"title": "new"}, stream)

        assert stream.getvalue() == "---\n\n---\nBody\n"

    def test_rejects_toml_frontmatter(self):
        parser = DummyParser()
        frontmatter = FrontmatterParser(parser)

        with pytest.raises(FrontmatterException):
            frontmatter.load("+++\ntitle='x'\n+++")

    def test_rejects_unclosed_yaml_frontmatter(self):
        parser = DummyParser()
        frontmatter = FrontmatterParser(parser)

        with pytest.raises(FrontmatterException):
            frontmatter.load("---\ntitle: x\n")

    def test_json_brace_is_not_frontmatter_opener(self):
        parser = DummyParser()
        frontmatter = FrontmatterParser(parser)
        markdown = """{
  \"title\": \"json\"
}

# Body
"""

        loaded = frontmatter.load(markdown)

        assert loaded == markdown

    def test_falls_back_when_no_frontmatter_marker(self):
        parser = DummyParser()
        frontmatter = FrontmatterParser(parser)
        markdown = "# Not frontmatter\ncontent\n"

        loaded = frontmatter.load(markdown)
        loaded_all = list(frontmatter.load_all(markdown))

        assert loaded == markdown
        assert loaded_all == [markdown]

    def test_empty_input_is_not_frontmatter(self):
        parser = DummyParser()
        frontmatter = FrontmatterParser(parser)

        assert frontmatter.load("") == ""
        assert list(frontmatter.load_all("")) == [""]

    def test_strict_mode_rejects_missing_frontmatter_opener(self):
        parser = DummyParser()
        frontmatter = FrontmatterParser(parser, require_frontmatter=True)

        with pytest.raises(FrontmatterException):
            frontmatter.load("# Heading\nBody\n")

    def test_strict_mode_rejects_empty_document(self):
        parser = DummyParser()
        frontmatter = FrontmatterParser(parser, require_frontmatter=True)

        with pytest.raises(FrontmatterException):
            frontmatter.load("")

    def test_strict_mode_rejects_json_brace_as_missing_opener(self):
        parser = DummyParser()
        frontmatter = FrontmatterParser(parser, require_frontmatter=True)

        with pytest.raises(FrontmatterException):
            frontmatter.load("{\n  \"title\": nope\n}\n")

    def test_rejects_invalid_json_semicolon_frontmatter_in_load(self):
        parser = DummyParser()
        frontmatter = FrontmatterParser(parser)

        with pytest.raises(FrontmatterException):
            frontmatter.load(";;;\n{\"title\": nope}\n;;;\n")

    def test_rejects_invalid_json_semicolon_frontmatter_in_load_all(self):
        parser = DummyParser()
        frontmatter = FrontmatterParser(parser)

        with pytest.raises(FrontmatterException):
            list(frontmatter.load_all(";;;\n{\"title\": nope}\n;;;\n"))

    def test_load_all_accepts_valid_json_semicolon_frontmatter(self):
        parser = DummyParser()
        frontmatter = FrontmatterParser(parser)

        loaded_all = list(frontmatter.load_all(
            ";;;\n{\"title\": \"ok\"}\n;;;\n"
        ))

        assert loaded_all == ['{"title": "ok"}']

    def test_dump_converts_json_frontmatter(self):
        parser = DummyParser()
        frontmatter = FrontmatterParser(parser)
        parser.dump_payload = "---\ntitle: Changed\n...\n"
        markdown = ";;;\n{\"title\": \"Old\"}\n;;;\nBody\n"

        frontmatter.load(markdown)
        stream = StringIO()
        frontmatter.dump({"title": "Changed"}, stream)

        dumped = stream.getvalue()
        assert dumped.startswith(";;;\n")
        assert "Body\n" in dumped

    def test_dump_rejects_unconvertible_json_frontmatter(self):
        parser = FailingJSONReloadParser()
        frontmatter = FrontmatterParser(parser)
        parser.dump_payload = "---\ntitle: Changed\n...\n"
        markdown = ";;;\n{\"title\": \"Old\"}\n;;;\nBody\n"

        frontmatter.load(markdown)
        with pytest.raises(FrontmatterException):
            frontmatter.dump({"title": "Changed"}, StringIO())
