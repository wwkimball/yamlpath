"""
Implement YAML document Merger.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from typing import Any, Dict, List, Set, Tuple
import json
from io import StringIO
from pathlib import Path

import ruamel.yaml # type: ignore
from ruamel.yaml.scalarstring import ScalarString
from ruamel.yaml.comments import CommentedSeq, CommentedMap

from yamlpath.func import (
    append_list_element,
    build_next_node,
)
from yamlpath.wrappers import ConsolePrinter, NodeCoords
from yamlpath.merger.exceptions import MergeException
from yamlpath.merger.enums import (
    AnchorConflictResolutions,
    AoHMergeOpts,
    ArrayMergeOpts,
    HashMergeOpts,
    OutputDocTypes,
)
from yamlpath.merger import MergerConfig
from yamlpath import YAMLPath, Processor


class Merger:
    """Performs YAML document merges."""

    def __init__(
            self, logger: ConsolePrinter, lhs: Any, config: MergerConfig
    ) -> None:
        """
        Instantiate this class into an object.

        Parameters:
        1. logger (ConsolePrinter) Instance of ConsoleWriter or subclass
        2. lhs (Any) The prime left-hand-side parsed YAML data
        3. config (MergerConfig) User-defined document merging rules

        Returns:  N/A

        Raises:  N/A
        """
        self.logger: ConsolePrinter = logger
        self.data: Any = lhs
        self.config: MergerConfig = config

        # ryamel.yaml unfortunately tracks comments AFTER each YAML node.  As
        # such, it is impossible to copy comments from RHS to LHS in any
        # sensible way.  Trying leads to absurd merge results that are data-
        # accurate but comment-insane.  This ruamel.yaml design decision forces
        # me to simply delete all comments from all merge documents to produce
        # a sensible result.
        Merger.delete_all_comments(self.data)

    def _delete_mergeref_keys(self, data: CommentedMap) -> None:
        """
        Delete all YAML merge reference keys from a CommentedMap.

        This is necessary when using the insert() method of a CommentedMap
        because doing so converts all YAML merge references (key-value pairs
        merged into a YAML Hash via the `<<:` operator) to concrete key-value
        pairs of the affected Hash.
        """
        concrete_keys = []
        for local_key, _ in data.non_merged_items():
            concrete_keys.append(local_key)

        reference_keys = set(data.keys()).difference(concrete_keys)
        for key in reference_keys:
            self.logger.debug(
                "Deleting key from LHS:",
                data=key, prefix="Merger::_delete_mergeref_keys:  ",
                header="!" * 50
            )
            del data[key]

    #pylint: disable=too-many-branches
    def _merge_dicts(
        self, lhs: CommentedMap, rhs: CommentedMap, path: YAMLPath
    ) -> CommentedMap:
        """
        Merge two YAML maps (CommentedMap-wrapped dicts).

        Parameters:
        1. lhs (CommentedMap) The merge target.
        2. rhs (CommentedMap) The merge source.
        3. path (YAMLPath) Location within the DOM where this merge is taking
           place.

        Keyword Parameters:
        * parent (Any) Parent node of `rhs`
        * parentref (Any) Child Key or Index of `rhs` within `parent`.

        Returns:  (CommentedMap) The merged result.

        Raises:
        - `MergeException` when a clean merge is impossible.
        """
        if not isinstance(lhs, CommentedMap):
            raise MergeException(
                "Impossible to add Hash data to non-Hash destination.", path)

        self.logger.debug(
            "Merging INTO dict with keys: {}:".format(", ".join(lhs.keys())),
            data=lhs, prefix="Merger::_merge_dicts:  ",
            header="--------------------")
        self.logger.debug(
            "Merging FROM dict with keys: {}:".format(", ".join(rhs.keys())),
            data=rhs, prefix="Merger::_merge_dicts:  ",
            footer="====================")

        # Delete all internal YAML merge reference keys lest any later
        # .insert() operation on LHS inexplicably convert them from reference
        # to concrete keys.  This seems like a bug in ruamel.yaml...
        self._delete_mergeref_keys(lhs)

        # Assume deep merge until a node's merge rule indicates otherwise
        buffer: List[Tuple[Any, Any]] = []
        buffer_pos = 0
        for key, val in rhs.non_merged_items():
            path_next = YAMLPath(path).append(str(key))
            if key in lhs:
                # Write the buffer if populated
                for b_key, b_val in buffer:
                    self.logger.debug(
                        "Merger::_merge_dicts:  Inserting key, {}, from"
                        " buffer to position, {}, at path, {}."
                        .format(b_key, buffer_pos, path_next),
                        header="INSERT " * 15)
                    self.logger.debug(
                        "Before INSERT, the LHS document was:",
                        data=lhs, prefix="Merger::_merge_dicts:  ")
                    self.logger.debug(
                        "... and before INSERT, the incoming value will be:",
                        data=b_val, prefix="Merger::_merge_dicts:  ")
                    lhs.insert(buffer_pos, b_key, b_val)
                    self.logger.debug(
                        "After INSERT, the LHS document became:",
                        data=lhs, prefix="Merger::_merge_dicts:  ")
                    buffer_pos += 1
                buffer = []

                # Short-circuit the deep merge if a different merge rule
                # applies to this node.
                node_coord = NodeCoords(val, rhs, key)
                merge_mode = (
                    self.config.hash_merge_mode(node_coord)
                    if isinstance(val, CommentedMap)
                    else self.config.aoh_merge_mode(node_coord)
                )
                self.logger.debug("Merger::_merge_dicts:  Got merge mode, {}."
                                  .format(merge_mode))
                if merge_mode in (HashMergeOpts.LEFT, AoHMergeOpts.LEFT):
                    continue
                if merge_mode in (HashMergeOpts.RIGHT, AoHMergeOpts.RIGHT):
                    self.logger.debug(
                        "Merger::_merge_dicts:  Overwriting key, {}, at path,"
                        " {}.".format(key, path_next),
                        header="OVERWRITE " * 15)
                    lhs[key] = val
                    continue

                if isinstance(val, CommentedMap):
                    lhs[key] = self._merge_dicts(lhs[key], val, path_next)
                    self.logger.debug(
                        "Document BEFORE calling combine_merge_anchors:",
                        data=lhs, prefix="Merger::_merge_dicts:  ",
                        header="+------------------+")
                    Merger.combine_merge_anchors(lhs[key], val)
                    self.logger.debug(
                        "Document AFTER calling combine_merge_anchors:",
                        data=lhs, prefix="Merger::_merge_dicts:  ",
                        footer="+==================+")
                elif isinstance(val, CommentedSeq):
                    lhs[key] = self._merge_lists(
                        lhs[key], val, path_next, parent=rhs, parentref=key)
                else:
                    self.logger.debug(
                        "Merger::_merge_dicts:  Updating key, {}, at path,"
                        " {}.".format(key, path_next), header="UPDATE " * 15)
                    self.logger.debug(
                        "Before UPDATE, the LHS document was:",
                        data=lhs, prefix="Merger::_merge_dicts:  ")
                    self.logger.debug(
                        "... and before UPDATE, the incoming value will be:",
                        data=val, prefix="Merger::_merge_dicts:  ")
                    lhs[key] = val
                    self.logger.debug(
                        "After UPDATE, the LHS document became:",
                        data=lhs, prefix="Merger::_merge_dicts:  ")
            else:
                # LHS lacks the RHS key.  Buffer this key-value pair in order
                # to insert it ahead of whatever key(s) follow this one in RHS
                # to keep anchor definitions before their aliases.
                buffer.append((key, val))

            buffer_pos += 1

        # Write any remaining buffered content to the end of LHS
        for b_key, b_val in buffer:
            self.logger.debug(
                "Merger::_merge_dicts:  Appending key, {}, from buffer at"
                " path, {}.".format(b_key, path), header="APPEND " * 15)
            lhs[b_key] = b_val

        self.logger.debug(
            "Completed merge result for path, {}:".format(path),
            data=lhs, prefix="Merger::_merge_dicts:  ")

        return lhs

    def _merge_simple_lists(
        self, lhs: CommentedSeq, rhs: CommentedSeq, path: YAMLPath,
        node_coord: NodeCoords
    ) -> CommentedSeq:
        """
        Merge two CommentedSeq-wrapped lists of Scalars or CommentedSeqs.

        Parameters:
        1. lhs (CommentedSeq) The merge target.
        2. rhs (CommentedSeq) The merge source.
        3. path (YAMLPath) Location within the DOM where this merge is taking
           place.
        4. node_coord (NodeCoords) The RHS root node, its parent, and reference
           within its parent; used for config lookups.

        Returns: (list) The merged result.

        Raises:
        - `MergeException` when a clean merge is impossible.
        """
        if not isinstance(lhs, CommentedSeq):
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
                "Processing element {} at {}.".format(idx, path_next),
                prefix="Merger::_merge_simple_lists:  ", data=ele)

            if append_all or (ele not in lhs):
                lhs.append(ele)
        return lhs

    # pylint: disable=locally-disabled,too-many-branches
    def _merge_arrays_of_hashes(
        self, lhs: CommentedSeq, rhs: CommentedSeq, path: YAMLPath,
        node_coord: NodeCoords
    ) -> CommentedSeq:
        """
        Merge two Arrays-of-Hashes.

        This is a deep merge operation.  Each dict is treated as a record with
        an identity key.  RHS records are merged with LHS records for which the
        identity key matches.  As such, an identity key is required in both LHS
        and RHS records.  This key is configurable.  When there is no LHS match
        for an RHS key, the RHS record is appended to the LHS list.

        Parameters:
        1. lhs (CommentedSeq) The merge target.
        2. rhs (CommentedSeq) The merge source.
        3. path (YAMLPath) Location within the DOM where this merge is taking
           place.
        4. node_coord (NodeCoords) The RHS root node, its parent, and reference
           within its parent; used for config lookups.

        Returns:  (CommentedSeq) The merged result.

        Raises:
        - `MergeException` when a clean merge is impossible.
        """
        if not isinstance(lhs, CommentedSeq):
            raise MergeException(
                "Impossible to add Array-of-Hash data to non-Array"
                " destination."
                , path)

        self.logger.debug(
            "Merging {} Hash(es) at {}.".format(len(rhs), path),
            prefix="Merger::_merge_arrays_of_hashes:  ", data=rhs)

        id_key: str = ""
        if len(rhs) > 0 and isinstance(rhs[0], CommentedMap):
            id_key = self.config.aoh_merge_key(
                NodeCoords(rhs[0], rhs, 0), rhs[0])
            self.logger.debug(
                "Merger::_merge_arrays_of_hashes:  RHS AoH yielded id_key:"
                "  {}.".format(id_key))

        merge_mode = self.config.aoh_merge_mode(node_coord)
        for idx, ele in enumerate(rhs):
            path_next = YAMLPath(path).append("[{}]".format(idx))
            self.logger.debug(
                "Processing element #{} at {}.".format(idx, path_next),
                prefix="Merger::_merge_arrays_of_hashes:  ", data=ele)

            if merge_mode is AoHMergeOpts.DEEP:
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
                    if isinstance(lhs_hash, CommentedMap)
                    and id_key in lhs_hash
                    and lhs_hash[id_key] == id_val
                ):
                    self._merge_dicts(lhs_hash, ele, path_next)
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
        self, lhs: CommentedSeq, rhs: CommentedSeq, path: YAMLPath,
        **kwargs: Any
    ) -> CommentedSeq:
        """
        Merge two lists; understands lists-of-dicts.

        Parameters:
        1. lhs (CommentedSeq) The list to merge into.
        2. rhs (CommentedSeq) The list to merge from.
        3. path (YAMLPath) Location of the `rhs` source list within its DOM.

        Keyword Parameters:
        * parent (Any) Parent node of `rhs`
        * parentref (Any) Child Key or Index of `rhs` within `parent`.

        Returns:  (CommentedSeq) The merged result.
        """
        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        node_coord = NodeCoords(rhs, parent, parentref)
        if len(rhs) > 0:
            if isinstance(rhs[0], CommentedMap):
                # This list is an Array-of-Hashes
                return self._merge_arrays_of_hashes(lhs, rhs, path, node_coord)

            # This list is an Array-of-Arrays or a simple list of Scalars
            return self._merge_simple_lists(lhs, rhs, path, node_coord)

        # No RHS list
        return lhs

    def _calc_unique_anchor(self, anchor: str, known_anchors: Set[str]) -> str:
        """
        Generate a unique anchor name within a document pair.

        Parameters:
        1. anchor (str) The original anchor name.
        2. known_anchors (dict) Dictionary of every anchor already in the
           document.

        Returns:  (str) The new, unique anchor name.
        """
        self.logger.debug(
            "Preexisting Anchors:", prefix="Merger::_calc_unique_anchor:  ",
            data=known_anchors)
        aid = 1
        while anchor in known_anchors:
            anchor = "{}_{}".format(anchor, aid)
            aid += 1
        return anchor

    def _resolve_anchor_conflicts(self, rhs: Any) -> None:
        """
        Resolve anchor conflicts between this and another document.

        Parameters:
        1. rhs (Any) The other document to consolidate with this one.

        Returns:  N/A
        """
        lhs_anchors: Dict[str, Any] = {}
        Merger.scan_for_anchors(self.data, lhs_anchors)
        self.logger.debug(
            "LHS Anchors:", prefix="Merger::_resolve_anchor_conflicts:  ",
            data=lhs_anchors)

        rhs_anchors: Dict[str, Any] = {}
        Merger.scan_for_anchors(rhs, rhs_anchors)
        self.logger.debug(
            "RHS Anchors:", prefix="Merger::_resolve_anchor_conflicts:  ",
            data=rhs_anchors)

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

            self.logger.debug(
                "Anchor is in both documents:",
                prefix="Merger::_resolve_anchor_conflicts:  ", data=anchor)
            self.logger.debug(
                "lhs_anchor:", prefix="Merger::_resolve_anchor_conflicts:  ",
                data=lhs_anchor)
            self.logger.debug(
                "rhs_anchor:", prefix="Merger::_resolve_anchor_conflicts:  ",
                data=rhs_anchor)

            if lhs_anchor != rhs_anchor:
                if conflict_mode is AnchorConflictResolutions.RENAME:
                    self.logger.debug(
                        "Anchor {} conflict; will RENAME anchors."
                        .format(anchor),
                        prefix="Merger::_resolve_anchor_conflicts:  ")
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
                        .format(anchor),
                        prefix="Merger::_resolve_anchor_conflicts:  ")
                    Merger.replace_anchor(rhs, rhs_anchor, lhs_anchor)
                elif conflict_mode is AnchorConflictResolutions.RIGHT:
                    self.logger.debug(
                        "Anchor {} conflict; RIGHT will override."
                        .format(anchor),
                        prefix="Merger::_resolve_anchor_conflicts:  ")
                    Merger.replace_anchor(self.data, lhs_anchor, rhs_anchor)
                else:
                    raise MergeException(
                        "Aborting due to anchor conflict with, {}."
                        .format(anchor))
            else:
                self.logger.debug(
                    "Anchor {} is symmetric; RIGHT will override to eliminate"
                    " spurious anchor re-definition.".format(anchor))
                # While the anchors are identical, the reference nodes are not.
                # So, overwrite all matching LHS nodes with their RHS
                # equivalents in order to stave off spurious anchor
                # re-definitions.
                Merger.replace_anchor(self.data, lhs_anchor, rhs_anchor)

    def merge_with(self, rhs: Any) -> None:
        """
        Merge this document with another.

        Parameters:
        1. rhs (Any) The document to merge into this one.

        Returns:  N/A

        Raises:
        - `MergeException` when a clean merge is impossible.
        """
        # Do nothing when RHS is None (empty document)
        if rhs is None:
            return

        # Remove all comments (no sensible way to merge them)
        Merger.delete_all_comments(rhs)

        # When LHS is None (empty document), just dump all of RHS into it,
        # honoring any --mergeat|-m location as best as possible.
        insert_at = self.config.get_insertion_point()
        if self.data is None:
            self.logger.debug(
                "Replacing None data with:", prefix="Merger::merge_with:  ",
                data=rhs, data_header="     *****")
            self.data = build_next_node(insert_at, 0, rhs)
            self.logger.debug(
                "Merged document is now:", prefix="Merger::merge_with:  ",
                data=self.data, footer="     ***** ***** *****")
            if isinstance(rhs, (dict, list)):
                # Only Scalar values need further processing
                return

        # Resolve any anchor conflicts
        self._resolve_anchor_conflicts(rhs)

        # Prepare the merge rules
        self.config.prepare(rhs)

        # Identify a reasonable default should a DOM need to be built up to
        # receive the RHS data.
        default_val = rhs
        if isinstance(rhs, CommentedMap):
            default_val = {}
        elif isinstance(rhs, CommentedSeq):
            default_val = []

        # Loop through all insertion points and the elements in RHS
        merge_performed = False
        nodes: List[NodeCoords] = []
        lhs_proc = Processor(self.logger, self.data)
        for node_coord in lhs_proc.get_nodes(
                insert_at, default_value=default_val
        ):
            nodes.append(node_coord)

        for node_coord in nodes:
            target_node = (node_coord.node
                if isinstance(node_coord.node, (CommentedMap, CommentedSeq))
                else node_coord.parent)

            Merger.set_flow_style(
                rhs, (target_node.fa.flow_style()
                      if hasattr(target_node, "fa")
                      else None))

            if isinstance(rhs, CommentedMap):
                # The RHS document root is a map
                if isinstance(target_node, CommentedSeq):
                    # But the destination is a list
                    self._merge_lists(
                        target_node, CommentedSeq([rhs]), insert_at)
                else:
                    self._merge_dicts(target_node, rhs, insert_at)
                merge_performed = True
            elif isinstance(rhs, CommentedSeq):
                # The RHS document root is a list
                self._merge_lists(target_node, rhs, insert_at)
                merge_performed = True
            else:
                # The RHS document root is a Scalar value
                target_node = node_coord.node
                if isinstance(target_node, CommentedSeq):
                    append_list_element(target_node, rhs)
                    merge_performed = True
                elif isinstance(target_node, CommentedMap):
                    raise MergeException(
                        "Impossible to add Scalar value, {}, to a Hash without"
                        " a key.  Change the value to a 'key: value' pair, a"
                        " '{{key: value}}' Hash, or change the merge target to"
                        " an Array or other Scalar value."
                        .format(rhs), insert_at)
                else:
                    lhs_proc.set_value(insert_at, rhs)
                    merge_performed = True

        self.logger.debug(
            "Completed merge operation, resulting in document:",
            prefix="Merger::merge_with:  ", data=self.data)

        if not merge_performed:
            raise MergeException(
                "A merge was not performed.  Ensure your target path matches"
                " at least one node in the left document(s).", insert_at)

    def prepare_for_dump(
        self, yaml_writer: Any, output_file: str = ""
    ) -> OutputDocTypes:
        """
        Prepare this merged document and its writer for final rendering.

        This coallesces the YAML writer's settings to, in particular,
        distinguish between YAML and JSON.  It will also force demarcation of
        every String key and value within the document when the output will be
        JSON.

        Parameters:
        1. yaml_writer (ruamel.yaml.YAML) The YAML document writer

        Returns:  (OutputDocTypes) One of:
          * OutputDocTypes.JSON:  The document and yaml_writer are JSON format.
          * OutputDocTypes.YAML:  The document and yaml_writer are YAML format.
        """
        # Check whether the user is forcing an output format
        doc_format = self.config.get_document_format()
        if doc_format is OutputDocTypes.AUTO:
            # Identify by file-extension, if it indicates a known type
            file_extension = (Path(output_file).suffix.lower()
                              if output_file else "")
            if file_extension in [".json", ".yaml", ".yml"]:
                is_flow = file_extension == ".json"
            else:
                # Check whether the document root is in flow or block format
                is_flow = True
                if hasattr(self.data, "fa"):
                    is_flow = self.data.fa.flow_style()
        else:
            is_flow = doc_format is OutputDocTypes.JSON

        if is_flow:
            # Dump the document as true JSON and reload it; this automatically
            # exlodes all aliases.
            xfer_buffer = StringIO()
            json.dump(self.data, xfer_buffer)
            xfer_buffer.seek(0)
            self.data = yaml_writer.load(xfer_buffer)

            # Ensure the writer doesn't emit a YAML Start-of-Document marker
            yaml_writer.explicit_start = False
        else:
            # Ensure block style output
            Merger.set_flow_style(self.data, False)

            # When writing YAML, ensure the document start mark is emitted
            yaml_writer.explicit_start = True

        return OutputDocTypes.JSON if is_flow else OutputDocTypes.YAML

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

        if isinstance(node, CommentedMap):
            for key, val in node.non_merged_items():
                Merger.set_flow_style(key, is_flow)
                Merger.set_flow_style(val, is_flow)
        elif isinstance(node, CommentedSeq):
            for ele in node:
                Merger.set_flow_style(ele, is_flow)

    @classmethod
    def scan_for_anchors(cls, dom: Any, anchors: Dict[str, Any]):
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
                    Merger.scan_for_anchors(val, anchors)

        elif isinstance(dom, CommentedSeq):
            for ele in dom:
                Merger.scan_for_anchors(ele, anchors)

        elif hasattr(dom, "anchor") and dom.anchor.value is not None:
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
        if isinstance(dom, CommentedMap):
            for key, val in dom.non_merged_items():
                if hasattr(key, "anchor") and key.anchor.value == anchor:
                    key.anchor.value = new_anchor
                if hasattr(val, "anchor") and val.anchor.value == anchor:
                    val.anchor.value = new_anchor
                Merger.rename_anchor(val, anchor, new_anchor)
        elif isinstance(dom, CommentedSeq):
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
    def combine_merge_anchors(cls, lhs: CommentedMap, rhs: CommentedMap):
        """Merge YAML merge keys."""
        for mele in rhs.merge:
            lhs.add_yaml_merge([mele])

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
        if isinstance(data, CommentedMap):
            Merger.replace_merge_anchor(data, old_node, repl_node)
            for idx, key in [
                (idx, key) for idx, key in enumerate(data.keys())
                if hasattr(key, "anchor")
                    and key.anchor.value == anchor_name
            ]:
                Merger.replace_merge_anchor(key, old_node, repl_node)
                data.insert(idx, repl_node, data.pop(key))

            for key, val in data.non_merged_items():
                Merger.replace_merge_anchor(key, old_node, repl_node)
                Merger.replace_merge_anchor(val, old_node, repl_node)
                if (hasattr(val, "anchor")
                        and val.anchor.value == anchor_name):
                    data[key] = repl_node
                else:
                    Merger.replace_anchor(val, old_node, repl_node)
        elif isinstance(data, CommentedSeq):
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
        if dom is None:
            return

        if isinstance(dom, CommentedMap):
            for key, val in dom.items():
                Merger.delete_all_comments(key)
                Merger.delete_all_comments(val)
        elif isinstance(dom, CommentedSeq):
            for ele in dom:
                Merger.delete_all_comments(ele)
        try:
            # literal scalarstring might have comment associated with them
            attr = "comment" if isinstance(dom, ScalarString) \
                else ruamel.yaml.comments.Comment.attrib
            delattr(dom, attr)
        except AttributeError:
            pass
