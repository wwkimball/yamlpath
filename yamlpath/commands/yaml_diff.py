"""
Calculate the differences between two YAML/JSON/Compatible documents.

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
import sys
import argparse

from yamlpath.common import YAMLPATH_VERSION
from yamlpath.wrappers import ConsolePrinter
from yamlpath.func import get_yaml_data, get_yaml_editor
from yamlpath.differ import Differ
from yamlpath.differ.enums import DiffActions

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

    sameness_group = parser.add_mutually_exclusive_group()
    sameness_group.add_argument(
        "-s", "--same", action="store_true",
        help="Show all nodes which are the same in addition to differences")
    sameness_group.add_argument(
        "-o", "--onlysame", action="store_true",
        help="Show only nodes which are the same, still reporting that"
             " differences exist -- when they do -- with an exit-state of 1")

    parser.add_argument(
        "-S", "--nostdin", action="store_true",
        help="Do not implicitly read from STDIN, even when there are no -"
             " pseudo-files in YAML_FILEs with a non-TTY session")

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

def print_report(log, args, diff):
    """Print user-customized report."""
    changes_found = False
    print_sep = False
    for entry in diff.get_report():
        is_different = entry.action is not DiffActions.SAME
        if is_different:
            changes_found = True

        if (
            (is_different and not args.onlysame)
            or (args.onlysame and not is_different)
            or args.same
        ):
            if print_sep:
                log.info("")
            log.info(entry)
            print_sep = True

    return changes_found

def main():
    """Main code."""
    args = processcli()
    log = ConsolePrinter(args)
    validateargs(args, log)
    exit_state = 0
    lhs_file = args.yaml_files[0]
    rhs_file = args.yaml_files[1] if len(args.yaml_files) > 1 else "-"
    lhs_yaml = get_yaml_editor()
    rhs_yaml = get_yaml_editor()

    (lhs_document, doc_loaded) = get_yaml_data(lhs_yaml, log, lhs_file)
    if not doc_loaded:
        # An error message has already been logged
        sys.exit(1)

    (rhs_document, doc_loaded) = get_yaml_data(rhs_yaml, log, rhs_file)
    if not doc_loaded:
        # An error message has already been logged
        sys.exit(1)

    diff = Differ(log, lhs_document)
    diff.compare_to(rhs_document)
    exit_state = 1 if print_report(log, args, diff) else 0
    sys.exit(exit_state)

if __name__ == "__main__":
    main()  # pragma: no cover
