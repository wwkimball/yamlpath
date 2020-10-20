"""
Calculate the differences between two YAML/JSON/Compatible documents.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
import sys
import argparse

from yamlpath.common import YAMLPATH_VERSION
from yamlpath.wrappers import ConsolePrinter
from yamlpath.func import get_yaml_data, get_yaml_editor
from yamlpath.differ import Differ


def processcli():
    """Process command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Calculate the difference between two"
                    " YAML/JSON/Compatible documents.",
        epilog="Only one YAML_FILE may be -.  For more information about YAML"
               " Paths, please visit https://github.com/wwkimball/yamlpath."
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
        help="increase output verbosity")
    noise_group.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="suppress all output except system errors")

    parser.add_argument("yaml_files", metavar="YAML_FILE",
                        nargs=2,
                        help="exactly two YAML/JSON/compatible files to"
                             " compare; omit one of these or use  - to read"
                             " one document from STDIN")

    return parser.parse_args()

def validateargs(args, log):
    """Validate command-line arguments."""
    has_errors = False

    # There must be at least one input file or stream
    input_file_count = len(args.yaml_files)
    if (input_file_count < 2 and (
            sys.stdin.isatty()
            or args.nostdin)
    ):
        has_errors = True
        log.error(
            "There must be at least two YAML_FILEs.")

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

def main():
    """Main code."""
    args = processcli()
    log = ConsolePrinter(args)
    validateargs(args, log)
    exit_state = 0
    lhs_file = args.yaml_files[0]
    #rhs_file = args.yaml_files[1] if len(args.yaml_files) > 1 else "-"
    yaml = get_yaml_editor()

    (yaml_data, doc_loaded) = get_yaml_data(yaml, log, lhs_file)
    if not doc_loaded:
        # An error message has already been logged
        sys.exit(1)

    diff = Differ(log, yaml_data)
    for line in diff.get_report():
        log.info(line)

    sys.exit(exit_state)

if __name__ == "__main__":
    main()  # pragma: no cover
