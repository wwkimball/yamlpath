"""
Implement DiffEntry.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
import json
from typing import Any

from ruamel.yaml.comments import CommentedBase

from yamlpath import YAMLPath
from yamlpath.func import stringify_dates
from .enums.diffactions import DiffActions


class DiffEntry:
    """One entry of a diff."""

    def __init__(
        self, action: DiffActions, path: YAMLPath, lhs: Any, rhs: Any,
        **kwargs
    ):
        """Initiate a new DiffEntry."""
        self._action: DiffActions = action
        self._path: YAMLPath = path
        self._lhs: Any = lhs
        self._rhs: Any = rhs
        self._set_line_col(lhs, rhs, **kwargs)

    @classmethod
    def _jsonify_data(cls, data: Any) -> str:
        """Generate JSON representation of data."""
        if isinstance(data, (list, dict)):
            return json.dumps(stringify_dates(data))
        return data

    @classmethod
    def _get_lc(cls, data: Any) -> str:
        """Get the line.column of a data element."""
        data_lc = "0.0"
        if isinstance(data, CommentedBase):
            dlc = data.lc
            data_lc = "{}.{}".format(
                dlc.line if dlc.line is not None else 0,
                dlc.col if dlc.col is not None else 0
            )
        return data_lc

    @classmethod
    def _get_index(cls, data: Any, parent: Any) -> str:
        """Get the document index of a data element."""
        data_lc = DiffEntry._get_lc(data)
        if data_lc == "0.0":
            data_lc = DiffEntry._get_lc(parent)
        return data_lc

    def _set_line_col(self, lhs: Any, rhs: Any, **kwargs) -> Any:
        """Sets the line-column number for this entry."""
        lhs_lc = DiffEntry._get_index(lhs, kwargs.pop("lhs_parent", None))
        rhs_lc = DiffEntry._get_index(rhs, kwargs.pop("rhs_parent", None))
        if lhs_lc == "0.0":
            lhs_lc = rhs_lc
            rhs_lc = "0.0"
        self._index = "{}.{}".format(lhs_lc, rhs_lc)

    def __str__(self) -> str:
        """Get the string representation of this object."""
        diffaction = self._action
        output = "{}{} {}\n".format(diffaction, self._index, self._path)
        if diffaction is DiffActions.ADD:
            output += "> {}".format(DiffEntry._jsonify_data(self._rhs))
        elif diffaction is DiffActions.CHANGE:
            output += "< {}\n---\n> {}".format(
                DiffEntry._jsonify_data(self._lhs),
                DiffEntry._jsonify_data(self._rhs))
        elif diffaction is DiffActions.DELETE:
            output += "< {}".format(DiffEntry._jsonify_data(self._lhs))
        else:
            output += "= {}".format(DiffEntry._jsonify_data(self._lhs))
        return output

    @property
    def action(self) -> DiffActions:
        """Get the action of this difference (read-only)."""
        return self._action
