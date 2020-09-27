"""
Implements MergeException.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from typing import Optional, Union

from yamlpath import YAMLPath


class MergeException(Exception):
    """Express an issue with a document merge."""

    def __init__(self, user_message: str,
                 yaml_path: Optional[Union[YAMLPath, str]] = None) -> None:
        """
        Initialize this Exception with all pertinent data.

        Parameters:
        1. user_message (str) The message to convey to the user
        2. yaml_path (YAMLPath) Location within the document where the issue
           was found, if available.

        Returns:  N/A
        """
        self.user_message = user_message
        self.yaml_path = yaml_path

        super().__init__("user_message: {}, yaml_path: {}"
                         .format(user_message, yaml_path))

    def __str__(self) -> str:
        """Return a String expression of this Exception."""
        message: str = ""
        if self.yaml_path is None:
            message = "{}".format(self.user_message)
        else:
            message = "{}  This issue occurred at YAML Path:  {}".format(
                self.user_message,
                self.yaml_path)
        return message
