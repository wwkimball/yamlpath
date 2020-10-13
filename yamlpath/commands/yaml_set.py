"""
Enable users to change YAML/Compatible files using YAML Paths.

Changes one or more values in a YAML file at a specified YAML Path.  Matched
values can be checked before they are replaced to mitigate accidental change.
When matching singular results, the value can be archived to another key
before it is replaced.  Further, EYAML can be employed to encrypt the new
values and/or decrypt old values before checking them.

Copyright 2018, 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
import sys
import tempfile
import argparse
import secrets
import string
import json
from os import remove, access, R_OK
from os.path import isfile, exists
from shutil import copy2, copyfileobj
from pathlib import Path


from yamlpath.common import YAMLPATH_VERSION
from yamlpath.func import (
    clone_node,
    build_next_node,
    get_yaml_data,
    get_yaml_editor
)
from yamlpath import YAMLPath
from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import YAMLValueFormats, PathSeperators
from yamlpath.eyaml.exceptions import EYAMLCommandException
from yamlpath.eyaml.enums import EYAMLOutputFormats
from yamlpath.eyaml import EYAMLProcessor

# pylint: disable=locally-disabled,unused-import
import yamlpath.patches
from yamlpath.wrappers import ConsolePrinter

def processcli():
    """Process command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Changes one or more Scalar values in a\
            YAML/JSON/Compatible document at a specified YAML Path.  Matched\
            values can be checked before they are replaced to mitigate\
            accidental change.  When matching singular results, the value can\
            be archived to another key before it is replaced.  Further, EYAML\
            can be employed to encrypt the new values and/or decrypt an old\
            value before checking it.",
        epilog="When no changes are made, no backup is created, even when\
            -b/--backup is specified.  For more information about YAML Paths,\
            please visit https://github.com/wwkimball/yamlpath."
    )
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s " + YAMLPATH_VERSION)

    required_group = parser.add_argument_group("required settings")
    required_group.add_argument(
        "-g", "--change",
        required=True,
        metavar="YAML_PATH",
        help="YAML Path where the target value is found")

    inputex_group = parser.add_argument_group("input options")
    input_group = inputex_group.add_mutually_exclusive_group()
    input_group.add_argument(
        "-a", "--value",
        help="set the new value from the command-line instead of STDIN")
    input_group.add_argument(
        "-f", "--file",
        help="read the new value from file (discarding any trailing\
              new-lines)")
    input_group.add_argument(
        "-i", "--stdin", action="store_true",
        help="accept the new value from STDIN (best for sensitive data)")
    input_group.add_argument(
        "-R", "--random",
        type=int,
        metavar="LENGTH",
        help="randomly generate a replacement value of a set length")

    parser.add_argument(
        "-F", "--format",
        default="default",
        choices=[l.lower() for l in YAMLValueFormats.get_names()],
        type=str.lower,
        help="override automatic formatting of the new value")
    parser.add_argument(
        "-c", "--check",
        help="check the value before replacing it")
    parser.add_argument(
        "-s", "--saveto", metavar="YAML_PATH",
        help="save the old value to YAML_PATH before replacing it; implies\
              --mustexist")
    parser.add_argument(
        "-m", "--mustexist", action="store_true",
        help="require that the --change YAML_PATH already exist in YAML_FILE")
    parser.add_argument(
        "-b", "--backup", action="store_true",
        help="save a backup YAML_FILE with an extra .bak file-extension")
    parser.add_argument(
        "-t", "--pathsep",
        default="dot",
        choices=PathSeperators,
        metavar=PathSeperators.get_choices(),
        type=PathSeperators.from_str,
        help="indicate which YAML Path seperator to use when rendering\
              results; default=dot")

    parser.add_argument(
        "-M", "--random-from",
        metavar="CHARS",
        default=(string.ascii_uppercase +
            string.ascii_lowercase +
            string.digits),
        help="characters from which to build a value for --random; default="
             "all upper- and lower-case letters and all digits"
    )

    eyaml_group = parser.add_argument_group(
        "EYAML options", "Left unset, the EYAML keys will default to your\
         system or user defaults.  You do not need to supply a private key\
         unless you enable --check and the old value is encrypted.")
    eyaml_group.add_argument(
        "-e", "--eyamlcrypt", action="store_true",
        help="encrypt the new value using EYAML")
    eyaml_group.add_argument(
        "-x", "--eyaml", default="eyaml",
        help="the eyaml binary to use when it isn't on the PATH")
    eyaml_group.add_argument("-r", "--privatekey", help="EYAML private key")
    eyaml_group.add_argument("-u", "--publickey", help="EYAML public key")

    parser.add_argument(
        "-S", "--nostdin", action="store_true",
        help=(
            "Do not implicitly read from STDIN, even when there is no"
            " YAML_FILE with a non-TTY session"))

    noise_group = parser.add_mutually_exclusive_group()
    noise_group.add_argument(
        "-d", "--debug", action="store_true",
        help="output debugging details")
    noise_group.add_argument(
        "-v", "--verbose", action="store_true",
        help="increase output verbosity")
    noise_group.add_argument(
        "-q", "--quiet", action="store_true",
        help="suppress all output except errors")

    parser.add_argument(
        "yaml_file", metavar="YAML_FILE", nargs="?",
        help="the YAML file to update; omit or use - to read from STDIN")
    return parser.parse_args()

