"""
Implements the SetMergeOpts enumeration.

Copyright 2021 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto
from typing import List


class SetMergeOpts(Enum):
    """
    Supported Set Merge Options.

    Options include:

    `LEFT`
        LHS Sets are not overwritten/appended by RHS Sets (no merge).

    `RIGHT`
        RHS Sets fully replace LHS Sets (no merge).

    `UNIQUE`
        Only RHS Set elements not alread in LHS Sets are appended to LHS Sets
        (merge).
    """

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
        return [entry.name.upper() for entry in SetMergeOpts]

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
        names = [l.lower() for l in SetMergeOpts.get_names()]
        choices = list(set(names))
        choices.sort()
        return choices

    @staticmethod
    def from_str(name: str) -> "SetMergeOpts":
        """
        Convert a string value to a value of this enumeration, if valid.

        Parameters:
            1. name (str) The name to convert

        Returns:  (SetMergeOpts) the converted enumeration value

        Raises:
            - `NameError` when name doesn't match any enumeration values
        """
        check: str = str(name).upper()
        if check in SetMergeOpts.get_names():
            return SetMergeOpts[check]
        raise NameError(
            "SetMergeOpts has no such item:  {}"
            .format(name))
