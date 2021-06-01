"""
Implement Searches, a static library of generally-useful code for searching.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
import re
from typing import Any, List

from yamlpath.enums import (
    AnchorMatches,
    PathSearchMethods,
)
from yamlpath.common import Anchors, Nodes
from yamlpath.types import PathAttributes
from yamlpath.path import SearchTerms


class Searches:
    """Helper methods for common data searching operations."""

    @staticmethod
    # pylint: disable=too-many-branches,too-many-statements
    def search_matches(
        method: PathSearchMethods, needle: str, haystack: Any
    ) -> bool:
        """
        Perform a search comparison.

        NOTE:  For less-than, greather-than and related operations, the test is
        whether `haystack` is less/greater-than `needle`.

        Parameters:
        1. method (PathSearchMethods) The search method to employ
        2. needle (str) The value to look for.
        3. haystack (Any) The value to look in.

        Returns:  (bool) True = comparision passes; False = comparison fails.
        """
        typed_haystack = Nodes.typed_value(haystack)
        typed_needle = Nodes.typed_value(needle)
        needle_type = type(typed_needle)
        matches: bool = False

        if method is PathSearchMethods.EQUALS:
            if isinstance(typed_haystack, bool) and needle_type is bool:
                matches = typed_haystack == typed_needle
            elif isinstance(typed_haystack, int) and needle_type is int:
                matches = typed_haystack == typed_needle
            elif isinstance(typed_haystack, float) and needle_type is float:
                matches = typed_haystack == typed_needle
            else:
                matches = str(typed_haystack) == str(needle)
        elif method is PathSearchMethods.STARTS_WITH:
            matches = str(typed_haystack).startswith(needle)
        elif method is PathSearchMethods.ENDS_WITH:
            matches = str(typed_haystack).endswith(needle)
        elif method is PathSearchMethods.CONTAINS:
            matches = needle in str(typed_haystack)
        elif method is PathSearchMethods.GREATER_THAN:
            if isinstance(typed_haystack, int):
                if isinstance(typed_needle, (int, float)):
                    matches = typed_haystack > typed_needle
                else:
                    matches = False
            elif isinstance(typed_haystack, float):
                if isinstance(typed_needle, (int, float)):
                    matches = typed_haystack > typed_needle
                else:
                    matches = False
            else:
                matches = str(typed_haystack) > str(needle)
        elif method is PathSearchMethods.LESS_THAN:
            if isinstance(typed_haystack, int):
                if isinstance(typed_needle, (int, float)):
                    matches = typed_haystack < typed_needle
                else:
                    matches = False
            elif isinstance(typed_haystack, float):
                if isinstance(typed_needle, (int, float)):
                    matches = typed_haystack < typed_needle
                else:
                    matches = False
            else:
                matches = str(typed_haystack) < str(needle)
        elif method is PathSearchMethods.GREATER_THAN_OR_EQUAL:
            if isinstance(typed_haystack, int):
                if isinstance(typed_needle, (int, float)):
                    matches = typed_haystack >= typed_needle
                else:
                    matches = False
            elif isinstance(typed_haystack, float):
                if isinstance(typed_needle, (int, float)):
                    matches = typed_haystack >= typed_needle
                else:
                    matches = False
            else:
                matches = str(typed_haystack) >= str(needle)
        elif method is PathSearchMethods.LESS_THAN_OR_EQUAL:
            if isinstance(typed_haystack, int):
                if isinstance(typed_needle, (int, float)):
                    matches = typed_haystack <= typed_needle
                else:
                    matches = False
            elif isinstance(typed_haystack, float):
                if isinstance(typed_needle, (int, float)):
                    matches = typed_haystack <= typed_needle
                else:
                    matches = False
            else:
                matches = str(typed_haystack) <= str(needle)
        elif method == PathSearchMethods.REGEX:
            matcher = re.compile(needle)
            matches = matcher.search(str(typed_haystack)) is not None
        else:
            raise NotImplementedError

        return matches

    @staticmethod
    def search_anchor(
        node: Any, terms: SearchTerms, seen_anchors: List[str], **kwargs: bool
    ) -> AnchorMatches:
        """
        Indicate whether a node has an Anchor matching given search terms.

        Parameters:
        1. node (Any) The node to search (the haystack)
        2. terms (SearchTerms) The search terms (the needle)
        3. seen_anchors (List[str]) Tracks whether the present Anchor under
           evaluation is really an Alias to another node

        Keyword Arguments:
        * search_anchors (bool) User-specific preference indicating whether to
          search Anchors and/or Aliases
        * include_aliases (bool) User-specified preference indicating whether
          to include Aliases in search results

        Returns:  (AnchorMatches) The search result
        """
        anchor_name = Anchors.get_node_anchor(node)
        if anchor_name is None:
            return AnchorMatches.NO_ANCHOR

        is_alias = True
        if anchor_name not in seen_anchors:
            is_alias = False
            seen_anchors.append(anchor_name)

        search_anchors: bool = kwargs.pop("search_anchors", False)
        if not search_anchors:
            retval = AnchorMatches.UNSEARCHABLE_ANCHOR
            if is_alias:
                retval = AnchorMatches.UNSEARCHABLE_ALIAS
            return retval

        include_aliases: bool = kwargs.pop("include_aliases", False)
        if is_alias and not include_aliases:
            return AnchorMatches.ALIAS_EXCLUDED

        retval = AnchorMatches.NO_MATCH
        matches = Searches.search_matches(
            terms.method, terms.term, anchor_name)
        if ((matches and not terms.inverted)
            or (terms.inverted and not matches)
        ):
            retval = AnchorMatches.MATCH
            if is_alias:
                retval = AnchorMatches.ALIAS_INCLUDED
        return retval

    @staticmethod
    def create_searchterms_from_pathattributes(
        rhs: PathAttributes
    ) -> SearchTerms:
        """
        Convert a PathAttributes instance to a SearchTerms instance.

        Parameters:
        1. rhs (PathAttributes) PathAttributes instance to convert

        Returns:  (SearchTerms) SearchTerms extracted from `rhs`
        """
        if isinstance(rhs, SearchTerms):
            newinst: SearchTerms = SearchTerms(
                rhs.inverted, rhs.method, rhs.attribute, rhs.term
            )
            return newinst
        raise AttributeError