def validateargs(args, log):
    """Validate command-line arguments."""
    has_errors = False
    in_file = args.yaml_file if args.yaml_file else ""
    in_stream_mode = in_file.strip() == "-" or (
        not in_file and not args.nostdin and not sys.stdin.isatty()
    )

    # When there is no YAML_FILE and no STDIN, there is nothing to read
    if not (in_file or in_stream_mode):
        has_errors = True
        log.error("There must be a YAML_FILE or STDIN document.")

    # Enforce sanity
    # * At least one of --value, --file, --stdin, or --random must be set
    if not (
            args.value
            or args.value == ""
            or args.file
            or args.stdin
            or args.random
    ):
        has_errors = True
        log.error(
            "Exactly one of the following must be set:  --value, --file,"
            + " --stdin, or --random")

    # * --stdin cannot be used with -, explicit or implied
    if args.stdin and in_stream_mode:
        has_errors = True
        log.error(
            "Impossible to read both document and replacement value from"
            " STDIN!")

    # * --backup has no meaning when reading the YAML file from STDIN
    if args.backup and in_stream_mode:
        has_errors = True
        log.error(
            "The --backup|-b option applies only when reading from a file, not"
            " STDIN.")

    # * When set, --saveto cannot be identical to --change
    if args.saveto and args.saveto == args.change:
        has_errors = True
        log.error(
            "Impossible to save the old value to the same YAML Path as the new"
            + " value!")

    # * When set, --privatekey must be a readable file
    if args.privatekey and not (
            isfile(args.privatekey)
            and access(args.privatekey, R_OK)
    ):
        has_errors = True
        log.error(
            "EYAML private key is not a readable file:  " + args.privatekey)

    # * When set, --publickey must be a readable file
    if args.publickey and not (
            isfile(args.publickey)
            and access(args.publickey, R_OK)
    ):
        has_errors = True
        log.error(
            "EYAML public key is not a readable file:  " + args.publickey)

    # * When set, --random-from must have at least one character
    if len(args.random_from) < 2:
        has_errors = True
        log.error("The pool of random CHARS must have at least 2 characters.")

    # When dumping the document to STDOUT, mute all non-errors
    force_verbose = args.verbose
    force_debug = args.debug
    if in_stream_mode and not (force_verbose or force_debug):
        args.quiet = True
        args.verbose = False
        args.debug = False

    if has_errors:
        sys.exit(1)

def save_to_json_file(args, log, yaml_data):
    """Save to a JSON file."""
    log.verbose("Writing changed data as JSON to {}.".format(args.yaml_file))
    with open(args.yaml_file, 'w') as out_fhnd:
        json.dump(yaml_data, out_fhnd)

