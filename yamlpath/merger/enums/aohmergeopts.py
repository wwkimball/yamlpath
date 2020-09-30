"""
Implements the AoHMergeOpts enumeration.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto
from typing import List


class AoHMergeOpts(Enum):
    """
    Supported Array-of-Hash (AKA: List of Map, list of dict) Merge Options.

    Options include:

    `ALL`
        RHS Hashes are appended to the LHS Array (shallow merge with no
        de-duplication).

    `DEEP`
        RHS Hashes are deeply merged into LHS Hashes (full merge) IIF an
        identifier key is also provided via the --aohkey option.

    `LEFT`
        RHS Hashes are neither merged with nor appended to LHS Hashes (no
        merge).

    `RIGHT`
        LHS Hashes are discarded and fully replaced by RHS Hashes (no merge).

    `UNIQUE`
        RHS Hashes which do not already exist IN FULL within LHS are appended
        to the LHS Array (no merge).
    """

    ALL = auto()
    DEEP = auto()
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
        return [entry.name.upper() for entry in AoHMergeOpts]

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
        names = [l.lower() for l in AoHMergeOpts.get_names()]
        choices = list(set(names))
        choices.sort()
        return choices

    @staticmethod
    def from_str(name: str) -> "AoHMergeOpts":
        """
        Convert a string value to a value of this enumeration, if valid.

        Parameters:
            1. name (str) The name to convert

        Returns:  (AoHMergeOpts) the converted enumeration value

        Raises:
            - `NameError` when name doesn't match any enumeration values
        """
        check: str = str(name).upper()
        if check in AoHMergeOpts.get_names():
            return AoHMergeOpts[check]
        raise NameError(
            "AoHMergeOpts has no such item:  {}"
            .format(name))
