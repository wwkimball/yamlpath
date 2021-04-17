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

class KeywordSearches:
    """Helper methods for common data searching operations."""

    @staticmethod
    def search_matches(
        terms: SearchKeywordTerms, haystack: Any, yaml_path: YAMLPath,
        **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """Performs a keyword search."""
        invert: bool = terms.inverted
        keyword: PathSearchKeywords = terms.keyword
        parameters: List[str] = terms.parameters
        nc_matches: Generator[NodeCoords, None, None] = False

        if keyword is PathSearchKeywords.HAS_CHILD:
            nc_matches = KeywordSearches.has_child(
                haystack, invert, parameters, yaml_path, **kwargs)
        else:
            raise NotImplementedError

        for nc_match in nc_matches:
            yield nc_match

    @staticmethod
    def has_child(
        data: Any, invert: bool, parameters: List[str], yaml_path: YAMLPath,
        **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """Indicate whether data has a named child."""
        parent = kwargs.pop("parent", None)
        parentref = kwargs.pop("parentref", None)
        traverse_lists = kwargs.pop("traverse_lists", True)
        translated_path = kwargs.pop("translated_path", YAMLPath(""))

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
            if not traverse_lists:
                return
            raise NotImplementedError

        # Against an AoH, this will scan each element's immediate children,
        # treating and yielding as if this search were performed directly
        # against each map in the list.
        else:
            raise NotImplementedError
