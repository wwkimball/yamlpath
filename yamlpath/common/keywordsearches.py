"""
Implement KeywordSearches.

This is a static library of generally-useful code for searching data based on
pre-defined keywords (in the programming language sense).

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from typing import Any, List

from yamlpath.enums import PathSearchKeywords
from yamlpath.path import SearchKeywordTerms


class KeywordSearches:
    """Helper methods for common data searching operations."""

    @staticmethod
    def search_matches(
        terms: SearchKeywordTerms,
        haystack: Any
    ) -> bool:
        """Performs a keyword search."""
        invert: bool = terms.inverted
        keyword: PathSearchKeywords = terms.keyword
        parameters: List[str] = terms.parameters

