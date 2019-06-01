"""
Returns zero or more YAML Paths indicating where in given YAML/Compatible data
a search expression matches.  Values and/or keys can be searched.  EYAML can be
employed to search encrypted values.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
import argparse
from os import access, R_OK
from os.path import isfile
from typing import Any, Generator, List, Optional

from ruamel.yaml.parser import ParserError
from ruamel.yaml.composer import ComposerError
from ruamel.yaml.scanner import ScannerError
from ruamel.yaml.comments import CommentedSeq, CommentedMap

from yamlpath.func import get_yaml_editor, search_matches, ensure_escaped
from yamlpath.enums import PathSeperators
from yamlpath.path import SearchTerms
from yamlpath import YAMLPath
from yamlpath.wrappers import ConsolePrinter
from yamlpath.eyaml import EYAMLProcessor

# Implied Constants
MY_VERSION = "0.0.1"

def processcli():
    """Process command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Returns zero or more YAML Paths indicating where in given\
            YAML/Compatible data one or more search expressions match.\
            Values, keys, and/or anchors can be searched.  EYAML can be\
            employed to search encrypted values.",
        epilog="For more information about YAML Paths, please visit\
            https://github.com/wwkimball/yamlpath."
    )
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s " + MY_VERSION)

    required_group = parser.add_argument_group("required settings")
    required_group.add_argument(
        "-s", "--search",
        required=True,
        metavar="EXPRESSION", action="append",
        help="the search expression; can be set more than once")

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
        "-t", "--pathsep",
        default="dot",
        choices=PathSeperators,
        metavar=PathSeperators.get_choices(),
        type=PathSeperators.from_str,
        help="indicate which YAML Path seperator to use when rendering\
              results; default=dot")

    parser.add_argument(
        "-n", "--anchors",
        action="store_true",
        help="search anchor names")

    keyname_group_ex = parser.add_argument_group("Key name searching options")
    keyname_group = keyname_group_ex.add_mutually_exclusive_group()
    keyname_group.add_argument(
        "-i", "--ignorekeynames",
        action="store_true",
        help="(default) do not search key names")
    keyname_group.add_argument(
        "-k", "--keynames",
        action="store_true",
        help="search key names in addition to values and array elements")
    keyname_group.add_argument(
        "-o", "--onlykeynames",
        action="store_true",
        help="only search key names (ignore all values and array elements)")

    dedup_group_ex = parser.add_argument_group(
        "Duplicate alias options",
        "An 'anchor' is an original, reusable key or value.  An 'alias' is a\
         copy of an 'anchor'.  These options specify how to handle this\
        duplication.")
    dedup_group = dedup_group_ex.add_mutually_exclusive_group()
    dedup_group.add_argument(
        "-c", "--originals",
        action="store_const",
        dest="include_aliases",
        const=False,
        help="(default) include only the original anchor in matching results")
    dedup_group.add_argument(
        "-a", "--duplicates",
        action="store_const",
        dest="include_aliases",
        const=True,
        help="include anchor and duplicate aliases in results")

    eyaml_group = parser.add_argument_group(
        "EYAML options", "Left unset, the EYAML keys will default to your\
         system or user defaults.  Both keys must be set either here or in\
         your system or user EYAML configuration file when using EYAML.")
    eyaml_group.add_argument(
        "-e", "--decrypt",
        action="store_true",
        help="decrypt EYAML values in order to search their original values"
    )
    eyaml_group.add_argument(
        "-x", "--eyaml",
        default="eyaml",
        help="the eyaml binary to use when it isn't on the PATH")
    eyaml_group.add_argument("-r", "--privatekey", help="EYAML private key")
    eyaml_group.add_argument("-u", "--publickey", help="EYAML public key")

    parser.add_argument("yaml_files", metavar="YAML_FILE", nargs="+",
                        help="one or more YAML files to search")

    return parser.parse_args()

def validateargs(args, log):
    """Validate command-line arguments."""
    has_errors = False

    # Enforce sanity
    # * When set, --privatekey must be a readable file
    if args.privatekey and not (
            isfile(args.privatekey) and access(args.privatekey, R_OK)
    ):
        has_errors = True
        log.error(
            "EYAML private key is not a readable file:  " + args.privatekey
        )

    # * When set, --publickey must be a readable file
    if args.publickey and not (
            isfile(args.publickey) and access(args.publickey, R_OK)
    ):
        has_errors = True
        log.error(
            "EYAML public key is not a readable file:  " + args.publickey
        )

    # * When either --publickey or --privatekey are set, the other must also
    #   be.  This is because the `eyaml` command requires them both when
    #   decrypting values.
    if (
            (args.publickey and not args.privatekey)
            or (args.privatekey and not args.publickey)
    ):
        has_errors = True
        log.error("Both private and public EYAML keys must be set.")

    if has_errors:
        exit(1)

