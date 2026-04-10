import pytest

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, merge_attrib
from ruamel.yaml.mergevalue import MergeValue

from yamlpath.common.mergerefs import MergeRefs


class Test_common_mergerefs:
    """Tests for the MergeRefs helper class."""

    def _load(self, yaml_text):
        return YAML().load(yaml_text)

    ###
    # iter_nodes
    ###
    def test_iter_nodes_no_merge_attr(self):
        result = list(MergeRefs.iter_nodes({"key": "value"}))
        assert result == []

    def test_iter_nodes_direct_format(self):
        doc = self._load("""---
base: &base
  source_key: source_value
merged:
  <<: *base
  own_key: own_value
""")
        result = list(MergeRefs.iter_nodes(doc["merged"]))
        assert len(result) == 1
        idx, node = result[0]
        assert idx == 0
        assert node["source_key"] == "source_value"

    def test_iter_nodes_tuple_format(self):
        data = CommentedMap({"key": "value"})
        source = CommentedMap({"src_key": "src_val"})
        mv = MergeValue()
        mv.append((0, source))
        setattr(data, merge_attrib, mv)
        result = list(MergeRefs.iter_nodes(data))
        assert len(result) == 1
        idx, node = result[0]
        assert idx == 0
        assert node is source

    ###
    # replace_node
    ###
    def test_replace_node_mergevalue_direct(self):
        doc = self._load("""---
old: &old
  ok: original
replacement: &replacement
  ok: replaced
merged:
  <<: *old
  own: own_val
""")
        merged = doc["merged"]
        new_node = doc["replacement"]
        MergeRefs.replace_node(merged, 0, new_node)
        _, retrieved = list(MergeRefs.iter_nodes(merged))[0]
        assert retrieved is new_node

    def test_replace_node_list_tuple_format(self):
        data = CommentedMap({"key": "value"})
        old_src = CommentedMap({"sk": "old"})
        new_src = CommentedMap({"sk": "new"})
        setattr(data, merge_attrib, [(0, old_src)])
        MergeRefs.replace_node(data, 0, new_src)
        _, retrieved = list(MergeRefs.iter_nodes(data))[0]
        assert retrieved is new_src

    ###
    # remove_node
    ###
    def test_remove_node_mergevalue(self):
        doc = self._load("""---
base: &base
  bk: bv
merged:
  <<: *base
  ok: ov
""")
        merged = doc["merged"]
        assert len(list(MergeRefs.iter_nodes(merged))) == 1
        MergeRefs.remove_node(merged, 0)
        assert list(MergeRefs.iter_nodes(merged)) == []

    def test_remove_node_list_format(self):
        data = CommentedMap({"key": "value"})
        node_a = CommentedMap({"a": 1})
        node_b = CommentedMap({"b": 2})
        setattr(data, merge_attrib, [node_a, node_b])
        MergeRefs.remove_node(data, 0)
        refs = getattr(data, merge_attrib)
        assert len(refs) == 1
        assert refs[0] is node_b

    ###
    # add_node
    ###
    def test_add_node_creates_mergevalue_from_none(self):
        data = CommentedMap({"key": "value"})
        source = CommentedMap({"sk": "sv"})
        MergeRefs.add_node(data, source)
        mv = getattr(data, merge_attrib)
        assert isinstance(mv, MergeValue)
        assert mv[0] is source

    def test_add_node_extends_from_list_refs(self):
        data = CommentedMap({"key": "value"})
        old_node = CommentedMap({"ok": "ov"})
        new_node = CommentedMap({"nk": "nv"})
        setattr(data, merge_attrib, [old_node])
        MergeRefs.add_node(data, new_node)
        mv = getattr(data, merge_attrib)
        assert isinstance(mv, MergeValue)
        assert len(mv) == 2
        assert mv[0] is old_node
        assert mv[1] is new_node

    def test_add_node_appends_to_existing_mergevalue(self):
        data = CommentedMap({"key": "value"})
        node1 = CommentedMap({"k1": "v1"})
        node2 = CommentedMap({"k2": "v2"})
        MergeRefs.add_node(data, node1)
        mv = getattr(data, merge_attrib)
        mv.merge_pos = 5
        MergeRefs.add_node(data, node2)
        assert len(mv) == 2
        assert mv.merge_pos == 5

    def test_add_node_sets_merge_pos_when_none(self):
        data = CommentedMap({"key": "value"})
        mv = MergeValue()
        mv.append(CommentedMap({"k1": "v1"}))
        mv.merge_pos = None
        setattr(data, merge_attrib, mv)
        MergeRefs.add_node(data, CommentedMap({"k2": "v2"}))
        assert mv.merge_pos == 0

    def test_add_node_materialize_keys(self):
        data = CommentedMap({"existing": "keep"})
        source = CommentedMap({"existing": "override", "new_key": "new_val"})
        MergeRefs.add_node(data, source, materialize_keys=True)
        assert data["existing"] == "keep"
        assert data["new_key"] == "new_val"
