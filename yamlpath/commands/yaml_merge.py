"""
Enable users to merge YAML/Compatible files.

Due to the complexities of merging, users are given deep control over the merge
operation via both default behaviors as well as per YAML Path behaviors.

Copyright 2020, 2021 William W. Kimball, Jr. MBA MSIS
"""
import sys
import argparse
import json
from os import access, R_OK, remove
from os.path import isfile, exists
from shutil import copy2
from typing import List, Tuple

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
    SetMergeOpts,
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
        "-E", "--sets",
        choices=[l.lower() for l in SetMergeOpts.get_names()],
        type=str.lower,
        help=(
            "default means by which Sets are merged together\n"
            "(overrides [defaults]sets but is overridden on a\n"
            "YAML Path basis via --config|-c); default=unique"))
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

def write_output_document(
    args: argparse.Namespace, log: ConsolePrinter, yaml_editor: YAML,
    docs: List[Merger]
) -> None:
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
        docs[0].prepare_for_dump(yaml_editor, args.output)
        is OutputDocTypes.JSON)

    dumps = []
    for doc in docs:
        doc.prepare_for_dump(yaml_editor, args.output)
        dumps.append(doc.data)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as out_fhnd:
            if document_is_json:
                if len(dumps) > 1:
                    for dump in dumps:
                        print(
                            json.dumps(Parsers.jsonify_yaml_data(dump)),
                            file=out_fhnd)
                else:
                    json.dump(Parsers.jsonify_yaml_data(dumps[0]), out_fhnd)
            else:
                if len(dumps) > 1:
                    yaml_editor.explicit_end = True  # type: ignore
                    yaml_editor.dump_all(dumps, out_fhnd)
                else:
                    yaml_editor.dump(dumps[0], out_fhnd)
    else:
        if document_is_json:
            if len(dumps) > 1:
                for dump in dumps:
                    print(json.dumps(Parsers.jsonify_yaml_data(dump)))
            else:
                json.dump(Parsers.jsonify_yaml_data(dumps[0]), sys.stdout)
        else:
            if len(dumps) > 1:
                yaml_editor.explicit_end = True  # type: ignore
                yaml_editor.dump_all(dumps, sys.stdout)
            else:
                yaml_editor.dump(dumps[0], sys.stdout)

def get_doc_mergers(
    log: ConsolePrinter, yaml_editor: YAML, config: MergerConfig,
    yaml_file: str
) -> Tuple[List[Merger], bool]:
    """Create a list of Mergers, one for each source document."""
    docs_loaded = True
    if yaml_file != "-" and not isfile(yaml_file):
        log.error("Not a file:  {}".format(yaml_file))
        return ([], False)

    doc_mergers: List[Merger] = []
    for (yaml_data, doc_loaded) in Parsers.get_yaml_multidoc_data(
        yaml_editor, log, yaml_file
    ):
        if not doc_loaded:
            # An error message has already been logged
            doc_mergers.clear()
            docs_loaded = False
            break

        doc_mergers.append(Merger(log, yaml_data, config))

    return (doc_mergers, docs_loaded)

def merge_condense_all(
    log: ConsolePrinter, lhs_docs: List[Merger], rhs_docs: List[Merger]
) -> int:
    """Condense LHS and RHS multi-docs together into one."""
    return_state = 0
    lhs_prime = lhs_docs[0]
    if len(lhs_docs) > 1:
        for lhs_doc in lhs_docs[1:]:
            try:
                lhs_prime.merge_with(lhs_doc.data)
            except MergeException as mex:
                log.error(mex)
                return_state = 11
            except YAMLPathException as yex:
                log.error(yex)
                return_state = 12

    # With all subdocs merged into the first, eliminate all subdocs
    for i in reversed(range(1, len(lhs_docs))):
        del lhs_docs[i]

    # Merge every RHS doc into the prime LHS doc
    for rhs_doc in rhs_docs:
        try:
            lhs_prime.merge_with(rhs_doc.data)
        except MergeException as mex:
            log.error(mex)
            return_state = 13
        except YAMLPathException as yex:
            log.error(yex)
            return_state = 14

    return return_state

def merge_across(
    log: ConsolePrinter, lhs_docs: List[Merger], rhs_docs: List[Merger]
) -> int:
    """Condense LHS and RHS multi-docs together into one."""
    return_state = 0
    lhs_len = len(lhs_docs)
    rhs_len = len(rhs_docs)
    max_len = lhs_len if lhs_len > rhs_len else rhs_len
    lhs_limit = lhs_len - 1
    rhs_limit = rhs_len - 1
    for i in range(0, max_len):
        if i > rhs_limit:
            break
        if i > lhs_limit:
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

    return return_state

def merge_matrix(
    log: ConsolePrinter, lhs_docs: List[Merger], rhs_docs: List[Merger]
) -> int:
    """Condense LHS and RHS multi-docs together into one."""
    return_state = 0
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

def merge_docs(
    log: ConsolePrinter, yaml_editor: YAML, config: MergerConfig,
    lhs_docs: List[Merger], rhs_file: str
) -> int:
    """Merge RHS into LHS."""
    return_state = 0
    merge_mode = config.get_multidoc_mode()
    (rhs_docs, rhs_loaded) = get_doc_mergers(
        log, yaml_editor, config, rhs_file)
    if not rhs_loaded:
        # Failed to load any RHS documents
        return 3

    if merge_mode is MultiDocModes.CONDENSE_ALL:
        return_state = merge_condense_all(log, lhs_docs, rhs_docs)

    elif merge_mode is MultiDocModes.MERGE_ACROSS:
        return_state = merge_across(log, lhs_docs, rhs_docs)

    elif merge_mode is MultiDocModes.MATRIX_MERGE:
        return_state = merge_matrix(log, lhs_docs, rhs_docs)

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
    merge_count = 0
    for yaml_file in args.yaml_files:
        if yaml_file.strip() == '-':
            consumed_stdin = True

        log.debug(
            "yaml_merge::main:  Processing file, {}".format(
                "STDIN" if yaml_file.strip() == "-" else yaml_file))

        if len(mergers) < 1:
            (mergers, mergers_loaded) = get_doc_mergers(
                log, yaml_editor, merge_config, yaml_file)
            if not mergers_loaded:
                exit_state = 4
                break
        else:
            # Merge RHS into LHS
            exit_state = merge_docs(
                log, yaml_editor, merge_config, mergers, yaml_file)
            if not exit_state == 0:
                break
            merge_count += 1

    # Check for a waiting STDIN document
    if (exit_state == 0
        and not consumed_stdin
        and not args.nostdin
        and not sys.stdin.isatty()
    ):
        exit_state = merge_docs(log, yaml_editor, merge_config, mergers, "-")
        merge_count += 1

    # When no merges have occurred, check for a single-doc merge request
    if (exit_state == 0
        and merge_count == 0
        and merge_config.get_multidoc_mode() is MultiDocModes.CONDENSE_ALL
    ):
        exit_state = merge_condense_all(log, mergers, [])

    # Output the final document
    if exit_state == 0:
        write_output_document(args, log, yaml_editor, mergers)

    sys.exit(exit_state)

if __name__ == "__main__":
    main()  # pragma: no cover
