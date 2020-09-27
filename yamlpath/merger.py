"""
Implement YAML document Merger.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from typing import Any

import ruamel.yaml
from ruamel.yaml.scalarstring import ScalarString

from yamlpath.wrappers import ConsolePrinter, NodeCoords
from yamlpath.exceptions import MergeException
from yamlpath.enums import (
    AnchorConflictResolutions,
    AoHMergeOpts,
    ArrayMergeOpts,
    HashMergeOpts
)
from yamlpath.func import append_list_element
from yamlpath import YAMLPath, Processor, MergerConfig


class Merger:
    """Performs YAML document merges."""

    def __init__(
            self, logger: ConsolePrinter, lhs: Any, config: MergerConfig
    ) -> None:
        """
        Instantiate this class into an object.

        Parameters:
        1. logger (ConsolePrinter) Instance of ConsoleWriter or subclass
        2. args (dict) Default options for merge rules
        3. lhs (Any) The prime left-hand-side parsed YAML data
        4. config (Processor) Processor-wrapped user-defined YAML Paths
            providing precise document merging rules

        Returns:  N/A

        Raises:  N/A
        """
        self.logger: ConsolePrinter = logger
        self.data: Any = lhs
        self.config: Processor = config

    def _merge_dicts(
        self, lhs: dict, rhs: dict, path: YAMLPath, **kwargs: Any
    ) -> dict:
        """
        Merges two YAML maps (dicts).

        Parameters:
        1. lhs (list) The merge target.
        2. rhs (list) The merge source.
        3. path (YAMLPath) Location within the DOM where this merge is taking
           place.

        Keyword Parameters:
        * parent (Any) Parent node of `rhs`
        * parentref (Any) Child Key or Index of `rhs` within `parent`.

        Returns:  (dict) The merged result.

        Raises:
        - `MergeException` when a clean merge is impossible.
        """
        if not isinstance(lhs, dict):
            raise MergeException(
                "Impossible to add Hash data to non-Hash destination.", path)

        # The document root is ALWAYS a Hash.  For everything deeper, do not
        # merge when the user sets LEFT|RIGHT Hash merge options.
        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        if len(path) > 0:
            merge_mode = self.config.hash_merge_mode(
                NodeCoords(rhs, parent, parentref))
            if merge_mode is HashMergeOpts.LEFT:
                return lhs
            if merge_mode is HashMergeOpts.RIGHT:
                return rhs

        # Deep merge
        buffer = []
        buffer_pos = 0
        for key, val in rhs.items():
            path_next = YAMLPath(path).append(str(key))
            self.logger.debug(
                "Merger::_merge_dicts:  Processing key {} {} at {}."
                .format(key, type(key), path_next))
            if key in lhs:
                # Write the buffer if populated
                for b_key, b_val in buffer:
                    lhs.insert(buffer_pos, b_key, b_val)
                buffer = []

                # LHS has the RHS key
                if isinstance(val, dict):
                    lhs[key] = self._merge_dicts(
                        lhs[key], val, path_next, parent=rhs, parentref=key)
                elif isinstance(val, list):
                    lhs[key] = self._merge_lists(
                        lhs[key], val, path_next, parent=rhs, parentref=key)
                else:
                    lhs[key] = val
            else:
                # LHS lacks the RHS key.  Buffer this key-value pair in order
                # to insert it ahead of whatever key(s) follow this one in RHS
                # to keep anchor definitions before their aliases.
                buffer.append((key, val))

            buffer_pos += 1

        # Write any remaining buffered content to the end of LHS
        for b_key, b_val in buffer:
            lhs[b_key] = b_val

        return lhs

    def _merge_simple_lists(
        self, lhs: list, rhs: list, path: YAMLPath,
        node_coord: NodeCoords
    ) -> list:
        """
        Merge two lists of Scalars or lists.

        Parameters:
        1. lhs (list) The merge target.
        2. rhs (list) The merge source.
        3. path (YAMLPath) Location within the DOM where this merge is taking
           place.
        4. node_coord (NodeCoords) The RHS root node, its parent, and reference
           within its parent; used for config lookups.

        Returns: (list) The merged result.

        Raises:
        - `MergeException` when a clean merge is impossible.
        """
        if not isinstance(lhs, list):
            raise MergeException(
                "Impossible to add Array data to non-Array destination.", path)

        merge_mode = self.config.array_merge_mode(node_coord)
        if merge_mode is ArrayMergeOpts.LEFT:
            return lhs
        if merge_mode is ArrayMergeOpts.RIGHT:
            return rhs

        append_all = merge_mode is ArrayMergeOpts.ALL
        for idx, ele in enumerate(rhs):
            path_next = YAMLPath(path).append("[{}]".format(idx))
            self.logger.debug(
                "Merger::_merge_simple_lists:  Processing element {}{} at {}."
                .format(ele, type(ele), path_next))

            if append_all or (ele not in lhs):
                append_list_element(
                    lhs, ele,
                    ele.anchor.value if hasattr(ele, "anchor") else None)
        return lhs

    def _merge_arrays_of_hashes(
        self, lhs: list, rhs: list, path: YAMLPath,
        node_coord: NodeCoords
    ) -> list:
        """
        Merge two lists of dicts (Arrays-of-Hashes).

        This is a deep merge operation.  Each dict is treated as a record with
        an identity key.  RHS records are merged with LHS records for which the
        identity key matches.  As such, an identity key is required in both LHS
        and RHS records.  This key is configurable.  When there is no LHS match
        for an RHS key, the RHS record is appended to the LHS list.

        Parameters:
        1. lhs (list) The merge target.
        2. rhs (list) The merge source.
        3. path (YAMLPath) Location within the DOM where this merge is taking
           place.
        4. node_coord (NodeCoords) The RHS root node, its parent, and reference
           within its parent; used for config lookups.

        Returns: (list) The merged result.

        Raises:
        - `MergeException` when a clean merge is impossible.
        """
        if not isinstance(lhs, list):
            raise MergeException(
                "Impossible to add Array-of-Hash data to non-Array"
                " destination."
                , path)

        self.logger.debug(
            "Merger::_merge_arrays_of_hashes:  Merging {} Hash(es) at {}."
            .format(len(rhs), path))

        merge_mode = self.config.aoh_merge_mode(node_coord)
        if merge_mode is AoHMergeOpts.LEFT:
            return lhs
        if merge_mode is AoHMergeOpts.RIGHT:
            return rhs

        for idx, ele in enumerate(rhs):
            path_next = YAMLPath(path).append("[{}]".format(idx))
            node_next = NodeCoords(ele, rhs, idx)
            self.logger.debug(
                "Merger::_merge_arrays_of_hashes:  Processing element {} {}"
                " at {}.".format(ele, type(ele), path_next))

            if merge_mode is AoHMergeOpts.DEEP:
                id_key = self.config.aoh_merge_key(node_next, ele)
                if id_key in ele:
                    id_val = ele[id_key]
                else:
                    raise MergeException(
                        "Mandatory identity key, {}, not present in Hash with"
                        " keys:  {}."
                        .format(id_key, ", ".join(ele.keys()))
                        , path_next
                    )

                merged_hash = False
                for lhs_hash in (
                    lhs_hash for lhs_hash in lhs
                    if id_key in lhs_hash and lhs_hash[id_key] == id_val
                ):
                    self._merge_dicts(
                        lhs_hash, ele, path_next, parent=rhs, parentref=idx)
                    merged_hash = True
                    break
                if not merged_hash:
                    append_list_element(lhs, ele,
                        ele.anchor.value if hasattr(ele, "anchor") else None)
            elif merge_mode is AoHMergeOpts.UNIQUE:
                if ele not in lhs:
                    append_list_element(
                        lhs, ele,
                        ele.anchor.value if hasattr(ele, "anchor") else None)
            else:
                append_list_element(lhs, ele,
                    ele.anchor.value if hasattr(ele, "anchor") else None)
        return lhs

    def _merge_lists(
        self, lhs: list, rhs: list, path: YAMLPath, **kwargs: Any
    ) -> list:
        """
        Merge two lists; understands lists-of-dicts.

        Parameters:
        1. lhs (list) The list to merge into.
        2. rhs (list) The list to merge from.
        3. path (YAMLPath) Location of the `rsh` source list within its DOM.

        Keyword Parameters:
        * parent (Any) Parent node of `rhs`
        * parentref (Any) Child Key or Index of `rhs` within `parent`.

        Returns:  (list) The merged result.
        """
        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        node_coord = NodeCoords(rhs, parent, parentref)
        if len(rhs) > 0:
            if isinstance(rhs[0], dict):
                # This list is an Array-of-Hashes
                return self._merge_arrays_of_hashes(lhs, rhs, path, node_coord)

            # This list is an Array-of-Arrays or a simple list of Scalars
            return self._merge_simple_lists(lhs, rhs, path, node_coord)

        # No RHS list
        return lhs

    def _calc_unique_anchor(self, anchor: str, known_anchors: dict) -> str:
        """
        Generate a unique anchor name within a document pair.

        Parameters:
        1. anchor (str) The original anchor name.
        2. known_anchors (dict) Dictionary of every anchor already in the
           document.

        Returns:  (str) The new, unique anchor name.
        """
        self.logger.debug("Merger::_calc_unique_anchor:  Preexisting Anchors:")
        self.logger.debug(known_anchors)
        while anchor in known_anchors:
            anchor = "{}_{}".format(
                anchor,
                str(hash(anchor)).replace("-", "_"))
            self.logger.debug(
                "Merger::_calc_unique_anchor:  Trying new anchor name, {}."
                .format(anchor))
        return anchor

    def _resolve_anchor_conflicts(self, rhs: Any) -> None:
        """
        Resolve anchor conflicts between this and another document.

        Parameters:
        1. rhs (Any) The other document to consolidate with this one.

        Returns:  N/A
        """
        lhs_anchors = {}
        Merger.scan_for_anchors(self.data, lhs_anchors)
        self.logger.debug("Merger::_resolve_anchor_conflicts:  LHS Anchors:")
        self.logger.debug(lhs_anchors)

        rhs_anchors = {}
        Merger.scan_for_anchors(rhs, rhs_anchors)
        self.logger.debug("Merger::_resolve_anchor_conflicts:  RHS Anchors:")
        self.logger.debug(rhs_anchors)

        for anchor in [anchor
                for anchor in rhs_anchors
                if anchor in lhs_anchors
        ]:
            # It is only a conflict if the value differs; however, the
            # value may be a scalar, list, or dict.  Further, lists and
            # dicts may contain other aliased values which must also be
            # checked for equality (or pointing at identical anchors).
            lhs_anchor = lhs_anchors[anchor]
            rhs_anchor = rhs_anchors[anchor]
            conflict_mode = self.config.anchor_merge_mode()

            if lhs_anchor != rhs_anchor:
                if conflict_mode is AnchorConflictResolutions.RENAME:
                    self.logger.debug(
                        "Anchor {} conflict; will RENAME anchors."
                        .format(anchor))
                    Merger.rename_anchor(
                        rhs, anchor,
                        self._calc_unique_anchor(
                            anchor,
                            set(lhs_anchors.keys())
                            .union(set(rhs_anchors.keys()))
                        )
                    )
                elif conflict_mode is AnchorConflictResolutions.LEFT:
                    self.logger.debug(
                        "Anchor {} conflict; LEFT will override."
                        .format(anchor))
                    Merger.replace_anchor(rhs, rhs_anchor, lhs_anchor)
                elif conflict_mode is AnchorConflictResolutions.RIGHT:
                    self.logger.debug(
                        "Anchor {} conflict; RIGHT will override."
                        .format(anchor))
                    Merger.replace_anchor(self.data, lhs_anchor, rhs_anchor)
                else:
                    raise MergeException(
                        "Aborting due to anchor conflict with, {}."
                        .format(anchor))

    def merge_with(self, rhs: Any) -> None:
        """
        Merge this document with another.

        Parameters:
        1. rhs (Any) The document to merge into this one.

        Returns:  N/A

        Raises:
        - `MergeException` when a clean merge is impossible.
        """
        lhs_proc = Processor(self.logger, self.data)
        insert_at = self.config.get_insertion_point()

        # Remove all comments (no sensible way to merge them)
        Merger.delete_all_comments(rhs)

        # Resolve any anchor conflicts
        self._resolve_anchor_conflicts(rhs)

        # Prepare the merge rules
        self.config.prepare(rhs)

        # Identify a reasonable default should a DOM need to be built up to
        # receive the RHS data.
        default_val = rhs
        if isinstance(rhs, dict):
            default_val = {}
        elif isinstance(rhs, list):
            default_val = []

        # Loop through all insertion points and the elements in RHS
        merge_performed = False
        for node_coord in lhs_proc.get_nodes(
                insert_at, default_value=default_val
        ):
            target_node = (node_coord.node
                if isinstance(node_coord.node, (dict, list))
                else node_coord.parent)

            Merger.set_flow_style(
                rhs, (target_node.fa.flow_style()
                      if hasattr(target_node, "fa")
                      else None))

            if isinstance(rhs, dict):
                # The RHS document root is a map
                if isinstance(target_node, list):
                    # But the destination is a list
                    self._merge_lists(target_node, [rhs], insert_at)
                else:
                    self._merge_dicts(target_node, rhs, insert_at)
                merge_performed = True
            elif isinstance(rhs, list):
                # The RHS document root is a list
                self._merge_lists(target_node, rhs, insert_at)
                merge_performed = True
            else:
                # The RHS document root is a Scalar value
                target_node = node_coord.node
                if isinstance(target_node, list):
                    append_list_element(target_node, rhs)
                    merge_performed = True
                elif isinstance(target_node, dict):
                    raise MergeException(
                        "Impossible to add Scalar value, {}, to a Hash without"
                        " a key.  Change the value to a 'key: value' pair, a"
                        " '{{key: value}}' Hash, or change the merge target to"
                        " an Array or other Scalar value."
                        .format(rhs), insert_at)
                else:
                    lhs_proc.set_value(insert_at, rhs)
                    merge_performed = True

        if not merge_performed:
            raise MergeException(
                "A merge was not performed.  Ensure your target path matches"
                " at least one node in the left document(s).", insert_at)

    @classmethod
    def set_flow_style(cls, node: Any, is_flow: bool) -> None:
        """
        Recursively apply flow|block style to a node.

        Parameters:
        1. node (Any) The node to apply flow|block style to.
        2. is_flow (bool) True=flow-style, False=block-style

        Returns:  N/A
        """
        if hasattr(node, "fa"):
            if is_flow:
                node.fa.set_flow_style()
            else:
                node.fa.set_block_style()

        if isinstance(node, dict):
            for key, val in node.items():
                Merger.set_flow_style(key, is_flow)
                Merger.set_flow_style(val, is_flow)
        elif isinstance(node, list):
            for ele in node:
                Merger.set_flow_style(ele, is_flow)

    @classmethod
    def scan_for_anchors(cls, dom: Any, anchors: dict):
        """
        Scan a document for all anchors contained within.

        Parameters:
        1. dom (Any) The document to scan.
        2. anchors (dict) Collection of discovered anchors along with
           references to the nodes they apply to.

        Returns:  N/A
        """
        if isinstance(dom, dict):
            for key, val in dom.items():
                if hasattr(key, "anchor") and key.anchor.value is not None:
                    anchors[key.anchor.value] = key

                if hasattr(val, "anchor") and val.anchor.value is not None:
                    anchors[val.anchor.value] = val

                # Recurse into complex values
                if isinstance(val, (dict, list)):
                    Merger.scan_for_anchors(val, anchors)

        elif isinstance(dom, list):
            for ele in dom:
                Merger.scan_for_anchors(ele, anchors)

        elif hasattr(dom, "anchor"):
            anchors[dom.anchor.value] = dom

    @classmethod
    def rename_anchor(cls, dom: Any, anchor: str, new_anchor: str):
        """
        Rename every use of an anchor in a document.

        Parameters:
        1. dom (Any) The document to modify.
        2. anchor (str) The old anchor name to rename.
        3. new_anchor (str) The new name to apply to the anchor.

        Returns:  N/A
        """
        if isinstance(dom, dict):
            for key, val in dom.items():
                if hasattr(key, "anchor") and key.anchor.value == anchor:
                    key.anchor.value = new_anchor
                if hasattr(val, "anchor") and val.anchor.value == anchor:
                    val.anchor.value = new_anchor
                Merger.rename_anchor(val, anchor, new_anchor)
        elif isinstance(dom, list):
            for ele in dom:
                Merger.rename_anchor(ele, anchor, new_anchor)
        elif hasattr(dom, "anchor") and dom.anchor.value == anchor:
            dom.anchor.value = new_anchor

    @classmethod
    def replace_merge_anchor(
        cls, data: Any, old_node: Any, repl_node: Any
    ) -> None:
        """
        Replace anchor merge references.

        Anchor merge references in YAML are formed using the `<<: *anchor`
        operator.

        Parameters:
        1. data (Any) The DOM to adjust.
        2. old_node (Any) The former anchor node.
        3. repl_node (Any) The replacement anchor node.

        Returns:  N/A
        """
        if hasattr(data, "merge") and len(data.merge) > 0:
            for midx, merge_node in enumerate(data.merge):
                if merge_node[1] is old_node:
                    data.merge[midx] = (data.merge[midx][0], repl_node)

    @classmethod
    def replace_anchor(
        cls, data: Any, old_node: Any, repl_node: Any
    ) -> None:
        """
        Recursively replace every use of an anchor within a DOM.

        Parameters:
        1. data (Any) The DOM to adjust.
        2. old_node (Any) The former anchor node.
        3. repl_node (Any) The replacement anchor node.

        Returns:  N/A
        """
        anchor_name = repl_node.anchor.value
        if isinstance(data, dict):
            Merger.replace_merge_anchor(data, old_node, repl_node)
            for idx, key in [
                (idx, key) for idx, key in enumerate(data.keys())
                if hasattr(key, "anchor")
                    and key.anchor.value == anchor_name
            ]:
                Merger.replace_merge_anchor(key, old_node, repl_node)
                data.insert(idx, repl_node, data.pop(key))

            for key, val in data.items():
                Merger.replace_merge_anchor(key, old_node, repl_node)
                Merger.replace_merge_anchor(val, old_node, repl_node)
                if (hasattr(val, "anchor")
                        and val.anchor.value == anchor_name):
                    data[key] = repl_node
                else:
                    Merger.replace_anchor(val, old_node, repl_node)
        elif isinstance(data, list):
            for idx, ele in enumerate(data):
                Merger.replace_merge_anchor(ele, old_node, repl_node)
                if (hasattr(ele, "anchor")
                        and ele.anchor.value == anchor_name):
                    data[idx] = repl_node
                else:
                    Merger.replace_anchor(ele, old_node, repl_node)

    # pylint: disable=line-too-long
    @classmethod
    def delete_all_comments(cls, dom: Any) -> None:
        """
        Recursively delete all comments from a YAML document.

        See:  https://stackoverflow.com/questions/60080325/how-to-delete-all-comments-in-ruamel-yaml/60099750#60099750

        Parameters:
        1. dom (Any) The document to strip of all comments.

        Returns:  N/A
        """
        if isinstance(dom, dict):
            for key, val in dom.items():
                Merger.delete_all_comments(key)
                Merger.delete_all_comments(val)
        elif isinstance(dom, list):
            for ele in dom:
                Merger.delete_all_comments(ele)
        try:
            # literal scalarstring might have comment associated with them
            attr = "comment" if isinstance(dom, ScalarString) \
                else ruamel.yaml.comments.Comment.attrib
            delattr(dom, attr)
        except AttributeError:
            pass
