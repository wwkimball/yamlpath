"""
Implement YAML document Merger.

Copyright 2019, 2020 William W. Kimball, Jr. MBA MSIS


=========
DEV NOTES
=========
yaml-merge [OPTIONS] file1 [file... [fileN]]

OPTIONS:
* DEFAULT behaviors when handling:
  * arrays (keep LHS, keep RHS, append uniques, append all [default])
  * hashes (keep LHS, keep RHS, deep merge [default])
  * arrays-of-hashes (requires identifier key; then regular hash options)
  * arrays-of-arrays (regular array options)
* anchor conflict handling (keep LHS, keep RHS, rename per file [aliases in
  same file follow suit], stop merge [default])
* merge-at (a YAML Path which indicates where in the LHS document all RHS
  documents are merged into [default=/])
* output (file)
* Configuration file for per-path options, like:
---
/just/an/array:  first|last|unique|all
/juat/a/hash:  first|last|shallow|deep
some.path.pointing.at.an.array.of.hashes:
  identity: key_with_unique_identifying_values
  merge: deep

Array-of-Arrays:
[[5,6],[1,2],[4,3]]
- - 5
  - 6
- - 1
  - 2
- - 4
  - 3

================================== EXAMPLE ====================================
aliases:
 - &scalar_anchor LHS aliased value
 - &unchanging_anchor Same value everywhere
key: LHS value
hash:
  key1: sub LHS value 1
  key2: sub LHS value 2
  complex:
    subkeyA: *scalar_anchor
array:
  - LHS element 1
  - non-unique element
  - *scalar_anchor
  - *unchanging_anchor

<< (RHS overrides LHS scalars;
    deep Hash merge;
    keep only unique Array elements; and
    rename conflicting anchors)

aliases:
 - &scalar_anchor RHS aliased value
 - &unchanging_anchor Same value everywhere
key: RHS value
hash:
  key1: sub RHS value 1
  key3: sub RHS value 3
  complex:
    subkeyA: *scalar_anchor
    subkeyB:
      - a
      - list
array:
  - RHS element 1
  - non-unique element
  - *scalar_anchor
  - *unchanging_anchor

==

aliases:
 - &scalar_anchor_1 LHS aliased value
 - &scalar_anchor_2 RHS aliased value
 - &unchanging_anchor Same value everywhere
key: RHS value
hash:
  key1: sub RHS value 1
  key2: sub LHS value 2
  key3: sub RHS value 3
  complex:
    subkeyA: *scalar_anchor_2  # Because "RHS overrides LHS scalars"
    subkeyB:
      - a
      - list
array:
  - LHS element 1
  - non-unique element
  - *scalar_anchor_1
  - *unchanging_anchor
  - RHS element 1
  - *scalar_anchor_2
===============================================================================

Processing Requirements:
1. Upon opening a YAML document, immediately scan the entire file for all
   anchor names.  Track those names across all documents as they are opened
   because conflicts must be resolved per user option selection.
2. LHS and RHS anchored maps must have identical names AND anchor names to be
   readily merged.  If only one of them is anchored, a merge is possible; keep
   the only anchor name on the map.  If they have different anchor names, treat
   as an anchor conflict and resolve per user option setting.
"""
from typing import Any

import ruamel.yaml
from ruamel.yaml.scalarstring import ScalarString

from yamlpath.wrappers import ConsolePrinter
from yamlpath.enums import AnchorConflictResolutions, HashMergeOpts
from yamlpath.func import append_list_element
from yamlpath import Processor


