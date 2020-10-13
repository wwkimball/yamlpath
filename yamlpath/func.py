"""
Collection of general helper functions.

Copyright 2018, 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
import warnings
import ast
import re
from sys import maxsize, stdin
from distutils.util import strtobool
from typing import Any, Generator, List, Optional

from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError
from ruamel.yaml.composer import ComposerError, ReusedAnchorWarning
from ruamel.yaml.constructor import ConstructorError, DuplicateKeyError
from ruamel.yaml.scanner import ScannerError
from ruamel.yaml.comments import CommentedSeq, CommentedMap
from ruamel.yaml.scalarstring import (
    PlainScalarString,
    DoubleQuotedScalarString,
    SingleQuotedScalarString,
    FoldedScalarString,
    LiteralScalarString,
)
from ruamel.yaml.scalarbool import ScalarBoolean
from ruamel.yaml.scalarfloat import ScalarFloat
from ruamel.yaml.scalarint import ScalarInt

from yamlpath.enums import (
    AnchorMatches,
    PathSearchMethods,
    PathSegmentTypes,
    PathSeperators,
    YAMLValueFormats,
)
from yamlpath.wrappers import ConsolePrinter, NodeCoords
from yamlpath.types import PathAttributes
from yamlpath.path import SearchTerms
from yamlpath import YAMLPath

def get_yaml_editor(**kwargs: Any) -> Any:
    """
    Build and return a generic YAML editor based on ruamel.yaml.

    Parameters:  N/A

    Keyword Arguments:
    * explicit_start (bool) True = ensure the YAML Start-of-Document marker
      (---<EOL>) is written in the output; False = remove it; default=True
    * explode_aliases (bool) True = convert all aliases (*name) and YAML merge
      operators (<<: *name) to their referenced content, removing the aliases
      and merge operators; False = maintain the references; default=False
    * preserve_quotes (bool) True = retain any and all quoting of keys and
      values including whatever demarcation symbol was used (" versus ');
      False = only quote values when necessary, removing unnecessary
      demarcation; default=True

    Returns (Any) The ready-for-use YAML editor.

    Raises:  N/A
    """
    explicit_start = kwargs.pop("explicit_start", True)
    explode_aliases = kwargs.pop("explode_aliases", False)
    preserve_quotes = kwargs.pop("preserve_quotes", True)

    # The ruamel.yaml class appears to be missing some typing data, so these
    # valid assignments cannot be type-checked.
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.explicit_start = explicit_start       # type: ignore
    yaml.preserve_quotes = preserve_quotes     # type: ignore
    yaml.width = maxsize                       # type: ignore

    if explode_aliases:
        yaml.default_flow_style = False

    return yaml

# pylint: disable=locally-disabled,too-many-branches,too-many-statements
def get_yaml_data(parser: Any, logger: ConsolePrinter, source: str) -> Any:
    """
    Parse YAML/Compatible data and return the ruamel.yaml object result.

    All known issues are caught and distinctively logged.  Returns None when
    the data could not be loaded.
    """
    yaml_data = None

    # This code traps errors and warnings from ruamel.yaml, substituting
    # lengthy stack-dumps with specific, meaningful feedback.  Further, some
    # warnings are treated as errors by ruamel.yaml, so these are also
    # coallesced into cleaner feedback.
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("error")
            if source == "-":
                yaml_data = parser.load(stdin.read())
            else:
                with open(source, 'r') as fhnd:
                    yaml_data = parser.load(fhnd)
    except KeyboardInterrupt:
        logger.error("Aborting data load due to keyboard interrupt!")
        yaml_data = False
    except FileNotFoundError:
        logger.error("File not found:  {}".format(source))
        yaml_data = False
    except ParserError as ex:
        logger.error("YAML parsing error {}:  {}"
                     .format(str(ex.problem_mark).lstrip(), ex.problem))
        yaml_data = False
    except ComposerError as ex:
        logger.error("YAML composition error {}:  {}"
                     .format(str(ex.problem_mark).lstrip(), ex.problem))
        yaml_data = False
    except ConstructorError as ex:
        logger.error("YAML construction error {}:  {}"
                     .format(str(ex.problem_mark).lstrip(), ex.problem))
        yaml_data = False
    except ScannerError as ex:
        logger.error("YAML syntax error {}:  {}"
                     .format(str(ex.problem_mark).lstrip(), ex.problem))
        yaml_data = False
    except DuplicateKeyError as dke:
        omits = [
            "while constructing", "To suppress this", "readthedocs",
            "future releases", "the new API",
        ]
        message = str(dke).split("\n")
        newmsg = ""
        for line in message:
            line = line.strip()
            if not line:
                continue
            write_line = True
            for omit in omits:
                if omit in line:
                    write_line = False
                    break
            if write_line:
                newmsg += "\n   " + line
        logger.error("Duplicate Hash key detected:  {}"
                     .format(newmsg))
        yaml_data = False
    except ReusedAnchorWarning as raw:
        logger.error("Duplicate YAML Anchor detected:  {}"
                     .format(
                         str(raw)
                         .replace("occurrence   ", "occurrence ")
                         .replace("\n", "\n   ")))
        yaml_data = False

    return yaml_data

# pylint: disable=locally-disabled,too-many-branches,too-many-statements,too-many-locals
def get_yaml_multidoc_data(
    parser: Any, logger: ConsolePrinter, source: str
) -> Generator[Any, None, None]:
    """
    Parse YAML/Compatible multi-docs and yield the ruamel.yaml object results.

    All known issues are caught and distinctively logged.  Nothing is generated
    when there is an error.

    Parameters:
    1. parser (ruamel.yaml.YAML) The YAML data parser
    2. logger (ConsolePrinter) The logging facility
    3. source (str) The source file to load; can be - for reading from STDIN
    """
    # This code traps errors and warnings from ruamel.yaml, substituting
    # lengthy stack-dumps with specific, meaningful feedback.  Further, some
    # warnings are treated as errors by ruamel.yaml, so these are also
    # coallesced into cleaner feedback.
    has_error = False
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("error")
            if source == "-":
                for document in parser.load_all(stdin.read()):
                    logger.debug(
                        "Yielding document from {}:".format(source),
                        prefix="get_yaml_multidoc_data: ", data=document)
                    yield document
            else:
                with open(source, 'r') as fhnd:
                    for document in parser.load_all(fhnd):
                        logger.debug(
                            "Yielding document from {}:".format(source),
                            prefix="get_yaml_multidoc_data: ", data=document)
                        yield document
    except KeyboardInterrupt:
        has_error = True
        logger.error("Aborting data load due to keyboard interrupt!")
    except FileNotFoundError:
        has_error = True
        logger.error("File not found:  {}".format(source))
    except ParserError as ex:
        has_error = True
        logger.error("YAML parsing error {}:  {}"
                     .format(str(ex.problem_mark).lstrip(), ex.problem))
    except ComposerError as ex:
        has_error = True
        logger.error("YAML composition error {}:  {}"
                    .format(str(ex.problem_mark).lstrip(), ex.problem))
    except ConstructorError as ex:
        has_error = True
        logger.error("YAML construction error {}:  {}"
                     .format(str(ex.problem_mark).lstrip(), ex.problem))
    except ScannerError as ex:
        has_error = True
        logger.error("YAML syntax error {}:  {}"
                     .format(str(ex.problem_mark).lstrip(), ex.problem))
    except DuplicateKeyError as dke:
        has_error = True
        omits = [
            "while constructing", "To suppress this", "readthedocs",
            "future releases", "the new API",
        ]
        message = str(dke).split("\n")
        newmsg = ""
        for line in message:
            line = line.strip()
            if not line:
                continue
            write_line = True
            for omit in omits:
                if omit in line:
                    write_line = False
                    break
            if write_line:
                newmsg += "\n   " + line
        logger.error("Duplicate Hash key detected:  {}"
                     .format(newmsg))
    except ReusedAnchorWarning as raw:
        has_error = True
        logger.error("Duplicate YAML Anchor detected:  {}"
                     .format(
                         str(raw)
                         .replace("occurrence   ", "occurrence ")
                         .replace("\n", "\n   ")))

    if has_error:
        yield False

def build_next_node(yaml_path: YAMLPath, depth: int,
                    value: Any = None) -> Any:
    """
    Get the best default value for the next entry in a YAML Path.

    Parameters:
    1. yaml_path (deque) The pre-parsed YAML Path to follow
    2. depth (int) Index of the YAML Path segment to evaluate
    3. value (Any) The expected value for the final YAML Path entry

    Returns:  (Any) The most appropriate default value

    Raises:  N/A
    """
    default_value = wrap_type(value)
    segments = yaml_path.escaped
    if not (segments and len(segments) > depth):
        return default_value

    typ = segments[depth][0]
    if typ == PathSegmentTypes.INDEX:
        default_value = CommentedSeq()
    elif typ == PathSegmentTypes.KEY:
        default_value = CommentedMap()

    return default_value

def append_list_element(data: Any, value: Any = None,
                        anchor: str = None) -> Any:
    """
    Append a new element to an ruamel.yaml List.

    This method preserves any tailing comment for the former last element of
    the same list.

    Parameters:
    1. data (Any) The parsed YAML data to process
    2. value (Any) The value of the element to append
    3. anchor (str) An Anchor or Alias name for the new element

    Returns:  (Any) The newly appended element node

    Raises:  N/A
    """
    if anchor is not None and value is not None:
        value = wrap_type(value)
        if not hasattr(value, "anchor"):
            raise ValueError(
                "Impossible to add an Anchor to value:  {}".format(value)
            )
        value.yaml_set_anchor(anchor)

    old_tail_pos = len(data) - 1
    data.append(value)
    new_element = data[-1]

    # Note that ruamel.yaml will inexplicably add a newline before the tail
    # element irrespective of this ca handling.  This issue appears to be
    # uncontrollable, from here.
    if hasattr(data, "ca") and old_tail_pos in data.ca.items:
        old_comment = data.ca.items[old_tail_pos][0]
        if old_comment is not None:
            data.ca.items[old_tail_pos][0] = None
            data.ca.items[old_tail_pos + 1] = [
                old_comment, None, None, None
            ]

    return new_element

def wrap_type(value: Any) -> Any:
    """
    Wrap a value in one of the ruamel.yaml wrapper types.

    Parameters:
    1. value (Any) The value to wrap.

    Returns: (Any) The wrapped value or the original value when a better
        wrapper could not be identified.

    Raises:  N/A
    """
    wrapped_value = value

    try:
        ast_value = ast.literal_eval(value)
    except ValueError:
        ast_value = value
    except SyntaxError:
        ast_value = value

    typ = type(ast_value)
    if typ is list:
        wrapped_value = CommentedSeq(value)
    elif typ is dict:
        wrapped_value = CommentedMap(value)
    elif typ is str:
        wrapped_value = PlainScalarString(value)
    elif typ is int:
        wrapped_value = ScalarInt(value)
    elif typ is float:
        wrapped_value = make_float_node(ast_value)
    elif typ is bool:
        wrapped_value = ScalarBoolean(bool(value))

    return wrapped_value

def clone_node(node: Any) -> Any:
    """
    Duplicate a YAML Data node.

    This is necessary because otherwise, Python would treat any copies of a
    value as references to each other such that changes to one automatically
    affect all copies.  This is not desired when an original value must be
    duplicated elsewhere in the data and then the original changed without
    impacting the copy.

    Parameters:
    1. node (Any) The node to clone.

    Returns: (Any) Clone of the given node

    Raises:  N/A
    """
    # Clone str values lest the new node change whenever the original node
    # changes, which defeates the intention of preserving the present,
    # pre-change value to an entirely new node.
    clone_value = node
    if isinstance(clone_value, str):
        clone_value = ''.join(node)

    if hasattr(node, "anchor"):
        return type(node)(clone_value, anchor=node.anchor.value)
    return type(node)(clone_value)

def make_float_node(value: float, anchor: str = None):
    """
    Create a new ScalarFloat data node from a bare float.

    An optional anchor may be attached.

    Parameters:
    1. value (float) The bare float to wrap.
    2. anchor (str) OPTIONAL anchor to add.

    Returns: (ScalarNode) The new node
    """
    minus_sign = "-" if value < 0.0 else None
    strval = format(value, '.15f').rstrip('0').rstrip('.')
    precision = 0
    width = len(strval)
    lastdot = strval.rfind(".")
    if -1 < lastdot:
        precision = strval.rfind(".")

    if anchor is None:
        new_node = ScalarFloat(
            value,
            m_sign=minus_sign,
            prec=precision,
            width=width
        )
    else:
        new_node = ScalarFloat(
            value
            , anchor=anchor
            , m_sign=minus_sign
            , prec=precision
            , width=width
        )

    return new_node

# pylint: disable=locally-disabled,too-many-branches,too-many-statements,too-many-locals
def make_new_node(source_node: Any, value: Any,
                  value_format: YAMLValueFormats) -> Any:
    """
    Create a new data node based on a sample node.

    This is achieved by effectively duplicaing the type and anchor of the node
    but giving it a different value.

    Parameters:
    1. source_node (Any) The node from which to copy type
    2. value (Any) The value to assign to the new node
    3. value_format (YAMLValueFormats) The YAML presentation format to
       apply to value when it is dumped

    Returns: (Any) The new node

    Raises:
    - `NameError` when value_format is invalid
    - `ValueError' when the new value is not numeric and value_format
       requires it to be so
    """
    new_node = None
    new_type = type(source_node)
    new_value = value
    valform = YAMLValueFormats.DEFAULT

    if isinstance(value_format, YAMLValueFormats):
        valform = value_format
    else:
        strform = str(value_format)
        try:
            valform = YAMLValueFormats.from_str(strform)
        except NameError as wrap_ex:
            raise NameError(
                "Unknown YAML Value Format:  {}".format(strform)
                + ".  Please specify one of:  "
                + ", ".join(
                    [l.lower() for l in YAMLValueFormats.get_names()]
                )
            ) from wrap_ex

    if valform == YAMLValueFormats.BARE:
        new_type = PlainScalarString
        new_value = str(value)
    elif valform == YAMLValueFormats.DQUOTE:
        new_type = DoubleQuotedScalarString
        new_value = str(value)
    elif valform == YAMLValueFormats.SQUOTE:
        new_type = SingleQuotedScalarString
        new_value = str(value)
    elif valform == YAMLValueFormats.FOLDED:
        new_type = FoldedScalarString
        new_value = str(value)
    elif valform == YAMLValueFormats.LITERAL:
        new_type = LiteralScalarString
        new_value = str(value)
    elif valform == YAMLValueFormats.BOOLEAN:
        new_type = ScalarBoolean
        if isinstance(value, bool):
            new_value = value
        else:
            new_value = strtobool(value)
    elif valform == YAMLValueFormats.FLOAT:
        try:
            new_value = float(value)
        except ValueError as wrap_ex:
            raise ValueError(
                ("The requested value format is {}, but '{}' cannot be"
                 + " cast to a floating-point number.")
                .format(valform, value)
            ) from wrap_ex

        anchor_val = None
        if hasattr(source_node, "anchor"):
            anchor_val = source_node.anchor.value
        new_node = make_float_node(new_value, anchor_val)
    elif valform == YAMLValueFormats.INT:
        new_type = ScalarInt

        try:
            new_value = int(value)
        except ValueError as wrap_ex:
            raise ValueError(
                ("The requested value format is {}, but '{}' cannot be"
                 + " cast to an integer number.")
                .format(valform, value)
            ) from wrap_ex
    else:
        # Punt to whatever the best type may be
        wrapped_value = wrap_type(value)
        new_type = type(wrapped_value)
        new_format = YAMLValueFormats.from_node(wrapped_value)
        if new_format is not YAMLValueFormats.DEFAULT:
            new_node = make_new_node(source_node, value, new_format)

    if new_node is None:
        if hasattr(source_node, "anchor"):
            new_node = new_type(new_value, anchor=source_node.anchor.value)
        else:
            new_node = new_type(new_value)

    return new_node

def get_node_anchor(node: Any) -> Optional[str]:
    """Return a node's Anchor/Alias name or None wheh there isn't one."""
    if (
            not hasattr(node, "anchor")
            or node.anchor is None
            or node.anchor.value is None
            or not node.anchor.value
    ):
        return None
    return str(node.anchor.value)

def search_matches(method: PathSearchMethods, needle: str,
                   haystack: Any) -> bool:
    """Perform a search."""
    matches: bool = False

    if method is PathSearchMethods.EQUALS:
        if isinstance(haystack, int):
            try:
                matches = haystack == int(needle)
            except ValueError:
                matches = False
        elif isinstance(haystack, float):
            try:
                matches = haystack == float(needle)
            except ValueError:
                matches = False
        else:
            matches = haystack == needle
    elif method is PathSearchMethods.STARTS_WITH:
        matches = str(haystack).startswith(needle)
    elif method is PathSearchMethods.ENDS_WITH:
        matches = str(haystack).endswith(needle)
    elif method is PathSearchMethods.CONTAINS:
        matches = needle in str(haystack)
    elif method is PathSearchMethods.GREATER_THAN:
        if isinstance(haystack, int):
            try:
                matches = haystack > int(needle)
            except ValueError:
                matches = False
        elif isinstance(haystack, float):
            try:
                matches = haystack > float(needle)
            except ValueError:
                matches = False
        else:
            matches = haystack > needle
    elif method is PathSearchMethods.LESS_THAN:
        if isinstance(haystack, int):
            try:
                matches = haystack < int(needle)
            except ValueError:
                matches = False
        elif isinstance(haystack, float):
            try:
                matches = haystack < float(needle)
            except ValueError:
                matches = False
        else:
            matches = haystack < needle
    elif method is PathSearchMethods.GREATER_THAN_OR_EQUAL:
        if isinstance(haystack, int):
            try:
                matches = haystack >= int(needle)
            except ValueError:
                matches = False
        elif isinstance(haystack, float):
            try:
                matches = haystack >= float(needle)
            except ValueError:
                matches = False
        else:
            matches = haystack >= needle
    elif method is PathSearchMethods.LESS_THAN_OR_EQUAL:
        if isinstance(haystack, int):
            try:
                matches = haystack <= int(needle)
            except ValueError:
                matches = False
        elif isinstance(haystack, float):
            try:
                matches = haystack <= float(needle)
            except ValueError:
                matches = False
        else:
            matches = haystack <= needle
    elif method == PathSearchMethods.REGEX:
        matcher = re.compile(needle)
        matches = matcher.search(str(haystack)) is not None
    else:
        raise NotImplementedError

    return matches

def search_anchor(node: Any, terms: SearchTerms, seen_anchors: List[str],
                  **kwargs: bool) -> AnchorMatches:
    """Indicate whether a node has an Anchor matching given search terms."""
    anchor_name = get_node_anchor(node)
    if anchor_name is None:
        return AnchorMatches.NO_ANCHOR

    is_alias = True
    if anchor_name not in seen_anchors:
        is_alias = False
        seen_anchors.append(anchor_name)

    search_anchors: bool = kwargs.pop("search_anchors", False)
    if not search_anchors:
        retval = AnchorMatches.UNSEARCHABLE_ANCHOR
        if is_alias:
            retval = AnchorMatches.UNSEARCHABLE_ALIAS
        return retval

    include_aliases: bool = kwargs.pop("include_aliases", False)
    if is_alias and not include_aliases:
        return AnchorMatches.ALIAS_EXCLUDED

    retval = AnchorMatches.NO_MATCH
    matches = search_matches(terms.method, terms.term, anchor_name)
    if (matches and not terms.inverted) or (terms.inverted and not matches):
        retval = AnchorMatches.MATCH
        if is_alias:
            retval = AnchorMatches.ALIAS_INCLUDED
    return retval

def ensure_escaped(value: str, *symbols: str) -> str:
    r"""
    Escape all instances of a symbol within a value.

    Ensures all instances of a symbol are escaped (via \) within a value.
    Multiple symbols can be processed at once.
    """
    escaped: str = value
    for symbol in symbols:
        replace_term: str = "\\{}".format(symbol)
        oparts: List[str] = str(escaped).split(replace_term)
        eparts: List[str] = []
        for opart in oparts:
            eparts.append(opart.replace(symbol, replace_term))
        escaped = replace_term.join(eparts)
    return escaped

def escape_path_section(section: str, pathsep: PathSeperators) -> str:
    """
    Escape all special symbols present within a YAML Path segment.

    Renders inert via escaping all symbols within a string which have special
    meaning to YAML Path.  The resulting string can be consumed as a YAML Path
    section without triggering unwanted additional processing.
    """
    return ensure_escaped(
        section,
        '\\', str(pathsep), '(', ')', '[', ']', '^', '$', '%', ' ', "'", '"'
    )

def create_searchterms_from_pathattributes(
        rhs: PathAttributes) -> SearchTerms:
    """Convert a PathAttributes instance to a SearchTerms instance."""
    if isinstance(rhs, SearchTerms):
        newinst: SearchTerms = SearchTerms(
            rhs.inverted, rhs.method, rhs.attribute, rhs.term
        )
        return newinst
    raise AttributeError

def unwrap_node_coords(data: Any) -> Any:
    """Recursively strips all DOM tracking data off of a NodeCoords wrapper."""
    if isinstance(data, NodeCoords):
        return unwrap_node_coords(data.node)

    if isinstance(data, list):
        stripped_nodes = []
        for ele in data:
            stripped_nodes.append(unwrap_node_coords(ele))
        return stripped_nodes

    return data
