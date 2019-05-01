#!/usr/bin/env python3
################################################################################
# Changes one or more values in a YAML file at a specified YAML Path.  When
# singular, a value can be checked before it is replaced to mitigate accidental
# change.  Also when singular, the value can be archived to another key before
# it is replaced.  Further, EYAML can be employed to encrypt the new values
# and/or decrypt an old value before checking it.
#
# Requirements:
# 1. Python >= 3.6
#    * CentOS:  yum -y install epel-release && yum -y install python36 python36-pip
# 2. The ruamel.yaml module, version >= 0.15
#    * CentOS:  pip3 install ruamel.yaml
#
# Copyright 2018, 2019 William W. Kimball, Jr. MBA MSIS
################################################################################
import sys
import argparse
import secrets
import string
from os import remove, access, R_OK
from os.path import isfile, exists
from shutil import copy2

from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError

import ruamelpatches
from yamlexceptions import YAMLPathException
from consoleprinter import ConsolePrinter
from eyamlhelpers import EYAMLHelpers
from yamlhelpers import YAMLValueFormats

# Implied Constants
MY_VERSION = "1.0.0"

def processcli():
    # Process command-line arguments
    parser = argparse.ArgumentParser(
        description="Changes a value in a YAML file at a specified YAML\
            Path.  The value can be checked before it is replaced to mitigate\
            accidental changes.  The value can also be archived to another key\
            before it is replaced.  EYAML can also be employed to encrypt the\
            new value and/or decrypt the old value before checking it.",
        epilog="When no changes are made, no backup is created, even when\
            -b/--backup is specified."
    )
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s " + MY_VERSION)

    required_group = parser.add_argument_group("required settings")
    required_group.add_argument(
        "-k", "--key",
        required=True,
        metavar="YAML_PATH",
        help="YAML Path where the target value is found"
    )

    inputex_group = parser.add_argument_group("input options")
    input_group = inputex_group.add_mutually_exclusive_group()
    input_group.add_argument("-a", "--value",
        help="set the new value from the command-line instead of STDIN")
    input_group.add_argument("-f", "--file",
        help="read the new value from file (discarding any trailing\
              new-lines)")
    input_group.add_argument("-i", "--stdin", action="store_true",
        help="accept the new value from STDIN (best for sensitive data)")
    input_group.add_argument("-R", "--random",
        type=int,
        metavar="LENGTH",
        help="randomly generate a replacement value of a set length"
    )

    parser.add_argument("-F", "--format",
        default="default",
        choices=[l.lower() for l in YAMLValueFormats.get_names()],
        type=str.lower,
        help="override automatic formatting of the new value"
    )
    parser.add_argument("-c", "--check",
        help="check the value before replacing it")
    parser.add_argument("-s", "--saveto", metavar="YAML_PATH",
        help="save the old value to YAML_PATH before replacing it")
    parser.add_argument("-b", "--backup", action="store_true",
        help="save a backup YAML_FILE with an extra .bak file-extension")

    eyaml_group = parser.add_argument_group(
        "EYAML options", "Left unset, the EYAML keys will default to your\
         system or user defaults.  Both keys must be set when using EYAML.")
    eyaml_group.add_argument("-e", "--eyamlcrypt", action="store_true",
        help="encrypt the new value using EYAML")
    eyaml_group.add_argument("-x", "--eyaml", default="eyaml",
        help="the eyaml binary to use when it isn't on the PATH")
    eyaml_group.add_argument("-r", "--privatekey", help="EYAML private key")
    eyaml_group.add_argument("-u", "--publickey", help="EYAML public key")

    noise_group = parser.add_mutually_exclusive_group()
    noise_group.add_argument("-d", "--debug", action="store_true",
        help="output debugging details")
    noise_group.add_argument("-v", "--verbose", action="store_true",
        help="increase output verbosity")
    noise_group.add_argument("-q", "--quiet", action="store_true",
        help="suppress all output except errors")

    parser.add_argument("yaml_file", metavar="YAML_FILE",
        help="the YAML file to update")
    return parser.parse_args()

