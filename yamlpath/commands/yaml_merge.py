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
from typing import Any, List, Union

from ruamel.yaml import YAML

from yamlpath import __version__ as YAMLPATH_VERSION
from yamlpath.common import Parsers
from yamlpath.merger.enums import (
    AnchorConflictResolutions,
    AoHMergeOpts,
    ArrayMergeOpts,
    HashMergeOpts,
    MultiDocModes,
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
            "write the merged result to the indicated nonexistent\n"
            "file"))
    output_doc_group.add_argument(
        "-w", "--overwrite",
        help=(
            "write the merged result to the indicated file; will\n"
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
            "force the merged result to be presented in one of the\n"
            "supported formats or let it automatically match the\n"
            "known file-name extension of OUTPUT|OVERWRITE (when\n"
            "provided), or match the type of the first document;\n"
            "default=auto"))

    parser.add_argument(
        "-M", "--multi-doc-mode",
        choices=[l.lower() for l in MultiDocModes.get_names()],
        type=str.lower,
        default="condense_all",
        help=(
            "control how multi-document files and streams are\n"
            "merged together, with or without condensing them as\n"
            "part of the merge"))

    parser.add_argument(
        "-l", "--preserve-lhs-comments", action="store_true",
        help=(
            "while all comments are normally dicarded during a\n"
            "merge, this option will attempt to preserve\n"
            "comments in the left-most YAML_FILE; may produce\n"
            "unexpected comment-to-data associations or\n"
            "spurious new-lines and all other document comments\n"
            "are still discarded"))

    parser.add_argument(
        "-S", "--nostdin", action="store_true",
        help=(
            "do not implicitly read from STDIN, even when there are\n"
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

def condense_document(
    log: ConsolePrinter, yaml_editor: YAML, config: MergerConfig,
    yaml_file: str
) -> Union[None, Merger]:
    """Merge a multi-document file up into a single document."""
    if yaml_file != "-" and not isfile(yaml_file):
        log.error("Not a file:  {}".format(yaml_file))
        return None

    document = None
    for (yaml_data, doc_loaded) in Parsers.get_yaml_multidoc_data(
        yaml_editor, log, yaml_file
    ):
        if not doc_loaded:
            # An error message has already been logged
            document = None
            break

        if document is None:
            document = Merger(log, yaml_data, config)
            continue

        try:
            document.merge_with(yaml_data)
        except MergeException as mex:
            log.error(mex)
            document = None
            break
        except YAMLPathException as yex:
            log.error(yex)
            document = None
            break

    return document

def get_doc_mergers(
    log: ConsolePrinter, yaml_editor: YAML, config: MergerConfig,
    yaml_file: str
) -> List[Merger]:
    """Create a list of Mergers, one for each source document."""
    if yaml_file != "-" and not isfile(yaml_file):
        log.error("Not a file:  {}".format(yaml_file))
        return []

    doc_mergers: List[Merger] = []
    if config.get_multidoc_mode() is MultiDocModes.CONDENSE_ALL:
        condensed_doc = condense_document(log, yaml_editor, config, yaml_file)
        if condensed_doc is None:
            return []
        doc_mergers.append(condensed_doc)
    else:
        for (yaml_data, doc_loaded) in Parsers.get_yaml_multidoc_data(
            yaml_editor, log, yaml_file
        ):
            if not doc_loaded:
                # An error message has already been logged
                doc_mergers.clear()
                break

            doc_mergers.append(Merger(log, yaml_data, config))

    return doc_mergers

def merge_docs(
    log: ConsolePrinter, yaml_editor: YAML, config: MergerConfig,
    lhs_docs: List[Merger], rhs_file: str
) -> int:
    """Merge RHS into LHS."""
    merge_mode = config.get_multidoc_mode()
    return_state = 0

    if merge_mode is MultiDocModes.CONDENSE_ALL:
        condensed_rhs = condense_document(log, yaml_editor, config, rhs_file)
        if condensed_rhs is None:
            return_state = 10
        else:
            try:
                lhs_docs[0].merge_with(condensed_rhs.data)
            except MergeException as mex:
                log.error(mex)
                return_state = 11
            except YAMLPathException as yex:
                log.error(yex)
                return_state = 12

    elif merge_mode is MultiDocModes.CONDENSE_RHS:
        condensed_rhs = condense_document(log, yaml_editor, config, rhs_file)
        if condensed_rhs is None:
            return_state = 20
        else:
            for lhs_doc in lhs_docs:
                try:
                    lhs_doc.merge_with(condensed_rhs.data)
                except MergeException as mex:
                    log.error(mex)
                    return_state = 21
                    break
                except YAMLPathException as yex:
                    log.error(yex)
                    return_state = 22
                    break

    elif merge_mode is MultiDocModes.MERGE_ACROSS:
        rhs_docs = get_doc_mergers(log, yaml_editor, config, rhs_file)
        if len(rhs_docs) < 1:
            return_state = 30
        else:
            lhs_len = len(lhs_docs)
            rhs_len = len(rhs_docs)
            max_len = lhs_len if lhs_len > rhs_len else rhs_len
            for i in range(0, max_len):
                if i > rhs_len:
                    break
                if i > lhs_len:
                    lhs_docs.append(rhs_docs[i])
                    continue
                try:
                    lhs_docs[i].merge_with(rhs_docs[i].data)
                except MergeException as mex:
                    log.error(mex)
                    return_state = 31
                    break
                except YAMLPathException as yex:
                    log.error(yex)
                    return_state = 32
                    break

    elif merge_mode is MultiDocModes.MATRIX_MERGE:
        rhs_docs = get_doc_mergers(log, yaml_editor, config, rhs_file)
        if len(rhs_docs) < 1:
            return_state = 40
        else:
            for lhs_doc in lhs_docs:
                for rhs_doc in rhs_docs:
                    try:
                        lhs_doc.merge_with(rhs_doc.data)
                    except MergeException as mex:
                        log.error(mex)
                        return_state = 41
                        break
                    except YAMLPathException as yex:
                        log.error(yex)
                        return_state = 42
                        break

    return return_state

def main():
    """Main code."""
    args = processcli()
    log = ConsolePrinter(args)
    validateargs(args, log)

    # For the remainder of processing, overwrite overwrites output
    if args.overwrite:
        args.output = args.overwrite

    # Merge all input files
    yaml_editor = Parsers.get_yaml_editor()
    merge_config = MergerConfig(log, args)
    exit_state = 0
    consumed_stdin = False
    mergers: List[Merger] = []
    for yaml_file in args.yaml_files:
        proc_state = 0
        if yaml_file.strip() == '-':
            consumed_stdin = True

        log.debug(
            "yaml_merge::main:  Processing file, {}".format(
                "STDIN" if yaml_file.strip() == "-" else yaml_file))

        if len(mergers) < 1:
            mergers = get_doc_mergers(log, yaml_editor, merge_config, yaml_file)
            if len(mergers) < 1:
                exit_state = 4
                break
        else:
            # Merge RHS into LHS
            exit_state = merge_docs(
                log, yaml_editor, merge_config, mergers, yaml_file)
            if not exit_state == 0:
                break

    # Check for a waiting STDIN document
    if (exit_state == 0
        and not consumed_stdin
        and not args.nostdin
        and not sys.stdin.isatty()
    ):
        exit_state = merge_docs(log, yaml_editor, merge_config, mergers, "-")

    # Output the final document
    if exit_state == 0:
        write_output_document(args, log, mergers[0], yaml_editor)

    sys.exit(exit_state)

if __name__ == "__main__":
    main()  # pragma: no cover
