"""
Implements the AnchorConflictResolutions enumeration.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto
from typing import List


class AnchorConflictResolutions(Enum):
    """
    Supported Anchor Conflict Resolutions.

    Resolutions include:

    `STOP`
        Abort the merge upon conflict detection.

    `LEFT`
        The first-encountered definition overrides all other uses.

    `RIGHT`
        The last-encountered definition overrides all other uses.

    `RENAME`
        Conflicting anchors are renamed within the affected documents.
    """

    STOP = auto()
    LEFT = auto()
    RIGHT = auto()
    RENAME = auto()

    @staticmethod
    def get_names() -> List[str]:
        """
        Get all upper-cased entry names for this enumeration.

        Parameters:  N/A

        Returns:  (List[str]) Upper-case names from this enumeration

        Raises:  N/A
        """
        return [entry.name.upper() for entry in AnchorConflictResolutions]

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
        names = [l.lower() for l in AnchorConflictResolutions.get_names()]
        choices = list(set(names))
        choices.sort()
        return choices

    @staticmethod
    def from_str(name: str) -> "AnchorConflictResolutions":
        """
        Convert a string value to a value of this enumeration, if valid.

        Parameters:
            1. name (str) The name to convert

        Returns:  (AnchorConflictResolutions) the converted enumeration value

        Raises:
            - `NameError` when name doesn't match any enumeration values
        """
        check: str = str(name).upper()
        if check in AnchorConflictResolutions.get_names():
            return AnchorConflictResolutions[check]
        raise NameError(
            "AnchorConflictResolutions has no such item:  {}"
            .format(name))
