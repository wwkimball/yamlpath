"""
Implements a reusable console print facility for simple command-line scripts.

Other implementations can easily wrap Python's standard logger/warning modules,
but this one does not because those are overkill for *simple* STDOUT/STDERR
printing (that must support squelching).

Requires an object on init which has the following properties:
  quiet:  <Boolean> suppresses all output except ConsolePrinter::error() and
          ::critical().
  verbose:  <Boolean> allows output from ConsolePrinter::verbose().
  debug:  <Boolean> allows output from ConsolePrinter::debug().

Copyright 2018, 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
import sys
from typing import Any, Dict, Generator, List, Set, Tuple, Union

from ruamel.yaml.comments import (
    CommentedBase,
    CommentedMap,
    CommentedSet,
    TaggedScalar
)

from yamlpath.wrappers.nodecoords import NodeCoords


class ConsolePrinter:
    """
    Generally-useful console messager.

    Writes INFO, VERBOSE, WARN, and DEBUG messages to STDOUT as well as ERROR
    messages to STDERR with multi-lne formatting.
    """

    def __init__(self, args):
        """
        Instantiate a ConsolePrinter.

        Positional Parameters:
        1. args (object) An object representing log level settings with these
           properties:
            - debug (Boolean) true = write debugging informational messages
            - verbose (Boolean) true = write verbose informational messages
            - quiet (Boolean) true = write only error messages

        Returns:  N/A

        Raises:  N/A
        """
        self.args = args

    def info(self, message):
        """
        Write an informational message to STDOUT unless quiet mode is active.

        Positional Parameters:
        1. message (str) The message to print

        Returns:  N/A

        Raises:  N/A
        """
        if not self.args.quiet:
            print(message)

    def verbose(self, message):
        """
        Write a verbose message to STDOUT.

        Writes only when verbose mode is active unless quiet mode is active.

        Positional Parameters:
        1. message (str) The message to print

        Returns:  N/A

        Raises:  N/A
        """
        if not self.args.quiet and (self.args.verbose or self.args.debug):
            print(message)

    def warning(self, message):
        """
        Write a warning message to STDOUT unless quiet mode is active.

        Positional Parameters:
        1. message (str) The message to print

        Returns:  N/A

        Raises:  N/A
        """
        if not self.args.quiet:
            print("WARNING:  " + str(message).replace("\n", "\nWARNING:  "))

    def error(self, message, exit_code=None):
        """
        Write a recoverable error message to STDERR.

        Optionally terminates the program, exiting with a specific error code.

        Positional Parameters:
        1. message (str) The message to print
        2. exit_code (int) The exit code to terminate the program with;
           default=None

        Returns:  N/A

        Raises:  N/A
        """
        print(
            "ERROR:  " + str(message).replace("\n", "\nERROR:  "),
            file=sys.stderr
        )
        print("Please try --help for more information.")
        sys.stdout.flush()

        # Optionally terminate program execution with a specified exit code
        if exit_code is not None:
            self.debug("Terminating with exit code, {}.".format(exit_code))
            sys.exit(exit_code)

    def critical(self, message, exit_code=1):
        """
        Write a critical, nonrecoverable failure message to STDERR and abend.

        Terminates the program, exiting with a specific error code.

        Positional Parameters:
        1. message (str) The message to print
        2. exit_code (int) The exit code to terminate the program with;
           default=1

        Returns:  N/A

        Raises:  N/A
        """
        print(
            "CRITICAL:  " + str(message).replace("\n", "\nCRITICAL:  "),
            file=sys.stderr
        )
        sys.stdout.flush()

        # Terminate program execution with a specified exit code
        self.debug("Terminating with exit code, {}.".format(exit_code))
        sys.exit(exit_code)

    def debug(self, message, **kwargs):
        """
        Write a debug message to STDOUT unless quiet mode is active.

        Dumps all key-value pairs of a dictionary or all elements of a list,
        when the message is either.

        Positional Parameters:
        1. message (str) The message to print

        Keyword Arguments:
        * data (Any) Data to recursively add to the DEBUG message
        * header (str) Line printed before the body of the DEBUG message
        * footer (str) Line printed after the body of the DEBUG message
        * prefix (str) String prefixed to every DEBUG line comprising the
          entirety of the DEBUG message, including any optional data
        * data_header (str) Line printed before the optional data, if any
        * data_footer (str) Line printed after the optional data, if any

        Returns:  N/A

        Raises:  N/A
        """
        if self.args.debug and not self.args.quiet:
            header = kwargs.pop("header", "")
            footer = kwargs.pop("footer", "")
            prefix = kwargs.pop("prefix", "")

            if header:
                print(ConsolePrinter._debug_prefix_lines(
                    "{}{}".format(prefix, header)))

            for line in ConsolePrinter._debug_dump(message, prefix=prefix):
                print(line)

            if "data" in kwargs:
                data_header = kwargs.pop("data_header", "")
                data_footer = kwargs.pop("data_footer", "")

                if data_header:
                    print(ConsolePrinter._debug_prefix_lines(
                        "{}{}".format(prefix, data_header)))

                for line in ConsolePrinter._debug_dump(
                    kwargs.pop("data"), prefix=prefix, print_type=True
                ):
                    print(line)

                if data_footer:
                    print(ConsolePrinter._debug_prefix_lines(
                        "{}{}".format(prefix, data_footer)))

            if footer:
                print(ConsolePrinter._debug_prefix_lines(
                    "{}{}".format(prefix, footer)))

    @staticmethod
    def _debug_prefix_lines(line: str) -> str:
        """Helper for debug."""
        return "DEBUG:  {}".format(str(line).replace("\n", "\nDEBUG:  "))

    @staticmethod
    def _debug_get_anchor(data: Any) -> str:
        """Helper for debug."""
        return ("&{}".format(data.anchor.value)
                if hasattr(data, "anchor") and data.anchor.value is not None
                else "")

    @staticmethod
    def _debug_get_tag(data: Any) -> str:
        """Helper for debug."""
        return str(data.tag.value
                if hasattr(data, "tag") and data.tag.value is not None
                else "")

    @staticmethod
    def _debug_dump(data: Any, **kwargs) -> Generator[str, None, None]:
        """Helper for debug."""
        prefix = kwargs.pop("prefix", "")
        if isinstance(data, dict):
            for line in ConsolePrinter._debug_dict(
                data, prefix=prefix, **kwargs
            ):
                yield line
        elif isinstance(data, (list, set, tuple)):
            for line in ConsolePrinter._debug_list(
                data, prefix=prefix, **kwargs
            ):
                yield line
        elif isinstance(data, NodeCoords):
            for line in ConsolePrinter._debug_node_coord(
                data, prefix=prefix, **kwargs
            ):
                yield line
        else:
            yield ConsolePrinter._debug_scalar(data, prefix=prefix, **kwargs)

    @staticmethod
    def _debug_scalar(data: Any, **kwargs) -> str:
        """Helper for debug."""
        prefix = kwargs.pop("prefix", "")
        print_anchor = kwargs.pop("print_anchor", True)
        print_tag = kwargs.pop("print_tag", True)
        print_type = kwargs.pop("print_type", False)
        dtype = type(data) if print_type else ""
        anchor_prefix = ""
        print_prefix = prefix

        if print_anchor:
            anchor = ConsolePrinter._debug_get_anchor(data)
            if anchor:
                anchor_prefix = "({})".format(anchor)

        if print_tag:
            if isinstance(data, TaggedScalar):
                tag_prefix = "{}{}<{}>".format(
                    print_prefix, anchor_prefix, data.tag.value)
                return ConsolePrinter._debug_scalar(
                        data.value, prefix=tag_prefix,
                        print_anchor=False, print_tag=False, print_type=True)

        # The "true" type of the value is nested in TaggedScalar.value
        if isinstance(data, TaggedScalar):
            dtype = "{}({})".format(dtype, type(data.value))

        print_prefix += anchor_prefix
        return ConsolePrinter._debug_prefix_lines(
            "{}{}{}".format(print_prefix, data, dtype))

    @staticmethod
    def _debug_node_coord(
        data: NodeCoords, **kwargs
    ) -> Generator[str, None, None]:
        """Helper method for debug."""
        prefix = kwargs.pop("prefix", "")
        path_prefix = "{}(path)".format(prefix)
        node_prefix = "{}(node)".format(prefix)
        parent_prefix = "{}(parent)".format(prefix)
        parentref_prefix = "{}(parentref)".format(prefix)

        for line in ConsolePrinter._debug_dump(data.path, prefix=path_prefix):
            yield line

        for line in ConsolePrinter._debug_dump(data.node, prefix=node_prefix):
            yield line

        for line in ConsolePrinter._debug_dump(
            data.parent, prefix=parent_prefix
        ):
            yield line

        for line in ConsolePrinter._debug_dump(
            data.parentref, prefix=parentref_prefix
        ):
            yield line

    @staticmethod
    def _debug_list(
        data: Union[List[Any], Tuple[Any, ...], Set[Any]], **kwargs
    ) -> Generator[str, None, None]:
        """Helper for debug."""
        prefix = kwargs.pop("prefix", "")
        print_tag = kwargs.pop("print_tag", True)

        if (print_tag
            and isinstance(data, (CommentedBase, CommentedSet))
            and hasattr(data, "tag")
            and data.tag.value
        ):
            prefix += "<{}>".format(data.tag.value)

        for idx, ele in enumerate(data):
            ele_prefix = "{}[{}]".format(prefix, idx)

            # if (isinstance(data, (CommentedBase, CommentedSet))
            #     and hasattr(ele, "tag")
            #     and ele.tag.value
            # ):
            #     ele_prefix += "<{}>".format(ele.tag.value)

            for line in ConsolePrinter._debug_dump(
                ele, prefix=ele_prefix, print_anchor=True, print_tag=True,
                print_type=True
            ):
                yield line

    @staticmethod
    def _debug_get_kv_anchors(key: Any, value: Any) -> str:
        """Helper for debug."""
        key_anchor = ConsolePrinter._debug_get_anchor(key)
        val_anchor = ConsolePrinter._debug_get_anchor(value)
        display_anchor = ""
        if key_anchor and val_anchor:
            display_anchor = "({},{})".format(key_anchor, val_anchor)
        elif key_anchor:
            display_anchor = "({},_)".format(key_anchor)
        elif val_anchor:
            display_anchor = "(_,{})".format(val_anchor)
        return display_anchor

    @staticmethod
    def _debug_get_kv_tags(key: Any, value: Any) -> str:
        """Helper for debug."""
        key_tag = ConsolePrinter._debug_get_tag(key)
        val_tag = ConsolePrinter._debug_get_tag(value)
        display_tag = ""
        if key_tag and val_tag:
            display_tag = "<{},{}>".format(key_tag, val_tag)
        elif key_tag:
            display_tag = "<{},_>".format(key_tag)
        elif val_tag:
            display_tag = "<_,{}>".format(val_tag)
        return display_tag

    @staticmethod
    def _debug_dict(
        data: Union[Dict, CommentedMap], **kwargs
    ) -> Generator[str, None, None]:
        """Helper for debug."""
        prefix = kwargs.pop("prefix", "")

        local_keys = []
        if isinstance(data, CommentedMap):
            for local_key, _ in data.non_merged_items():
                local_keys.append(local_key)
        else:
            for key in data.keys():
                local_keys.append(key)

        for key, val in data.items():
            display_key = (str(key)
                           if key in local_keys
                           else "<<:{}:>>".format(key))
            display_anchor = ConsolePrinter._debug_get_kv_anchors(key, val)
            display_tag = ConsolePrinter._debug_get_kv_tags(key, val)
            kv_prefix = "{}[{}]{}{}".format(
                prefix, display_key, display_anchor, display_tag)

            for line in ConsolePrinter._debug_dump(
                val, prefix=kv_prefix, print_type=True, print_tag=False,
                print_anchor=False
            ):
                yield line
