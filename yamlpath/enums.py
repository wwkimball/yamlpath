from enum import Enum, auto

class YAMLValueFormats(Enum):
    """Supported representation formats for YAML values."""
    BARE = auto()
    BOOLEAN = auto()
    DEFAULT = auto()
    DQUOTE = auto()
    FLOAT = auto()
    FOLDED = auto()
    INT = auto()
    LITERAL = auto()
    SQUOTE = auto()

    @staticmethod
    def get_names():
        """Returns all entry names for this enumeration.

        Positional Parameters:  N/A

        Returns:  (list) Upper-case names from this enumeration

        Raises:  N/A
        """
        return [entry.name.upper() for entry in YAMLValueFormats]

    @staticmethod
    def from_str(name):
        """Converts a string value to a value of this enumeration, if valid.

        Positional Parameters:
          1. name (str) The name to convert

        Returns:  (YAMLValueFormats) the converted enumeration value

        Raises:
          NameError when name doesn't match any enumeration values.
        """
        check = str(name).upper()
        if check in YAMLValueFormats.get_names():
            return YAMLValueFormats[check]
        else:
            raise NameError("YAMLValueFormats has no such item, " + check)

class PathSegmentTypes(Enum):
    """Supported YAML Path segments"""
    ANCHOR = auto()
    INDEX = auto()
    KEY = auto()
    SEARCH = auto()

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
        operator = "???"
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
        else:
            raise NotImplementedError

        return operator
