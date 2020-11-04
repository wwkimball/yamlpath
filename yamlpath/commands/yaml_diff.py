"""
Calculate the differences between two YAML/JSON/Compatible documents.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
import sys
import argparse
from os import access, R_OK
from os.path import isfile

from yamlpath import __version__ as YAMLPATH_VERSION
from yamlpath.common import Parsers
from yamlpath.enums import PathSeperators
from yamlpath.differ.enums import AoHDiffOpts, ArrayDiffOpts
from yamlpath.wrappers import ConsolePrinter
from yamlpath.differ import DifferConfig, Differ
from yamlpath.differ.enums import DiffActions
from yamlpath.eyaml.exceptions.eyamlcommand import EYAMLCommandException

def processcli():
    """Process command-line arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=(
            "Compare YAML/JSON/Compatible documents node by node.  EYAML can"
            " be employed to\ncompare encrypted values."),
        epilog="""
configuration file:
  The CONFIG file is an INI file with up to three sections:
  [defaults] Sets equivalents of --arrays|-A and --aoh|-O.
  [rules]    Each entry is a YAML Path assigning --arrays|-A or --aoh|-O for
             precise nodes.
  [keys]     Wherever --aoh=key (or -O key) or --aoh=deep (or -O deep), each
             entry is treated as a record with an identity key.  In order to
             match RHS records to LHS records, a key must be known and is
             identified on a YAML Path basis via this section.  Where not
             specified, the first attribute of the first record in the
             Array-of-Hashes is presumed the identity key for all records in
             the set.

input files:
  Only one input file may be the - pseudo-file (read from STDIN).  Because the
  relative position of the two input files is important, this will not be
  inferred; you must use - to indicate which document is read from STDIN.

  It doesn't make any sense to compare multi-document files, so only single-
  document files are supported.

For more information about YAML Paths, please visit
https://github.com/wwkimball/yamlpath/wiki.

To report issues with this tool or to request enhancements, please visit
https://github.com/wwkimball/yamlpath/issues.
""")
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s " + YAMLPATH_VERSION)

    parser.add_argument(
        "-c", "--config",
        help="INI syle configuration file for YAML Path specified\ncomparison"
             " control options")

    parser.add_argument(
        "-A", "--arrays",
        choices=[l.lower() for l in ArrayDiffOpts.get_names()],
        type=str.lower,
        help="default means by which Arrays are compared (overrides\n"
            "[defaults]arrays but is overridden on a YAML Path\nbasis via"
            " --config|-c); default={}".format(ArrayDiffOpts.POSITION))
    parser.add_argument(
        "-O", "--aoh",
        choices=[l.lower() for l in AoHDiffOpts.get_names()],
        type=str.lower,
        help=(
            "default means by which Arrays-of-Hashes are compared\n(overrides"
            " [defaults]aoh but is overridden on a YAML\nPath basis in [rules]"
            " set via --config|-c);\ndefault={}".format(AoHDiffOpts.POSITION)))

    sameness_group = parser.add_mutually_exclusive_group()
    sameness_group.add_argument(
        "-s", "--same", action="store_true",
        help="Show all nodes which are the same in addition to\ndifferences")
    sameness_group.add_argument(
        "-o", "--onlysame", action="store_true",
        help="Show only nodes which are the same, still reporting\nthat"
             " differences exist -- when they do -- with an\nexit-state of 1")

    parser.add_argument(
        "-t", "--pathsep",
        default="dot",
        choices=PathSeperators,
        metavar=PathSeperators.get_choices(),
        type=PathSeperators.from_str,
        help="indicate which YAML Path seperator to use when\nrendering"
             " results; default=dot")

    eyaml_group = parser.add_argument_group(
        "EYAML options", "Left unset, the EYAML keys will default to your"
        "system or user defaults.\nBoth keys must be set either here or in"
        "your system or user EYAML\nconfiguration file when using EYAML.")
    eyaml_group.add_argument(
        "-x", "--eyaml",
        default="eyaml",
        help="the eyaml binary to use when it isn't on the PATH")
    eyaml_group.add_argument("-r", "--privatekey", help="EYAML private key")
    eyaml_group.add_argument("-u", "--publickey", help="EYAML public key")
    eyaml_group.add_argument(
        "-E", "--ignore-eyaml-values",
        action="store_true",
        help="Do not use EYAML to compare encrypted data; rather,\ntreat"
             " ENC[...] values as regular strings")

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
                             " compare; use\n- to read one document from"
                             " STDIN")

    return parser.parse_args()

def validateargs(args, log):
    """Validate command-line arguments."""
    has_errors = False

    # There can be only one -
    pseudofile_count = 0
    for infile in args.yaml_files:
        if infile.strip() == '-':
            pseudofile_count += 1
    if pseudofile_count > 1:
        has_errors = True
        log.error("Only one YAML_FILE may be the - pseudo-file.")

    # --quiet cannot be used with --same or --onlysame
    if args.quiet and (args.same or args.onlysame):
        has_errors = True
        log.error(
            "The --quiet|-q option suppresses all output, including that of"
            " --same|-s and --onlysame|-o, so they cannot be set together.")

    # When set, the configuration file must be a readable file
    if args.config and not (
            isfile(args.config)
            and access(args.config, R_OK)
    ):
        has_errors = True
        log.error(
            "INI style configuration file is not readable:  {}"
            .format(args.config))

    # When set, --privatekey must be a readable file
    if args.privatekey and not (
            isfile(args.privatekey)
            and access(args.privatekey, R_OK)
    ):
        has_errors = True
        log.error(
            "EYAML private key is not a readable file:  " + args.privatekey)

    # When set, --publickey must be a readable file
    if args.publickey and not (
            isfile(args.publickey)
            and access(args.publickey, R_OK)
    ):
        has_errors = True
        log.error(
            "EYAML public key is not a readable file:  " + args.publickey)

    if has_errors:
        sys.exit(1)

def print_report(log, args, diff):
    """Print user-customized report."""
    changes_found = False
    print_sep = False
    print_verbosely = args.verbose or args.debug
    for entry in diff.get_report():
        is_different = entry.action is not DiffActions.SAME
        if is_different:
            changes_found = True

        if args.quiet:
            continue

        if (
            (is_different and not args.onlysame)
            or (args.onlysame and not is_different)
            or args.same
        ):
            if print_sep:
                log.info("")
            entry.pathsep = args.pathsep
            entry.verbose = print_verbosely
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
    rhs_file = args.yaml_files[1]
    lhs_yaml = Parsers.get_yaml_editor()
    rhs_yaml = Parsers.get_yaml_editor()

    (lhs_document, doc_loaded) = Parsers.get_yaml_data(lhs_yaml, log, lhs_file)
    if not doc_loaded:
        # An error message has already been logged
        sys.exit(1)

    (rhs_document, doc_loaded) = Parsers.get_yaml_data(rhs_yaml, log, rhs_file)
    if not doc_loaded:
        # An error message has already been logged
        sys.exit(1)

    diff = Differ(
        DifferConfig(log, args), log, lhs_document,
        ignore_eyaml_values=args.ignore_eyaml_values, binary=args.eyaml,
        publickey=args.publickey, privatekey=args.privatekey)

    try:
        diff.compare_to(rhs_document)
    except EYAMLCommandException as ex:
        log.critical(ex, 1)

    exit_state = 1 if print_report(log, args, diff) else 0
    sys.exit(exit_state)

if __name__ == "__main__":
    main()  # pragma: no cover
