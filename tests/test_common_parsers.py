import pytest
import datetime as dt

import ruamel.yaml as ry

from yamlpath.enums import YAMLValueFormats
from yamlpath.common import Parsers

class Test_common_parsers():
    """Tests for the Parsers helper class."""

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
    def test_jsonify_complex_data(self):
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
                dt.date(2020, 11, 3)
            ])
        })
        jdata = Parsers.jsonify_yaml_data(cdata)
        assert jdata["tagged"] == tagged_value
        assert jdata["null"] == null_value
        assert jdata["dates"][0] == "2020-10-31"
        assert jdata["dates"][1] == "2020-11-03"
