"""
Enable users to discover the YAML Path of every expression-matching term.

Returns zero or more YAML Paths indicating where in given YAML/Compatible data
a search expression matches.  Values and/or keys can be searched.  EYAML can be
employed to search encrypted values.

Copyright 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
import sys
import argparse
import json
from os import access, R_OK
from os.path import isfile
from typing import Any, Generator, List, Optional, Tuple

from ruamel.yaml.comments import CommentedSeq, CommentedMap

from yamlpath import __version__ as YAMLPATH_VERSION
from yamlpath.common import Parsers, Searches
from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import (
    AnchorMatches,
    IncludeAliases,
    PathSeperators,
    PathSearchMethods
)
from yamlpath.path import SearchTerms
from yamlpath import YAMLPath
from yamlpath.wrappers import ConsolePrinter
from yamlpath.eyaml import EYAMLProcessor

def processcli():
    """Process command-line arguments."""
    search_ops = ", ".join(PathSearchMethods.get_operators()) + ", or !"
    parser = argparse.ArgumentParser(
        description=(
            "Returns zero or more YAML Paths indicating where in given"
            " YAML/JSON/Compatible data one or more search expressions match."
            "  Values, keys, and/or anchors can be searched.  EYAML can be"
            " employed to search encrypted values."),
        epilog=(
            "A search or exception EXPRESSION takes the form of a YAML Path"
            " search operator -- {} -- followed by the search term, omitting"
            " the left-hand operand.  For more information about YAML Paths,"
            " please visit https://github.com/wwkimball/yamlpath/wiki.  To"
            " report issues with this tool or to request enhancements, please"
            " visit https://github.com/wwkimball/yamlpath/issues.")
            .format(search_ops)
    )
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s " + YAMLPATH_VERSION)

    required_group = parser.add_argument_group("required settings")
    required_group.add_argument(
        "-s", "--search",
        required=True,
        metavar="EXPRESSION", action="append",
        help="the search expression; can be set more than once")

    parser.add_argument(
        "-c", "--except",
        metavar="EXPRESSION", action="append", dest="except_expression",
        help="except results matching this search expression; can be set more\
            than once")

    parser.add_argument(
        "-m", "--expand",
        action="store_true",
        help="expand matching parent nodes to list all permissible child leaf\
              nodes (see \"reference handling options\" for restrictions)")

    valdump_group = parser.add_argument_group("result printing options")
    valdump_group.add_argument(
        "-L", "--values",
        action="store_true",
        help="print the values or elements along with each YAML Path (complex\
            results are emitted as JSON; use --expand to emit only simple\
            values)")
    valdump_group.add_argument(
        "-F", "--nofile",
        action="store_true",
        help="omit source file path and name decorators from the output\
            (applies only when searching multiple files)")
    valdump_group.add_argument(
        "-X", "--noexpression",
        action="store_true",
        help="omit search expression decorators from the output")
    valdump_group.add_argument(
        "-P", "--noyamlpath",
        action="store_true",
        help="omit YAML Paths from the output (useful with --values or to\
            indicate whether a file has any matches without printing them\
            all, perhaps especially with --noexpression)")

    parser.add_argument(
        "-t", "--pathsep",
        default="dot",
        choices=PathSeperators,
        metavar=PathSeperators.get_choices(),
        type=PathSeperators.from_str,
        help="indicate which YAML Path seperator to use when rendering\
              results; default=dot")

    keyname_group_ex = parser.add_argument_group("key name searching options")
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
        "-K", "--onlykeynames",
        action="store_true",
        help="only search key names (ignore all values and array elements)")

    parser.add_argument(
        "-a", "--refnames",
        action="store_true",
        help="also search the names of &anchor and *alias references")

    dedup_group_ex = parser.add_argument_group(
        "reference handling options",
        "Indicate how to treat anchor and alias references.  An anchor is an\
         original, reusable key or value.  All aliases become replaced by the\
         anchors they reference when YAML data is read.  These options specify\
         how to handle this duplication of keys and values.  Note that the\
         default behavior includes all aliased keys but not aliased values.")
    dedup_group = dedup_group_ex.add_mutually_exclusive_group()
    dedup_group.add_argument(
        "-A", "--anchorsonly",
        action="store_const",
        dest="include_aliases",
        const=IncludeAliases.ANCHORS_ONLY,
        help="include only original matching key and value anchors in results,\
              discarding all aliased keys and values (including child nodes)")
    dedup_group.add_argument(
        "-Y", "--allowkeyaliases",
        action="store_const",
        dest="include_aliases",
        const=IncludeAliases.INCLUDE_KEY_ALIASES,
        help="(default) include matching key aliases, permitting search\
              traversal into their child nodes")
    dedup_group.add_argument(
        "-y", "--allowvaluealiases",
        action="store_const",
        dest="include_aliases",
        const=IncludeAliases.INCLUDE_VALUE_ALIASES,
        help="include matching value aliases (does not permit search traversal\
              into aliased keys)")
    dedup_group.add_argument(
        "-l", "--allowaliases",
        action="store_const",
        dest="include_aliases",
        const=IncludeAliases.INCLUDE_ALL_ALIASES,
        help="include all matching key and value aliases")

    eyaml_group = parser.add_argument_group(
        "EYAML options", "Left unset, the EYAML keys will default to your\
         system or user defaults.  Both keys must be set either here or in\
         your system or user EYAML configuration file when using EYAML.")
    eyaml_group.add_argument(
        "-e", "--decrypt",
        action="store_true",
        help="decrypt EYAML values in order to search them (otherwise, search\
            the encrypted blob)"
    )
    eyaml_group.add_argument(
        "-x", "--eyaml",
        default="eyaml",
        help="the eyaml binary to use when it isn't on the PATH")
    eyaml_group.add_argument("-r", "--privatekey", help="EYAML private key")
    eyaml_group.add_argument("-u", "--publickey", help="EYAML public key")

    parser.add_argument(
        "-S", "--nostdin", action="store_true",
        help=(
            "Do not implicitly read from STDIN, even when there are\n"
            "no - pseudo-files in YAML_FILEs with a non-TTY session"))

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
        help="suppress all non-result output except errors")

    parser.add_argument("yaml_files", metavar="YAML_FILE", nargs="*",
                        help="one or more YAML files to search; omit or use -"
                        " to read from STDIN")

    parser.set_defaults(include_aliases=IncludeAliases.INCLUDE_KEY_ALIASES)

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
            "There must be at least one YAML_FILE or STDIN document.")

    # There can be only one -
    pseudofile_count = 0
    for infile in args.yaml_files:
        if infile.strip() == '-':
            pseudofile_count += 1
    if pseudofile_count > 1:
        has_errors = True
        log.error("Only one YAML_FILE may be the - pseudo-file.")

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
        sys.exit(1)

# pylint: disable=locally-disabled,too-many-arguments,too-many-locals,too-many-branches
def yield_children(logger: ConsolePrinter, data: Any,
                   terms: SearchTerms, pathsep: PathSeperators,
                   build_path: str, seen_anchors: List[str],
                   **kwargs: bool) -> Generator[YAMLPath, None, None]:
    """
    Dump the YAML Path of every child node beneath a given parent.

    Except for unwanted aliases, the dump is unconditional.
    """
    include_key_aliases: bool = kwargs.pop("include_key_aliases", True)
    include_value_aliases: bool = kwargs.pop("include_value_aliases", False)
    search_anchors: bool = kwargs.pop("search_anchors", False)
    logger.debug(
        "Dumping all children in data of type, {}:"
        .format(type(data)), data=data,
        prefix="yaml_paths::yield_children:  ")

    exclude_alias_matchers = [AnchorMatches.UNSEARCHABLE_ALIAS,
                              AnchorMatches.ALIAS_EXCLUDED]

    if isinstance(data, CommentedSeq):
        if not build_path and pathsep is PathSeperators.FSLASH:
            build_path = str(pathsep)
        build_path += "["

        for idx, ele in enumerate(data):
            anchor_matched = Searches.search_anchor(
                ele, terms, seen_anchors, search_anchors=search_anchors,
                include_aliases=include_value_aliases)
            logger.debug(
                ("yaml_paths::yield_children<list>:  "
                 + "element[{}] has anchor search => {}.")
                .format(idx, anchor_matched))

            # Build the temporary YAML Path using either Anchor or Index
            if anchor_matched is AnchorMatches.NO_ANCHOR:
                # Not an anchor/alias, so ref this node by its index
                tmp_path = build_path + str(idx) + "]"
            else:
                tmp_path = "{}&{}]".format(
                    build_path,
                    YAMLPath.escape_path_section(ele.anchor.value, pathsep)
                )

            if (not include_value_aliases
                    and anchor_matched in exclude_alias_matchers):
                continue

            if isinstance(ele, (CommentedMap, CommentedSeq)):
                for path in yield_children(
                        logger, ele, terms, pathsep, tmp_path, seen_anchors,
                        search_anchors=search_anchors,
                        include_key_aliases=include_key_aliases,
                        include_value_aliases=include_value_aliases):
                    yield path
            else:
                yield YAMLPath(tmp_path)

    elif isinstance(data, CommentedMap):
        if build_path:
            build_path += str(pathsep)
        elif pathsep is PathSeperators.FSLASH:
            build_path = str(pathsep)

        pool = data.non_merged_items()
        if include_key_aliases or include_value_aliases:
            pool = data.items()

        for key, val in pool:
            tmp_path = build_path + YAMLPath.escape_path_section(key, pathsep)

            key_anchor_matched = Searches.search_anchor(
                key, terms, seen_anchors, search_anchors=search_anchors,
                include_aliases=include_key_aliases)
            val_anchor_matched = Searches.search_anchor(
                val, terms, seen_anchors, search_anchors=search_anchors,
                include_aliases=include_value_aliases)
            logger.debug(
                ("yaml_paths::yield_children<dict>:  "
                 + "key[{}]:value have value anchor search => {}:{}.")
                .format(key, key_anchor_matched, val_anchor_matched))

            if (
                    (not include_key_aliases
                     and key_anchor_matched in exclude_alias_matchers)
                    or (not include_value_aliases
                        and val_anchor_matched in exclude_alias_matchers)
            ):
                continue

            if isinstance(val, (CommentedSeq, CommentedMap)):
                for path in yield_children(
                        logger, val, terms, pathsep, tmp_path, seen_anchors,
                        search_anchors=search_anchors,
                        include_key_aliases=include_key_aliases,
                        include_value_aliases=include_value_aliases):
                    yield path
            else:
                yield YAMLPath(tmp_path)

    else:
        if not build_path and pathsep is PathSeperators.FSLASH:
            build_path = str(pathsep)
        yield YAMLPath(build_path)

# pylint: disable=locally-disabled,too-many-arguments,too-many-locals,too-many-branches,too-many-statements
def search_for_paths(logger: ConsolePrinter, processor: EYAMLProcessor,
                     data: Any, terms: SearchTerms,
                     pathsep: PathSeperators = PathSeperators.DOT,
                     build_path: str = "",
                     seen_anchors: Optional[List[str]] = None,
                     **kwargs: bool) -> Generator[YAMLPath, None, None]:
    """
    Recursively search a data structure for nodes matching an expression.

    The nodes can be keys, values, and/or elements.  When dealing with anchors
    and their aliases, the caller indicates whether to include only the
    original anchor or the anchor and all of its (duplicate) aliases.
    """
    search_values: bool = kwargs.pop("search_values", True)
    search_keys: bool = kwargs.pop("search_keys", False)
    search_anchors: bool = kwargs.pop("search_anchors", False)
    include_key_aliases: bool = kwargs.pop("include_key_aliases", True)
    include_value_aliases: bool = kwargs.pop("include_value_aliases", False)
    decrypt_eyaml: bool = kwargs.pop("decrypt_eyaml", False)
    expand_children: bool = kwargs.pop("expand_children", False)
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
            # Any element may or may not have an Anchor/Alias
            anchor_matched = Searches.search_anchor(
                ele, terms, seen_anchors, search_anchors=search_anchors,
                include_aliases=include_value_aliases)
            logger.debug(
                ("yaml_paths::search_for_paths<list>:"
                 + "anchor search => {}.")
                .format(anchor_matched)
            )

            # Build the temporary YAML Path using either Anchor or Index
            if anchor_matched is AnchorMatches.NO_ANCHOR:
                # Not an anchor/alias, so ref this node by its index
                tmp_path = build_path + str(idx) + "]"
            else:
                tmp_path = "{}&{}]".format(
                    build_path,
                    YAMLPath.escape_path_section(ele.anchor.value, pathsep)
                )

            if anchor_matched is AnchorMatches.ALIAS_EXCLUDED:
                continue

            if anchor_matched in [AnchorMatches.MATCH,
                                  AnchorMatches.ALIAS_INCLUDED]:
                logger.debug(
                    ("yaml_paths::search_for_paths<list>:"
                     + "yielding an Anchor/Alias match, {}.")
                    .format(tmp_path)
                )
                if expand_children:
                    for path in yield_children(
                            logger, ele, terms, pathsep, tmp_path,
                            seen_anchors, search_anchors=search_anchors,
                            include_key_aliases=include_key_aliases,
                            include_value_aliases=include_value_aliases):
                        yield path
                else:
                    yield YAMLPath(tmp_path)
                continue

            if isinstance(ele, (CommentedSeq, CommentedMap)):
                logger.debug(
                    "Recursing into complex data:", data=ele,
                    prefix="yaml_paths::search_for_paths<list>:  ",
                    footer=">>>> >>>> >>>> >>>> >>>> >>>> >>>>")
                for subpath in search_for_paths(
                        logger, processor, ele, terms, pathsep, tmp_path,
                        seen_anchors, search_values=search_values,
                        search_keys=search_keys, search_anchors=search_anchors,
                        include_key_aliases=include_key_aliases,
                        include_value_aliases=include_value_aliases,
                        decrypt_eyaml=decrypt_eyaml,
                        expand_children=expand_children
                ):
                    logger.debug(
                        "Yielding RECURSED match, {}.".format(subpath),
                        prefix="yaml_paths::search_for_paths<list>:  ",
                        footer="<<<< <<<< <<<< <<<< <<<< <<<< <<<<"
                    )
                    yield subpath
            elif search_values:
                if (anchor_matched is AnchorMatches.UNSEARCHABLE_ALIAS
                        and not include_value_aliases):
                    continue

                check_value = ele
                if decrypt_eyaml and processor.is_eyaml_value(ele):
                    check_value = processor.decrypt_eyaml(ele)

                matches = Searches.search_matches(method, term, check_value)
                if (matches and not invert) or (invert and not matches):
                    logger.debug(
                        ("yaml_paths::search_for_paths<list>:"
                         + "yielding VALUE match, {}:  {}."
                        ).format(check_value, tmp_path)
                    )
                    yield YAMLPath(tmp_path)

    # pylint: disable=too-many-nested-blocks
    elif isinstance(data, CommentedMap):
        if build_path:
            build_path += strsep
        elif pathsep is PathSeperators.FSLASH:
            build_path = strsep

        pool = data.non_merged_items()
        if include_key_aliases or include_value_aliases:
            pool = data.items()

        for key, val in pool:
            tmp_path = build_path + YAMLPath.escape_path_section(key, pathsep)

            # Search the value anchor to have it on record, in case the key
            # anchor match would otherwise block the value anchor from
            # appearing in seen_anchors (which is important).
            val_anchor_matched = Searches.search_anchor(
                val, terms, seen_anchors, search_anchors=search_anchors,
                include_aliases=include_value_aliases)
            logger.debug(
                ("yaml_paths::search_for_paths<dict>:"
                 + "VALUE anchor search => {}.")
                .format(val_anchor_matched)
            )

            # Search the key when the caller wishes it.
            if search_keys:
                # The key itself may be an Anchor or Alias.  Search it when the
                # caller wishes.
                key_anchor_matched = Searches.search_anchor(
                    key, terms, seen_anchors, search_anchors=search_anchors,
                    include_aliases=include_key_aliases)
                logger.debug(
                    ("yaml_paths::search_for_paths<dict>:"
                     + "KEY anchor search, {}:  {}.")
                    .format(key, key_anchor_matched)
                )

                if key_anchor_matched in [AnchorMatches.MATCH,
                                          AnchorMatches.ALIAS_INCLUDED]:
                    logger.debug(
                        ("yaml_paths::search_for_paths<dict>:"
                         + "yielding a KEY-ANCHOR match, {}."
                        ).format(key, tmp_path)
                    )
                    if expand_children:
                        for path in yield_children(
                                logger, val, terms, pathsep, tmp_path,
                                seen_anchors, search_anchors=search_anchors,
                                include_key_aliases=include_key_aliases,
                                include_value_aliases=include_value_aliases):
                            yield path
                    else:
                        yield YAMLPath(tmp_path)
                    continue

                # Search the name of the key, itself
                matches = Searches.search_matches(method, term, key)
                if (matches and not invert) or (invert and not matches):
                    logger.debug(
                        ("yaml_paths::search_for_paths<dict>:"
                         + "yielding KEY name match, {}:  {}."
                        ).format(key, tmp_path)
                    )
                    if expand_children:
                        # Include every non-excluded child node under this
                        # matched parent node.
                        for path in yield_children(
                                logger, val, terms, pathsep, tmp_path,
                                seen_anchors, search_anchors=search_anchors,
                                include_key_aliases=include_key_aliases,
                                include_value_aliases=include_value_aliases):
                            yield path
                    else:
                        # No other matches within this node matter because they
                        # are already in the result.
                        yield YAMLPath(tmp_path)
                    continue

            # The value may itself be anchored; search it if requested
            if val_anchor_matched is AnchorMatches.ALIAS_EXCLUDED:
                continue

            if val_anchor_matched in [AnchorMatches.MATCH,
                                      AnchorMatches.ALIAS_INCLUDED]:
                logger.debug(
                    ("yaml_paths::search_for_paths<dict>:"
                     + "yielding a VALUE-ANCHOR match, {}.")
                    .format(tmp_path)
                )
                if expand_children:
                    for path in yield_children(
                            logger, val, terms, pathsep, tmp_path,
                            seen_anchors, search_anchors=search_anchors,
                            include_key_aliases=include_key_aliases,
                            include_value_aliases=include_value_aliases):
                        yield path
                else:
                    yield YAMLPath(tmp_path)
                continue

            if isinstance(val, (CommentedSeq, CommentedMap)):
                logger.debug(
                    "Recursing into complex data:", data=val,
                    prefix="yaml_paths::search_for_paths<dict>:  ",
                    footer=">>>> >>>> >>>> >>>> >>>> >>>> >>>>"
                )
                for subpath in search_for_paths(
                        logger, processor, val, terms, pathsep, tmp_path,
                        seen_anchors, search_values=search_values,
                        search_keys=search_keys, search_anchors=search_anchors,
                        include_key_aliases=include_key_aliases,
                        include_value_aliases=include_value_aliases,
                        decrypt_eyaml=decrypt_eyaml,
                        expand_children=expand_children
                ):
                    logger.debug(
                        "Yielding RECURSED match, {}.".format(subpath),
                        prefix="yaml_paths::search_for_paths<dict>:  ",
                        footer="<<<< <<<< <<<< <<<< <<<< <<<< <<<<"
                    )
                    yield subpath
            elif search_values:
                if (val_anchor_matched is AnchorMatches.UNSEARCHABLE_ALIAS
                        and not include_value_aliases):
                    continue

                check_value = val
                if decrypt_eyaml and processor.is_eyaml_value(val):
                    check_value = processor.decrypt_eyaml(val)

                matches = Searches.search_matches(method, term, check_value)
                if (matches and not invert) or (invert and not matches):
                    logger.debug(
                        ("yaml_paths::search_for_paths<dict>:"
                         + "yielding VALUE match, {}:  {}."
                        ).format(check_value, tmp_path)
                    )
                    yield YAMLPath(tmp_path)

def get_search_term(logger: ConsolePrinter,
                    expression: str) -> Optional[SearchTerms]:
    """
    Attempt to cast a search expression into a SearchTerms instance.

    Will log an error and return None on failure.
    """
    # The leading character must be a known search operator
    check_operator = expression[0] if expression else ""
    if not (PathSearchMethods.is_operator(check_operator)
            or check_operator == '!'):
        logger.error(
            ("Invalid search expression, '{}'.  The first symbol of"
             + " every search expression must be one of:  {}")
            .format(expression,
                    ", ".join(PathSearchMethods.get_operators())))
        return None

    if not len(expression) > 1:
        # Empty expressions do nothing
        logger.error(
            "An EXPRESSION with only a search operator has no effect, '{}'."
            .format(expression))
        return None

    try:
        exterm = Searches.create_searchterms_from_pathattributes(
            YAMLPath("[*{}]".format(expression)).escaped[0][1]
        )
    except YAMLPathException as ex:
        logger.error(
            ("Invalid search expression, '{}', due to:  {}")
            .format(expression, ex)
        )
        return None

    return exterm

def print_results(
    args: Any, processor: EYAMLProcessor, yaml_file: str,
    yaml_paths: List[Tuple[str, YAMLPath]], document_index: int
) -> None:
    """Dump search results to STDOUT with optional and dynamic formatting."""
    in_expressions = len(args.search)
    print_file_path = not args.nofile
    print_expression = in_expressions > 1 and not args.noexpression
    print_yaml_path = not args.noyamlpath
    print_value = args.values
    buffers = [
        ": " if print_file_path or print_expression and (
            print_yaml_path or print_value
            ) else "",
        ": " if print_yaml_path and print_value else "",
    ]
    for entry in yaml_paths:
        expression, result = entry
        resline = ""

        if print_file_path:
            display_file_name = ("STDIN"
                                 if yaml_file.strip() == "-"
                                 else yaml_file)
            resline += "{}/{}".format(display_file_name, document_index)

        if print_expression:
            resline += "[{}]".format(expression)

        resline += buffers[0]
        if print_yaml_path:
            resline += "{}".format(result)

        resline += buffers[1]
        if print_value:
            # These results can have only one match, but make sure lest the
            # output become messy.
            for node_coordinate in processor.get_nodes(result, mustexist=True):
                node = node_coordinate.node
                if isinstance(node, (dict, list)):
                    resline += "{}".format(
                        json.dumps(Parsers.jsonify_yaml_data(node)))
                else:
                    resline += "{}".format(str(node).replace("\n", r"\n"))
                break

        print(resline)

def process_yaml_file(
    args, yaml, log, yaml_file, processor, search_values, search_keys,
    include_key_aliases, include_value_aliases, file_tally = 0
):
    """Process a (potentially multi-doc) YAML file."""
    # Try to open the file
    exit_state = 0
    subdoc_index = -1

    # pylint: disable=too-many-nested-blocks
    for (yaml_data, doc_loaded) in Parsers.get_yaml_multidoc_data(
        yaml, log, yaml_file
    ):
        file_tally += 1
        subdoc_index += 1
        if not doc_loaded:
            # An error message has already been logged
            exit_state = 3
            continue

        # Process all searches
        processor.data = yaml_data
        yaml_paths = []
        for expression in args.search:
            exterm = get_search_term(log, expression)
            log.debug(("yaml_paths::process_yaml_file:"
                    + "converting search expression '{}' into '{}'"
                    ).format(expression, exterm))
            if exterm is None:
                exit_state = 1
                continue

            for result in search_for_paths(
                    log, processor, yaml_data, exterm, args.pathsep,
                    search_values=search_values, search_keys=search_keys,
                    search_anchors=args.refnames,
                    include_key_aliases=include_key_aliases,
                    include_value_aliases=include_value_aliases,
                    decrypt_eyaml=args.decrypt,
                    expand_children=args.expand):
                # Record only unique results
                add_entry = True
                for entry in yaml_paths:
                    if str(result) == str(entry[1]):
                        add_entry = False
                        break
                if add_entry:
                    yaml_paths.append((expression, result))

        if not yaml_paths:
            # Nothing further to do when there are no results
            continue

        if args.except_expression:
            for expression in args.except_expression:
                exterm = get_search_term(log, expression)
                log.debug(("yaml_paths::process_yaml_file:"
                        + "converted except expression '{}' into '{}'"
                        ).format(expression, exterm))
                if exterm is None:
                    exit_state = 1
                    continue

                for result in search_for_paths(
                        log, processor, yaml_data, exterm, args.pathsep,
                        search_values=search_values,
                        search_keys=search_keys,
                        search_anchors=args.refnames,
                        include_key_aliases=include_key_aliases,
                        include_value_aliases=include_value_aliases,
                        decrypt_eyaml=args.decrypt,
                        expand_children=args.expand):
                    for entry in yaml_paths:
                        if str(result) == str(entry[1]):
                            yaml_paths.remove(entry)
                            break  # Entries are already unique

        print_results(
            args, processor, yaml_file, yaml_paths, subdoc_index)

    return exit_state

def main():
    """Main code."""
    # Process any command-line arguments
    args = processcli()
    log = ConsolePrinter(args)
    validateargs(args, log)
    search_values = True
    search_keys = False
    include_key_aliases = False
    include_value_aliases = False

    if args.onlykeynames:
        search_values = False
        search_keys = True
    elif args.keynames:
        search_keys = True

    if args.include_aliases is IncludeAliases.INCLUDE_ALL_ALIASES:
        include_key_aliases = True
        include_value_aliases = True
    elif args.include_aliases is IncludeAliases.INCLUDE_KEY_ALIASES:
        include_key_aliases = True
    elif args.include_aliases is IncludeAliases.INCLUDE_VALUE_ALIASES:
        include_value_aliases = True

    # Prepare the YAML processor
    yaml = Parsers.get_yaml_editor()
    processor = EYAMLProcessor(
        log, None, binary=args.eyaml,
        publickey=args.publickey, privatekey=args.privatekey)

    # Process the input file(s)
    exit_state = 0
    file_tally = -1
    consumed_stdin = False

    for yaml_file in args.yaml_files:
        file_tally += 1
        if yaml_file.strip() == "-":
            consumed_stdin = True

        log.debug(
            "yaml_merge::main:  Processing file, {}".format(
                "STDIN" if yaml_file.strip() == "-" else yaml_file))

        proc_state = process_yaml_file(
            args, yaml, log, yaml_file, processor, search_values, search_keys,
            include_key_aliases, include_value_aliases, file_tally
        )

        if proc_state != 0:
            exit_state = proc_state

    # Check for a waiting STDIN document
    if (exit_state == 0
        and not consumed_stdin
        and not args.nostdin
        and not sys.stdin.isatty()
    ):
        file_tally += 1
        exit_state = process_yaml_file(
            args, yaml, log, "-", processor, search_values, search_keys,
            include_key_aliases, include_value_aliases, file_tally
        )

    sys.exit(exit_state)

if __name__ == "__main__":
    main()  # pragma: no cover
