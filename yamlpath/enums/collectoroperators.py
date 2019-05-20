"""Implements the CollectorOperators enumeration.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto
from typing import List


class CollectorOperators(Enum):
    """Supported Collector operators."""
    ADDITION = auto()
    NONE = auto()
    SUBTRACTION = auto()

    @staticmethod
    def get_names() -> List[str]:
        """Returns all entry names for this enumeration.

        Positional Parameters:  N/A

        Returns:  (list) Upper-case names from this enumeration

        Raises:  N/A
        """
        return [entry.name.upper() for entry in CollectorOperators]

    @staticmethod
    def to_operator(name: "CollectorOperators") -> str:
        """Converts a value of this enumeration into a human-friendly
        operator.

        Positional Parameters:
            1. method (PathSearchMethods) The enumeration value to convert

        Returns: (str) The operator

        Raises:
            NotImplementedError when method is unknown to this method.
        """
        operator: str = ''
        if name is CollectorOperators.ADDITION:
            operator = '+'
        elif name is CollectorOperators.SUBTRACTION:
            operator = '-'

        return operator

    @staticmethod
    def from_operator(operator: str) -> "CollectorOperators":
        """Converts a string value to a value of this enumeration, if valid.

        Positional Parameters:
          1. name (str) The name to convert

        Returns:  (PathSeperators) the converted enumeration value

        Raises:
          NameError when name doesn't match any enumeration values.
        """
        if isinstance(operator, CollectorOperators):
            return operator

        check: str = str(operator).upper()

        if check == '+':
            check = "ADDITION"
        elif check == '-':
            check = "SUBTRACTION"

        if check in CollectorOperators.get_names():
            return CollectorOperators[check]
        raise NameError(
            "CollectorOperators has no such item, {}.".format(check))