def save_to_yaml_file(args, log, yaml_parser, yaml_data, backup_file):
    """Save to a YAML file."""
    log.verbose("Writing changed data as YAML to {}.".format(args.yaml_file))
    with tempfile.TemporaryFile() as tmphnd:
        with open(args.yaml_file, 'rb') as inhnd:
            copyfileobj(inhnd, tmphnd)

        with open(args.yaml_file, 'w') as yaml_dump:
            try:
                yaml_parser.dump(yaml_data, yaml_dump)
            except AssertionError as ex:
                yaml_dump.close()
                tmphnd.seek(0)
                with open(args.yaml_file, 'wb') as outhnd:
                    copyfileobj(tmphnd, outhnd)

                # No sense in preserving a backup file with no changes
                if args.backup:
                    remove(backup_file)

                log.debug(
                    "yaml_set::save_to_yaml_file:  Assertion error: {}"
                    .format(ex))
                log.critical((
                    "Indeterminate assertion error encountered while"
                    + " attempting to write updated data to {}.  The original"
                    + " file content was restored.").format(args.yaml_file), 3)

def docroot_is_flow(yaml_data):
    """Determine whether a document root is in flow (JSON) style."""
    is_flow = False
    if hasattr(yaml_data, "fa"):
        is_flow = yaml_data.fa.flow_style()
    return is_flow

def write_document_as_yaml(output_file_name, yaml_data):
    """Determine whether to write out YAML (or JSON)."""
    write_yaml = True
    if docroot_is_flow(yaml_data):
        write_yaml = False

    # Allow a JSON file extension to override the inference
    if write_yaml:
        write_yaml = Path(output_file_name).suffix.lower() != ".json"

    return write_yaml

def save_to_file(args, log, yaml_parser, yaml_data, backup_file):
    """Save as YAML or JSON."""
    if write_document_as_yaml(args.yaml_file, yaml_data):
        save_to_yaml_file(args, log, yaml_parser, yaml_data, backup_file)
    else:
        save_to_json_file(args, log, yaml_data)

def write_output_document(args, log, yaml, yaml_data):
    """Write the updated document to file or STDOUT."""
    # Save a backup of the original file, if requested
    backup_file = args.yaml_file + ".bak"
    if args.backup:
        log.verbose(
            "Saving a backup of {} to {}."
            .format(args.yaml_file, backup_file))
        if exists(backup_file):
            remove(backup_file)
        copy2(args.yaml_file, backup_file)

    # Save the changed file
    if args.yaml_file.strip() == "-":
        if write_document_as_yaml(args.yaml_file, yaml_data):
            yaml.dump(yaml_data, sys.stdout)
        else:
            json.dump(yaml_data, sys.stdout)
    else:
        save_to_file(args, log, yaml, yaml_data, backup_file)

def _try_load_input_file(args, log, yaml, change_path, new_value):
    """Attempt to load the input data file or abend on error."""
    yaml_data = get_yaml_data(yaml, log, args.yaml_file)
    if yaml_data is None:
        yaml_data = build_next_node(change_path, 0, new_value)
    elif not yaml_data and isinstance(yaml_data, bool):
        # An error message has already been logged
        sys.exit(1)
    return yaml_data

