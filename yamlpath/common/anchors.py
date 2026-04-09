"""
Implement Anchors, a static library of generally-useful code for YAML Anchors.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from typing import Any, Dict, Optional

from ruamel.yaml.comments import CommentedSeq, CommentedMap, merge_attrib
from ruamel.yaml.mergevalue import MergeValue

from yamlpath.wrappers import NodeCoords


def _iter_merge_nodes(data: Any):  # pragma: no cover
    """Yield merge references as (index, node)."""
    refs = data.merge if hasattr(data, "merge") else []
    for idx, merge_item in enumerate(refs):
        if isinstance(merge_item, tuple) and len(merge_item) > 1:
            yield idx, merge_item[1]
        else:
            yield idx, merge_item


def _replace_merge_node(
    data: Any, idx: int, new_node: Any
) -> None:  # pragma: no cover
    """Replace one merge reference node in-place."""
    refs = data.merge if hasattr(data, "merge") else []
    ref_store = refs.value if isinstance(refs, MergeValue) else refs
    current = ref_store[idx]
    if isinstance(current, tuple) and len(current) > 1:
        ref_store[idx] = (current[0], new_node)
    else:
        ref_store[idx] = new_node


def _sync_merge_sequence(merge_value: MergeValue) -> None:  # pragma: no cover
    """Keep MergeValue sequence representation synchronized."""
    if len(merge_value.value) <= 1:
        merge_value.set_sequence(None)
        return

    sequence = CommentedSeq(merge_value.value)
    sequence.fa.set_flow_style()
    merge_value.set_sequence(sequence)


def _add_merge_node(data: Any, merge_node: Any) -> None:  # pragma: no cover
    """Append one merge reference."""
    refs = getattr(data, merge_attrib, None)
    if isinstance(refs, MergeValue):
        refs.append(merge_node)
        if refs.merge_pos is None:
            refs.merge_pos = 0
        _sync_merge_sequence(refs)
    else:
        merge_value = MergeValue()
        if isinstance(refs, list):
            merge_value.extend(refs)
        merge_value.append(merge_node)
        merge_value.merge_pos = 0
        _sync_merge_sequence(merge_value)
        setattr(data, merge_attrib, merge_value)

    if hasattr(merge_node, "add_referent"):
        merge_node.add_referent(data)


class Anchors:
    """Helper methods for common YAML Anchor operations."""

    @staticmethod
    def scan_for_anchors(dom: Any, anchors: Dict[str, Any]):
        """
        Scan a document for all anchors contained within.

        Parameters:
        1. dom (Any) The document to scan.
        2. anchors (dict) Collection of discovered anchors along with
           references to the nodes they apply to.

        Returns:  N/A
        """
        if isinstance(dom, CommentedMap):
            for key, val in dom.items():
                if hasattr(key, "anchor") and key.anchor.value is not None:
                    anchors[key.anchor.value] = key

                if hasattr(val, "anchor") and val.anchor.value is not None:
                    anchors[val.anchor.value] = val

                # Recurse into complex values
                if isinstance(val, (CommentedMap, CommentedSeq)):
                    Anchors.scan_for_anchors(val, anchors)

        elif isinstance(dom, CommentedSeq):
            for ele in dom:
                Anchors.scan_for_anchors(ele, anchors)

        elif hasattr(dom, "anchor") and dom.anchor.value is not None:
            anchors[dom.anchor.value] = dom

    @staticmethod
    def rename_anchor(dom: Any, anchor: str, new_anchor: str):
        """
        Rename every use of an anchor in a document.

        Parameters:
        1. dom (Any) The document to modify.
        2. anchor (str) The old anchor name to rename.
        3. new_anchor (str) The new name to apply to the anchor.

        Returns:  N/A
        """
        if isinstance(dom, CommentedMap):
            for key, val in dom.non_merged_items():
                if hasattr(key, "anchor") and key.anchor.value == anchor:
                    key.anchor.value = new_anchor
                if hasattr(val, "anchor") and val.anchor.value == anchor:
                    val.anchor.value = new_anchor
                Anchors.rename_anchor(val, anchor, new_anchor)
        elif isinstance(dom, CommentedSeq):
            for ele in dom:
                Anchors.rename_anchor(ele, anchor, new_anchor)
        elif hasattr(dom, "anchor") and dom.anchor.value == anchor:
            dom.anchor.value = new_anchor

    @staticmethod
    def replace_merge_anchor(data: Any, old_node: Any, repl_node: Any) -> None:
        """
        Replace YAML Merge Key references.

        Anchor merge references in YAML are formed using the `<<: *anchor`
        operator.

        Parameters:
        1. data (Any) The DOM to adjust.
        2. old_node (Any) The former anchor node.
        3. repl_node (Any) The replacement anchor node.

        Returns:  N/A
        """
        if hasattr(data, "merge") and len(data.merge) > 0:
            for midx, merge_node in _iter_merge_nodes(data):
                if merge_node is old_node:
                    _replace_merge_node(data, midx, repl_node)

    @staticmethod
    def combine_merge_anchors(lhs: CommentedMap, rhs: CommentedMap) -> None:
        """
        Merge YAML Merge Keys.

        Parameters:
        1. lhs (CommentedMap) The map to merge into
        2. rhs (CommentedMap) The map to merge from
        """
        for _, mele in _iter_merge_nodes(rhs):
            _add_merge_node(lhs, mele)

    @staticmethod
    def replace_anchor(data: Any, old_node: Any, repl_node: Any) -> None:
        """
        Recursively replace every use of an anchor within a DOM.

        Parameters:
        1. data (Any) The DOM to adjust.
        2. old_node (Any) The former anchor node.
        3. repl_node (Any) The replacement anchor node.

        Returns:  N/A
        """
        anchor_name = repl_node.anchor.value
        if isinstance(data, CommentedMap):
            Anchors.replace_merge_anchor(data, old_node, repl_node)
            for idx, key in [
                (idx, key) for idx, key in enumerate(data.keys())
                if hasattr(key, "anchor")
                    and key.anchor.value == anchor_name
            ]:
                Anchors.replace_merge_anchor(key, old_node, repl_node)
                data.insert(idx, repl_node, data.pop(key))

            for key, val in data.non_merged_items():
                Anchors.replace_merge_anchor(key, old_node, repl_node)
                Anchors.replace_merge_anchor(val, old_node, repl_node)
                if (hasattr(val, "anchor")
                        and val.anchor.value == anchor_name):
                    data[key] = repl_node
                else:
                    Anchors.replace_anchor(val, old_node, repl_node)
        elif isinstance(data, CommentedSeq):
            for idx, ele in enumerate(data):
                Anchors.replace_merge_anchor(ele, old_node, repl_node)
                if (hasattr(ele, "anchor")
                        and ele.anchor.value == anchor_name):
                    data[idx] = repl_node
                else:
                    Anchors.replace_anchor(ele, old_node, repl_node)

    @staticmethod
    def generate_unique_anchor_name(
        document: Any, node_coord: NodeCoords,
        known_anchors: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a unique Anchor name to a given node.

        Parameters:
        1. document (Any) The DOM to adjust.
        2. node_coord (NodeCoords) The node to adjust.
        3. known_anchors (Dict[str, Any]) Optional set of Anchors already in
           `document`; will be generated on-the-fly when unset.

        Returns:  (str) The newly generated Anchor name.
        """
        if not known_anchors:
            known_anchors = {}
            Anchors.scan_for_anchors(document, known_anchors)

        parentref = node_coord.parentref
        base_name = "id"
        if isinstance(parentref, str):
            base_name = parentref
            if base_name not in known_anchors:
                return base_name

        anchor_id = 1
        new_anchor = "{}{:03d}".format(base_name, anchor_id)
        while new_anchor in known_anchors:
            anchor_id += 1
            new_anchor = "{}{:03d}".format(base_name, anchor_id)

        return new_anchor

    @staticmethod
    def get_node_anchor(node: Any) -> Optional[str]:
        """
        Return a node's Anchor/Alias name or None when there isn't one.

        Parameters:
        1. node (Any) The node to evaluate

        Returns:  (str) The node's Anchor/Alias name or None when unset
        """
        if (
                not hasattr(node, "anchor")
                or node.anchor is None
                or node.anchor.value is None
                or not node.anchor.value
        ):
            return None
        return str(node.anchor.value)
