"""
Implements the ArrayDiffOpts enumeration.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto
from typing import List


class ArrayDiffOpts(Enum):
    """
    Supported Array (AKA: List) Diff Options.

    Options include:

    `POSITION`
        Array elements are compared based on their ordinal position in each
        document.

    `VALUE`
        Array alements are synchronized by value before being compared.
    """

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
        return [entry.name.upper() for entry in ArrayDiffOpts]

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
        names = [l.lower() for l in ArrayDiffOpts.get_names()]
        choices = list(set(names))
        choices.sort()
        return choices

    @staticmethod
    def from_str(name: str) -> "ArrayDiffOpts":
        """
        Convert a string value to a value of this enumeration, if valid.

        Parameters:
            1. name (str) The name to convert

        Returns:  (ArrayDiffOpts) the converted enumeration value

        Raises:
            - `NameError` when name doesn't match any enumeration values
        """
        check: str = str(name).upper()
        if check in ArrayDiffOpts.get_names():
            return ArrayDiffOpts[check]
        raise NameError(
            "ArrayDiffOpts has no such item:  {}"
            .format(name))
