"""
Implements the OutputDocTypes enumeration.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto
from typing import List


class OutputDocTypes(Enum):
    """
    Supported Output Document Types.

    Options include:

    `AUTO`
        The output type is inferred from the first source document.

    `JSON`
        Force output to be JSON.

    `YAML`
        Force output to be YAML.
    """

    AUTO = auto()
    JSON = auto()
    YAML = auto()

    @staticmethod
    def get_names() -> List[str]:
        """
        Get all upper-cased entry names for this enumeration.

        Parameters:  N/A

        Returns:  (List[str]) Upper-case names from this enumeration

        Raises:  N/A
        """
        return [entry.name.upper() for entry in OutputDocTypes]

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
        names = [l.lower() for l in OutputDocTypes.get_names()]
        choices = list(set(names))
        choices.sort()
        return choices

    @staticmethod
    def from_str(name: str) -> "OutputDocTypes":
        """
        Convert a string value to a value of this enumeration, if valid.

        Parameters:
            1. name (str) The name to convert

        Returns:  (OutputDocTypes) the converted enumeration value

        Raises:
            - `NameError` when name doesn't match any enumeration values
        """
        check: str = str(name).upper()
        if check in OutputDocTypes.get_names():
            return OutputDocTypes[check]
        raise NameError(
            "OutputDocTypes has no such item:  {}"
            .format(name))
