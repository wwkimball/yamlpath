"""
Implement DiffEntry.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
import json
from typing import Any

from ruamel.yaml.comments import CommentedBase, TaggedScalar

from yamlpath.common import Parsers
from yamlpath.enums import PathSeperators
from yamlpath import YAMLPath
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
        self._key_tag = kwargs.pop("key_tag", None)
        self._set_index(lhs, rhs, **kwargs)
        self._verbose = False

    def _set_index(self, lhs: Any, rhs: Any, **kwargs) -> Any:
        """Build the sortable index for this entry."""
        lhs_lc = DiffEntry._get_index(lhs, kwargs.pop("lhs_parent", None))
        rhs_lc = DiffEntry._get_index(rhs, kwargs.pop("rhs_parent", None))
        lhs_iteration = kwargs.pop("lhs_iteration", 0)
        rhs_iteration = kwargs.pop("rhs_iteration", 0)
        lhs_iteration = 0 if lhs_iteration is None else lhs_iteration
        rhs_iteration = 0 if rhs_iteration is None else rhs_iteration
        lhs_line = float(lhs_lc)
        if lhs_line == 0.0 or self.action is DiffActions.ADD:
            lhs_lc, rhs_lc = rhs_lc, lhs_lc
        self._index = "{}.{}.{}.{}".format(
            lhs_lc, lhs_iteration, rhs_lc, rhs_iteration)

    def __str__(self) -> str:
        """Get the string representation of this object."""
        diffaction = self._action
        path = self._path if self._path else "-"
        key_tag = ""
        if self._key_tag:
            key_tag = " {}".format(self._key_tag)
        output = "{}{} {}{}\n".format(
            diffaction, self._index if self.verbose else "", path, key_tag)
        if diffaction is DiffActions.ADD:
            output += DiffEntry._present_data(self._rhs, ">")
        elif diffaction is DiffActions.CHANGE:
            output += "{}\n---\n{}".format(
                DiffEntry._present_data(self._lhs, "<"),
                DiffEntry._present_data(self._rhs, ">"))
        elif diffaction is DiffActions.DELETE:
            output += "{}".format(DiffEntry._present_data(self._lhs, "<"))
        else:
            output += "{}".format(DiffEntry._present_data(self._lhs, "="))
        return output

    @property
    def action(self) -> DiffActions:
        """Get the action of this difference (read-only)."""
        return self._action

    @property
    def path(self) -> YAMLPath:
        """Get the YAML Path of this difference (read-only)."""
        return self._path

    @property
    def lhs(self) -> Any:
        """Get the LHS value of this difference (read-only)."""
        return self._lhs

    @property
    def index(self) -> str:
        """Get the sortable index for this entry (read-only)."""
        return self._index

    @property
    def pathsep(self) -> PathSeperators:
        """Seperator used to delimit reported YAML Paths (accessor)."""
        return self._path.seperator

    @pathsep.setter
    def pathsep(self, value: PathSeperators) -> None:
        """Seperator used to delimit reported YAML Paths (mutator)."""
        # No unnecessary changes
        if value is not self.pathsep:
            self._path.seperator = value

    @property
    def verbose(self) -> bool:
        """Output verbosity (accessor)."""
        return self._verbose

    @verbose.setter
    def verbose(self, value: bool) -> None:
        """Output verbosity (mutator)."""
        # No unnecessary changes
        if value != self.verbose:
            self._verbose = value

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

    @classmethod
    def _present_data(cls, data: Any, prefix: str) -> str:
        """Stringify data."""
        json_safe_data = Parsers.jsonify_yaml_data(data)
        formatted_data = json_safe_data
        if isinstance(json_safe_data, str):
            formatted_data = json_safe_data.strip()
        json_data = json.dumps(formatted_data).replace(
                               "\\n", "\n{} ".format(prefix))
        data_tag = ""
        if isinstance(data, TaggedScalar) and data.tag.value:
            data_tag = "{} ".format(data.tag.value)
        return "{} {}{}".format(prefix, data_tag, json_data)
