import pytest
import json
import datetime as dt
from typing import Any, List

import ruamel.yaml as ry

from yamlpath.patches.timestamp import AnchoredTimeStamp, AnchoredDate
    #from ruamel.yaml.timestamp import AnchoredTimeStamp
    # From whence shall come AnchoredDate?

from yamlpath.enums import YAMLValueFormats
from yamlpath.common import Parsers


class TrackingParserLogger:
    """Minimal logger implementation for parser helper tests."""

    def __init__(self) -> None:
        """Initialize this class instance."""
        self.debug_messages: List[str] = []
        self.error_messages: List[str] = []

    def debug(self, message: str, **kwargs: Any) -> None:
        """Record DEBUG messages."""
        self.debug_messages.append(message)

    def error(self, message: str, exit_code: Any = None) -> None:
        """Record ERROR messages."""
        self.error_messages.append(message)

class Test_common_parsers():
    """Tests for the Parsers helper class."""

    ###
    # get_yaml_data (literal=True)
    ###
    def test_get_yaml_data_literally(self, quiet_logger):
        serialized_yaml = """---
hash:
  key: value

list:
  - ichi
  - ni
  - san
"""
        yaml = Parsers.get_yaml_editor()
        (data, loaded) = Parsers.get_yaml_data(
            yaml, quiet_logger, serialized_yaml,
            literal=True)
        assert loaded == True
        assert data["hash"]["key"] == "value"
        assert data["list"][0] == "ichi"
        assert data["list"][1] == "ni"
        assert data["list"][2] == "san"

    ###
    # get_yaml_multidoc_data (literal=True)
    ###
    def test_get_yaml_multidoc_data_literally(self, quiet_logger):
        serialized_yaml = """---
document: 1st
has: data
...
---
document: 2nd
has: different data
"""
        yaml = Parsers.get_yaml_editor()
        doc_id = 0
        for (data, loaded) in Parsers.get_yaml_multidoc_data(
                yaml, quiet_logger, serialized_yaml,
                literal=True):
            assert loaded == True
            if doc_id == 0:
                document = "1st"
                has = "data"
            else:
                document= "2nd"
                has = "different data"
            doc_id = doc_id + 1

            assert data["document"] == document
            assert data["has"] == has

    def test_get_yaml_data_accepts_logger_protocol(self):
        serialized_yaml = """---
hash:
  key: value
"""
        yaml = Parsers.get_yaml_editor()
        logger = TrackingParserLogger()

        (data, loaded) = Parsers.get_yaml_data(
            yaml, logger, serialized_yaml,
            literal=True)

        assert loaded is True
        assert data["hash"]["key"] == "value"
        assert logger.error_messages == []

    def test_get_yaml_data_markdown_frontmatter(self, tmp_path_factory, quiet_logger):
        from tests.conftest import create_temp_markdown_file

        markdown = """---
title: Example
enabled: true
---
# Heading

Body text.
"""
        markdown_file = create_temp_markdown_file(tmp_path_factory, markdown)
        yaml = Parsers.get_yaml_editor()

        (data, loaded) = Parsers.get_yaml_data(yaml, quiet_logger, markdown_file)

        assert loaded is True
        assert data["title"] == "Example"
        assert data["enabled"] is True

    def test_get_yaml_multidoc_data_accepts_logger_protocol(self):
        serialized_yaml = """---
document: 1st
...
---
document: 2nd
"""
        yaml = Parsers.get_yaml_editor()
        logger = TrackingParserLogger()

        docs = list(Parsers.get_yaml_multidoc_data(
            yaml, logger, serialized_yaml,
            literal=True))

        assert len(docs) == 2
        assert docs[0] == ({"document": "1st"}, True)
        assert docs[1] == ({"document": "2nd"}, True)
        assert logger.error_messages == []

    def test_get_yaml_multidoc_data_markdown_frontmatter(self, tmp_path_factory, quiet_logger):
        from tests.conftest import create_temp_markdown_file

        markdown = """---
title: Example
---
Body.
---
name: another
---
"""
        markdown_file = create_temp_markdown_file(tmp_path_factory, markdown)
        yaml = Parsers.get_yaml_editor()

        docs = list(Parsers.get_yaml_multidoc_data(
            yaml, quiet_logger, markdown_file))

        # Frontmatter applies only to the starting metadata block.
        assert len(docs) == 1
        assert docs[0] == ({"title": "Example"}, True)

    def test_get_yaml_data_markdown_frontmatter_json_semicolon(
        self, tmp_path_factory, quiet_logger
    ):
        from tests.conftest import create_temp_markdown_file

        markdown = """;;;
{
  "title": "JSON Title",
  "published": true
}
;;;

# Heading
"""
        markdown_file = create_temp_markdown_file(tmp_path_factory, markdown)
        yaml = Parsers.get_yaml_editor()

        (data, loaded) = Parsers.get_yaml_data(yaml, quiet_logger, markdown_file)

        assert loaded is True
        assert data["title"] == "JSON Title"
        assert data["published"] is True

    def test_get_yaml_data_markdown_frontmatter_rejects_toml(
        self, tmp_path_factory
    ):
        from tests.conftest import create_temp_markdown_file

        markdown = """+++
title = \"Nope\"
+++
"""
        markdown_file = create_temp_markdown_file(tmp_path_factory, markdown)
        yaml = Parsers.get_yaml_editor()
        logger = TrackingParserLogger()

        (_, loaded) = Parsers.get_yaml_data(yaml, logger, markdown_file)

        assert loaded is False
        assert any("TOML frontmatter" in msg for msg in logger.error_messages)

    def test_get_yaml_data_markdown_frontmatter_rejects_missing_closer(
        self, tmp_path_factory
    ):
        from tests.conftest import create_temp_markdown_file

        markdown = """---
title: Missing End
"""
        markdown_file = create_temp_markdown_file(tmp_path_factory, markdown)
        yaml = Parsers.get_yaml_editor()
        logger = TrackingParserLogger()

        (_, loaded) = Parsers.get_yaml_data(yaml, logger, markdown_file)

        assert loaded is False
        assert any("missing closing delimiter" in msg for msg in logger.error_messages)

    def test_get_yaml_multidoc_data_markdown_frontmatter_rejects_toml(
        self, tmp_path_factory
    ):
        from tests.conftest import create_temp_markdown_file

        markdown = """+++
title = \"Nope\"
+++
"""
        markdown_file = create_temp_markdown_file(tmp_path_factory, markdown)
        yaml = Parsers.get_yaml_editor()
        logger = TrackingParserLogger()

        docs = list(Parsers.get_yaml_multidoc_data(yaml, logger, markdown_file))

        assert docs == [(None, False)]
        assert any("TOML frontmatter" in msg for msg in logger.error_messages)

    ###
    # stringify_dates
    ###
    def test_stringify_complex_data_with_dates(self):
        cdata = ry.comments.CommentedMap({
            "dates": ry.comments.CommentedSeq([
                dt.date(2020, 10, 31),
                dt.date(2020, 11, 3)
            ])
        })
        sdata = Parsers.stringify_dates(cdata)
        assert sdata["dates"][0] == "2020-10-31"
        assert sdata["dates"][1] == "2020-11-03"

    ###
    # jsonify_yaml_data
    ###
    def test_jsonify_complex_ruamel_data(self):
        tagged_tag = "!tagged"
        tagged_value = "tagged value"
        tagged_scalar = ry.scalarstring.PlainScalarString(tagged_value)
        tagged_node = ry.comments.TaggedScalar(tagged_scalar, tag=tagged_tag)

        null_tag = "!null"
        null_value = None
        null_node = ry.comments.TaggedScalar(None, tag=null_tag)

        cdata = ry.comments.CommentedMap({
            "tagged": tagged_node,
            "null": null_node,
            "dates": ry.comments.CommentedSeq([
                dt.date(2020, 10, 31),
                dt.date(2020, 11, 3),
                AnchoredDate(2020, 12, 1),
                AnchoredTimeStamp(2021, 1, 13, 1, 2, 3)
            ]),
            "t_bool": ry.scalarbool.ScalarBoolean(1),
            "f_bool": ry.scalarbool.ScalarBoolean(0)
        })
        jdata = Parsers.jsonify_yaml_data(cdata)
        assert jdata["tagged"] == tagged_value
        assert jdata["null"] == null_value
        assert jdata["dates"][0] == "2020-10-31"
        assert jdata["dates"][1] == "2020-11-03"
        assert jdata["dates"][2] == "2020-12-01"
        assert jdata["dates"][3] == "2021-01-13T01:02:03"
        assert jdata["t_bool"] == 1
        assert jdata["f_bool"] == 0

        jstr = json.dumps(jdata)
        assert jstr == """{"tagged": "tagged value", "null": null, "dates": ["2020-10-31", "2020-11-03", "2020-12-01", "2021-01-13T01:02:03"], "t_bool": true, "f_bool": false}"""

    def test_jsonify_complex_python_data(self):
        cdata = {
            "dates": [
                dt.date(2020, 10, 31),
                dt.date(2020, 11, 3)
            ],
            "bytes": b"abc",
            "t_bool": True,
            "f_bool": False
        }
        jdata = Parsers.jsonify_yaml_data(cdata)
        assert jdata["dates"][0] == "2020-10-31"
        assert jdata["dates"][1] == "2020-11-03"
        assert jdata["t_bool"] == True
        assert jdata["f_bool"] == False

        jstr = json.dumps(jdata)
        assert jstr == """{"dates": ["2020-10-31", "2020-11-03"], "bytes": "b'abc'", "t_bool": true, "f_bool": false}"""

    def test_jsonify_datetime_value(self):
        cdata = dt.datetime(2021, 1, 13, 1, 2, 3)
        jdata = Parsers.jsonify_yaml_data(cdata)
        assert jdata == "2021-01-13T01:02:03"

    def test_jsonify_datetime_value_date_only(self):
        cdata = dt.datetime(2021, 1, 13, 0, 0, 0)
        jdata = Parsers.jsonify_yaml_data(cdata)
        assert jdata == "2021-01-13"

    def test_jsonify_commented_map_with_merge_tuple(self):
        yaml = Parsers.get_yaml_editor()
        cdata = yaml.load("""
defaults: &defaults
    inherited: 7

data:
    <<: *defaults
    explicit: 8
""")

        jdata = Parsers.jsonify_yaml_data(cdata["data"])
        assert jdata["explicit"] == 8
        assert jdata["inherited"] == 7

    def test_jsonify_commented_map_with_legacy_merge_tuple(self):
        class MergeableMap(dict):
            """Test-double map with writable merge metadata."""

            def insert(self, index, key, value):
                items = list(self.items())
                if key in self:
                    self.pop(key)
                items.insert(index, (key, value))
                self.clear()
                self.update(items)

        cdata = MergeableMap({"explicit": 8})
        cdata.merge = [(0, ry.comments.CommentedMap({"inherited": 7}))]

        jdata = Parsers._jsonify_commented_map(cdata)
        assert jdata["explicit"] == 8
        assert jdata["inherited"] == 7
