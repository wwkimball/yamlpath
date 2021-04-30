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
    @pytest.mark.parametrize("match, method, needle, haystack", [
        (True, PathSearchMethods.CONTAINS, "a", "parents"),
        (True, PathSearchMethods.ENDS_WITH, "ts", "parents"),
        (True, PathSearchMethods.EQUALS, "parents", "parents"),
        (True, PathSearchMethods.EQUALS, 42, 42),
        (True, PathSearchMethods.EQUALS, "42", 42),
        (True, PathSearchMethods.EQUALS, 3.14159265385, 3.14159265385),
        (True, PathSearchMethods.EQUALS, "3.14159265385", 3.14159265385),
        (True, PathSearchMethods.EQUALS, True, True),
        (True, PathSearchMethods.EQUALS, "True", True),
        (True, PathSearchMethods.EQUALS, "true", True),
        (True, PathSearchMethods.EQUALS, False, False),
        (True, PathSearchMethods.EQUALS, "False", False),
        (True, PathSearchMethods.EQUALS, "false", False),
        (True, PathSearchMethods.GREATER_THAN, 2, 4),
        (True, PathSearchMethods.GREATER_THAN, "2", 4),
        (True, PathSearchMethods.GREATER_THAN, 2, "4"),
        (True, PathSearchMethods.GREATER_THAN, "2", "4"),
        (True, PathSearchMethods.GREATER_THAN, 2.1, 2.2),
        (True, PathSearchMethods.GREATER_THAN, "2.1", 2.2),
        (True, PathSearchMethods.GREATER_THAN, 2.1, "2.2"),
        (True, PathSearchMethods.GREATER_THAN, "2.1", "2.2"),
        (True, PathSearchMethods.GREATER_THAN, 2, 2.1),
        (True, PathSearchMethods.GREATER_THAN, "2", 2.1),
        (True, PathSearchMethods.GREATER_THAN, 2, "2.1"),
        (True, PathSearchMethods.GREATER_THAN, "2", "2.1"),
        (True, PathSearchMethods.GREATER_THAN, 2.9, 3),
        (True, PathSearchMethods.GREATER_THAN, "2.9", 3),
        (True, PathSearchMethods.GREATER_THAN, 2.9, "3"),
        (True, PathSearchMethods.GREATER_THAN, "2.9", "3"),
        (True, PathSearchMethods.GREATER_THAN_OR_EQUAL, 2, 4),
        (True, PathSearchMethods.GREATER_THAN_OR_EQUAL, "2", 4),
        (True, PathSearchMethods.GREATER_THAN_OR_EQUAL, 2, "4"),
        (True, PathSearchMethods.GREATER_THAN_OR_EQUAL, "2", "4"),
        (True, PathSearchMethods.GREATER_THAN_OR_EQUAL, 2.1, 2.2),
        (True, PathSearchMethods.GREATER_THAN_OR_EQUAL, "2.1", 2.2),
        (True, PathSearchMethods.GREATER_THAN_OR_EQUAL, 2.1, "2.2"),
        (True, PathSearchMethods.GREATER_THAN_OR_EQUAL, "2.1", "2.2"),
        (True, PathSearchMethods.GREATER_THAN_OR_EQUAL, 2, 2.1),
        (True, PathSearchMethods.GREATER_THAN_OR_EQUAL, "2", 2.1),
        (True, PathSearchMethods.GREATER_THAN_OR_EQUAL, 2, "2.1"),
        (True, PathSearchMethods.GREATER_THAN_OR_EQUAL, "2", "2.1"),
        (True, PathSearchMethods.GREATER_THAN_OR_EQUAL, 2.9, 3),
        (True, PathSearchMethods.GREATER_THAN_OR_EQUAL, "2.9", 3),
        (True, PathSearchMethods.GREATER_THAN_OR_EQUAL, 2.9, "3"),
        (True, PathSearchMethods.GREATER_THAN_OR_EQUAL, "2.9", "3"),
        (True, PathSearchMethods.LESS_THAN, 4, 2),
        (True, PathSearchMethods.LESS_THAN, "4", 2),
        (True, PathSearchMethods.LESS_THAN, 4, "2"),
        (True, PathSearchMethods.LESS_THAN, "4", "2"),
        (True, PathSearchMethods.LESS_THAN, 4.2, 4.1),
        (True, PathSearchMethods.LESS_THAN, "4.2", 4.1),
        (True, PathSearchMethods.LESS_THAN, 4.2, "4.1"),
        (True, PathSearchMethods.LESS_THAN, "4.2", "4.1"),
        (True, PathSearchMethods.LESS_THAN, 4.2, 4),
        (True, PathSearchMethods.LESS_THAN, "4.2", 4),
        (True, PathSearchMethods.LESS_THAN, 4.2, "4"),
        (True, PathSearchMethods.LESS_THAN, "4.2", "4"),
        (True, PathSearchMethods.LESS_THAN, 4, 3.9),
        (True, PathSearchMethods.LESS_THAN, "4", 3.9),
        (True, PathSearchMethods.LESS_THAN, 4, "3.9"),
        (True, PathSearchMethods.LESS_THAN, "4", "3.9"),
        (True, PathSearchMethods.LESS_THAN_OR_EQUAL, 4, 2),
        (True, PathSearchMethods.LESS_THAN_OR_EQUAL, "4", 2),
        (True, PathSearchMethods.LESS_THAN_OR_EQUAL, 4, "2"),
        (True, PathSearchMethods.LESS_THAN_OR_EQUAL, "4", "2"),
        (True, PathSearchMethods.LESS_THAN_OR_EQUAL, 4.2, 4.1),
        (True, PathSearchMethods.LESS_THAN_OR_EQUAL, "4.2", 4.1),
        (True, PathSearchMethods.LESS_THAN_OR_EQUAL, 4.2, "4.1"),
        (True, PathSearchMethods.LESS_THAN_OR_EQUAL, "4.2", "4.1"),
        (True, PathSearchMethods.LESS_THAN_OR_EQUAL, 4.2, 4),
        (True, PathSearchMethods.LESS_THAN_OR_EQUAL, "4.2", 4),
        (True, PathSearchMethods.LESS_THAN_OR_EQUAL, 4.2, "4"),
        (True, PathSearchMethods.LESS_THAN_OR_EQUAL, "4.2", "4"),
        (True, PathSearchMethods.LESS_THAN_OR_EQUAL, 4, 3.9),
        (True, PathSearchMethods.LESS_THAN_OR_EQUAL, "4", 3.9),
        (True, PathSearchMethods.LESS_THAN_OR_EQUAL, 4, "3.9"),
        (True, PathSearchMethods.LESS_THAN_OR_EQUAL, "4", "3.9"),
        (True, PathSearchMethods.REGEX, ".+", "a"),
        (True, PathSearchMethods.STARTS_WITH, "p", "parents")
    ])
    def test_search_matches(self, match, method, needle, haystack):
        assert match == Searches.search_matches(method, needle, haystack)

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
