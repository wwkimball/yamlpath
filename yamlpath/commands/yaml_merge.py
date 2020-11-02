"""
Enable users to merge YAML/Compatible files.

Due to the complexities of merging, users are given deep control over the merge
operation via both default behaviors as well as per YAML Path behaviors.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
import sys
import argparse
import json
from os import access, R_OK, remove
from os.path import isfile, exists
from shutil import copy2
from typing import Any

from yamlpath import __version__ as YAMLPATH_VERSION
from yamlpath.common import Parsers
from yamlpath.merger.enums import (
    AnchorConflictResolutions,
    AoHMergeOpts,
    ArrayMergeOpts,
    HashMergeOpts,
    OutputDocTypes,
)
from yamlpath.merger.exceptions import MergeException
from yamlpath.merger import Merger, MergerConfig
from yamlpath.exceptions import YAMLPathException

from yamlpath.wrappers import ConsolePrinter

def processcli():
    """Process command-line arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description="Merges two or more single- or multi-document"
                    " YAML/JSON/Compatible documents\ntogether, including"
                    " complex data provided via STDIN.",
        epilog="""
configuration file:
  The CONFIG file is an INI file with up to three sections:
  [defaults] Sets equivalents of --anchors|-a, --arrays|-A, --hashes|-H, and
             --aoh|-O.
  [rules]    Each entry is a YAML Path assigning --arrays|-A, --hashes|-H,
             or --aoh|-O for precise nodes.
  [keys]     Wherever --aoh=DEEP (or -O deep), each entry is treated as a
             record with an identity key.  In order to match RHS records to
             LHS records, a key must be known and is identified on a YAML
             Path basis via this section.  Where not specified, the first
             attribute of the first record in the Array-of-Hashes is presumed
             the identity key for all records in the set.

input files:
  The left-to-right order of YAML_FILEs is significant.  Except when this
  behavior is deliberately altered by your options, data from files on the
  right overrides data in files to their left.

  Only one input file may be the - pseudo-file (read from STDIN).  When no
  YAML_FILEs are provided, - will be inferred as long as you are running
  this program without a TTY (unless you set --nostdin|-S).

  Any file, including input from STDIN, may be a multi-document YAML, JSON,
  or compatible file.

For more information about YAML Paths, please visit
https://github.com/wwkimball/yamlpath/wiki.

To report issues with this tool or to request enhancements, please visit
https://github.com/wwkimball/yamlpath/issues.
""")

    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s " + YAMLPATH_VERSION)

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

    output_doc_group = parser.add_mutually_exclusive_group()
    output_doc_group.add_argument(
        "-o", "--output",
        help=(
            "Write the merged result to the indicated nonexistent\n"
            "file"))
    output_doc_group.add_argument(
        "-w", "--overwrite",
        help=(
            "Write the merged result to the indicated file; will\n"
            "replace the file when it already exists"))

    parser.add_argument(
        "-b", "--backup", action="store_true",
        help=(
            "save a backup OVERWRITE file with an extra .bak\n"
            "file-extension; applies only to OVERWRITE"))

    parser.add_argument(
        "-D", "--document-format",
        choices=[l.lower() for l in OutputDocTypes.get_names()],
        type=str.lower,
        default="auto",
        help=(
            "Force the merged result to be presented in one of the\n"
            "supported formats or let it automatically match the\n"
            "known file-name extension of OUTPUT|OVERWRITE (when\n"
            "provided), or match the type of the first document;\n"
            "default=auto"))

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
            "omit or use - to read from STDIN"))
    return parser.parse_args()

# pylint: disable=too-many-branches
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
    elif args.overwrite:
        if exists(args.overwrite):
            log.warning(
                "Output file exists and will be overwritten:  {}"
                .format(args.overwrite))
    else:
        # When dumping the document to STDOUT, mute all non-errors except when
        # forced.
        force_verbose = args.verbose
        force_debug = args.debug
        if not (force_verbose or force_debug):
            args.quiet = True
            args.verbose = False
            args.debug = False

    # When set, backup applies only to OVERWRITE
    if args.backup and not args.overwrite:
        has_errors = True
        log.error("The --backup|-b option applies only to OVERWRITE files.")

    if has_errors:
        sys.exit(1)

