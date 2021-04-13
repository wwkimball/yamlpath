"""
YAML path Keyword Search segment terms.

Copyright 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
from typing import List

from yamlpath.enums import PathSearchKeywords


class SearchKeywordTerms:
    """YAML path Keyword Search segment terms."""

    def __init__(self, inverted: bool, keyword: PathSearchKeywords,
                 parameters: List[str]) -> None:
        """
        Instantiate a Keyword Search Term segment.

        Parameters:
        1. inverted (bool) true = invert the search operation; false, otherwise
        2. keyword (PathSearchKeywords) the search keyword
        3. parameters (str) the parameters to the keyword-named operation
        """
        self._inverted: bool = inverted
        self._keyword: PathSearchKeywords = keyword
        self._parameters: str = parameters

    def __str__(self) -> str:
        """Get a String representation of this Keyword Search Term."""
        # Replace unescaped spaces with escaped spaces
        safe_parameters = ", ".join(
            r"\ ".join(
                list(map(
                    lambda ele: ele.replace(" ", r"\ ")
                    , self.parameters.split(r"\ ")
                ))
            ).replace(",", "\\,"))

        return (
            "["
            + ("!" if self.inverted else "")
            + str(self.keyword)
            + "("
            + safe_parameters
            + ")]"
        )

    @property
    def inverted(self) -> bool:
        """
        Access the inversion flag for this Keyword Search.

        This indicates whether the search logic is to be inverted.
        """
        return self._inverted

    @property
    def keyword(self) -> PathSearchKeywords:
        """
        Access the search keyword.

        This indicates what kind of search logic is to be performed.
        """
        return self._keyword

    @property
    def parameters(self) -> str:
        """
        Accessor for the parameters being fed to the search operation.
        """
        return self._parameters