def search_for_paths(processor: EYAMLProcessor, data: Any, terms: SearchTerms,
                     pathsep: PathSeperators = PathSeperators.DOT,
                     build_path: str = "",
                     seen_anchors: Optional[List[str]] = None,
                     **kwargs: bool) -> Generator[YAMLPath, None, None]:
    """
    Recursively searches a data structure for nodes matching a search
    expression.  The nodes can be keys, values, and/or elements.  When dealing
    with anchors and their aliases, the caller indicates whether to include
    only the original anchor or the anchor and all of its (duplicate) aliases.
    """
    search_values: bool = kwargs.pop("search_values", True)
    search_keys: bool = kwargs.pop("search_keys", False)
    search_anchors: bool = kwargs.pop("search_anchors", False)
    include_aliases: bool = kwargs.pop("include_aliases", False)
    decrypt_eyaml: bool = kwargs.pop("decrypt_eyaml", False)
    strsep = str(pathsep)
    invert = terms.inverted
    method = terms.method
    term = terms.term

    if seen_anchors is None:
        seen_anchors = []

    if isinstance(data, CommentedSeq):
        # Build the path
        if not build_path and pathsep is PathSeperators.FSLASH:
            build_path = strsep
        build_path += "["

        for idx, ele in enumerate(data):
            # Screen out aliases if the anchor has already been seen, unless
            # the caller has asked for all the duplicate results.
            anchor_matched = False
            if hasattr(ele, "anchor") and ele.anchor.value is not None:
                # Dealing with an anchor/alias, so ref this node by name unless
                # it is to be excluded from the search results.
                anchor_name = ele.anchor.value
                if anchor_name in seen_anchors:
                    if not include_aliases:
                        # Ignore duplicate aliases
                        continue
                else:
                    # Record only original anchor names
                    seen_anchors.append(anchor_name)

                tmp_path = "{}&{}]".format(
                    build_path,
                    ensure_escaped(anchor_name, strsep),
                )

                # Search the anchor name itself, if requested
                if search_anchors:
                    matches = search_matches(method, term, anchor_name)
                    if (matches and not invert) or (invert and not matches):
                        yield YAMLPath(tmp_path)
                        anchor_matched = True
            else:
                # Not an anchor/alias, so ref this node by its index
                tmp_path = build_path + str(idx) + "]"

            if isinstance(ele, (CommentedSeq, CommentedMap)):
                # When an element is a list-of-lists/dicts, recurse into it.
                for subpath in search_for_paths(
                        processor, ele, terms, pathsep, tmp_path, seen_anchors,
                        search_values=search_values, search_keys=search_keys,
                        search_anchors=search_anchors,
                        include_aliases=include_aliases,
                        decrypt_eyaml=decrypt_eyaml
                ):
                    yield subpath
            elif search_values and not anchor_matched:
                # Otherwise, check the element for a match unless the caller
                # isn't interested in value searching.  Also ignore the value
                # if it is anchored and the anchor has already matched to avoid
                # duplication in the results.
                check_value = ele
                if decrypt_eyaml and processor.is_eyaml_value(ele):
                    check_value = processor.decrypt_eyaml(ele)

                matches = search_matches(method, term, check_value)
                if (matches and not invert) or (invert and not matches):
                    yield YAMLPath(tmp_path)

    elif isinstance(data, CommentedMap):
        if build_path:
            build_path += strsep
        elif pathsep is PathSeperators.FSLASH:
            build_path = strsep

        pool = data.non_merged_items()
        if include_aliases:
            pool = data.items()

        for key, val in pool:
            tmp_path = build_path + ensure_escaped(
                ensure_escaped(key, "\\"), strsep)
            key_matched = False

            # Search the key when the caller wishes it.
            if search_keys:
                # The key may be anchored.  Search its anchor name if the
                # caller wishes it.
                anchor_matched = False
                ignore_this_key = False
                if hasattr(key, "anchor") and key.anchor.value is not None:
                    anchor_name = key.anchor.value
                    if anchor_name in seen_anchors:
                        if not include_aliases:
                            # Ignore this duplicate anchor name
                            ignore_this_key = True
                    else:
                        # Record only original anchor names
                        seen_anchors.append(anchor_name)

                    # Search the anchor name itself, if requested
                    if search_anchors and not ignore_this_key:
                        matches = search_matches(method, term, anchor_name)
                        if ((matches and not invert)
                                or (invert and not matches)):
                            yield YAMLPath(tmp_path)
                            anchor_matched = True

                if not anchor_matched:
                    matches = search_matches(method, term, key)
                    if (matches and not invert) or (invert and not matches):
                        key_matched = True
                        yield YAMLPath(tmp_path)

            if isinstance(val, (CommentedSeq, CommentedMap)):
                # When the value is a list/dict, recurse into it.
                for subpath in search_for_paths(
                        processor, val, terms, pathsep, tmp_path, seen_anchors,
                        search_values=search_values, search_keys=search_keys,
                        search_anchors=search_anchors,
                        include_aliases=include_aliases,
                        decrypt_eyaml=decrypt_eyaml
                ):
                    yield subpath
            elif search_values and not key_matched:
                # Otherwise, search the value when the caller wishes it, but
                # not if the key has already matched (lest a duplicate result
                # be generated).  Exclude duplicate alias values unless the
                # caller wishes to receive them.
                anchor_matched = False
                if hasattr(val, "anchor") and val.anchor.value is not None:
                    anchor_name = val.anchor.value
                    if anchor_name in seen_anchors:
                        if not include_aliases:
                            # Ignore duplicate aliases
                            continue
                    else:
                        # Record only original anchor names
                        seen_anchors.append(anchor_name)

                    # Search the anchor name itself, if requested
                    if search_anchors:
                        matches = search_matches(method, term, anchor_name)
                        if ((matches and not invert)
                                or (invert and not matches)):
                            yield YAMLPath(tmp_path)
                            anchor_matched = True

                if not anchor_matched:
                    check_value = val
                    if decrypt_eyaml and processor.is_eyaml_value(val):
                        check_value = processor.decrypt_eyaml(val)

                    matches = search_matches(method, term, check_value)
                    if (matches and not invert) or (invert and not matches):
                        yield YAMLPath(tmp_path)

