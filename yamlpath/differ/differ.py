"""
Implement YAML document Differ.

Copyright 2020 William W. Kimball, Jr. MBA MSIS

DEVELOPMENT NOTES

Desired Output:
$ yaml-diff file1 file2
path.to.CHANGE:
< ORIGINAL NODE
---
> NEW NODE

path.to.DELETION:
< ORIGINAL NODE

path.to.ADDITION:
> NEW NODE

$ echo $?
1

$ yaml-diff file1 file1

$ echo $?
0
"""
from typing import Any, Generator

from yamlpath.wrappers import ConsolePrinter
from .enums.diffactions import DiffActions
from .diffentry import DiffEntry
from .difflist import DiffList


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
        self._diffs: DiffList = DiffList()
        self._data: Any = document
        self._prime_diff(document)

    def compare_to(self, document: Any) -> None:
        """Perform the diff calculation."""
        if document is None and self._data is not None:
            # Report deletion of every node
            pass
        elif self._data is None and document is not None:
            # Report addition of every node
            pass
        elif isinstance(document, dict):
            self._diff_dicts(document)
        elif isinstance(document, list):
            self._diff_lists(document)
        else:
            self._diff_scalars(document)

    def get_report(self) -> Generator[str, None, None]:
        """Get the diff report."""
        for entry in self._diffs.get_all():
            yield str(entry)

    def _prime_diff(self, doc: Any) -> None:
        """Prime the diff report based on the initial document."""
        if isinstance(doc, dict):
            self.logger.debug("Differ::_prime_diff:  Adding an empty Hash.")
            self._diffs.append(DiffEntry(DiffActions.ADD, {}))
            self._diff_dicts(doc)
        elif isinstance(doc, list):
            self.logger.debug("Differ::_prime_diff:  Adding an empty Array.")
            self._diffs.append(DiffEntry(DiffActions.ADD, []))
            self._diff_lists(doc)
        else:
            self.logger.debug(
                "Adding a populated Scalar:", prefix="Differ::_prime_diff:  ",
                data=doc)
            self._diffs.append(DiffEntry(DiffActions.ADD, doc))

    def _diff_dicts(self, rhs: dict) -> None:
        """Diff two dicts."""
        if rhs is None:
            return

        for key, val in rhs.items():
            if isinstance(val, dict):
                self.logger.debug(
                    "Differ::_diff_dicts:  Adding an empty Hash for key, {}."
                    .format(key))
                self._diffs.append(DiffEntry(DiffActions.ADD, {key: {}}))
                self._diff_dicts(val)
            elif isinstance(val, list):
                self.logger.debug(
                    "Differ::_diff_dicts:  Adding an empty Array for key, {}."
                    .format(key))
                self._diffs.append(DiffEntry(DiffActions.ADD, {key: []}))
                self._diff_lists(val)
            else:
                self.logger.debug(
                    "Adding a populated Scalar for key, {}.".format(key),
                    prefix="Differ::_diff_dicts:  ", data=val)
                self._diffs.append(DiffEntry(DiffActions.ADD, {key: val}))

    def _diff_lists(self, rhs: Any) -> None:
        """Diff two lists."""
        if rhs is None:
            return

        for idx, ele in enumerate(rhs):
            if isinstance(ele, dict):
                self.logger.debug(
                    "Differ::_diff_lists:  Adding an empty Hash for element,"
                    " {}.".format(idx))
                self._diffs.append(DiffEntry(DiffActions.ADD, [idx, {}]))
                self._diff_dicts(ele)
            elif isinstance(ele, list):
                self.logger.debug(
                    "Differ::_diff_lists:  Adding an empty Array for element,"
                    " {}.".format(idx))
                self._diffs.append(DiffEntry(DiffActions.ADD, [idx, []]))
                self._diff_lists(ele)
            else:
                self.logger.debug(
                    "Adding a populated Scalar for element, {}.".format(idx),
                    prefix="Differ::_diff_lists:  ", data=ele)
                self._diffs.append(DiffEntry(DiffActions.ADD, [idx, ele]))

    def _diff_scalars(self, rhs: Any) -> None:
        """Diff two Scalar values."""
