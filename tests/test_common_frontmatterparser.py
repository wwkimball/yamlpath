from io import StringIO

from yamlpath.common.frontmatterparser import FrontmatterParser


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


class Test_common_frontmatterparser:
    """Tests for the FrontmatterParser helper class."""

    def test_load_and_load_all_fallback_when_unmatched_marker(self):
        parser = DummyParser()
        frontmatter = FrontmatterParser(parser)
        markdown = "---\nkey: value\n"

        loaded = frontmatter.load(markdown)
        loaded_all = list(frontmatter.load_all(markdown))

        assert loaded == markdown
        assert parser.last_load == markdown
        assert loaded_all == [markdown]
        assert parser.last_load_all == markdown

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
