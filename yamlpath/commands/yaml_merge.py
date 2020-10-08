"""
Enable users to merge YAML/Compatible files.

Due to the complexities of merging, users are given deep control over the merge
operation via both default behaviors as well as per YAML Path behaviors.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
import sys
import argparse
import json
from os import access, R_OK
from os.path import isfile, exists
from pathlib import Path
from typing import Any

from yamlpath.merger.enums import (
    AnchorConflictResolutions,
    AoHMergeOpts,
    ArrayMergeOpts,
    HashMergeOpts,
    OutputDocTypes,
)
from yamlpath.func import get_yaml_multidoc_data, get_yaml_editor
from yamlpath.merger.exceptions import MergeException
from yamlpath.merger import Merger, MergerConfig
from yamlpath.exceptions import YAMLPathException

from yamlpath.wrappers import ConsolePrinter

# Implied Constants
MY_VERSION = "0.1.0"

def processcli():
    """Process command-line arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="Merges two or more YAML/Compatible files together.",
        epilog="""
            The CONFIG file is an INI file with up to three sections:
            [defaults] Sets equivalents of -a|--anchors, -A|--arrays,
                       -H|--hashes, and -O|--aoh.
            [rules]    Each entry is a YAML Path assigning -A|--arrays,
                       -H|--hashes, or -O|--aoh for precise nodes.
            [keys]     Wherever -O|--aoh=DEEP, each entry is treated as a
                       record with an identity key.  In order to match RHS
                       records to LHS records, a key must be known and is
                       identified on a YAML Path basis via this section.
                       Where not specified, the first attribute of the first
                       record in the Array-of-Hashes is presumed the identity
                       key for all records in the set.

            The left-to-right order of YAML_FILEs is significant.  Except
            when this behavior is deliberately altered by your options, data
            from files on the right overrides data in files to their left.  At
            least two YAML_FILEs are required.  Only one may be the -
            pseudo-file.  When only one YAML_FILE is provided, it cannot be the
            - pseudo-file and in this special-case - will be inferred as the
            second YAML_FILE as long as you are running this program without a
            TTY (unless you set --nostdin|-S).
            For more information about YAML Paths, please visit
            https://github.com/wwkimball/yamlpath."""
    )
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s " + MY_VERSION)

    parser.add_argument(
        "-c", "--config", help=(
            "INI syle configuration file for YAML Path specified\n"
            "merge control options"))

    parser.add_argument(
        "-a", "--anchors",
        choices=[l.lower() for l in AnchorConflictResolutions.get_names()],
        type=str.lower,
        help=(
            "means by which Anchor name conflicts are resolved\n"
            "(overrides [defaults]anchors set via --config|-c and\n"
            "cannot be overridden by [rules] because Anchors apply\n"
            "to the whole file); default=stop"))
    parser.add_argument(
        "-A", "--arrays",
        choices=[l.lower() for l in ArrayMergeOpts.get_names()],
        type=str.lower,
        help=(
            "default means by which Arrays are merged together\n"
            "(overrides [defaults]arrays but is overridden on a\n"
            "YAML Path basis via --config|-c); default=all"))
    parser.add_argument(
        "-H", "--hashes",
        choices=[l.lower() for l in HashMergeOpts.get_names()],
        type=str.lower,
        help=(
            "default means by which Hashes are merged together\n"
            "(overrides [defaults]hashes but is overridden on a\n"
            "YAML Path basis in [rules] set via --config|-c);\n"
            "default=deep"))
    parser.add_argument(
        "-O", "--aoh",
        choices=[l.lower() for l in AoHMergeOpts.get_names()],
        type=str.lower,
        help=(
            "default means by which Arrays-of-Hashes are merged\n"
            "together (overrides [defaults]aoh but is overridden on\n"
            "a YAML Path basis in [rules] set via --config|-c);\n"
            "default=all"))

    parser.add_argument(
        "-m", "--mergeat",
        metavar="YAML_PATH",
        default="/",
        help=(
            "YAML Path indicating where in left YAML_FILE the right\n"
            "YAML_FILE content is to be merged; default=/"))

    parser.add_argument(
        "-o", "--output",
        help=(
            "Write the merged result to the indicated file (or\n"
            "STDOUT when unset)"))

    parser.add_argument(
        "-D", "--document-format",
        choices=[l.lower() for l in OutputDocTypes.get_names()],
        type=str.lower,
        default="auto",
        help=(
            "Force the merged result to be presented in one of the\n"
            "supported formats or let it automatically match the type\n"
            "of the first document; default=auto"))

    parser.add_argument(
        "-S", "--nostdin", action="store_true",
        help=(
            "Do not implicitly read from STDIN, even when there are\n"
            "no - pseudo-files in YAML_FILEs with a non-TTY session"))

    noise_group = parser.add_mutually_exclusive_group()
    noise_group.add_argument(
        "-d", "--debug", action="store_true",
        help="output debugging details")
    noise_group.add_argument(
        "-v", "--verbose", action="store_true",
        help="increase output verbosity")
    noise_group.add_argument(
        "-q", "--quiet", action="store_true",
        help=(
            "suppress all output except errors (implied when\n"
            "-o|--output is not set)"))

    parser.add_argument(
        "yaml_files", metavar="YAML_FILE", nargs="*",
        help=(
            "one or more YAML files to merge, order-significant;\n"
            "use - to read from STDIN"))
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
            "There must be at least one YAML_FILE.")

    # There can be only one -
    pseudofile_count = 0
    for infile in args.yaml_files:
        if infile.strip() == '-':
            pseudofile_count += 1
    if pseudofile_count > 1:
        has_errors = True
        log.error("Only one YAML_FILE may be the - pseudo-file.")

    # When set, the configuration file must be a readable file
    if args.config and not (
            isfile(args.config)
            and access(args.config, R_OK)
    ):
        has_errors = True
        log.error(
            "INI style configuration file is not readable:  {}"
            .format(args.config))

    # When set, the output file must not already exist
    if args.output:
        if exists(args.output):
            has_errors = True
            log.error("Output file already exists:  {}".format(args.output))
    else:
        # When dumping the document to STDOUT, mute all non-errors
        args.quiet = True
        args.verbose = False
        args.debug = False

    if has_errors:
        sys.exit(1)

