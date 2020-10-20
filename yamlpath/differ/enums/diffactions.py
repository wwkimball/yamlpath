"""
Implements the DiffActions enumeration.

Copyright 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto


class DiffActions(Enum):
    """
    The action taken for one document to become the next.

    `ADD`
        Add an entry

    `CHANGE`
        An entry has changed.

    `DELETE`
        Remove an entry.

    `SAME`
        The two entries are identical.
    """

    ADD = auto()
    CHANGE = auto()
    DELETE = auto()
    SAME = auto()
