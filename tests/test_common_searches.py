import pytest

import ruamel.yaml as ry

from yamlpath.enums import AnchorMatches, PathSearchMethods
from yamlpath.path import SearchTerms
from yamlpath.common import Searches

class Test_common_searches():
    """Tests for the Searches helper class."""

    ###
    # search_matches
    ###
    def test_search_matches(self):
        method = PathSearchMethods.CONTAINS
        needle = "a"
        haystack = "parents"
        assert Searches.search_matches(method, needle, haystack) == True


    ###
    # search_anchor
    ###
    def test_search_anchor(self):
        anchor_value = "anchor_name"
        node = ry.scalarstring.PlainScalarString("anchored value", anchor=anchor_value)
        terms = SearchTerms(False, PathSearchMethods.CONTAINS, ".", "name")
        seen_anchors = []
        search_anchors = True
        include_aliases = True
        assert Searches.search_anchor(node, terms, seen_anchors, search_anchors=search_anchors, include_aliases=include_aliases) == AnchorMatches.MATCH
