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

    `NAME`
        Matches only the key-name or element-index of the present node,
        discarding any and all child node data.  Can be used to rename the
        matched key as long as the new name is unique within the parent, lest
        the preexisting node be overwritten.  Cannot be used to reassign an
        Array/sequence/list element to another position.

    `MAX`
        Matches whichever node(s) has/have the maximum value for a named child
        key or the maximum value within an Array/sequence/list.  When used
        against a scalar value, that value is always its own maximum.

    `MIN`
        Matches whichever node(s) has/have the minimum value for a named child
        key or the minimum value within an Array/sequence/list.  When used
        against a scalar value, that value is always its own minimum.

    `PARENT`
        Access the parent(s) of the present node.
    """

    HAS_CHILD = auto()
    NAME = auto()
    MAX = auto()
    MIN = auto()
    PARENT = auto()

    def __str__(self) -> str:
        """Get a String representation of an employed value of this enum."""
        keyword = ''
        if self is PathSearchKeywords.HAS_CHILD:
            keyword = 'has_child'
        elif self is PathSearchKeywords.NAME:
            keyword = 'name'
        elif self is PathSearchKeywords.MAX:
            keyword = 'max'
        elif self is PathSearchKeywords.MIN:
            keyword = 'min'
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
