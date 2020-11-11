"""
Validate YAML/JSON/Compatible data.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
import sys
import argparse

from yamlpath import __version__ as YAMLPATH_VERSION
from yamlpath.common import Parsers
from yamlpath.wrappers import ConsolePrinter

class LogErrorCap:
    """Capture only ERROR messages as a fake ConsolePrinter."""

    def __init__(self):
        """Initialize this class instance."""
        self.lines = []
    def info(self, message):
        """Discard INFO messages."""
    def verbose(self, message):
        """Discard verbose INFO messages."""
    def warning(self, message):
        """Discard WARNING messages."""
    # pylint: disable=unused-argument
    def error(self, message, *args):
        """Capture ERROR messages."""
        self.lines.append(message)
    # pylint: disable=unused-argument
    def critical(self, message, *args):
        """Discard critical ERROR messages."""
    def debug(self, message, **kwargs):
        """Discard DEBUG messages."""

def processcli():
    """Process command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate YAML, JSON, and compatible files.",
        epilog=(
            "Except when suppressing all report output with --quiet|-q,"
            " validation issues are printed to STDOUT (not STDERR).  Further,"
            " the exit-state will report 0 when there are no issues, 1 when"
            " there is an issue with the supplied command-line arguments, or 2"
            " when validation has failed for any document.  To report issues"
            " with this tool or to request enhancements, please visit"
            " https://github.com/wwkimball/yamlpath/issues.")
    )
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s " + YAMLPATH_VERSION)

    parser.add_argument(
        "-S", "--nostdin", action="store_true",
        help=(
            "Do not implicitly read from STDIN, even when there are\n"
            "no - pseudo-files in YAML_FILEs with a non-TTY session"))

    noise_group = parser.add_mutually_exclusive_group()
    noise_group.add_argument(
        "-d", "--debug",
        action="store_true",
        help="output debugging details")
    noise_group.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="increase output verbosity (show valid documents)")
    noise_group.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="suppress all output except system errors")

    parser.add_argument("yaml_files", metavar="YAML_FILE", nargs="*",
                        help="one or more single- or multi-document"
                        " YAML/JSON/compatible files to validate; omit or use"
                        " - to read from STDIN")

    return parser.parse_args()

def validateargs(args, log):
    """Validate command-line arguments."""
    has_errors = False

    # There must be at least one input file or stream
    input_file_count = len(args.yaml_files)
    if (input_file_count == 0 and (
            sys.stdin.isatty()
            or args.nostdin)
    ):
        has_errors = True
        log.error(
            "There must be at least one YAML_FILE or STDIN document.")

    # There can be only one -
    pseudofile_count = 0
    for infile in args.yaml_files:
        if infile.strip() == '-':
            pseudofile_count += 1
    if pseudofile_count > 1:
        has_errors = True
        log.error("Only one YAML_FILE may be the - pseudo-file.")

    if has_errors:
        sys.exit(1)

def process_file(log, yaml, yaml_file):
    """Process a (potentially multi-doc) YAML file."""
    logcap = LogErrorCap()
    subdoc_index = 0
    exit_state = 0
    file_name = "STDIN" if yaml_file.strip() == "-" else yaml_file
    for (_, doc_loaded) in Parsers.get_yaml_multidoc_data(
        yaml, logcap, yaml_file
    ):
        if doc_loaded:
            log.verbose("{}/{} is valid.".format(file_name, subdoc_index))
        else:
            # An error message has been captured
            exit_state = 2
            log.info(
                "{}/{} is invalid due to:".format(file_name, subdoc_index))
            for line in logcap.lines:
                log.info("  * {}".format(line))
        logcap.lines.clear()
        subdoc_index += 1

    return exit_state

def main():
    """Main code."""
    # Process any command-line arguments
    args = processcli()
    log = ConsolePrinter(args)
    validateargs(args, log)
    exit_state = 0
    consumed_stdin = False
    yaml = Parsers.get_yaml_editor()

    for yaml_file in args.yaml_files:
        if yaml_file.strip() == '-':
            consumed_stdin = True

        log.debug(
            "yaml_merge::main:  Processing file, {}".format(
                "STDIN" if yaml_file.strip() == "-" else yaml_file))

        proc_state = process_file(log, yaml, yaml_file)

        if proc_state != 0:
            exit_state = proc_state

    # Check for a waiting STDIN document
    if (exit_state == 0
        and not consumed_stdin
        and not args.nostdin
        and not sys.stdin.isatty()
    ):
        exit_state = process_file(log, yaml, "-")

    sys.exit(exit_state)

if __name__ == "__main__":
    main()  # pragma: no cover
