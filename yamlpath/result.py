"""YAML Path processing result.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from yamlpath import Path

class Result:
    """Enables YAML Path processing on virtual data along with set math.

    For example, when a YAML Path returns a set of scalars that were not
    sourced from the same Array, it is normally impossible to select one of
    those results as part of the same YAML Path expression; a virtual data set
    was returned and the selector is invalid within the source data.  Adding
    this Result handler enables YAML Paths to express further processing on the
    virtual output.  Further, set logic becomes possible, like:
        `(((path) - (path)) + (path))/2`
    """

    def __init__(self, yaml_path: Path) -> None:
        """Init this class.

        Positional Parameters:
          1. yaml_path (yamlpath.Path) A YAML Path parser instance

        Returns:  N/A

        Raises:  N/A
        """
        self._path = yaml_path
