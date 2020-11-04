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
        cdata = {
            "dates": [
                dt.date(2020, 10, 31),
                dt.date(2020, 11, 3)
            ]
        }
        sdata = Parsers.stringify_dates(cdata)
        assert sdata["dates"][0] == "2020-10-31"
        assert sdata["dates"][1] == "2020-11-03"

    ###
    # jsonify_yaml_data
    ###
    def test_jsonify_complex_data_with_dates(self):
        node_tag = "!tagged"
        node_data = "tagged value"
        tagged_value = ry.scalarstring.PlainScalarString(node_data)
        tagged_node = ry.comments.TaggedScalar(tagged_value, tag=node_tag)

        cdata = {
            "tagged": tagged_node,
            "dates": [
                dt.date(2020, 10, 31),
                dt.date(2020, 11, 3)
            ]
        }
        jdata = Parsers.jsonify_yaml_data(cdata)
        assert jdata["tagged"] == node_data
        assert jdata["dates"][0] == "2020-10-31"
        assert jdata["dates"][1] == "2020-11-03"
