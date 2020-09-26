"""
Implement YAML document Merger.

Copyright 2020 William W. Kimball, Jr. MBA MSIS

=========
TODOs
=========
Processing Requirements:
1. LHS and RHS anchored maps must have identical names AND anchor names to be
   readily merged.  If only one of them is anchored, a merge is possible; keep
   the only anchor name on the map.  If they have different anchor names, treat
   as an anchor conflict and resolve per user option setting.
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
    HashMergeOpts,
    PathSeperators
)
from yamlpath.func import append_list_element, escape_path_section
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
        self, lhs: dict, rhs: dict, path: YAMLPath,
        parent: Any = None, parentref: Any = None,
    ) -> dict:
        """Merges two YAML maps (dicts)."""
        if not isinstance(lhs, dict):
            raise MergeException(
                "Impossible to add Hash data to non-Hash destination.", path)

        # The document root is ALWAYS a Hash.  For everything deeper, do not
        # merge when the user sets LEFT|RIGHT Hash merge options.
        node_coord = NodeCoords(rhs, parent, parentref)
        if len(path) > 0:
            merge_mode = self.config.hash_merge_mode(node_coord)
            if merge_mode is HashMergeOpts.LEFT:
                return lhs
            if merge_mode is HashMergeOpts.RIGHT:
                return rhs

        # Deep merge
        buffer = []
        buffer_pos = 0
        for key, val in rhs.items():
            path_next = path.append(str(key))
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
                        lhs[key], val, path_next, rhs, key)
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
        """Merge two lists of Scalars or lists."""
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
            path_next = path.append("[{}]".format(idx))
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
        """Merge two lists of dicts (Arrays-of-Hashes)."""
        if not isinstance(lhs, list):
            raise MergeException(
                "Impossible to add Array-of-Hash data to non-Array"
                " destination."
                , path)

        self.logger.debug(
            "Merger::_merge_arrays_of_hashes:  Merging {} Hash(es)."
            .format(len(rhs)))

        merge_mode = self.config.aoh_merge_mode(node_coord)
        if merge_mode is AoHMergeOpts.LEFT:
            return lhs
        if merge_mode is AoHMergeOpts.RIGHT:
            return rhs

        for idx, ele in enumerate(rhs):
            path_next = path.append("[{}]".format(idx))
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
                for lhs_hash in lhs:
                    if id_key in lhs_hash and lhs_hash[id_key] == id_val:
                        self._merge_dicts(lhs_hash, ele, path_next, rhs, idx)
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
                    self._overwrite_aliased_values(lhs_anchor, rhs)
                elif conflict_mode is AnchorConflictResolutions.RIGHT:
                    self.logger.debug(
                        "Anchor {} conflict; RIGHT will override."
                        .format(anchor))
                    self._overwrite_aliased_values(rhs_anchor, self.data)
                else:
                    raise MergeException(
                        "Aborting due to anchor conflict with, {}."
                        .format(anchor))

    def _overwrite_aliased_values(
        self, source_node: Any, target_dom: Any
    ) -> None:
        """
        Replace the value of every alias of an anchor.

        Parameters:
        1. source_node (Any) The original anchor with its value.
        2. target_dom (Any) The document in which to replace the value for
           every use of the source_node

        Returns:  N/A
        """
        def recursive_anchor_replace(
            data: Any, anchor_val: str, repl_node: Any
        ):
            if isinstance(data, dict):
                data_anchor = (data.anchor.value
                    if hasattr(data, "anchor") else "")
                self.logger.debug(
                    "Merger::_overwrite_aliased_values"
                    "::recursive_anchor_replace:  Entering a dict with keys:"
                    "  {}; and anchor={}."
                    .format(", ".join(data.keys()), data_anchor))
                for idx, key in [
                    (idx, key) for idx, key in enumerate(data.keys())
                    if hasattr(key, "anchor")
                        and key.anchor.value == anchor_val
                ]:
                    self.logger.debug(
                        "Merger::_overwrite_aliased_values"
                        "::recursive_anchor_replace:  REPLACING aliased key,"
                        " {}.".format(key))
                    data.insert(idx, repl_node, data.pop(key))

                for key, val in data.items():
                    key_anchor = (key.anchor.value
                        if hasattr(key, "anchor") else "")
                    val_anchor = (val.anchor.value
                        if hasattr(val, "anchor") else "")
                    self.logger.debug(
                        "Merger::_overwrite_aliased_values"
                        "::recursive_anchor_replace:  key_anchor={},"
                        " val_anchor={}".format(key_anchor, val_anchor))

                    if (hasattr(val, "anchor")
                            and val.anchor.value == anchor_val):
                        self.logger.debug(
                            "Merger::_overwrite_aliased_values"
                            "::recursive_anchor_replace:  REPLACING aliased"
                            " value of key, {}.".format(key))
                        data[key] = repl_node
                    else:
                        self.logger.debug(
                            "Merger::_overwrite_aliased_values"
                            "::recursive_anchor_replace:  Recursing into"
                            " non-matched value at key, {}.".format(key))
                        recursive_anchor_replace(
                            val, anchor_val, repl_node)
            elif isinstance(data, list):
                self.logger.debug(
                    "Merger::_overwrite_aliased_values"
                    "::recursive_anchor_replace:  Entering a list with {}"
                    " element(s).".format(len(data)))
                for idx, ele in enumerate(data):
                    ele_anchor = (ele.anchor.value
                        if hasattr(ele, "anchor") else "")
                    self.logger.debug(
                        "Merger::_overwrite_aliased_values"
                        "::recursive_anchor_replace:  ele_anchor={}."
                        .format(ele_anchor))

                    if (hasattr(ele, "anchor")
                            and ele.anchor.value == anchor_val):
                        self.logger.debug(
                            "Merger::_overwrite_aliased_values"
                            "::recursive_anchor_replace:  REPLACING aliased"
                            " value of list at index, {}.".format(idx))
                        data[idx] = repl_node
                    else:
                        self.logger.debug(
                            "Merger::_overwrite_aliased_values"
                            "::recursive_anchor_replace:  Recursing into"
                            " non-matched list element at index, {}."
                            .format(idx))
                        recursive_anchor_replace(ele, anchor_val, repl_node)
            else:
                self.logger.debug(
                    "Merger::_overwrite_aliased_values"
                    "::recursive_anchor_replace:  Stuck with a Scalar, {},"
                    " having Anchor, {}."
                    .format(data, data.anchor.value
                        if hasattr(data, "anchor") else "None"))

        # Python will treat the source and target anchors as distinct even
        # when their string values are identical.  This will cause the
        # resulting YAML to have duplicate anchor definitions, which is illegal
        # and would produce unusable output.  In order for Python to treat all
        # of the post-synchronized aliases as copies of each other -- and thus
        # produce a useful, de-duplicated YAML output -- a reference to the
        # source anchor node must be copied over the target nodes.  To do so, a
        # Path to at least one alias in the source document must be known.
        # With it, retrieve one of the source nodes and use it to recursively
        # overwrite every occurence of the same anchor within the target DOM.
        recursive_anchor_replace(
            target_dom, source_node.anchor.value, source_node)

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

        # Loop through all insertion points and the elements in RHS
        default_val = rhs
        if isinstance(rhs, dict):
            default_val = {}
        elif isinstance(rhs, list):
            default_val = []

        merge_performed = False
        for node_coord in lhs_proc.get_nodes(
                insert_at, default_value=default_val
        ):
            if isinstance(node_coord.node, (dict, list)):
                target_node = node_coord.node
            else:
                target_node = node_coord.parent

            if isinstance(rhs, dict):
                # The document root is a map
                self._merge_dicts(target_node, rhs, insert_at)
                merge_performed = True
            elif isinstance(rhs, list):
                # The document root is a list
                self._merge_lists(target_node, rhs, insert_at)
                merge_performed = True
            else:
                # The document root is a Scalar value
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
    def search_for_anchor(cls, dom: Any, anchor: str, path: str = "") -> str:
        """
        Returns the YAML Path to the first appearance of an Anchor.

        Parameters:
        1. dom (Any) The document to scan.
        2. anchor (str) The anchor name to search for.
        3. path (str) YAML Path tracking the scan location within `dom`.

        Returns:  (None|str) YAML Path to the first use of `anchor` within
        `dom` or None when it cannot be found.
        """
        if isinstance(dom, dict):
            for key, val in dom.items():
                path_next = path + "/{}".format(
                    escape_path_section(str(key), PathSeperators.FSLASH))
                if hasattr(key, "anchor") and key.anchor.value == anchor:
                    return path + "/&{}".format(anchor)
                if hasattr(val, "anchor") and val.anchor.value == anchor:
                    return path_next
                return Merger.search_for_anchor(val, anchor, path_next)
        elif isinstance(dom, list):
            for idx, ele in enumerate(dom):
                path_next = path + "[{}]".format(idx)
                return Merger.search_for_anchor(ele, anchor, path_next)
        elif hasattr(dom, "anchor") and dom.anchor.value == anchor:
            return path

        return None

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
