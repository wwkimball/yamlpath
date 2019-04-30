#!/usr/bin/env python3
################################################################################
# Defines a reusable console print facility for YAML-oriented scripts.
#
# Requires a dictionary on init which has the following entries:
# quiet:  <Boolean> suppresses all output except ConsolePrinter::error().
# verbose:  <Boolean> allows output from ConsolePrinter::verbose().
# debug:  <Boolean> allows output from ConsolePrinter::debug().
#
# Copyright 2018, 2019 William W. Kimball, Jr. MBA MSIS
################################################################################
import sys

class ConsolePrinter:
    """Generally-useful console messager, writing INFO, VERBOSE, WARN, and DEBUG
    messages to STDOUT as well as ERROR messages to STDERR with multi-lne
    formatting."""

    def __init__(self, args):
        """Init this class.

        Positional Parameters:
          1. args (dict) Dictionary of log level settings with:
             - debug (Boolean) true = write debugging informational messages
             - verbose (Boolean) true = write verbose informational messages
             - quiet (Boolean) true = write only error messages

        Returns:  N/A

        Raises:  N/A
        """
        self.args = args

    def info(self, message):
        """Writes an informational message to STDOUT unless quiet mode is
        active.

        Positional Parameters:
          1. message (str) The message to print

        Returns:  N/A

        Raises:  N/A
        """
        if not self.args.quiet:
            print(message)

    def verbose(self, message):
        """Writes a verbose message to STDOUT when verbose mode is active unless
        quiet mode is active.

        Positional Parameters:
          1. message (str) The message to print

        Returns:  N/A

        Raises:  N/A
        """
        if not self.args.quiet and (self.args.verbose or self.args.debug):
            print(message)

    def warning(self, message):
        """Writes a warning message to STDOUT unless quiet mode is active.

        Positional Parameters:
          1. message (str) The message to print

        Returns:  N/A

        Raises:  N/A
        """
        if not self.args.quiet:
            print("WARNING:  " + str(message).replace("\n", "\nWARNING:  "))

    def error(self, message, exit_code=None):
        """Writes an error message to STDERR and optionally terminates the
        program, exiting with a specific error code.

        Positional Parameters:
          1. message (str) The message to print
          2. exit_code (int) The exit code to terminate the program
             with; default=None

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
            exit(exit_code)

    def debug(self, message):
        """Writes a debug message to STDOUT unless quiet mode is active, dumping
        all key-value pairs of a dictionary or all elements of a list, when the
        message is either.

        Positional Parameters:
          1. message (str) The message to print

        Returns:  N/A

        Raises:  N/A
        """
        if self.args.debug and not self.args.quiet:
            if isinstance(message, list):
                for i, e in enumerate(message):
                    attr = ""
                    if hasattr(e, 'anchor') and e.anchor.value is not None:
                        attr = "; &" + e.anchor.value
                    pe = str(e) + attr
                    print("DEBUG: [" + str(i) + "]=" + str(pe).replace("\n", "\nDEBUG: "))
            elif isinstance(message, dict):
                for k, v in message.items():
                    attr = ""
                    if hasattr(v, 'anchor') and v.anchor.value is not None:
                        attr = "; &" + v.anchor.value
                    pv = str(v) + attr
                    print("DEBUG: [" + str(k) + "]=>" + str(pv).replace("\n", "\nDEBUG: "))
            else:
                attr = ""
                if hasattr(message, 'anchor') and message.anchor.value is not None:
                    attr = "; &" + message.anchor.value
                pm = str(message) + attr
                print("DEBUG: " + str(pm).replace("\n", "\nDEBUG: "))
