"""
Implements the PathSeparators enumeration.

Copyright 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto
from typing import List


class PathSeparators(Enum):
    """
    Supported YAML Path segment separators.

    Separators include:

    `AUTO`
        The separator must be manually dictated or automatically inferred from
        the YAML Path being evaluated.

    `DOT`
        YAML Path segments are separated via dots (.).

    `FSLASH`
        YAML Path segments are separated via forward-slashes (/).
    """

    AUTO = auto()
    DOT = auto()
    FSLASH = auto()

    def __str__(self) -> str:
        """Get a String representation of this employed enum's value."""
        separator = '.'
        if self is PathSeparators.FSLASH:
            separator = '/'
        return separator

    @staticmethod
    def get_names() -> List[str]:
        """
        Get all upper-cased entry names for this enumeration.

        Parameters:  N/A

        Returns:  (List[str]) Upper-case names from this enumeration

        Raises:  N/A
        """
        return [entry.name.upper() for entry in PathSeparators]

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
        names = [l.lower() for l in PathSeparators.get_names()]
        symbols = [str(e) for e in PathSeparators]
        choices = list(set(names + symbols))
        choices.sort()
        return choices

    @staticmethod
    def from_str(name: str) -> "PathSeparators":
        """
        Convert a string value to a value of this enumeration, if valid.

        Parameters:
            1. name (str) The name to convert

        Returns:  (PathSeparators) the converted enumeration value

        Raises:
            - `NameError` when name doesn't match any enumeration values
        """
        if isinstance(name, PathSeparators):
            return name

        check: str = str(name).upper()
        if check == '.':
            check = "DOT"
        elif check == '/':
            check = "FSLASH"

        if check in PathSeparators.get_names():
            return PathSeparators[check]
        raise NameError("PathSeparators has no such item, {}.".format(check))

    @staticmethod
    def infer_separator(yaml_path: str) -> "PathSeparators":
        """
        Infer the separator used within a sample YAML Path.

        Will attempt to return the best PathSeparators match.  Always returns
        `PathSeparators.AUTO` when the sample is empty.

        Parameters:
            1. yaml_path (str) The sample YAML Path to evaluate

        Returns: (PathSeparators) the inferred PathSeparators value

        Raises:  N/A
        """
        separator: PathSeparators = PathSeparators.AUTO

        if yaml_path:
            if yaml_path[0] == '/':
                separator = PathSeparators.FSLASH
            else:
                separator = PathSeparators.DOT

        return separator

    @staticmethod
    def infer_seperator(yaml_path: str) -> "PathSeparators":
        """
        Infer the separator used within a sample YAML Path.

        Will attempt to return the best PathSeparators match.  Always returns
        `PathSeparators.AUTO` when the sample is empty.

        This is provided for compatibility with older versions,
        before the spelling was updated to "separator."

        Parameters:
            1. yaml_path (str) The sample YAML Path to evaluate

        Returns: (PathSeparators) the inferred PathSeparators value

        Raises:  N/A
        """
        return PathSeparators.infer_separator(yaml_path)
