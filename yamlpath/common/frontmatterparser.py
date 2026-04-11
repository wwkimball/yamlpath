"""Parse Markdown files with YAML frontmatter sections."""
from io import StringIO
from os.path import splitext
from typing import Any, Dict, List


class FrontmatterParser:
    """Wrap a ruamel parser to support Markdown frontmatter sections."""

    MARKDOWN_EXTENSIONS = {".md", ".markdown", ".mdown", ".mkd"}

    def __init__(self, parser: Any) -> None:
        """Initialize this class instance."""
        self.parser = parser
        self._source_markdown = ""
        self._sections: List[Dict[str, int]] = []

    @staticmethod
    def is_markdown_file(source: str) -> bool:
        """Indicate whether source appears to be a Markdown file."""
        extension = splitext(source.lower())[1]
        return extension in FrontmatterParser.MARKDOWN_EXTENSIONS

    @staticmethod
    def _read_input(source: Any) -> str:
        """Read serialized input from either stream or string."""
        if hasattr(source, "read"):
            read_data = source.read()
            return read_data if isinstance(read_data, str) else str(read_data)
        return str(source)

    def _scan_markdown(self, markdown: str) -> List[str]:
        """Find all YAML sections bounded by standalone --- lines."""
        self._source_markdown = markdown
        self._sections = []
        yaml_sections: List[str] = []
        lines = markdown.splitlines(keepends=True)
        line_offsets: List[int] = []
        char_pos = 0
        for line in lines:
            line_offsets.append(char_pos)
            char_pos += len(line)

        line_idx = 0
        line_count = len(lines)
        while line_idx < line_count:
            if lines[line_idx].strip() != "---":
                line_idx += 1
                continue

            start_line = line_idx
            line_idx += 1
            while line_idx < line_count and lines[line_idx].strip() != "---":
                line_idx += 1

            if line_idx >= line_count:
                # Unmatched delimiter; not a valid YAML section.
                break

            end_line = line_idx
            body_start = line_offsets[start_line] + len(lines[start_line])
            body_end = line_offsets[end_line]
            self._sections.append({
                "body_start": body_start,
                "body_end": body_end,
            })
            yaml_sections.append(markdown[body_start:body_end])
            line_idx += 1

        return yaml_sections

    @staticmethod
    def _compose_multidoc(yaml_sections: List[str]) -> str:
        """Compose a synthetic YAML multi-document stream."""
        docs: List[str] = []
        for section in yaml_sections:
            normalized = section if section.endswith("\n") else section + "\n"
            docs.append("---\n{}...\n".format(normalized))
        return "".join(docs)

    @staticmethod
    def _strip_yaml_markers(serialized_yaml: str) -> str:
        """Remove YAML document markers from serialized data."""
        lines = serialized_yaml.splitlines(keepends=True)
        if lines and lines[0].strip() == "---":
            lines = lines[1:]
        if lines and lines[-1].strip() == "...":
            lines = lines[:-1]
        return "".join(lines)

    def load(self, source: Any) -> Any:
        """Load one YAML document from Markdown frontmatter."""
        serialized = self._read_input(source)
        yaml_sections = self._scan_markdown(serialized)
        if yaml_sections:
            return self.parser.load(yaml_sections[0])
        return self.parser.load(serialized)

    def load_all(self, source: Any):
        """Load all YAML documents from Markdown frontmatter sections."""
        serialized = self._read_input(source)
        yaml_sections = self._scan_markdown(serialized)
        if yaml_sections:
            return self.parser.load_all(self._compose_multidoc(yaml_sections))
        return self.parser.load_all(serialized)

    def dump(self, data: Any, stream: Any) -> None:
        """Write YAML content back to Markdown when sections were detected."""
        if not self._sections:
            self.parser.dump(data, stream)
            return

        yaml_stream = StringIO()
        self.parser.dump(data, yaml_stream)
        new_body = self._strip_yaml_markers(yaml_stream.getvalue())
        if not new_body.endswith("\n"):
            new_body += "\n"

        first_section = self._sections[0]
        updated = (
            self._source_markdown[:first_section["body_start"]]
            + new_body
            + self._source_markdown[first_section["body_end"]:]
        )
        stream.write(updated)
