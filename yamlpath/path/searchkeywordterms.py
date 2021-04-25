"""
Implement SearchKeywordTerms.

Copyright 2021 William W. Kimball, Jr. MBA MSIS
"""
from typing import List

from yamlpath.enums import PathSearchKeywords


class SearchKeywordTerms:
    """YAML path Search Keyword segment terms."""

    def __init__(
        self, inverted: bool, keyword: PathSearchKeywords, parameters: str
    ) -> None:
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
        return (
            "["
            + ("!" if self._inverted else "")
            + str(self._keyword)
            + "("
            + self._parameters
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
    # pylint: disable=locally-disabled,too-many-branches
    def parameters(self) -> List[str]:
        """Accessor for the parameters being fed to the search operation."""
        if self._parameters_parsed:
            return self._lparameters

        if self._parameters is None:
            self._parameters_parsed = True
            self._lparameters = []
            return self._lparameters

        param: str = ""
        params: List[str] = []
        escape_next: bool = False
        demarc_stack: List[str] = []
        demarc_count: int = 0

        # pylint: disable=locally-disabled,too-many-nested-blocks
        for char in self._parameters:
            demarc_count = len(demarc_stack)

            if escape_next:
                # Pass-through; capture this escaped character
                escape_next = False

            elif char == "\\":
                escape_next = True
                continue

            elif (
                    char == " "
                    and (demarc_count < 1)
            ):
                # Ignore unescaped, non-demarcated whitespace
                continue

            elif char in ['"', "'"]:
                # Found a string demarcation mark
                if demarc_count > 0:
                    # Already appending to an ongoing demarcated value
                    if char == demarc_stack[-1]:
                        # Close a matching pair
                        demarc_stack.pop()
                        demarc_count -= 1

                        if demarc_count < 1:
                            # Final close; seek the next delimiter
                            continue

                    else:
                        # Embed a nested, demarcated component
                        demarc_stack.append(char)
                        demarc_count += 1
                else:
                    # Fresh demarcated value
                    demarc_stack.append(char)
                    demarc_count += 1
                    continue

            elif demarc_count < 1 and char == ",":
                params.append(param)
                param = ""
                continue

            param = param + char

        # Check for mismatched demarcations
        if demarc_count > 0:
            raise ValueError(
                "Keyword search parameters contain one or more unmatched"
                " demarcation symbol(s): {}".format(" ".join(demarc_stack)))

        # Add the last parameter, if there is one
        if param:
            params.append(param)

        self._lparameters = params
        self._parameters_parsed = True
        return self._lparameters
