"""
Enable users to get data out of YAML/Compatible files using YAML Paths.

Retrieves one or more values from a YAML file at a specified YAML Path.
Output is printed to STDOUT, one line per match.  When a result is a complex
data-type (Array or Hash), a JSON dump is produced to represent each complex
result.  EYAML can be employed to decrypt the values.

Copyright 2018, 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
import sys
import argparse
import json
from os import access, R_OK
from os.path import isfile

from yamlpath import __version__ as YAMLPATH_VERSION
from yamlpath.common import Parsers
from yamlpath import YAMLPath
from yamlpath.exceptions import YAMLPathException
from yamlpath.eyaml.exceptions import EYAMLCommandException
from yamlpath.enums import PathSeperators
from yamlpath.wrappers import NodeCoords
from yamlpath.eyaml import EYAMLProcessor

from yamlpath.wrappers import ConsolePrinter

def processcli():
    """Process command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Retrieves one or more values from a YAML/JSON/Compatible"
            " file at a specified YAML Path.  Output is printed to STDOUT, one"
            " line per result.  When a result is a complex data-type (Array or"
            " Hash), a JSON dump is produced to represent it.  EYAML can be"
            " employed to decrypt the values."),
        epilog=(
            "For more information about YAML Paths, please visit"
            " https://github.com/wwkimball/yamlpath/wiki.  To report issues"
            " with this tool or to request enhancements, please visit"
            " https://github.com/wwkimball/yamlpath/issues.")
    )
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s " + YAMLPATH_VERSION)

    required_group = parser.add_argument_group("required settings")
    required_group.add_argument(
        "-p", "--query",
        required=True,
        metavar="YAML_PATH",
        help="YAML Path to query"
    )

    parser.add_argument(
        "-t", "--pathsep",
        default="dot",
        choices=PathSeperators,
        metavar=PathSeperators.get_choices(),
        type=PathSeperators.from_str,
        help="indicate which YAML Path seperator to use when rendering\
              results; default=dot")

    parser.add_argument(
        "-S", "--nostdin", action="store_true",
        help=(
            "Do not implicitly read from STDIN, even when YAML_FILE is not set"
            " and the session is non-TTY"))

    eyaml_group = parser.add_argument_group(
        "EYAML options", "Left unset, the EYAML keys will default to your\
         system or user defaults.  Both keys must be set either here or in\
         your system or user EYAML configuration file when using EYAML.")
    eyaml_group.add_argument(
        "-x", "--eyaml",
        default="eyaml",
        help="the eyaml binary to use when it isn't on the PATH")
    eyaml_group.add_argument("-r", "--privatekey", help="EYAML private key")
    eyaml_group.add_argument("-u", "--publickey", help="EYAML public key")

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
        help="suppress all output except errors")

    parser.add_argument(
        "yaml_file", metavar="YAML_FILE",
        nargs="?",
        help="the YAML file to query; omit or use - to read from STDIN")

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
        log.error("YAML_FILE must be set or be read from STDIN.")

    # When set, --privatekey must be a readable file
    if args.privatekey and not (
            isfile(args.privatekey) and access(args.privatekey, R_OK)
    ):
        has_errors = True
        log.error(
            "EYAML private key is not a readable file:  " + args.privatekey
        )

    # When set, --publickey must be a readable file
    if args.publickey and not (
            isfile(args.publickey) and access(args.publickey, R_OK)
    ):
        has_errors = True
        log.error(
            "EYAML public key is not a readable file:  " + args.publickey
        )

    # When either --publickey or --privatekey are set, the other must also
    # be.  This is because the `eyaml` command requires them both when
    # decrypting values.
    if (
            (args.publickey and not args.privatekey)
            or (args.privatekey and not args.publickey)
    ):
        has_errors = True
        log.error("Both private and public EYAML keys must be set.")

    # When dumping the document to STDOUT, mute all non-errors
    force_verbose = args.verbose
    force_debug = args.debug
    if in_stream_mode and not (force_verbose or force_debug):
        args.quiet = True
        args.verbose = False
        args.debug = False

    if has_errors:
        sys.exit(1)

def main():
    """Main code."""
    args = processcli()
    log = ConsolePrinter(args)
    validateargs(args, log)
    yaml_path = YAMLPath(args.query, pathsep=args.pathsep)

    # Prep the YAML parser
    yaml = Parsers.get_yaml_editor()

    # Attempt to open the YAML file; check for parsing errors
    (yaml_data, doc_loaded) = Parsers.get_yaml_data(
        yaml, log,
        args.yaml_file if args.yaml_file else "-")
    if not doc_loaded:
        # An error message has already been logged
        sys.exit(1)

    # Seek the queried value(s)
    discovered_nodes = []
    processor = EYAMLProcessor(
        log, yaml_data, binary=args.eyaml,
        publickey=args.publickey, privatekey=args.privatekey)
    try:
        for node in processor.get_eyaml_values(yaml_path, mustexist=True):
            log.debug(
                "Got node from {}:".format(yaml_path), data=node,
                prefix="yaml_get::main:  ")
            discovered_nodes.append(NodeCoords.unwrap_node_coords(node))
    except YAMLPathException as ex:
        log.critical(ex, 1)
    except EYAMLCommandException as ex:
        log.critical(ex, 2)

    try:
        for node in discovered_nodes:
            if isinstance(node, (dict, list)):
                print(json.dumps(Parsers.jsonify_yaml_data(node)))
            else:
                if node is None:
                    node = "\x00"
                print("{}".format(str(node).replace("\n", r"\n")))
    except RecursionError:
        log.critical(
            "The YAML data contains an infinitely recursing YAML Alias!", 1)

if __name__ == "__main__":
    main()  # pragma: no cover
