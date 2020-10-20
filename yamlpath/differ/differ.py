"""
Implement YAML document Differ.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from typing import Any

from yamlpath.wrappers import ConsolePrinter


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

    def get_report(self) -> str:
        """Get the diff report."""

    def _diff_dicts(self, rhs: Any) -> None:
        """Diff two dicts."""

    def _diff_lists(self, rhs: Any) -> None:
        """Diff two lists."""

    def _diff_scalars(self, rhs: Any) -> None:
        """Diff two Scalar values."""
