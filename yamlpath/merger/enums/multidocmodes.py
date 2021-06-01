"""
Implements the MultiDocModes enumeration.

Copyright 2021 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto
from typing import List


class MultiDocModes(Enum):
    """
    Supported means of merging multi-document content.

    Options include:

    `CONDENSE_ALL`
        Merge all multi-documents up into single documents during the merge.

    `MERGE_ACROSS`
        Condence no multi-documents; rather, only merge documents "across" from
        right to left.

    `MATRIX_MERGE`
        Condence no multi-documents; rather, merge every RHS document into
        every LHS document.
    """

    CONDENSE_ALL = auto()
    MERGE_ACROSS = auto()
    MATRIX_MERGE = auto()

    @staticmethod
    def get_names() -> List[str]:
        """
        Get all upper-cased entry names for this enumeration.

        Parameters:  N/A

        Returns:  (List[str]) Upper-case names from this enumeration

        Raises:  N/A
        """
        return [entry.name.upper() for entry in MultiDocModes]

    @staticmethod
    def get_choices() -> List[str]:
        """
        Get all entry names with symbolic representations for this enumeration.

        All returned entries are lower-cased.

        Parameters:  N/A

        Returns:  (List[str]) Lower-case names and symbols from this
            enumeration

        Raises:  N/A
        """
        names = [l.lower() for l in MultiDocModes.get_names()]
        choices = list(set(names))
        choices.sort()
        return choices

    @staticmethod
    def from_str(name: str) -> "MultiDocModes":
        """
        Convert a string value to a value of this enumeration, if valid.

        Parameters:
            1. name (str) The name to convert

        Returns:  (MultiDocModes) the converted enumeration value

        Raises:
            - `NameError` when name doesn't match any enumeration values
        """
        check: str = str(name).upper()
        if check in MultiDocModes.get_names():
            return MultiDocModes[check]
        raise NameError(
            "MultiDocModes has no such item:  {}"
            .format(name))
