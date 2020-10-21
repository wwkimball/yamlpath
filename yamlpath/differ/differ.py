"""
Implement YAML document Differ.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from itertools import zip_longest
from typing import Any, Generator, List

from yamlpath import YAMLPath
from yamlpath.wrappers import ConsolePrinter
from .enums.diffactions import DiffActions
from .diffentry import DiffEntry


class Differ:
    """Calculates the difference between two YAML documents."""

    def __init__(self, logger: ConsolePrinter, document: Any) -> None:
        """
        Instantiate this class into an object.

        Parameters:
        1. logger (ConsolePrinter) Instance of ConsoleWriter or subclass
        2. document (Any) The basis document

        Returns:  N/A

        Raises:  N/A
        """
        self.logger: ConsolePrinter = logger
        self._data: Any = document
        self._diffs: List[DiffEntry] = []

    def compare_to(self, document: Any) -> None:
        """Perform the diff calculation."""
        self._diffs.clear()
        self._diff_between(YAMLPath(), self._data, document)

    def get_report(self) -> Generator[DiffEntry, None, None]:
        """Get the diff report."""
        for entry in self._diffs:
            yield entry

    def _purge_document(self, path: YAMLPath, data: Any):
        """Delete every node in the document."""
        if isinstance(data, dict):
            for key, val in data.items():
                next_path = YAMLPath(path).append(key)
                self._diffs.append(
                    DiffEntry(
                        DiffActions.DELETE, next_path, val, None,
                        lhs_parent=data))
        elif isinstance(data, list):
            for idx, _ in enumerate(data):
                next_path = YAMLPath(path).append("[{}]".format(idx))
                self._diffs.append(
                    DiffEntry(
                        DiffActions.DELETE, next_path, idx, None,
                        lhs_parent=data))
        else:
            if data is not None:
                self._diffs.append(
                    DiffEntry(DiffActions.DELETE, path, data, None)
                )

    def _add_everything(self, path: YAMLPath, data: Any) -> None:
        """Add every node in the document."""
        if isinstance(data, dict):
            for key, val in data.items():
                next_path = YAMLPath(path).append(key)
                self._diffs.append(
                    DiffEntry(
                        DiffActions.ADD, next_path, None, val,
                        rhs_parent=data))
        elif isinstance(data, list):
            for idx, ele in enumerate(data):
                next_path = YAMLPath(path).append("[{}]".format(idx))
                self._diffs.append(
                    DiffEntry(
                        DiffActions.ADD, next_path, None, ele,
                        rhs_parent=data))
        else:
            if data is not None:
                self._diffs.append(
                    DiffEntry(DiffActions.ADD, path, None, data)
                )

    def _diff_between(self, path: YAMLPath, lhs: Any, rhs: Any) -> None:
        """Calculate the differences between two document nodes."""
        # If the roots are different, delete all LHS and add all RHS.
        lhs_is_dict = isinstance(lhs, dict)
        lhs_is_list = isinstance(lhs, list)
        lhs_is_scalar = not (lhs_is_dict or lhs_is_list)
        rhs_is_dict = isinstance(rhs, dict)
        rhs_is_list = isinstance(rhs, list)
        rhs_is_scalar = not (rhs_is_dict or rhs_is_list)
        same_types = (
            (lhs_is_dict and rhs_is_dict)
            or (lhs_is_list and rhs_is_list)
            or (lhs_is_scalar and rhs_is_scalar)
        )
        if same_types:
            if lhs_is_dict:
                self._diff_dicts(path, lhs, rhs)
            elif lhs_is_list:
                self._diff_lists(path, lhs, rhs)
            else:
                self._diff_scalars(path, lhs, rhs)
        else:
            self._purge_document(path, lhs)
            self._add_everything(path, rhs)

    def _diff_dicts(self, path: YAMLPath, lhs: dict, rhs: dict) -> None:
        """Diff two dicts."""
        lhs_keys = set(lhs)
        rhs_keys = set(rhs)

        # Look for deleted keys
        for key in lhs_keys - rhs_keys:
            next_path = YAMLPath(path).append(key)
            self._diffs.append(
                DiffEntry(
                    DiffActions.DELETE, next_path, lhs[key], None,
                    lhs_parent=lhs))

        # Look for new keys
        for key in rhs_keys - lhs_keys:
            next_path = YAMLPath(path).append(key)
            self._diffs.append(
                DiffEntry(
                    DiffActions.ADD, next_path, None, rhs[key],
                    rhs_parent=rhs))

        # Recurse into the rest
        for key, val in [
            (key, val) for key, val in rhs.items()
            if key in lhs and key in rhs
        ]:
            next_path = YAMLPath(path).append(key)
            self._diff_between(next_path, lhs[key], val)

    def _diff_lists(self, path: YAMLPath, lhs: list, rhs: list) -> None:
        """Diff two lists."""
        idx = 0
        for (lele, rele) in zip_longest(lhs, rhs):
            next_path = YAMLPath(path).append("[{}]".format(idx))
            idx += 1
            if lele is None:
                self._diffs.append(
                    DiffEntry(
                        DiffActions.ADD, next_path, None, rele,
                        rhs_parent=rhs))
            elif rele is None:
                self._diffs.append(
                    DiffEntry(
                        DiffActions.DELETE, next_path, lele, None,
                        lhs_parent=lhs))
            else:
                self._diff_between(next_path, lele, rele)

    def _diff_scalars(self, path: YAMLPath, lhs: Any, rhs: Any) -> None:
        """Diff two Scalar values."""
        if lhs == rhs:
            self._diffs.append(
                DiffEntry(DiffActions.SAME, path, lhs, rhs)
            )
        else:
            self._diffs.append(
                DiffEntry(DiffActions.CHANGE, path, lhs, rhs)
            )
