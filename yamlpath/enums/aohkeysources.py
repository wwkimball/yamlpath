"""
Implements the AoHKeySources enumeration.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto
from typing import List


class AoHKeySources(Enum):
    """
    Supported Array-of-Hash DEEP merge Key Sources.

    Options include:

    `FIRST`
        The first key of the first Hash within an Array-of-Hashes is presumed
		the identifier key for all Hashes within that Array-of-Hashes.

    `CONFIG`
        An external configuration file dictates the identifier key for every
		Array-of-Hashes in the merge.  Any missing key causes a fatal error.
    """

    FIRST = auto()
    CONFIG = auto()

    @staticmethod
    def get_names() -> List[str]:
        """
        Get all upper-cased entry names for this enumeration.

        Parameters:  N/A

        Returns:  (List[str]) Upper-case names from this enumeration

        Raises:  N/A
        """
        return [entry.name.upper() for entry in AoHKeySources]

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
        names = [l.lower() for l in AoHKeySources.get_names()]
        symbols = [str(e) for e in AoHKeySources]
        choices = list(set(names + symbols))
        choices.sort()
        return choices

    @staticmethod
    def from_str(name: str) -> "AoHKeySources":
        """
        Convert a string value to a value of this enumeration, if valid.

        Parameters:
            1. name (str) The name to convert

        Returns:  (AoHKeySources) the converted enumeration value

        Raises:
            - `NameError` when name doesn't match any enumeration values
        """
        check: str = str(name).upper()
        if check in AoHKeySources.get_names():
            return AoHKeySources[check]
        raise NameError(
            "AoHKeySources has no such item:  {}"
            .format(name))
