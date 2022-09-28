import pytest
import json
import datetime as dt

import ruamel.yaml as ry
from ruamel.yaml import version_info as ryversion
if ryversion < (0, 17, 22):                   # pragma: no cover
    from yamlpath.patches.timestamp import (
        AnchoredTimeStamp,
        AnchoredDate,
    )  # type: ignore
else:                                         # pragma: no cover
    # Temporarily fool MYPY into resolving the future-case imports
    from ruamel.yaml.timestamp import TimeStamp as AnchoredTimeStamp
    AnchoredDate = AnchoredTimeStamp
    #from ruamel.yaml.timestamp import AnchoredTimeStamp
    # From whence shall come AnchoredDate?

from yamlpath.enums import YAMLValueFormats
from yamlpath.common import Parsers

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
