"""Implements the PathSeperators enumeration.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto


class PathSeperators(Enum):
    """Supported representation formats for YAML values."""
    AUTO = auto()
    DOT = auto()
    FSLASH = auto()

    @staticmethod
    def get_names():
        """Returns all entry names for this enumeration.

        Positional Parameters:  N/A

        Returns:  (list) Upper-case names from this enumeration

        Raises:  N/A
        """
        return [entry.name.upper() for entry in PathSeperators]

    @staticmethod
    def from_str(name):
        """Converts a string value to a value of this enumeration, if valid.

        Positional Parameters:
          1. name (str) The name to convert

        Returns:  (PathSeperators) the converted enumeration value

        Raises:
          NameError when name doesn't match any enumeration values.
        """
        if isinstance(name, PathSeperators):
            return name

        check = str(name).upper()

        if check == '.':
            check = "DOT"
        elif check == '/':
            check = "FSLASH"

        if check in PathSeperators.get_names():
            return PathSeperators[check]
        else:
            raise NameError("PathSeperators has no such item, " + check)

    @staticmethod
    def to_seperator(name):
        seperator = '.'
        if name == PathSeperators.FSLASH:
            seperator = '/'

        return seperator
