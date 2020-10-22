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

    def __str__(self) -> str:
        """Get the diff-like entry code for this action."""
        diff_type = ""
        if self is DiffActions.ADD:
            diff_type = "a"
        elif self is DiffActions.CHANGE:
            diff_type = "c"
        elif self is DiffActions.DELETE:
            diff_type = "d"
        else:
            diff_type = "s"
        return diff_type
