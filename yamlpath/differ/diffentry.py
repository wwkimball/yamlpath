"""
Implement DiffEntry.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from typing import Any

from yamlpath import YAMLPath
from .enums.diffactions import DiffActions


class DiffEntry:
    """One entry of a diff."""

    def __init__(
        self, action: DiffActions, path: YAMLPath, lhs: Any, rhs: Any
    ):
        """Initiate a new DiffEntry."""
        self._action: DiffActions = action
        self._path: YAMLPath = path
        self._lhs: Any = lhs
        self._rhs: Any = rhs

    def __str__(self):
        """Get the string representation of this object."""
        diffaction = self._action
        output = "{}\n".format(self._path)
        if diffaction is DiffActions.ADD:
            output += "> {}".format(self._rhs)
        elif diffaction is DiffActions.CHANGE:
            output += "< {}\n---\n> {}".format(self._lhs, self._rhs)
        elif diffaction is DiffActions.DELETE:
            output += "< {}".format(self._lhs)
        else:
            output += "= {}".format(self._lhs)
        return output
