"""
Implement KeywordSearches.

This is a static library of generally-useful code for searching data based on
pre-defined keywords (in the programming language sense).

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from typing import Any, Dict, Generator, List

from ruamel.yaml.comments import CommentedMap

from yamlpath.types import AncestryEntry, PathSegment
from yamlpath.enums import PathSearchKeywords, PathSearchMethods
from yamlpath.common import Anchors, Nodes, Searches
from yamlpath.path import SearchKeywordTerms
from yamlpath.exceptions import YAMLPathException
from yamlpath.wrappers import NodeCoords
from yamlpath import YAMLPath

class KeywordSearches:
    """Helper methods for common data searching operations."""

    @staticmethod
    def search_matches(
        terms: SearchKeywordTerms, haystack: Any, yaml_path: YAMLPath,
        **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """
        Perform a keyword search.

        Parameters:
        1. terms (SearchKeywordTerms) The search operation to perform
        2. haystack (Any) The data to evaluate
        3. yaml_path (YAMLPath) YAML Path containing this search keyword

        Keyword Arguments:  See each of the called KeywordSearches methods

        Returns:  (Generator[NodeCoords, None, None]) Matching data as it is
            generated
        """
        invert: bool = terms.inverted
        keyword: PathSearchKeywords = terms.keyword
        parameters: List[str] = terms.parameters
        nc_matches: Generator[NodeCoords, None, None]

        if keyword is PathSearchKeywords.HAS_CHILD:
            nc_matches = KeywordSearches.has_child(
                haystack, invert, parameters, yaml_path, **kwargs)
        elif keyword is PathSearchKeywords.NAME:
            nc_matches = KeywordSearches.name(
                invert, parameters, yaml_path, **kwargs)
        elif keyword is PathSearchKeywords.MAX:
            nc_matches = KeywordSearches.max(
                haystack, invert, parameters, yaml_path, **kwargs)
        elif keyword is PathSearchKeywords.MIN:
            nc_matches = KeywordSearches.min(
                haystack, invert, parameters, yaml_path, **kwargs)
        elif keyword is PathSearchKeywords.PARENT:
            nc_matches = KeywordSearches.parent(
                haystack, invert, parameters, yaml_path, **kwargs)
        else:
            raise YAMLPathException(
                "Unsupported search keyword {} in".format(keyword),
                str(yaml_path))

        for nc_match in nc_matches:
            yield nc_match

    @staticmethod
    # pylint: disable=locally-disabled,too-many-locals
    def has_child(
        data: Any, invert: bool, parameters: List[str], yaml_path: YAMLPath,
        **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """
        Indicate whether data has a named or anchored child.

        Parameters:
        1. data (Any) The data to evaluate
        2. invert (bool) Invert the evaluation
        3. parameters (List[str]) Parsed parameters
        4. yaml_path (YAMLPath) YAML Path begetting this operation

        Keyword Arguments:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent
        * relay_segment (PathSegment) YAML Path segment presently under
          evaluation
        * translated_path (YAMLPath) YAML Path indicating precisely which node
          is being evaluated
        * ancestry (List[AncestryEntry]) Stack of ancestors preceding the
          present node under evaluation

        Returns:  (Generator[NodeCoords, None, None]) each result as it is
            generated
        """
        # There must be exactly one parameter
        param_count = len(parameters)
        if param_count != 1:
            raise YAMLPathException(
                ("Invalid parameter count to {}; {} required, got {} in"
                 " YAML Path").format(
                     PathSearchKeywords.HAS_CHILD, 1, param_count),
                str(yaml_path))
        match_key = parameters[0]

        if match_key[0] == "&":
            matches = KeywordSearches._has_anchored_child(
                data, invert, parameters, yaml_path, **kwargs)
        else:
            matches = KeywordSearches._has_concrete_child(
                data, invert, parameters, yaml_path, **kwargs)

        for match in matches:
            yield match

    @staticmethod
    # pylint: disable=locally-disabled,too-many-locals
    def _has_concrete_child(
        data: Any, invert: bool, parameters: List[str], yaml_path: YAMLPath,
        **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """
        Indicate whether data has a named child.

        Parameters:
        1. data (Any) The data to evaluate
        2. invert (bool) Invert the evaluation
        3. parameters (List[str]) Parsed parameters
        4. yaml_path (YAMLPath) YAML Path begetting this operation

        Keyword Arguments:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent
        * relay_segment (PathSegment) YAML Path segment presently under
          evaluation
        * translated_path (YAMLPath) YAML Path indicating precisely which node
          is being evaluated
        * ancestry (List[AncestryEntry]) Stack of ancestors preceding the
          present node under evaluation

        Returns:  (Generator[NodeCoords, None, None]) each result as it is
            generated
        """
        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))
        ancestry: List[AncestryEntry] = kwargs.pop("ancestry", [])
        relay_segment: PathSegment = kwargs.pop("relay_segment", None)

        match_key = parameters[0]

        # Against a map, this will return nodes which have an immediate
        # child key exactly named as per parameters.  When inverted, only
        # parents with no such key are yielded.
        if isinstance(data, dict):
            child_present = data is not None and match_key in data
            if (
                (invert and not child_present) or
                (child_present and not invert)
            ):
                yield NodeCoords(
                    data, parent, parentref, translated_path, ancestry,
                    relay_segment)

        # Against a list, this will merely require an exact match between
        # parameters and any list elements.  When inverted, every
        # non-matching element is yielded.
        elif isinstance(data, list):
            # Against an AoH, this will scan each element's immediate children,
            # treating and yielding as if this search were performed directly
            # against each map in the list.
            if Nodes.node_is_aoh(data):
                for idx, ele in enumerate(data):
                    next_path = translated_path.append("[{}]".format(str(idx)))
                    for aoh_match in KeywordSearches._has_concrete_child(
                        ele, invert, parameters, yaml_path,
                        parent=data, parentref=idx, translated_path=next_path
                    ):
                        yield aoh_match
                return

            child_present = match_key in data
            if (
                (invert and not child_present) or
                (child_present and not invert)
            ):
                yield NodeCoords(
                    data, parent, parentref, translated_path, ancestry,
                    relay_segment)

        elif data is None:
            if invert:
                yield NodeCoords(
                    data, parent, parentref, translated_path, ancestry,
                    relay_segment)

        else:
            raise YAMLPathException(
                ("{} data has no child nodes in YAML Path").format(type(data)),
                str(yaml_path))

    @staticmethod
    # pylint: disable=locally-disabled,too-many-locals,too-many-branches,too-many-statements
    def _has_anchored_child(
        data: Any, invert: bool, parameters: List[str], yaml_path: YAMLPath,
        **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """
        Indicate whether data has an anchored child.

        Parameters:
        1. data (Any) The data to evaluate
        2. invert (bool) Invert the evaluation
        3. parameters (List[str]) Parsed parameters
        4. yaml_path (YAMLPath) YAML Path begetting this operation

        Keyword Arguments:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent
        * relay_segment (PathSegment) YAML Path segment presently under
          evaluation
        * translated_path (YAMLPath) YAML Path indicating precisely which node
          is being evaluated
        * ancestry (List[AncestryEntry]) Stack of ancestors preceding the
          present node under evaluation

        Returns:  (Generator[NodeCoords, None, None]) each result as it is
            generated
        """
        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))
        ancestry: List[AncestryEntry] = kwargs.pop("ancestry", [])
        relay_segment: PathSegment = kwargs.pop("relay_segment", None)

        match_key = parameters[0]
        anchor_name = match_key[1:] if match_key[0] == "&" else match_key

        if isinstance(data, CommentedMap):
            # Look for YAML Merge Keys by the Anchor name
            all_data = ancestry[0][0] if len(ancestry) > 0 else data
            all_anchors: Dict[str, Any] = {}
            Anchors.scan_for_anchors(all_data, all_anchors)
            compare_node = (all_anchors[anchor_name]
                            if anchor_name in all_anchors
                            else None)
            is_ymk_anchor = (
                compare_node is not None and isinstance(compare_node, dict))

            if is_ymk_anchor:
                child_present = False
                if hasattr(data, "merge") and len(data.merge) > 0:
                    # Ignore comparision if there is no source
                    for (idx, merge_node) in data.merge:
                        if merge_node == compare_node:
                            child_present = True
                            break

                if (
                    (invert and not child_present) or
                    (child_present and not invert)
                ):
                    yield NodeCoords(
                        data, parent, parentref, translated_path,
                        ancestry, relay_segment)
                    return

            # Look for Anchored keys; include merged nodes
            else:
                child_present = False
                for (key, val) in data.items():
                    key_anchor = Anchors.get_node_anchor(key)
                    val_anchor = Anchors.get_node_anchor(val)
                    if key_anchor and key_anchor == anchor_name:
                        child_present = True
                        break
                    if val_anchor and val_anchor == anchor_name:
                        child_present = True
                        break

                if (
                    (invert and not child_present) or
                    (child_present and not invert)
                ):
                    yield NodeCoords(
                        data, parent, parentref, translated_path,
                        ancestry, relay_segment)

        elif Nodes.node_is_aoh(data, accept_nulls=True):
            for idx, ele in enumerate(data):
                if ele is None:
                    continue

                next_path = translated_path.append("[{}]".format(str(idx)))
                next_ancestry = ancestry + [(data, idx)]
                for aoh_match in KeywordSearches._has_anchored_child(
                    ele, invert, parameters, yaml_path,
                    parent=data, parentref=idx, translated_path=next_path,
                    ancestry=next_ancestry
                ):
                    yield aoh_match

        elif isinstance(data, list):
            child_present = False
            for ele in data:
                ele_anchor = Anchors.get_node_anchor(ele)
                if ele_anchor and ele_anchor == anchor_name:
                    child_present = True
                    break

            if (
                (invert and not child_present) or
                (child_present and not invert)
            ):
                yield NodeCoords(
                    data, parent, parentref, translated_path,
                    ancestry, relay_segment)

    @staticmethod
    # pylint: disable=locally-disabled,too-many-locals
    def name(
        invert: bool, parameters: List[str], yaml_path: YAMLPath,
        **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """
        Match only the key-name of the present node.

        Parameters:
        1. invert (bool) Invert the evaluation
        2. parameters (List[str]) Parsed parameters
        3. yaml_path (YAMLPath) YAML Path begetting this operation

        Keyword Arguments:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent
        * relay_segment (PathSegment) YAML Path segment presently under
          evaluation
        * translated_path (YAMLPath) YAML Path indicating precisely which node
          is being evaluated
        * ancestry (List[AncestryEntry]) Stack of ancestors preceding the
          present node under evaluation

        Returns:  (Generator[NodeCoords, None, None]) each result as it is
            generated
        """
        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))
        ancestry: List[AncestryEntry] = kwargs.pop("ancestry", [])
        relay_segment: PathSegment = kwargs.pop("relay_segment", None)

        # There are no parameters
        param_count = len(parameters)
        if param_count > 1:
            raise YAMLPathException((
                "Invalid parameter count to {}(); {} are permitted, "
                " got {} in YAML Path"
                ).format(PathSearchKeywords.NAME, 0, param_count),
                str(yaml_path))

        if invert:
            raise YAMLPathException((
                "Inversion is meaningless to {}()"
                ).format(PathSearchKeywords.NAME),
                str(yaml_path))

        yield NodeCoords(
            parentref, parent, parentref, translated_path, ancestry,
            relay_segment)

    @staticmethod
    # pylint: disable=locally-disabled,too-many-locals,too-many-branches,too-many-statements
    def max(
        data: Any, invert: bool, parameters: List[str], yaml_path: YAMLPath,
        **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """
        Find whichever nodes/elements have a maximum value.

        Parameters:
        1. data (Any) The data to evaluate
        2. invert (bool) Invert the evaluation
        3. parameters (List[str]) Parsed parameters
        4. yaml_path (YAMLPath) YAML Path begetting this operation

        Keyword Arguments:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent
        * relay_segment (PathSegment) YAML Path segment presently under
          evaluation
        * translated_path (YAMLPath) YAML Path indicating precisely which node
          is being evaluated
        * ancestry (List[AncestryEntry]) Stack of ancestors preceding the
          present node under evaluation

        Returns:  (Generator[NodeCoords, None, None]) each result as it is
            generated
        """
        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))
        ancestry: List[AncestryEntry] = kwargs.pop("ancestry", [])
        relay_segment: PathSegment = kwargs.pop("relay_segment", None)

        # There may be 0 or 1 parameters
        param_count = len(parameters)
        if param_count > 1:
            raise YAMLPathException((
                "Invalid parameter count to {}([NAME]); up to {} permitted, "
                " got {} in YAML Path"
                ).format(PathSearchKeywords.MAX, 1, param_count),
                str(yaml_path))

        scan_node = parameters[0] if param_count > 0 else None
        match_value: Any = None
        match_nodes: List[NodeCoords] = []
        discard_nodes: List[NodeCoords] = []
        unwrapped_data: Any = NodeCoords.unwrap_node_coords(data)
        if Nodes.node_is_aoh(
            unwrapped_data, accept_nulls=True
        ):
            # A named child node is mandatory
            if scan_node is None:
                raise YAMLPathException((
                    "The {}([NAME]) Search Keyword requires a key name to scan"
                    " when evaluating an Array-of-Hashes in YAML Path"
                    ).format(PathSearchKeywords.MAX),
                    str(yaml_path))

            for idx, wrapped_ele in enumerate(data):
                ele = NodeCoords.unwrap_node_coords(wrapped_ele)
                next_path = translated_path + "[{}]".format(idx)
                next_ancestry = ancestry + [(data, idx)]
                if ele is not None and scan_node in ele:
                    eval_val = ele[scan_node]
                    if (match_value is None
                        or Searches.search_matches(
                            PathSearchMethods.GREATER_THAN, match_value,
                            eval_val)
                    ):
                        match_value = eval_val
                        discard_nodes.extend(match_nodes)
                        match_nodes = [
                            NodeCoords(
                                ele, data, idx, next_path, next_ancestry,
                                relay_segment)
                        ]
                        continue

                    if (match_value is None
                        or Searches.search_matches(
                            PathSearchMethods.EQUALS, match_value,
                            eval_val)
                    ):
                        match_nodes.append(NodeCoords(
                            ele, data, idx, next_path, next_ancestry,
                            relay_segment))
                        continue

                discard_nodes.append(NodeCoords(
                    ele, data, idx, next_path, next_ancestry,
                    relay_segment))

        elif isinstance(data, dict):
            # A named child node is mandatory
            if scan_node is None:
                raise YAMLPathException((
                    "The {}([NAME]) Search Keyword requires a key name to scan"
                    " when comparing Hash/map/dict children in YAML Path"
                    ).format(PathSearchKeywords.MAX),
                    str(yaml_path))

            for key, val in data.items():
                next_path = (
                    translated_path + YAMLPath.escape_path_section(
                        key, translated_path.seperator))
                next_ancestry = ancestry + [(data, key)]
                if isinstance(val, dict):
                    if val is not None and scan_node in val:
                        eval_val = val[scan_node]
                        if (match_value is None
                            or Searches.search_matches(
                                PathSearchMethods.GREATER_THAN, match_value,
                                eval_val)
                        ):
                            match_value = eval_val
                            discard_nodes.extend(match_nodes)
                            match_nodes = [
                                NodeCoords(
                                    val, data, key, next_path, next_ancestry,
                                    relay_segment)
                            ]
                            continue

                        if (match_value is None
                            or Searches.search_matches(
                                PathSearchMethods.EQUALS, match_value,
                                eval_val)
                        ):
                            match_nodes.append(NodeCoords(
                                val, data, key, next_path, next_ancestry,
                                relay_segment))
                            continue

                elif scan_node in data:
                    # The user probably meant to operate against the parent
                    raise YAMLPathException((
                        "The {}([NAME]) Search Keyword operates against"
                        " collections of data which share a common attribute"
                        " yet there is only a single node to consider.  Did"
                        " you mean to evaluate the parent of the selected"
                        " node?  Please review your YAML Path"
                        ).format(PathSearchKeywords.MAX),
                        str(yaml_path))

                discard_nodes.append(NodeCoords(
                    val, data, key, next_path, next_ancestry,
                    relay_segment))

        elif isinstance(data, list):
            # A named child node is useless
            if scan_node is not None:
                raise YAMLPathException((
                    "The {}([NAME]) Search Keyword cannot utilize a key name"
                    " when comparing Array/sequence/list elements to one"
                    " another in YAML Path"
                    ).format(PathSearchKeywords.MAX),
                    str(yaml_path))

            for idx, ele in enumerate(data):
                next_path = translated_path + "[{}]".format(idx)
                next_ancestry = ancestry + [(data, idx)]
                if (ele is not None
                    and (
                        match_value is None or
                        Searches.search_matches(
                            PathSearchMethods.GREATER_THAN, match_value,
                            ele)
                )):
                    match_value = ele
                    discard_nodes.extend(match_nodes)
                    match_nodes = [
                        NodeCoords(
                            ele, data, idx, next_path, next_ancestry,
                            relay_segment)
                    ]
                    continue

                if (ele is not None
                    and Searches.search_matches(
                        PathSearchMethods.EQUALS, match_value,
                        ele)
                ):
                    match_nodes.append(NodeCoords(
                        ele, data, idx, next_path, next_ancestry,
                        relay_segment))
                    continue

                discard_nodes.append(NodeCoords(
                    ele, data, idx, next_path, next_ancestry,
                    relay_segment))

        else:
            # Non-complex data is always its own maximum and does not invert
            match_value = data
            match_nodes = [
                NodeCoords(
                    data, parent, parentref, translated_path, ancestry,
                    relay_segment)
            ]

        yield_nodes = discard_nodes if invert else match_nodes
        for node_coord in yield_nodes:
            yield node_coord


    @staticmethod
    # pylint: disable=locally-disabled,too-many-locals,too-many-branches,too-many-statements
    def min(
        data: Any, invert: bool, parameters: List[str], yaml_path: YAMLPath,
        **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """
        Find whichever nodes/elements have a minimum value.

        Parameters:
        1. data (Any) The data to evaluate
        2. invert (bool) Invert the evaluation
        3. parameters (List[str]) Parsed parameters
        4. yaml_path (YAMLPath) YAML Path begetting this operation

        Keyword Arguments:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent
        * relay_segment (PathSegment) YAML Path segment presently under
          evaluation
        * translated_path (YAMLPath) YAML Path indicating precisely which node
          is being evaluated
        * ancestry (List[AncestryEntry]) Stack of ancestors preceding the
          present node under evaluation

        Returns:  (Generator[NodeCoords, None, None]) each result as it is
            generated
        """
        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))
        ancestry: List[AncestryEntry] = kwargs.pop("ancestry", [])
        relay_segment: PathSegment = kwargs.pop("relay_segment", None)

        # There may be 0 or 1 parameters
        param_count = len(parameters)
        if param_count > 1:
            raise YAMLPathException((
                "Invalid parameter count to {}([NAME]); up to {} permitted, "
                " got {} in YAML Path"
                ).format(PathSearchKeywords.MIN, 1, param_count),
                str(yaml_path))

        scan_node = parameters[0] if param_count > 0 else None
        match_value: Any = None
        match_nodes: List[NodeCoords] = []
        discard_nodes: List[NodeCoords] = []
        unwrapped_data: Any = NodeCoords.unwrap_node_coords(data)
        if Nodes.node_is_aoh(
            unwrapped_data, accept_nulls=True
        ):
            # A named child node is mandatory
            if scan_node is None:
                raise YAMLPathException((
                    "The {}([NAME]) Search Keyword requires a key name to scan"
                    " when evaluating an Array-of-Hashes in YAML Path"
                    ).format(PathSearchKeywords.MIN),
                    str(yaml_path))

            for idx, wrapped_ele in enumerate(data):
                ele = NodeCoords.unwrap_node_coords(wrapped_ele)
                next_path = translated_path + "[{}]".format(idx)
                next_ancestry = ancestry + [(data, idx)]
                if ele is not None and scan_node in ele:
                    eval_val = ele[scan_node]
                    if (match_value is None
                        or Searches.search_matches(
                            PathSearchMethods.LESS_THAN, match_value,
                            eval_val)
                    ):
                        match_value = eval_val
                        discard_nodes.extend(match_nodes)
                        match_nodes = [
                            NodeCoords(
                                ele, data, idx, next_path, next_ancestry,
                                relay_segment)
                        ]
                        continue

                    if (match_value is None
                        or Searches.search_matches(
                            PathSearchMethods.EQUALS, match_value,
                            eval_val)
                    ):
                        match_nodes.append(NodeCoords(
                            ele, data, idx, next_path, next_ancestry,
                            relay_segment))
                        continue

                discard_nodes.append(NodeCoords(
                    ele, data, idx, next_path, next_ancestry,
                    relay_segment))

        elif isinstance(data, dict):
            # A named child node is mandatory
            if scan_node is None:
                raise YAMLPathException((
                    "The {}([NAME]) Search Keyword requires a key name to scan"
                    " when comparing Hash/map/dict children in YAML Path"
                    ).format(PathSearchKeywords.MIN),
                    str(yaml_path))

            for key, val in data.items():
                next_ancestry = ancestry + [(data, key)]
                next_path = (
                    translated_path + YAMLPath.escape_path_section(
                        key, translated_path.seperator))
                if isinstance(val, dict):
                    if val is not None and scan_node in val:
                        eval_val = val[scan_node]
                        if (match_value is None
                            or Searches.search_matches(
                                PathSearchMethods.LESS_THAN, match_value,
                                eval_val)
                        ):
                            match_value = eval_val
                            discard_nodes.extend(match_nodes)
                            match_nodes = [
                                NodeCoords(
                                    val, data, key, next_path, next_ancestry,
                                    relay_segment)
                            ]
                            continue

                        if (match_value is None
                            or Searches.search_matches(
                                PathSearchMethods.EQUALS, match_value,
                                eval_val)
                        ):
                            match_nodes.append(NodeCoords(
                                val, data, key, next_path, next_ancestry,
                                relay_segment))
                            continue

                elif scan_node in data:
                    # The user probably meant to operate against the parent
                    raise YAMLPathException((
                        "The {}([NAME]) Search Keyword operates against"
                        " collections of data which share a common attribute"
                        " yet there is only a single node to consider.  Did"
                        " you mean to evaluate the parent of the selected"
                        " node?  Please review your YAML Path"
                        ).format(PathSearchKeywords.MIN),
                        str(yaml_path))

                discard_nodes.append(NodeCoords(
                    val, data, key, next_path, next_ancestry,
                    relay_segment))

        elif isinstance(data, list):
            # A named child node is useless
            if scan_node is not None:
                raise YAMLPathException((
                    "The {}([NAME]) Search Keyword cannot utilize a key name"
                    " when comparing Array/sequence/list elements to one"
                    " another in YAML Path"
                    ).format(PathSearchKeywords.MIN),
                    str(yaml_path))

            for idx, ele in enumerate(data):
                next_path = translated_path + "[{}]".format(idx)
                next_ancestry = ancestry + [(data, idx)]
                if (ele is not None
                    and (
                        match_value is None or
                        Searches.search_matches(
                            PathSearchMethods.LESS_THAN, match_value,
                            ele)
                )):
                    match_value = ele
                    discard_nodes.extend(match_nodes)
                    match_nodes = [
                        NodeCoords(
                            ele, data, idx, next_path, next_ancestry,
                            relay_segment)
                    ]
                    continue

                if (ele is not None
                    and Searches.search_matches(
                        PathSearchMethods.EQUALS, match_value,
                        ele)
                ):
                    match_nodes.append(NodeCoords(
                        ele, data, idx, next_path, next_ancestry,
                        relay_segment))
                    continue

                discard_nodes.append(NodeCoords(
                    ele, data, idx, next_path, next_ancestry,
                    relay_segment))

        else:
            # Non-complex data is always its own maximum and does not invert
            match_value = data
            match_nodes = [
                NodeCoords(
                    data, parent, parentref, translated_path, ancestry,
                    relay_segment)
            ]

        yield_nodes = discard_nodes if invert else match_nodes
        for node_coord in yield_nodes:
            yield node_coord

    @staticmethod
    # pylint: disable=locally-disabled,too-many-locals
    def parent(
        data: Any, invert: bool, parameters: List[str], yaml_path: YAMLPath,
        **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """
        Climb back up N parent levels in the data hierarchy.

        Parameters:
        1. data (Any) The data to evaluate
        2. invert (bool) Invert the evaluation; not possible for parent()
        3. parameters (List[str]) Parsed parameters
        4. yaml_path (YAMLPath) YAML Path begetting this operation

        Keyword Arguments:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent
        * relay_segment (PathSegment) YAML Path segment presently under
          evaluation
        * translated_path (YAMLPath) YAML Path indicating precisely which node
          is being evaluated
        * ancestry (List[AncestryEntry]) Stack of ancestors preceding the
          present node under evaluation

        Returns:  (Generator[NodeCoords, None, None]) each result as it is
            generated
        """
        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))
        ancestry: List[AncestryEntry] = kwargs.pop("ancestry", [])
        relay_segment: PathSegment = kwargs.pop("relay_segment", None)

        # There may be 0 or 1 parameters
        param_count = len(parameters)
        if param_count > 1:
            raise YAMLPathException((
                "Invalid parameter count to {}([STEPS]); up to {} permitted, "
                " got {} in YAML Path"
                ).format(PathSearchKeywords.PARENT, 1, param_count),
                str(yaml_path))

        if invert:
            raise YAMLPathException((
                "Inversion is meaningless to {}([STEPS])"
                ).format(PathSearchKeywords.PARENT),
                str(yaml_path))

        parent_levels: int = 1
        ancestry_len: int = len(ancestry)
        steps_max = ancestry_len
        if param_count > 0:
            try:
                parent_levels = int(parameters[0])
            except ValueError as ex:
                raise YAMLPathException((
                    "Invalid parameter passed to {}([STEPS]), {}; must be"
                    " unset or an integer number indicating how may parent"
                    " STEPS to climb in YAML Path"
                    ).format(PathSearchKeywords.PARENT, parameters[0]),
                    str(yaml_path)) from ex

        if parent_levels > steps_max:
            raise YAMLPathException((
                "Cannot {}([STEPS]) higher than the document root.  {} steps"
                " requested when {} available in YAML Path"
                ).format(PathSearchKeywords.PARENT, parent_levels, steps_max),
                str(yaml_path))

        if parent_levels < 1:
            # parent(0) is the present node
            yield NodeCoords(
                data, parent, parentref, translated_path, ancestry,
                relay_segment)
        else:
            for _ in range(parent_levels):
                translated_path.pop()
                (data, _) = ancestry.pop()
                ancestry_len -= 1

            parentref = ancestry[-1][1] if ancestry_len > 0 else None
            parent = ancestry[-1][0] if ancestry_len > 0 else None
            yield NodeCoords(
                data, parent, parentref, translated_path, ancestry,
                relay_segment)
