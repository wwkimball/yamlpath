"""
Implements the DiffActions enumeration.

Copyright 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto


class DiffActions(Enum):
    """
    The action taken for one document to become the next.

    `SAME`
        The two entries are identical.

    `ADD`
        Add an entry

    `DELETE`
        Remove an entry.

    `CHANGE_SPACE`
        Change an entry only by way of white-space.

    `CHANGE_VALUE`
        Change the value of an entry.
    """

    ADD = auto()
    ADD_ANCHOR = auto()
    ADD_COMMENT = auto()
    CHANGE_ANCHOR = auto()
    CHANGE_COMMENT = auto()
    CHANGE_DEMARCATION = auto()
    CHANGE_SPACE = auto()
    CHANGE_VALUE = auto()
    DELETE = auto()
    DELETE_ANCHOR = auto()
    DELETE_COMMENT = auto()
    SAME = auto()

    def __str__(self) -> str:
        """Get the string representation of this value."""
        action: str = ""
        if self is DiffActions.ADD:
            action = "+++"
        elif self is DiffActions.ADD_ANCHOR:
            action = "+++ &"
        elif self is DiffActions.ADD_COMMENT:
            action = "+++ #"
        elif self is DiffActions.CHANGE_ANCHOR:
            action = "&"
        elif self is DiffActions.CHANGE_COMMENT:
            action = "#"
        elif self is DiffActions.CHANGE_DEMARCATION:
            action = ""
        elif self is DiffActions.CHANGE_SPACE:
            action = ""
        elif self is DiffActions.CHANGE_VALUE:
            action = ""
        elif self is DiffActions.DELETE:
            action = "---"
        elif self is DiffActions.DELETE_ANCHOR:
            action = "--- &"
        elif self is DiffActions.DELETE_COMMENT:
            action = "--- #"

        return action