def merge_multidoc(yaml_file, yaml_editor, log, merger):
    """Merge all documents within a multi-document source."""
    exit_state = 1
    for yaml_data in get_yaml_multidoc_data(yaml_editor, log, yaml_file):
        if not yaml_data and isinstance(yaml_data, bool):
            # An error message has already been logged
            exit_state = 3
            break
        try:
            merger.merge_with(yaml_data)
        except MergeException as mex:
            log.error(mex)
            exit_state = 6
            break
        except YAMLPathException as yex:
            log.error(yex)
            exit_state = 7
            break
        else:
            exit_state = 0

    log.debug("merge_multidoc:  Reporting status, {}.".format(exit_state))
    return exit_state

def process_rhs(
    merger: Merger, log: ConsolePrinter, rhs_yaml: Any, rhs_file: str
):
    """Merge RHS document(s) into the prime document."""
    # Except for - (STDIN), each YAML_FILE must actually be a file; because
    # merge data is expected, this is a fatal failure.
    if rhs_file != "-" and not isfile(rhs_file):
        log.error("Not a file:  {}".format(rhs_file))
        return 2

    log.info("Processing {}..."
                .format("STDIN" if rhs_file == "-" else rhs_file))

    return merge_multidoc(rhs_file, rhs_yaml, log, merger)

def calc_output_document_type(args):
    """Determine whether the output document will be JSON or YAML."""
    document_format = OutputDocTypes.from_str(args.document_format)

    if document_format is OutputDocTypes.AUTO:
        output_is_json = False
        output_file = args.output
        if output_file:
            output_is_json = Path(output_file).suffix.lower() == ".json"

        document_format = (OutputDocTypes.JSON
                           if output_is_json
                           else OutputDocTypes.YAML)

    return document_format

def main():
    """Main code."""
    args = processcli()
    log = ConsolePrinter(args)
    validateargs(args, log)
    merger = Merger(log, None, MergerConfig(log, args))

    # The first input file is the prime
    fileiterator = iter(args.yaml_files)
    document_is_json = calc_output_document_type(args) is OutputDocTypes.JSON
    document_is_yaml = not document_is_json
    prime_yaml = get_yaml_editor(
        explode_aliases=document_is_json,
        preserve_quotes=document_is_yaml
    )
    prime_file = next(fileiterator, '-')
    consumed_stdin = prime_file.strip() == '-'
    exit_state = merge_multidoc(prime_file, prime_yaml, log, merger)

    if exit_state != 0:
        # An error message has already been logged
        sys.exit(exit_state)

    # Merge additional input files into the prime
    rhs_yaml = get_yaml_editor(
        explode_aliases=document_is_json,
        preserve_quotes=document_is_yaml
    )
    for rhs_file in fileiterator:
        log.debug(
            "yaml_merge::main:  Processing next file, {}".format(rhs_file))
        proc_state = process_rhs(merger, log, rhs_yaml, rhs_file)

        if proc_state != 0:
            exit_state = proc_state
            break

        if rhs_file.strip() == '-':
            consumed_stdin = True

    # Check for a waiting STDIN document
    if (exit_state == 0
        and not consumed_stdin
        and not args.nostdin
        and not sys.stdin.isatty()
    ):
        exit_state = process_rhs(merger, log, rhs_yaml, '-')

    # Output the final document
    if exit_state == 0:
        merger.prepare_for_dump(prime_yaml)
        if args.output:
            with open(args.output, 'w') as out_fhnd:
                if document_is_json:
                    json.dump(merger.data, out_fhnd)
                else:
                    prime_yaml.dump(merger.data, out_fhnd)
        else:
            if document_is_json:
                json.dump(merger.data, sys.stdout)
            else:
                prime_yaml.dump(merger.data, sys.stdout)

    sys.exit(exit_state)

if __name__ == "__main__":
    main()  # pragma: no cover
