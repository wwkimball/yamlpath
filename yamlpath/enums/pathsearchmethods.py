"""Implements the PathSearchMethods enumeration."""
from enum import Enum, auto


class PathSearchMethods(Enum):
    """Supported methods for search YAML Path segments"""
    CONTAINS = auto()
    ENDS_WITH = auto()
    EQUALS = auto()
    STARTS_WITH = auto()
    GREATER_THAN = auto()
    LESS_THAN = auto()
    GREATER_THAN_OR_EQUAL = auto()
    LESS_THAN_OR_EQUAL = auto()
    REGEX = auto()

    @staticmethod
    def to_operator(method):
        """Converts a value of this enumeration into a human-friendly
        operator.

        Positional Parameters:
            1. method (PathSearchMethods) The enumeration value to convert

        Returns: (str) The operator

        Raises:
            NotImplementedError when method is unknown to this method.
        """
        operator = ""
        if method is PathSearchMethods.EQUALS:
            operator = "="
        elif method is PathSearchMethods.STARTS_WITH:
            operator = "^"
        elif method is PathSearchMethods.ENDS_WITH:
            operator = "$"
        elif method is PathSearchMethods.CONTAINS:
            operator = "%"
        elif method is PathSearchMethods.LESS_THAN:
            operator = "<"
        elif method is PathSearchMethods.GREATER_THAN:
            operator = ">"
        elif method is PathSearchMethods.LESS_THAN_OR_EQUAL:
            operator = "<="
        elif method is PathSearchMethods.GREATER_THAN_OR_EQUAL:
            operator = ">="
        elif method is PathSearchMethods.REGEX:
            operator = "=~"
        else:
            raise NotImplementedError

        return operator
