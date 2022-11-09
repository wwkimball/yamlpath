import pytest
from datetime import date, datetime
from types import SimpleNamespace

from ruamel.yaml.comments import CommentedSeq, CommentedMap, TaggedScalar
from ruamel.yaml.scalarstring import PlainScalarString
from ruamel.yaml.scalarbool import ScalarBoolean
from ruamel.yaml.scalarfloat import ScalarFloat
from ruamel.yaml.scalarint import ScalarInt
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
from yamlpath.common import Nodes

class Test_common_nodes():
    """Tests for the Nodes helper class."""

    ###
    # make_new_node
    ###
    def test_dict_to_str(self):
        assert "{}" == Nodes.make_new_node("", "{}", YAMLValueFormats.DEFAULT)

    def test_list_to_str(self):
        assert "[]" == Nodes.make_new_node("", "[]", YAMLValueFormats.DEFAULT)

    def test_anchored_string(self):
        node = PlainScalarString("value")
        node.yaml_set_anchor("anchored")
        new_node = Nodes.make_new_node(node, "new", YAMLValueFormats.DEFAULT)
        assert new_node.anchor.value == node.anchor.value


    ###
    # apply_yaml_tag
    ###
    def test_tag_map(self):
        new_tag = "!something"
        old_node = CommentedMap({"key": "value"})
        new_node = Nodes.apply_yaml_tag(old_node, new_tag)
        assert new_node.tag.value == new_tag

    def test_update_tag(self):
        old_tag = "!tagged"
        new_tag = "!changed"
        old_node = PlainScalarString("tagged value")
        tagged_node = TaggedScalar(old_node, tag=old_tag)
        new_node = Nodes.apply_yaml_tag(tagged_node, new_tag)
        assert new_node.tag.value == new_tag
        assert new_node.value == old_node

    def test_delete_tag(self):
        old_tag = "!tagged"
        new_tag = ""
        old_node = PlainScalarString("tagged value")
        tagged_node = TaggedScalar(old_node, tag=old_tag)
        new_node = Nodes.apply_yaml_tag(tagged_node, new_tag)
        assert not hasattr(new_node, "tag")
        assert new_node == old_node


    ###
    # tagless_value
    ###
    def test_tagless_value_syntax_error(self):
        assert "[abc" == Nodes.tagless_value("[abc")


    ###
    # node_is_aoh
    ###
    def test_aoh_node_is_none(self):
        assert False == Nodes.node_is_aoh(None)

    def test_aoh_node_is_not_list(self):
        assert False == Nodes.node_is_aoh({"key": "value"})

    def test_aoh_is_inconsistent(self):
        assert False == Nodes.node_is_aoh([
            {"key": "value"},
            None
        ])


    ###
    # wrap_type
    ###
    @pytest.mark.parametrize("value,checktype", [
        ([], CommentedSeq),
        ({}, CommentedMap),
        ("", PlainScalarString),
        (1, ScalarInt),
        (1.1, ScalarFloat),
        (True, ScalarBoolean),
        (date(2022, 8, 2), AnchoredDate),
        (datetime(2022, 8, 2, 13, 22, 31), AnchoredTimeStamp),
        (SimpleNamespace(), SimpleNamespace),
    ])
    def test_wrap_type(self, value, checktype):
        assert isinstance(Nodes.wrap_type(value), checktype)
