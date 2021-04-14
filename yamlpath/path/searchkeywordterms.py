"""
YAML path Keyword Search segment terms.

Copyright 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
from typing import List

from yamlpath.enums import PathSearchKeywords


class SearchKeywordTerms:
    """YAML path Keyword Search segment terms."""

    def __init__(self, inverted: bool, keyword: PathSearchKeywords,
                 parameters: str) -> None:
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
        self._lparameters: List[str] = []
        self._parameters_parsed: bool = False

    def __str__(self) -> str:
        """Get a String representation of this Keyword Search Term."""
        # Replace unescaped spaces with escaped spaces
        safe_parameters = ", ".join(self.parameters)

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
    def parameters(self) -> List[str]:
        """Accessor for the parameters being fed to the search operation."""
        if self._parameters_parsed:
            return self._lparameters

        param = ""
        params = []
        escape_next = False
        for char in self._parameters:
            if escape_next:
                escape_next = False

            elif char == "\\":
                escape_next = True
                continue

            elif char == ",":
                params.append(param)
                param = ""
                continue

            param = param + char

        # Add the last parameter, if there is one
        if param:
            params.append(param)

        self._lparameters = params
        self._parameters_parsed = True
        return self._lparameters
