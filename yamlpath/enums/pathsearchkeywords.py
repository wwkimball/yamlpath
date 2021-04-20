"""
Implements the PathSearchKeywords enumeration.

Copyright 2021 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto
from typing import List


class PathSearchKeywords(Enum):
    """
    Supported keyword methods for searching YAML Path segments.

    These include:

    `HAS_CHILD`
        Matches when the node has a direct child with a given name.
    `PARENT`
        Access the parent of the present node.
    """

    HAS_CHILD = auto()
    PARENT = auto()

    def __str__(self) -> str:
        """Get a String representation of an employed value of this enum."""
        keyword = ''
        if self is PathSearchKeywords.HAS_CHILD:
            keyword = 'has_child'
        elif self is PathSearchKeywords.PARENT:
            keyword = 'parent'

        return keyword

    @staticmethod
    def get_keywords() -> List[str]:
        """Return the full list of supported search keywords."""
        return [str(o).lower() for o in PathSearchKeywords]

    @staticmethod
    def is_keyword(keyword: str) -> bool:
        """Indicate whether keyword is known."""
        return keyword in PathSearchKeywords.get_keywords()
