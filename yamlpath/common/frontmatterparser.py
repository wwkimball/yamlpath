"""Parse Markdown files with YAML frontmatter sections."""
import json
from io import StringIO
from os.path import splitext
from typing import Any, Dict, List

from yamlpath.exceptions import FrontmatterException


class FrontmatterParser:
    """Wrap a ruamel parser to support Markdown frontmatter sections."""

    MARKDOWN_EXTENSIONS = {".md", ".markdown", ".mdown", ".mkd"}

    def __init__(self, parser: Any, require_frontmatter: bool = False) -> None:
        """Initialize this class instance."""
        self.parser = parser
        self.require_frontmatter = require_frontmatter
        self._source_markdown = ""
        self._sections: List[Dict[str, int]] = []
        self._format = "yaml"

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

    # pylint: disable=too-many-locals
    def _scan_markdown(self, markdown: str) -> List[str]:
        """Extract one compliant YAML/JSON frontmatter block from Markdown."""
        self._source_markdown = markdown
        self._sections = []
        self._format = "yaml"
        yaml_sections: List[str] = []
        normalized = (
            markdown[1:] if markdown.startswith("\ufeff") else markdown
        )
        lines = normalized.splitlines(keepends=True)

        if not lines:
            if self.require_frontmatter:
                raise FrontmatterException(
                    "Frontmatter violation: expected a frontmatter opener"
                    " at the start of the Markdown document, but the"
                    " document is empty."
                )
            return yaml_sections

        opener = lines[0].strip()
        if opener == "+++":
            raise FrontmatterException(
                "Frontmatter violation: TOML frontmatter ('+++') is not"
                " supported by yamlpath; only YAML ('---') and JSON (';;;'"
                " delimiters are supported."
            )

        if opener not in ("---", ";;;"):
            if self.require_frontmatter:
                raise FrontmatterException(
                    "Frontmatter violation: expected a frontmatter opener"
                    " (--- for YAML or ;;; for JSON) at the start of the"
                    " Markdown document."
                )
            return yaml_sections

        line_offsets: List[int] = []
        char_pos = 0
        for line in lines:
            line_offsets.append(char_pos)
            char_pos += len(line)

        close_delim = opener
        line_idx = 1
        line_count = len(lines)
        while (
            line_idx < line_count
            and lines[line_idx].strip() != close_delim
        ):
            line_idx += 1

        if line_idx >= line_count:
            raise FrontmatterException(
                "Frontmatter violation: missing closing delimiter '{}';"
                " metadata blocks must be enclosed and complete at the"
                " start of the Markdown document.".format(close_delim)
            )

        body_start = line_offsets[0] + len(lines[0])
        body_end = line_offsets[line_idx]
        self._sections.append({
            "body_start": body_start,
            "body_end": body_end,
        })
        yaml_sections.append(normalized[body_start:body_end])
        self._format = "yaml" if opener == "---" else "json_semicolon"
        return yaml_sections

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
            if self._format.startswith("json"):
                try:
                    parsed_json = json.loads(yaml_sections[0])
                except json.JSONDecodeError as ex:
                    raise FrontmatterException(
                        "Frontmatter violation: invalid JSON metadata near"
                        " line {}, column {}: {}"
                        .format(ex.lineno, ex.colno, ex.msg)
                    ) from ex
                yaml_sections[0] = json.dumps(parsed_json)
            return self.parser.load(yaml_sections[0])
        return self.parser.load(serialized)

    def load_all(self, source: Any):
        """Load one metadata document via an iterable parser interface."""
        serialized = self._read_input(source)
        yaml_sections = self._scan_markdown(serialized)
        if yaml_sections:
            if self._format.startswith("json"):
                try:
                    parsed_json = json.loads(yaml_sections[0])
                except json.JSONDecodeError as ex:
                    raise FrontmatterException(
                        "Frontmatter violation: invalid JSON metadata near"
                        " line {}, column {}: {}"
                        .format(ex.lineno, ex.colno, ex.msg)
                    ) from ex
                yaml_sections[0] = json.dumps(parsed_json)

            # Frontmatter is a single metadata block by specification.
            return [self.parser.load(yaml_sections[0])]
        return self.parser.load_all(serialized)

    def dump(self, data: Any, stream: Any) -> None:
        """Write YAML content back to Markdown when sections were detected."""
        if not self._sections:
            self.parser.dump(data, stream)
            return

        yaml_stream = StringIO()
        self.parser.dump(data, yaml_stream)
        new_body = self._strip_yaml_markers(yaml_stream.getvalue())
        if self._format.startswith("json"):
            try:
                reparsed = self.parser.load(new_body)
            except Exception as ex:
                raise FrontmatterException(
                    "Frontmatter violation: unable to convert updated"
                    " metadata into JSON: {}".format(ex)
                ) from ex
            new_body = json.dumps(reparsed, indent=2) + "\n"
        elif not new_body.endswith("\n"):
            new_body += "\n"

        first_section = self._sections[0]
        updated = (
            self._source_markdown[:first_section["body_start"]]
            + new_body
            + self._source_markdown[first_section["body_end"]:]
        )
        stream.write(updated)
