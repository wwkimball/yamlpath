"""
Implements the PathSegmentTypes enumeration.

Copyright 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto


class PathSegmentTypes(Enum):
    """
    Supported YAML Path segment types.

    These include:

    `ANCHOR`
        A named YAML Anchor.

    `COLLECTOR`
        A sub YAML Path for which the result will be returned as a list.  The
        data pointer is left where it was before the Collector expression is
        resolved.

    `INDEX`
        A list element index.

    `KEY`
        A dictionary key name.

    `SEARCH`
        A search operation for which results are returned as they are matched.

    `TRAVERSE`
        Traverses the document tree deeply.  If there is a next segment, it
        must match or no data is matched.  When there is no next segment, every
        leaf node matches.
    """

    ANCHOR = auto()
    COLLECTOR = auto()
    INDEX = auto()
    KEY = auto()
    SEARCH = auto()
    TRAVERSE = auto()
