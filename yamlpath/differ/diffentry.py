"""
Implement DiffEntry.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from typing import Any

from .enums.diffactions import DiffActions


class DiffEntry:
    """One entry of a diff."""

    def __init__(
        self, action: DiffActions = DiffActions.ADD, value: Any = None
    ):
        """Initiate a new DiffEntry."""
        self.action: DiffActions = action
        self.value: Any = value
        self.next_entry: "DiffEntry" = None

    def __str__(self):
        """Get the string representation of this object."""
        return "{} {}".format(self._action.__str__(), self._value)

    @property
    def action(self) -> DiffActions:
        """Diff action (accessor)."""
        return self._action

    @action.setter
    def action(self, value: DiffActions) -> None:
        """Diff action (mutator)."""
        self._action = value

    @property
    def next_entry(self) -> "DiffEntry":
        """Next diff entry (accessor)."""
        return self._next_entry

    @next_entry.setter
    def next_entry(self, value: "DiffEntry") -> None:
        """Next diff entry (mutator)."""
        self._next_entry = value

    @property
    def value(self) -> Any:
        """Value stored by this entry (accessor)."""
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        """Value stored by this entry (mutator)."""
        self._value = value