def main():
    """Main code."""
    # Process any command-line arguments
    args = processcli()
    log = ConsolePrinter(args)
    validateargs(args, log)
    search_values = True
    search_keys = False
    if args.onlykeynames:
        search_values = False
        search_keys = True
    elif args.keynames:
        search_keys = True

    # Prepare the YAML processor
    yaml = get_yaml_editor()
    processor = EYAMLProcessor(
        log, None, binary=args.eyaml,
        publickey=args.publickey, privatekey=args.privatekey)

    # Process the input file(s)
    in_file_count = len(args.yaml_files)
    in_expressions = len(args.search)
    exit_state = 0
    for yaml_file in args.yaml_files:
        # Try to open the file
        try:
            with open(yaml_file, 'r') as fhnd:
                yaml_data = yaml.load(fhnd)
        except ParserError as ex:
            log.error("YAML parsing error {}:  {}"
                      .format(str(ex.problem_mark).lstrip(), ex.problem))
            exit_state = 3
            continue
        except ComposerError as ex:
            log.error("YAML composition error {}:  {}"
                      .format(str(ex.problem_mark).lstrip(), ex.problem))
            exit_state = 3
            continue
        except ScannerError as ex:
            log.error("YAML syntax error {}:  {}"
                      .format(str(ex.problem_mark).lstrip(), ex.problem))
            exit_state = 3
            continue

        # Process all searches
        processor.data = yaml_data
        for expression in args.search:
            expath = YAMLPath("[*{}]".format(expression))
            for result in search_for_paths(
                    processor,
                    yaml_data,
                    expath.escaped[0][1],
                    args.pathsep,
                    search_values=search_values,
                    search_keys=search_keys,
                    search_anchors=args.anchors,
                    include_aliases=args.include_aliases,
                    decrypt_eyaml=args.decrypt):
                if in_file_count > 1:
                    if in_expressions > 1:
                        print("{}[{}]: {}".format(
                            yaml_file, expression, result))
                    else:
                        print("{}: {}".format(yaml_file, result))
                else:
                    if in_expressions > 1:
                        print("[{}]: {}".format(expression, result))
                    else:
                        print("{}".format(result))

    exit(exit_state)

if __name__ == "__main__":
    main()
