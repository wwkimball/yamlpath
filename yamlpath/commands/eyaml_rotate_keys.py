"""
Enable users to rotate EYAML encryption keys used for pre-encrypted files.

Rotates the encryption keys used for all EYAML values within a set of YAML
files, decrypting with old keys and re-encrypting using replacement keys.

Copyright 2018, 2019 William W. Kimball, Jr. MBA MSIS
"""
import sys
import argparse
from shutil import copy2
from os import remove, access, R_OK
from os.path import isfile, exists

from ruamel.yaml.scalarstring import FoldedScalarString

from yamlpath import __version__ as YAMLPATH_VERSION
from yamlpath.common import Anchors, Parsers
from yamlpath.eyaml.exceptions import EYAMLCommandException
from yamlpath.eyaml.enums import EYAMLOutputFormats
from yamlpath.eyaml import EYAMLProcessor
from yamlpath.wrappers import ConsolePrinter

def processcli():
    """Process command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Rotates the encryption keys used for all EYAML values"
            " within a set of YAML files, decrypting with old keys and"
            " re-encrypting using replacement keys."),
        epilog=(
            "Any YAML_FILEs lacking EYAML values will not be modified (or"
            " backed up, even when -b/--backup is specified).  For more"
            " information about YAML Paths, please visit"
            " https://github.com/wwkimball/yamlpath/wiki.  To report issues"
            " with this tool or to request enhancements, please visit"
            " https://github.com/wwkimball/yamlpath/issues.")
    )
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s " + YAMLPATH_VERSION)

    noise_group = parser.add_mutually_exclusive_group()
    noise_group.add_argument("-d", "--debug", action="store_true",
                             help="output debugging details")
    noise_group.add_argument("-v", "--verbose", action="store_true",
                             help="increase output verbosity")
    noise_group.add_argument("-q", "--quiet", action="store_true",
                             help="suppress all output except errors")

    parser.add_argument("-b", "--backup", action="store_true",
                        help="save a backup of each modified YAML_FILE with an"
                        + " extra .bak file-extension")
    parser.add_argument("-x", "--eyaml", default="eyaml",
                        help="the eyaml binary to use when it isn't on the"
                        + " PATH")

    key_group = parser.add_argument_group(
        "EYAML_KEYS", "All key arguments are required"
    )
    key_group.add_argument("-r", "--newprivatekey", required=True,
                           help="the new EYAML private key")
    key_group.add_argument("-u", "--newpublickey", required=True,
                           help="the new EYAML public key")
    key_group.add_argument("-i", "--oldprivatekey", required=True,
                           help="the old EYAML private key")
    key_group.add_argument("-c", "--oldpublickey", required=True,
                           help="the old EYAML public key")

    parser.add_argument("yaml_files", metavar="YAML_FILE", nargs="+",
                        help="one or more YAML files containing EYAML values")
    return parser.parse_args()

def validateargs(args, log):
    """Validate command-line arguments."""
    has_errors = False

    # Enforce sanity
    # * The new and old EYAML keys must be different
    if ((args.newprivatekey == args.oldprivatekey)
            or (args.newpublickey == args.oldpublickey)):
        has_errors = True
        log.error("The new and old EYAML keys must be different.")

    # * All EYAML certs must exist and be readable to the present user
    for check_file in [args.newprivatekey,
                       args.newpublickey,
                       args.oldprivatekey,
                       args.oldpublickey]:
        if not (isfile(check_file) and access(check_file, R_OK)):
            has_errors = True
            log.error(
                "EYAML key is not a readable file:  " + check_file
            )

    if has_errors:
        sys.exit(1)

# pylint: disable=locally-disabled,too-many-locals,too-many-branches,too-many-statements
def main():
    """Perform the work specified via CLI arguments and exit.

    Main code.
    """
    # Process any command-line arguments
    args = processcli()
    log = ConsolePrinter(args)
    validateargs(args, log)
    processor = EYAMLProcessor(log, None, binary=args.eyaml)

    # Prep the YAML parser
    yaml = Parsers.get_yaml_editor()

    # Process the input file(s)
    in_file_count = len(args.yaml_files)
    exit_state = 0
    for yaml_file in args.yaml_files:
        file_changed = False
        backup_file = yaml_file + ".bak"
        seen_anchors = []

        # Each YAML_FILE must actually be a file
        if not isfile(yaml_file):
            log.error("Not a file:  {}".format(yaml_file))
            exit_state = 2
            continue

        # Don't bother with the file change update when there's only one input
        # file.
        if in_file_count > 1:
            log.info("Processing {}...".format(yaml_file))

        # Try to open the file
        (yaml_data, doc_loaded) = Parsers.get_yaml_data(yaml, log, yaml_file)
        if not doc_loaded:
            # An error message has already been logged
            exit_state = 3
            continue

        # Process all EYAML values
        processor.data = yaml_data
        for yaml_path in processor.find_eyaml_paths():
            # Use ::get_nodes() instead of ::get_eyaml_values() here in order
            # to ignore values that have already been rotated via their
            # Anchors.
            for node_coordinate in processor.get_nodes(
                yaml_path, mustexist=True
            ):
                # Ignore values which are Aliases for those already decrypted
                node = node_coordinate.node
                anchor_name = Anchors.get_node_anchor(node)
                if anchor_name is not None:
                    if anchor_name in seen_anchors:
                        continue

                    seen_anchors.append(anchor_name)

                log.verbose("Decrypting value(s) at {}.".format(yaml_path))
                processor.publickey = args.oldpublickey
                processor.privatekey = args.oldprivatekey

                try:
                    txtval = processor.decrypt_eyaml(node)
                except EYAMLCommandException as ex:
                    log.error(ex)
                    exit_state = 3
                    continue

                # Prefer block (folded) values unless the original YAML value
                # was already a massivly long (string) line.
                output = EYAMLOutputFormats.BLOCK
                if not isinstance(node, FoldedScalarString):
                    output = EYAMLOutputFormats.STRING

                # Re-encrypt the value with new EYAML keys
                processor.publickey = args.newpublickey
                processor.privatekey = args.newprivatekey

                try:
                    processor.set_eyaml_value(yaml_path, txtval, output=output)
                except EYAMLCommandException as ex:
                    log.error(ex)
                    exit_state = 3
                    continue

                file_changed = True

        # Save the changes
        if file_changed:
            if args.backup:
                log.verbose("Saving a backup of {} to {}."
                            .format(yaml_file, backup_file))
                if exists(backup_file):
                    remove(backup_file)
                copy2(yaml_file, backup_file)

            log.verbose("Writing changed data to {}.".format(yaml_file))
            with open(yaml_file, 'w', encoding='utf-8') as yaml_dump:
                yaml.dump(yaml_data, yaml_dump)

    sys.exit(exit_state)

if __name__ == "__main__":
    main()  # pragma: no cover