def validateargs(args, log):
    # Enforce sanity
    # * At least one of --value, --file, --stdin, or --random must be set
    if not (args.value
        or args.file
        or args.stdin
        or args.random
    ):
        log.error(
            "Exactly one of the following must be set:  --value, --file,"
                 + " --stdin, or --random",
            1
        )

    # * When set, --saveto cannot be identical to --key
    if args.saveto and args.saveto == args.key:
        log.error(
            "Impossible to save the old value to the same YAML Path as the new"
                + " value!",
            1
        )

    # * When set, --privatekey must be a readable file
    if args.privatekey and not (
        isfile(args.privatekey) and access(args.privatekey, R_OK)
    ):
        log.error(
            "EYAML private key is not a readable file:  " + args.privatekey,
            1
        )

    # * When set, --publickey must be a readable file
    if args.publickey and not (
        isfile(args.publickey) and access(args.publickey, R_OK)
    ):
        log.error(
            "EYAML public key is not a readable file:  " + args.publickey,
            1
        )

    # * When either --publickey or --privatekey are set, the other must also be
    if (
        (args.publickey and not args.privatekey)
        or (args.privatekey and not args.publickey)
    ):
        log.error("Both private and public EYAML keys must be set.", 1)

args = processcli()
log = ConsolePrinter(args)
validateargs(args, log)
yh = EYAMLHelpers(
    log,
    eyaml=args.eyaml,
    publickey=args.publickey,
    privatekey=args.privatekey
)
backup_file = args.yaml_file + ".bak"

# Obtain the replacement value
if args.value:
    new_value = args.value
elif args.stdin:
    new_value = ''.join(sys.stdin.readlines())
elif args.file:
    with open(args.file, 'r') as f:
        new_value = f.read().rstrip()
elif args.random is not None:
    new_value = ''.join(
        secrets.choice(
            string.ascii_uppercase + string.ascii_lowercase + string.digits
        ) for _ in range(args.random)
    )
else:
    log.error("Unsupported input method.", 1)

# Prep the YAML parser
yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.explicit_start = True
yaml.preserve_quotes = True
yaml.width = sys.maxsize

# Attempt to open the YAML file; check for parsing errors
try:
    with open(args.yaml_file, 'r') as f:
        yaml_data = yaml.load(f)
except ParserError as e:
    log.error("YAML parsing error " + str(e.problem_mark).lstrip() + ": " + e.problem)

# Load the present value at the specified YAML Path
change_path = yh.str_path(args.key)
change_nodes = []

try:
    for node in yh.get_eyaml_values(yaml_data, change_path):
        if node is None:
            continue

        log.verbose("Got {} from {}.".format(node, change_path))

        # Do nothing if the value will not be changing, unless we can infer that
        # this is an EYAML recrypt attempt.
        if new_value == node and not args.eyamlcrypt:
            log.warning("New and old values are identical.")
            continue

        change_nodes.append(node)
except YAMLPathException as ex:
    log.error(ex, 1)

log.debug("Collected nodes:")
log.debug(change_nodes)

if 1 > len(change_nodes):
    log.warning("Nothing to do!")
    exit(0)

# Check the value(s), if desired
for node in change_nodes:
    if args.check:
        if not args.check == node:
            log.error("{} does not match the check value.".format(node), 20)

# Save the old value, if desired and possible
if args.saveto:
    # Only one can be saved; otherwise it is impossible to meaningfully convey
    # to the end-user from exactly which other YAML node each saved value came.
    if 1 < len(change_nodes):
        log.error(
            "It is impossible to meaningly save more than one matched value."
            + "  Please omit --saveto or set --key to affect exactly one value."
            , 1
        )

    log.verbose("Saving the old value to {}.".format(args.saveto))
    try:
        log.verbose("Writing a single value...")
        yh.set_value(yaml_data, args.saveto, yh.clone_node(change_nodes[0]))
        log.verbose("DONE writing a single value...")
    except YAMLPathException as ex:
        log.error(ex, 1)

# Set the requested value
log.verbose("Setting {} to {}.".format(change_path, new_value))
if args.eyamlcrypt:
    output_type = "string"
    format_type = YAMLValueFormats.from_str(args.format)
    if format_type in [YAMLValueFormats.FOLDED, YAMLValueFormats.LITERAL]:
        output_type = "block"
    try:
        yh.set_eyaml_value(yaml_data, change_path, new_value, output_type, False)
    except YAMLPathException as ex:
        log.error(ex, 1)
else:
    try:
        log.verbose("Overwriting a single value...")
        yh.set_value(yaml_data, change_path, new_value, False, args.format)
    except YAMLPathException as ex:
        log.error(ex, 1)

# Save a backup of the original file, if requested
if args.backup:
    log.verbose("Saving a backup of " + args.yaml_file + " to " + backup_file)
    if exists(backup_file):
        remove(backup_file)
    copy2(args.yaml_file, backup_file)

# Save the changed file
log.verbose("Writing changed data to " + args.yaml_file)
with open(args.yaml_file, 'w') as yaml_dump:
    yaml.dump(yaml_data, yaml_dump)
