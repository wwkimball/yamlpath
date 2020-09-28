"""
Implements the ArrayMergeOpts enumeration.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto
from typing import List


class ArrayMergeOpts(Enum):
    """
    Supported Array (AKA: List) Merge Options.

    Options include:

    `ALL`
        All RHS Arrays elements are appended to LHS Arrays (no deduplication).

    `LEFT`
        LHS Arrays are not overwritten/appended by RHS Arrays (no merge).

    `RIGHT`
        RHS Arrays fully replace LHS Arrays (no merge).

    `UNIQUE`
        Only unique RHS Array elements are appended to LHS Arrays (merge).
    """

    ALL = auto()
    LEFT = auto()
    RIGHT = auto()
    UNIQUE = auto()

    @staticmethod
    def get_names() -> List[str]:
        """
        Get all upper-cased entry names for this enumeration.

        Parameters:  N/A

        Returns:  (List[str]) Upper-case names from this enumeration

        Raises:  N/A
        """
        return [entry.name.upper() for entry in ArrayMergeOpts]

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
        names = [l.lower() for l in ArrayMergeOpts.get_names()]
        choices = list(set(names))
        choices.sort()
        return choices

    @staticmethod
    def from_str(name: str) -> "ArrayMergeOpts":
        """
        Convert a string value to a value of this enumeration, if valid.

        Parameters:
            1. name (str) The name to convert

        Returns:  (ArrayMergeOpts) the converted enumeration value

        Raises:
            - `NameError` when name doesn't match any enumeration values
        """
        check: str = str(name).upper()
        if check in ArrayMergeOpts.get_names():
            return ArrayMergeOpts[check]
        raise NameError(
            "ArrayMergeOpts has no such item:  {}"
            .format(name))