def merge_multidoc(yaml_file, yaml_editor, log, merger, merger_primed):
    """Merge all documents within a multi-document source."""
    exit_state = 0
    for (yaml_data, doc_loaded) in Parsers.get_yaml_multidoc_data(
        yaml_editor, log, yaml_file
    ):
        if not doc_loaded:
            # An error message has already been logged
            exit_state = 3
            break
        try:
            if merger_primed:
                merger.merge_with(yaml_data)
            else:
                merger.data = yaml_data
                merger_primed = True
        except MergeException as mex:
            log.error(mex)
            exit_state = 6
            break
        except YAMLPathException as yex:
            log.error(yex)
            exit_state = 7
            break

    log.debug("yaml_merge::merge_multidoc:  Reporting status, {}."
              .format(exit_state))
    return exit_state

def process_yaml_file(
    merger: Merger, log: ConsolePrinter, rhs_yaml: Any, rhs_file: str,
    merger_primed: bool
):
    """Merge RHS document(s) into the prime document."""
    # Except for - (STDIN), each YAML_FILE must actually be a file; because
    # merge data is expected, this is a fatal failure.
    if rhs_file != "-" and not isfile(rhs_file):
        log.error("Not a file:  {}".format(rhs_file))
        return 2

    log.info(
        "Processing {}...".format(
            "STDIN" if rhs_file.strip() == "-" else rhs_file))

    return merge_multidoc(rhs_file, rhs_yaml, log, merger, merger_primed)

def write_output_document(args, log, merger, yaml_editor):
    """Save a backup of the overwrite file, if requested."""
    if args.backup:
        backup_file = args.overwrite + ".bak"
        log.verbose(
            "Saving a backup of {} to {}."
            .format(args.overwrite, backup_file))
        if exists(backup_file):
            remove(backup_file)
        copy2(args.overwrite, backup_file)

    document_is_json = (
        merger.prepare_for_dump(yaml_editor, args.output)
        is OutputDocTypes.JSON)
    if args.output:
        with open(args.output, 'w') as out_fhnd:
            if document_is_json:
                json.dump(Parsers.jsonify_yaml_data(merger.data), out_fhnd)
            else:
                yaml_editor.dump(merger.data, out_fhnd)
    else:
        if document_is_json:
            json.dump(Parsers.jsonify_yaml_data(merger.data), sys.stdout)
        else:
            yaml_editor.dump(merger.data, sys.stdout)

def main():
    """Main code."""
    args = processcli()
    log = ConsolePrinter(args)
    validateargs(args, log)

    # For the remainder of processing, overwrite overwrites output
    if args.overwrite:
        args.output = args.overwrite

    # Merge all input files
    merger = Merger(log, None, MergerConfig(log, args))
    yaml_editor = Parsers.get_yaml_editor()
    exit_state = 0
    consumed_stdin = False
    merger_primed = False
    for yaml_file in args.yaml_files:
        if yaml_file.strip() == '-':
            consumed_stdin = True

        log.debug(
            "yaml_merge::main:  Processing file, {}".format(
                "STDIN" if yaml_file.strip() == "-" else yaml_file))
        proc_state = process_yaml_file(
            merger, log, yaml_editor, yaml_file, merger_primed)

        if proc_state == 0:
            merger_primed = True
        else:
            exit_state = proc_state
            break

    # Check for a waiting STDIN document
    if (exit_state == 0
        and not consumed_stdin
        and not args.nostdin
        and not sys.stdin.isatty()
    ):
        exit_state = process_yaml_file(
            merger, log, yaml_editor, '-', merger_primed)

    # Output the final document
    if exit_state == 0:
        write_output_document(args, log, merger, yaml_editor)

    sys.exit(exit_state)

if __name__ == "__main__":
    main()  # pragma: no cover
