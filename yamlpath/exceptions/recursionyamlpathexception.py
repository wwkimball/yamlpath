"""
Implement RecursionYAMLPathException.

Copyright 2023 William W. Kimball, Jr. MBA MSIS
"""
from typing import Optional

from yamlpath.exceptions.yamlpathexception import YAMLPathException


class RecursionYAMLPathException(YAMLPathException):
    """
    Indicate a YAML Path causes an inescapable recursion loop.

    Occurs when a YAML Path is improperly formed or fails to lead to a required
    YAML node.
    """

    def __init__(
        self, user_message: str, yaml_path: str, segment: Optional[str] = None
    ) -> None:
        """
        Initialize this Exception with all pertinent data.

        Parameters:
        1. user_message (str) The message to convey to the user
        2. yaml_path (str) The stringified YAML Path which lead to the
           exception
        3. segment (Optional[str]) The segment of the YAML Path which triggered
           the exception, if available

        Returns:  N/A

        Raises:  N/A
        """
        super().__init__(
            user_message=user_message, yaml_path=yaml_path, segment=segment)
