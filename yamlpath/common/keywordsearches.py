"""
Implement KeywordSearches.

This is a static library of generally-useful code for searching data based on
pre-defined keywords (in the programming language sense).

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from typing import Any, Generator, List

from yamlpath.enums import PathSearchKeywords
from yamlpath.path import SearchKeywordTerms
from yamlpath.exceptions import YAMLPathException
from yamlpath.wrappers import NodeCoords
from yamlpath import YAMLPath
import yamlpath.common

class KeywordSearches:
    """Helper methods for common data searching operations."""

    @staticmethod
    def search_matches(
        terms: SearchKeywordTerms, haystack: Any, yaml_path: YAMLPath,
        **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """Perform a keyword search."""
        invert: bool = terms.inverted
        keyword: PathSearchKeywords = terms.keyword
        parameters: List[str] = terms.parameters
        nc_matches: Generator[NodeCoords, None, None]

        if keyword is PathSearchKeywords.HAS_CHILD:
            nc_matches = KeywordSearches.has_child(
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
        """Indicate whether data has a named child."""
        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        traverse_lists: bool = kwargs.pop("traverse_lists", True)
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))

        # There must be exactly one parameter
        param_count = len(parameters)
        if param_count != 1:
            raise YAMLPathException(
                ("Invalid parameter count to {}; {} required, got {} in"
                 " YAML Path").format(
                     PathSearchKeywords.HAS_CHILD, 1, param_count),
                str(yaml_path))
        match_key = parameters[0]

        # Against a map, this will return nodes which have an immediate
        # child key exactly named as per parameters.  When inverted, only
        # parents with no such key are yielded.
        if isinstance(data, dict):
            child_present = match_key in data
            if (
                (invert and not child_present) or
                (child_present and not invert)
            ):
                yield NodeCoords(
                    data, parent, parentref,
                    translated_path)

        # Against a list, this will merely require an exact match between
        # parameters and any list elements.  When inverted, every
        # non-matching element is yielded.
        elif isinstance(data, list):
            # Against an AoH, this will scan each element's immediate children,
            # treating and yielding as if this search were performed directly
            # against each map in the list.
            if yamlpath.common.Nodes.node_is_aoh(data):
                for idx, ele in enumerate(data):
                    next_path = translated_path.append("[{}]".format(str(idx)))
                    for aoh_match in KeywordSearches.has_child(
                        ele, invert, parameters, yaml_path,
                        parent=data, parentref=idx, translated_path=next_path,
                        traverse_lists=traverse_lists
                    ):
                        yield aoh_match
                return

            child_present = match_key in data
            if (
                (invert and not child_present) or
                (child_present and not invert)
            ):
                yield NodeCoords(
                    data, parent, parentref,
                    translated_path)

        else:
            raise YAMLPathException(
                ("{} data has no child nodes in YAML Path").format(type(data)),
                str(yaml_path))
