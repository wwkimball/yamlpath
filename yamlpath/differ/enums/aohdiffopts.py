"""
Implements the AoHDiffOpts enumeration.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto
from typing import List


class AoHDiffOpts(Enum):
    """
    Supported Array-of-Hash (AKA: List-of-Dictionaries) Diff Options.

    Options include:

    `DEEP`
        Like KEY except the record pairs are deeply traversed, looking for
        specific internal differences, after being matched up.

    `DPOS`
        Like POSITION (no KEY matching) except the record pairs are deeply
        traversed to report every specific difference between them.

    `KEY`
        AoH records are synchronized by their identity key before being
        compared as whole units (no deep traversal).

    `POSITION`
        AoH records are compared as whole units (no deep traversal) based on
        their ordinal position in each document.

    `VALUE`
        AoH records are synchronized as whole units (no deep traversal) before
        being compared.
    """

    DEEP = auto()
    DPOS = auto()
    KEY = auto()
    POSITION = auto()
    VALUE = auto()

    def __str__(self) -> str:
        """
        Stringify one instance of this enumeration.

        Parameters:  N/A

        Returns:  (str) String value of this enumeration.

        Raises:  N/A
        """
        return str(self.name).lower()

    @staticmethod
    def get_names() -> List[str]:
        """
        Get all upper-cased entry names for this enumeration.

        Parameters:  N/A

        Returns:  (List[str]) Upper-case names from this enumeration

        Raises:  N/A
        """
        return [entry.name.upper() for entry in AoHDiffOpts]

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
        names = [l.lower() for l in AoHDiffOpts.get_names()]
        choices = list(set(names))
        choices.sort()
        return choices

    @staticmethod
    def from_str(name: str) -> "AoHDiffOpts":
        """
        Convert a string value to a value of this enumeration, if valid.

        Parameters:
            1. name (str) The name to convert

        Returns:  (AoHDiffOpts) the converted enumeration value

        Raises:
            - `NameError` when name doesn't match any enumeration values
        """
        check: str = str(name).upper()
        if check in AoHDiffOpts.get_names():
            return AoHDiffOpts[check]
        raise NameError(
            "AoHDiffOpts has no such item:  {}"
            .format(name))