# pylint: disable=locally-disabled,too-many-locals,too-many-branches,too-many-statements
def main():
    """Main code."""
    args = processcli()
    log = ConsolePrinter(args)
    validateargs(args, log)
    change_path = YAMLPath(args.change, pathsep=args.pathsep)
    must_exist=args.mustexist or args.saveto

    # Obtain the replacement value
    consumed_stdin = False
    if args.value or args.value == "":
        new_value = args.value
    elif args.stdin:
        new_value = ''.join(sys.stdin.readlines())
        consumed_stdin = True
    elif args.file:
        with open(args.file, 'r') as fhnd:
            new_value = fhnd.read().rstrip()
    elif args.random is not None:
        new_value = ''.join(
            secrets.choice(args.random_from) for _ in range(args.random)
        )

    # Prep the YAML parser
    yaml = get_yaml_editor()

    # Attempt to open the YAML file; check for parsing errors
    if args.yaml_file:
        yaml_data = _try_load_input_file(
            args, log, yaml, change_path, new_value)
        if args.yaml_file.strip() == '-':
            consumed_stdin = True

    # Check for a waiting STDIN document
    if (not consumed_stdin
        and not args.yaml_file
        and not args.nostdin
        and not sys.stdin.isatty()
    ):
        args.yaml_file = "-"
        yaml_data = _try_load_input_file(
            args, log, yaml, change_path, new_value)

    # Load the present value at the specified YAML Path
    change_node_coordinates = []
    old_format = YAMLValueFormats.DEFAULT
    processor = EYAMLProcessor(
        log, yaml_data, binary=args.eyaml,
        publickey=args.publickey, privatekey=args.privatekey)
    try:
        for node_coordinate in processor.get_nodes(
                change_path, mustexist=must_exist,
                default_value=("" if new_value else " ")):
            log.debug(
                "Got node from {}:".format(change_path),
                data=node_coordinate, prefix="yaml_set::main:  ")
            change_node_coordinates.append(node_coordinate)
    except YAMLPathException as ex:
        log.critical(ex, 1)

    if len(change_node_coordinates) == 1:
        # When there is exactly one result, its old format can be known.  This
        # is necessary to retain whether the replacement value should be
        # represented later as a multi-line string when the new value is to be
        # encrypted.
        old_format = YAMLValueFormats.from_node(
            change_node_coordinates[0].node)

    log.debug(
        "Collected nodes:", data=change_node_coordinates,
        prefix="yaml_set::main:  ")

    # Check the value(s), if desired
    if args.check:
        for node_coordinate in change_node_coordinates:
            if processor.is_eyaml_value(node_coordinate.node):
                # Sanity check:  If either --publickey or --privatekey were set
                # then they must both be set in order to decrypt this value.
                # This is enforced only when the value must be decrypted due to
                # a --check request.
                if (
                        (args.publickey and not args.privatekey)
                        or (args.privatekey and not args.publickey)
                ):
                    log.error(
                        "Neither or both private and public EYAML keys must be"
                        + " set when --check is required to decrypt the old"
                        + " value.")
                    sys.exit(1)

                try:
                    check_value = processor.decrypt_eyaml(node_coordinate.node)
                except EYAMLCommandException as ex:
                    log.critical(ex, 1)
            else:
                check_value = node_coordinate.node

            if not args.check == check_value:
                log.critical(
                    '"{}" does not match the check value.'
                    .format(args.check),
                    20
                )

    # Save the old value, if desired and possible
    if args.saveto:
        # Only one can be saved; otherwise it is impossible to meaningfully
        # convey to the end-user from exactly which other YAML node each saved
        # value came.
        if len(change_node_coordinates) > 1:
            log.critical(
                "It is impossible to meaningly save more than one matched"
                + " value.  Please omit --saveto or set --change to affect"
                + " exactly one value.", 1)

        saveto_path = YAMLPath(args.saveto, pathsep=args.pathsep)
        log.verbose("Saving the old value to {}.".format(saveto_path))

        # Folded EYAML values have their embedded newlines converted to spaces
        # when read.  As such, writing them back out breaks their original
        # format, despite being properly typed.  To restore the original
        # written form, reverse the conversion, here.
        old_value = change_node_coordinates[0].node
        if (
                (old_format is YAMLValueFormats.FOLDED
                 or old_format is YAMLValueFormats.LITERAL
                )
                and EYAMLProcessor.is_eyaml_value(old_value)
        ):
            old_value = old_value.replace(" ", "\n")

        try:
            processor.set_value(
                saveto_path, clone_node(old_value),
                value_format=old_format)
        except YAMLPathException as ex:
            log.critical(ex, 1)

    # Set the requested value
    log.verbose("Setting the new value for {}.".format(change_path))
    if args.eyamlcrypt:
        # If the user hasn't specified a format, use the same format as the
        # value being replaced, if known.
        format_type = YAMLValueFormats.from_str(args.format)
        if format_type is YAMLValueFormats.DEFAULT:
            format_type = old_format

        output_type = EYAMLOutputFormats.STRING
        if format_type in [YAMLValueFormats.FOLDED, YAMLValueFormats.LITERAL]:
            output_type = EYAMLOutputFormats.BLOCK

        try:
            processor.set_eyaml_value(
                change_path, new_value, output=output_type, mustexist=False)
        except EYAMLCommandException as ex:
            log.critical(ex, 2)
    else:
        try:
            processor.set_value(
                change_path, new_value, value_format=args.format,
                mustexist=must_exist)
        except YAMLPathException as ex:
            log.critical(ex, 1)

    # Write out the result
    write_output_document(args, log, yaml, yaml_data)

if __name__ == "__main__":
    main()  # pragma: no cover
