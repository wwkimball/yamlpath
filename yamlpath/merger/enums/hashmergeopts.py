"""
Implements the HashMergeOpts enumeration.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto
from typing import List


class HashMergeOpts(Enum):
    """
    Supported Hash (AKA: Map, dict) Merge Options.

    Options include:

    `DEEP`
        RHS Hashes are deeply merged into LHS Hashes (full merge).

    `LEFT`
        LHS Hashes are not overwritten by RHS Hashes (no merge).

    `RIGHT`
        RHS Hashes fully replace LHS Hashes (no merge).
    """

    DEEP = auto()
    LEFT = auto()
    RIGHT = auto()

    @staticmethod
    def get_names() -> List[str]:
        """
        Get all upper-cased entry names for this enumeration.

        Parameters:  N/A

        Returns:  (List[str]) Upper-case names from this enumeration

        Raises:  N/A
        """
        return [entry.name.upper() for entry in HashMergeOpts]

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
        names = [l.lower() for l in HashMergeOpts.get_names()]
        choices = list(set(names))
        choices.sort()
        return choices

    @staticmethod
    def from_str(name: str) -> "HashMergeOpts":
        """
        Convert a string value to a value of this enumeration, if valid.

        Parameters:
            1. name (str) The name to convert

        Returns:  (HashMergeOpts) the converted enumeration value

        Raises:
            - `NameError` when name doesn't match any enumeration values
        """
        check: str = str(name).upper()
        if check in HashMergeOpts.get_names():
            return HashMergeOpts[check]
        raise NameError(
            "HashMergeOpts has no such item:  {}"
            .format(name))
