"""
Implement DiffList.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from typing import Generator

from .diffentry import DiffEntry


class DiffList:
    """A diff report by way of a linked list."""

    def __init__(self) -> None:
        """
        Instantiate this class into an object.

        Parameters:  N/A

        Returns:  N/A

        Raises:  N/A
        """
        self._head: DiffEntry = None
        self._tail: DiffEntry = None

    def append(self, entry: DiffEntry) -> None:
        """Append an entry to the tail."""
        # def print_line(line):
        #     print("DiffList::append:  {}".format(line))

        # def print_entry(entry):
        #     print("-=- DiffEntry -=-")
        #     if entry is None:
        #         print("None")
        #     else:
        #         print(str(entry))
        #         print("   next:")
        #         if entry.next_entry is None:
        #             print("None")
        #         else:
        #             print(str(entry.next_entry))
        #     print("-=-=-=-=-=-=-=-=-")

        # print_line("Got entry:")
        # print_entry(entry)

        if self._tail is None:
            # print_line("... no tail")
            if self._head is None:
                # print_line("... no tail, no head")
                self._head = entry
                # print_line("... no tail, no head, head has been set")
            else:
                # print_line("... no tail, head is already set:")
                # print_entry(self._head)
                self._tail = entry
                self._head.next_entry = self._tail
                # print_line("... no tail, tail has been set")
        else:
            # print_line("... with tail:")
            # print_entry(self._tail)
            if self._head is None:
                # print_line("... with tail, but no head")
                self._head = self._tail
                self._tail = entry
                self._head.next_entry = self._tail
                # print_line("... with tail, but no head, head has been set")
            else:
                # print_line("... with tail, with head:")
                # print_entry(self._head)
                self._tail.next_entry = entry
                self._tail = entry
                # print_line("... with tail, with head, new tail has been set:")
                # print_entry(self._tail)

        # print_line("Final head:")
        # print_entry(self._head)
        # print_line("Final tail:")
        # print_entry(self._tail)

    def get_all(self) -> Generator[DiffEntry, None, None]:
        """Get a generator of all entries."""
        entry = self._head
        while entry is not None:
            yield entry
            entry = entry.next_entry