class Merger:
    """Performs YAML document merges."""

    def __init__(self, logger: ConsolePrinter, args: dict, lhs: Any,
            config: Processor) -> None:
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
        self.args: dict = args
        self.data: Any = lhs
        self.config: Processor = config

    def _merge_dicts(self, lhs: dict, rhs: dict, path: str = "") -> dict:
        """Merges two YAML maps (dicts)."""
        self.logger.debug(
            "Merger::_merge_dicts:  Evaluating dict at '{}'."
            .format(path))

        # lhs_is_dict = isinstance(lhs, dict)
        # rhs_is_dict = isinstance(rhs, dict)
        # if not rhs_is_dict:
        #     self.logger.error("The RHS data is not a Hash.", 30)
        # if not lhs_is_dict:
        #     self.logger.error("The LHS data is not a Hash.", 30)
        # if (rhs_is_dict and not lhs_is_dict) or (
        #         lhs_is_dict and not rhs_is_dict):
        #     self.logger.error("Incompatible data-types found at {}."
        #               .format(path), 30)

        # The document root is ALWAYS a Hash.  For everything deeper, do not
        # merge when the user sets LEFT|RIGHT Hash merge options.
        if len(path) > 0:
            merge_mode = HashMergeOpts.from_str(self.args.hashes)
            if merge_mode is HashMergeOpts.LEFT:
                return lhs
            if merge_mode is HashMergeOpts.RIGHT:
                return rhs

        # Deep merge
        buffer = []
        buffer_pos = 0
        for key, val in rhs.items():
            path_next = path + "/" + str(key).replace("/", "\\/")
            self.logger.debug(
                "Merger::_merge_dicts:  Processing key {}{} at '{}'."
                .format(key, type(key), path_next))
            if key in lhs:
                # Write the buffer if populated
                for b_key, b_val in buffer:
                    lhs.insert(buffer_pos, b_key, b_val)
                buffer = []

                # LHS has the RHS key
                if isinstance(val, dict):
                    lhs[key] = self._merge_dicts(
                        lhs[key], val, path_next)
                elif isinstance(val, list):
                    lhs[key] = self._merge_lists(
                        lhs[key], val, path_next)
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

    def _merge_lists(self, lhs: list, rhs: list, path: str = "") -> list:
        """Merge two lists."""
        for idx, ele in enumerate(rhs):
            path_next = path + "[{}]".format(idx)
            self.logger.debug(
                "Merger::_merge_lists:  Processing element {}{} at {}."
                .format(ele, type(ele), path_next))
            # TODO: Deeply traverse each element when non-scalar
            append_list_element(lhs, ele, ele.anchor.value)
        return lhs

    def _calc_unique_anchor(self, anchor: str, known_anchors: dict):
        """Generate a unique anchor name within a document pair."""
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

    def _resolve_anchor_conflicts(self, rhs):
        """Resolve anchor conflicts."""
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
            prime_alias = lhs_anchors[anchor]
            reader_alias = rhs_anchors[anchor]
            conflict_mode = AnchorConflictResolutions.from_str(
                self.args.anchors)

            if isinstance(prime_alias, dict):
                self.logger.error(
                    "Dictionary-based anchor conflict resolution is not yet"
                    " implemented.", 142)
            elif isinstance(prime_alias, list):
                self.logger.error(
                    "List-based anchor conflict resolution is not yet"
                    " implemented.", 142)
            else:
                if prime_alias != reader_alias:
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
                    elif conflict_mode is AnchorConflictResolutions.FIRST:
                        self.logger.debug(
                            "Anchor {} conflict; FIRST will override."
                            .format(anchor))
                        Merger.overwrite_aliased_values(
                            rhs, anchor, prime_alias)
                    elif conflict_mode is AnchorConflictResolutions.LAST:
                        self.logger.debug(
                            "Anchor {} conflict; LAST will override."
                            .format(anchor))
                        Merger.overwrite_aliased_values(
                            self.data, anchor, reader_alias)
                    else:
                        self.logger.error(
                            "Aborting due to anchor conflict, {}"
                            .format(anchor), 4)

    def merge_with(self, rhs: Any) -> None:
        """Merge this document with another."""
        # Remove all comments (no sensible way to merge them)
        Merger.delete_all_comments(rhs)

        # Resolve any anchor conflicts
        self._resolve_anchor_conflicts(rhs)

        # Loop through all elements in RHS
        if isinstance(rhs, dict):
            # The document root is a map
            self.data = self._merge_dicts(self.data, rhs)
        elif isinstance(rhs, list):
            # The document root is a list
            self.data = self._merge_lists(self.data, rhs)

    @classmethod
    def scan_for_anchors(cls, dom: Any, anchors: dict):
        """Scan a document for all anchors contained within."""
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
    def overwrite_aliased_values(cls, dom: Any, anchor: str, value: Any):
        """Replace the value of every alias of an anchor."""
        pass

    @classmethod
    def rename_anchor(cls, dom: Any, anchor: str, new_anchor: str):
        """Rename every use of an anchor in a document."""
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
