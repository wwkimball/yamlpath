# pylint: disable=too-many-lines
"""
YAML Path processor based on ruamel.yaml.

Copyright 2018, 2019 William W. Kimball, Jr. MBA MSIS
"""
from sys import maxsize
import re
from distutils.util import strtobool
from typing import Any, Generator, List, Union

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

from yamlpath.path import SearchTerms, CollectorTerms
from yamlpath.wrappers import ConsolePrinter
from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import (
    YAMLValueFormats,
    PathSegmentTypes,
    PathSearchMethods,
    CollectorOperators,
    PathSeperators,
)
from yamlpath import YAMLPath

# FIXME:  Scalars wipe out Arrays
class Processor:
    """
    Query and update YAML data via robust YAML Paths.

    Parameters:
        1. logger (ConsolePrinter) Instance of ConsoleWriter or subclass
        2. data (Any) Parsed YAML data

    Returns:  N/A

    Raises:  N/A
    """

    def __init__(self, logger: ConsolePrinter, data: Any) -> None:
        self.logger: ConsolePrinter = logger
        self.data: Any = data

    def get_nodes(self, yaml_path: Union[YAMLPath, str],
                  **kwargs: Any) -> Generator[Any, None, None]:
        """
        Retrieves zero or more node at YAML Path in YAML data.

        Parameters:
            1. yaml_path (Union[Path, str]) The YAML Path to evaluate

        Keyword Parameters:
            * mustexist (bool) Indicate whether yaml_path must exist
              in data prior to this query (lest an Exception be raised);
              default=False
            * default_value (Any) The value to set at yaml_path should
              it not already exist in data and mustexist is False;
              default=None
            * pathsep (PathSeperators) Forced YAML Path segment seperator; set
              only when automatic inference fails;
              default = PathSeperators.AUTO

        Returns:  (Generator) The requested YAML nodes as they are matched

        Raises:
            - `YAMLPathException` when YAML Path is invalid
        """
        mustexist: bool = kwargs.pop("mustexist", False)
        default_value: Any = kwargs.pop("default_value", None)
        pathsep: PathSeperators = kwargs.pop("pathsep", PathSeperators.AUTO)
        node: Any = None

        if self.data is None:
            return

        if isinstance(yaml_path, str):
            yaml_path = YAMLPath(yaml_path, pathsep)
        elif pathsep is not PathSeperators.AUTO:
            yaml_path.seperator = pathsep

        if mustexist:
            matched_nodes: int = 0
            for node in self._get_required_nodes(self.data, yaml_path):
                matched_nodes += 1
                self.logger.debug(
                    "Processor::get_nodes:  Relaying required node <{}>:"
                    .format(type(node))
                )
                self.logger.debug(node)
                yield node

            if matched_nodes < 1:
                raise YAMLPathException(
                    "Required YAML Path does not match any nodes",
                    yaml_path
                )
        else:
            for node in self._get_optional_nodes(
                    self.data, yaml_path, default_value
            ):
                self.logger.debug(
                    "Processor::get_nodes:  Relaying optional node <{}>:"
                    .format(type(node))
                )
                self.logger.debug(node)
                yield node

    def set_value(self, yaml_path: Union[YAMLPath, str],
                  value: Any, **kwargs) -> None:
        """
        Sets the value of zero or more nodes at YAML Path in YAML data.

        Parameters:
            1. yaml_path (Union[Path, str]) The YAML Path to evaluate
            2. value (Any) The value to set

        Keyword Parameters:
            * mustexist (bool) Indicate whether yaml_path must exist
              in data prior to this query (lest an Exception be raised);
              default=False
            * value_format (YAMLValueFormats) The demarcation or visual
              representation to use when writing the data;
              default=YAMLValueFormats.DEFAULT
            * pathsep (PathSeperators) Forced YAML Path segment seperator; set
              only when automatic inference fails;
              default = PathSeperators.AUTO

        Returns:  N/A

        Raises:
            - `YAMLPathException` when YAML Path is invalid
        """
        if self.data is None:
            return

        mustexist: bool = kwargs.pop("mustexist", False)
        value_format: YAMLValueFormats = kwargs.pop("value_format",
                                                    YAMLValueFormats.DEFAULT)
        pathsep: PathSeperators = kwargs.pop("pathsep", PathSeperators.AUTO)
        node: Any = None

        if isinstance(yaml_path, str):
            yaml_path = YAMLPath(yaml_path, pathsep)
        elif pathsep is not PathSeperators.AUTO:
            yaml_path.seperator = pathsep

        if mustexist:
            self.logger.debug(
                "Processor::set_value:  Seeking required node at {}."
                .format(yaml_path)
            )
            found_nodes: int = 0
            for node in self._get_required_nodes(self.data, yaml_path):
                found_nodes += 1
                self._update_node(node, value, value_format)

            if found_nodes < 1:
                raise YAMLPathException(
                    "No nodes matched required YAML Path",
                    yaml_path
                )
        else:
            self.logger.debug(
                "Processor::set_value:  Seeking optional node at {}."
                .format(yaml_path)
            )
            for node in self._get_optional_nodes(self.data, yaml_path, value):
                self._update_node(node, value, value_format)

    # pylint: disable=locally-disabled,too-many-branches
    def _get_nodes_by_path_segment(self, data: Any,
                                   yaml_path: YAMLPath, segment_index: int,
                                  ) -> Generator[Any, None, None]:
        """
        Returns zero or more nodes identified by one segment of a YAML Path
        within the present data context.

        Parameters:
            1. data (ruamel.yaml data) The parsed YAML data to process
            2. yaml_path (yamlpath.Path) The YAML Path being processed
            3. segment_index (int) Segment index of the YAML Path to process

        Returns:  (Generator[Any, None, None]) Each node as they are matched

        Raises:
            - `NotImplementedError` when the segment indicates an unknown
              PathSegmentTypes value.
        """
        if data is None:
            return

        segments = yaml_path.escaped
        if not (segments and len(segments) > segment_index):
            return

        (segment_type, stripped_attrs) = segments[segment_index]

        if segment_type == PathSegmentTypes.KEY:
            nodes = self._get_nodes_by_key(data, yaml_path, segment_index)
        elif segment_type == PathSegmentTypes.INDEX:
            nodes = self._get_nodes_by_index(data, yaml_path, segment_index)
        elif segment_type == PathSegmentTypes.ANCHOR:
            nodes = self._get_nodes_by_anchor(data, yaml_path, segment_index)
        elif (
                segment_type == PathSegmentTypes.SEARCH
                and isinstance(stripped_attrs, SearchTerms)
        ):
            nodes = self._get_nodes_by_search(data, stripped_attrs)
        elif (
                segment_type == PathSegmentTypes.COLLECTOR
                and isinstance(stripped_attrs, CollectorTerms)
        ):
            nodes = self._get_nodes_by_collector(data, yaml_path,
                                                 segment_index, stripped_attrs)
        else:
            raise NotImplementedError

        for node in nodes:
            yield node

    def _get_nodes_by_key(self, data: Any, yaml_path: YAMLPath,
                          segment_index: int) -> Generator[Any, None, None]:
        """
        Returns zero or more nodes identified by a dict key found at a specific
        segment of a YAML Path within the present data context.

        Parameters:
            1. data (ruamel.yaml data) The parsed YAML data to process
            2. yaml_path (yamlpath.Path) The YAML Path being processed
            3. segment_index (int) Segment index of the YAML Path to process

        Returns:  (Generator[Any, None, None]) Each node as they are matched

        Raises:  N/A
        """
        (_, stripped_attrs) = yaml_path.escaped[segment_index]
        str_stripped = str(stripped_attrs)

        self.logger.debug(
            "Processor::_get_nodes_by_key:  Seeking KEY node at {}."
            .format(str_stripped)
        )

        if isinstance(data, dict):
            if stripped_attrs in data:
                yield data[stripped_attrs]
            else:
                # Check for a string/int type mismatch
                try:
                    intkey = int(str(stripped_attrs))
                    if intkey in data:
                        yield data[intkey]
                except ValueError:
                    pass
        elif isinstance(data, list):
            try:
                # Try using the ref as a bare Array index
                idx = int(str_stripped)
                if len(data) > idx:
                    yield data[idx]
            except ValueError:
                # Pass-through search against possible Array-of-Hashes
                for element in data:
                    for node in self._get_nodes_by_path_segment(
                            element, yaml_path, segment_index):
                        yield node

    # pylint: disable=locally-disabled,too-many-locals
    def _get_nodes_by_index(self, data: Any, yaml_path: YAMLPath,
                            segment_index: int) -> Generator[Any, None, None]:
        """
        Returns zero or more nodes identified by a list element index found at
        a specific segment of a YAML Path within the present data context.

        Parameters:
            1. data (Any) The parsed YAML data to process
            2. yaml_path (Path) The YAML Path being processed
            3. segment_index (int) Segment index of the YAML Path to process

        Returns:  (Generator[Any, None, None]) Each node as they are matched

        Raises:  N/A
        """
        (_, stripped_attrs) = yaml_path.escaped[segment_index]
        (_, unstripped_attrs) = yaml_path.unescaped[segment_index]
        str_stripped = str(stripped_attrs)

        self.logger.debug(
            "Processor::_get_nodes_by_index:  Seeking INDEX node at {}."
            .format(str_stripped)
        )

        if ':' in str_stripped:
            # Array index or Hash key slice
            slice_parts: List[str] = str_stripped.split(':', 1)
            min_match: str = slice_parts[0]
            max_match: str = slice_parts[1]
            if isinstance(data, list):
                try:
                    intmin: int = int(min_match)
                    intmax: int = int(max_match)
                except ValueError:
                    raise YAMLPathException(
                        "{} is not an integer array slice"
                        .format(str_stripped)
                        , yaml_path
                        , str(unstripped_attrs)
                    )

                if intmin == intmax and len(data) > intmin:
                    yield [data[intmin]]
                else:
                    yield data[intmin:intmax]

            elif isinstance(data, dict):
                for key, val in data.items():
                    if min_match <= key <= max_match:
                        yield val
        else:
            try:
                idx: int = int(str_stripped)
            except ValueError:
                raise YAMLPathException(
                    "{} is not an integer array index"
                    .format(str_stripped)
                    , yaml_path
                    , str(unstripped_attrs)
                )

            if isinstance(data, list) and len(data) > idx:
                yield data[idx]

    def _get_nodes_by_anchor(self, data: Any, yaml_path: YAMLPath,
                             segment_index: int) -> Generator[Any, None, None]:
        """
        Returns zero or more nodes identified by an Anchor name found at a
        specific segment of a YAML Path within the present data context.

        Parameters:
            1. data (Any) The parsed YAML data to process
            2. yaml_path (Path) The YAML Path being processed
            3. segment_index (int) Segment index of the YAML Path to process

        Returns:  (Generator[Any, None, None]) Each node as they are matched

        Raises:  N/A
        """
        (_, stripped_attrs) = yaml_path.escaped[segment_index]

        self.logger.debug(
            "Processor::_get_nodes_by_anchor:  Seeking ANCHOR node at {}."
            .format(stripped_attrs)
        )

        if isinstance(data, list):
            for ele in data:
                if (hasattr(ele, "anchor")
                        and stripped_attrs == ele.anchor.value):
                    yield ele
        elif isinstance(data, dict):
            for _, val in data.items():
                if (hasattr(val, "anchor")
                        and stripped_attrs == val.anchor.value):
                    yield val

    # pylint: disable=locally-disabled,too-many-statements
    def _get_nodes_by_search(self, data: Any,
                             terms: SearchTerms) -> Generator[Any, None, None]:
        """
        Searches the the current data context for all nodes matching a search
        expression.

        Parameters:
            1. data (Any) The parsed YAML data to process
            2. terms (SearchTerms) The search terms

        Returns:  (Generator[Any, None, None]) Each node as they are matched

        Raises:  N/A
        """
        def search_matches(method: PathSearchMethods, needle: str,
                           haystack: Any) -> bool:
            self.logger.debug(
                ("Processor::_search::search_matches:  Searching for {}{}"
                 + " using {} against {}:"
                ).format(type(needle), needle, method, type(haystack))
            )
            self.logger.debug(haystack)
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

        self.logger.debug(
            ("Processor::_get_nodes_by_search:  Seeking SEARCH nodes matching"
             + " {}.")
            .format(terms)
        )

        invert = terms.inverted
        method = terms.method
        attr = terms.attribute
        term = terms.term
        if isinstance(data, list):
            for ele in data:
                if attr == '.':
                    matches = search_matches(method, term, ele)
                elif isinstance(ele, dict) and attr in ele:
                    matches = search_matches(method, term, ele[attr])

                if (matches and not invert) or (invert and not matches):
                    yield ele

        elif isinstance(data, dict):
            # Allow . to mean "each key's name"
            if attr == '.':
                for key, val in data.items():
                    matches = search_matches(method, term, key)
                    if (matches and not invert) or (invert and not matches):
                        yield val

            elif attr in data:
                value = data[attr]
                matches = search_matches(method, term, value)
                if (matches and not invert) or (invert and not matches):
                    yield value

        else:
            # Check the passed data itself for a match
            matches = search_matches(method, term, data)
            if (matches and not invert) or (invert and not matches):
                yield data

    def _get_nodes_by_collector(
            self, data: Any, yaml_path: YAMLPath, segment_index: int,
            terms: CollectorTerms
    ) -> Generator[Any, None, None]:
        """
        Returns zero or more nodes within a given data context that match an
        inner YAML Path found at a specific segment of an outer YAML Path.

        Parameters:
            1. data (ruamel.yaml data) The parsed YAML data to process
            2. yaml_path (Path) The YAML Path being processed
            3. segment_index (int) Segment index of the YAML Path to process
            4. terms (CollectorTerms) The collector terms

        Returns:  (Generator[Any, None, None]) Each node as they are matched

        Raises:  N/A
        """
        if not terms.operation is CollectorOperators.NONE:
            yield data
            return

        results = []
        for node in self._get_required_nodes(data, YAMLPath(terms.expression)):
            results.append(node)

        # This may end up being a bad idea for some cases, but this method will
        # unwrap all lists that look like `[[value]]` into just `[value]`.
        # When this isn't done, Collector syntax gets burdensome because
        # `(...)[0]` becomes necessary in too many use-cases.  This will be an
        # issue when the user actually expects a list-of-lists as output,
        # though I haven't yet come up with any use-case where that is what I
        # really wanted to get from the query.
        if len(results) == 1 and isinstance(results[0], list):
            results = results[0]

        # As long as each next segment is an ADDITION or SUBTRACTION
        # COLLECTOR, keep combining the results.
        segments = yaml_path.escaped
        next_segment_idx = segment_index + 1
        while next_segment_idx < len(segments):
            (peek_type, peek_attrs) = segments[next_segment_idx]
            if (
                    peek_type is PathSegmentTypes.COLLECTOR
                    and isinstance(peek_attrs, CollectorTerms)
            ):
                peek_path: YAMLPath = YAMLPath(peek_attrs.expression)
                if peek_attrs.operation == CollectorOperators.ADDITION:
                    add_results = []
                    for node in self._get_required_nodes(data, peek_path):
                        add_results.append(node)

                    # Flatten [[val1,val2]] into [val1,val2] so the following
                    # concatentation won't require the caller to specify
                    # `()+()[0]`.
                    if (len(add_results) == 1
                            and isinstance(add_results[0], list)):
                        add_results = add_results[0]

                    results += add_results
                elif peek_attrs.operation == CollectorOperators.SUBTRACTION:
                    rem_results = []
                    for node in self._get_required_nodes(data, peek_path):
                        rem_results.append(node)

                    # Flatten [[val1,val2]] into [val1,val2] so the following
                    # concatentation won't require the caller to specify
                    # `()-()[0]`.
                    if (len(rem_results) == 1
                            and isinstance(rem_results[0], list)):
                        rem_results = rem_results[0]

                    results = [e for e in results if e not in rem_results]
                else:
                    raise YAMLPathException(
                        "Adjoining Collectors without an operator has no"
                        + " meaning; try + or - between them"
                        , yaml_path
                        , str(peek_path)
                    )
            else:
                break

            next_segment_idx += 1

        # yield only when there are results
        if results:
            yield results

    def _get_required_nodes(self, data: Any, yaml_path: YAMLPath,
                            depth: int = 0) -> Generator[Any, None, None]:
        """
        Generates zero or more pre-existing nodes from YAML data matching a
        YAML Path.

        Parameters:
          1. data (Any) The parsed YAML data to process
          2. yaml_path (Path) The pre-parsed YAML Path to follow
          3. depth (int) Index within yaml_path to process; default=0

        Returns:  (Generator[Any, None, None]) The requested YAML nodes as they
            are matched or None

        Raises:  N/A
        """
        if data is None:
            return

        segments = yaml_path.escaped
        if segments and len(segments) > depth:
            (segment_type, unstripped_attrs) = yaml_path.unescaped[depth]
            except_segment = str(unstripped_attrs)
            self.logger.debug(
                ("Processor::_get_required_nodes:  Seeking segment <{}>{} in"
                 + " data of type {}:")
                .format(segment_type, except_segment, type(data))
            )
            self.logger.debug(data)
            self.logger.debug("")

            for node in self._get_nodes_by_path_segment(
                    data, yaml_path, depth):
                self.logger.debug(
                    ("Processor::_get_required_nodes:  Found node <{}>{} in"
                     + " the data and recursing into it...")
                    .format(segment_type, except_segment)
                )
                for subnode in self._get_required_nodes(
                        node, yaml_path, depth + 1):
                    yield subnode
        else:
            self.logger.debug(
                ("Processor::_get_required_nodes:  Finally returning data of"
                 + " type {}:")
                .format(type(data))
            )
            self.logger.debug(data)
            self.logger.debug("")

            yield data

    def _get_optional_nodes(self, data: Any, yaml_path: YAMLPath,
                            value: Any = None,
                            depth: int = 0) -> Generator[Any, None, None]:
        """
        Returns zero or more pre-existing nodes matching a YAML Path.  Will
        create nodes that are missing, as long as any missing segments are
        deterministic (SEARCH and COLLECTOR segments are non-deterministic).

        Parameters:
            1. data (Any) The parsed YAML data to process
            2. yaml_path (Path) The pre-parsed YAML Path to follow
            3. value (Any) The value to assign to the element
            4. depth (int) For recursion, this identifies which segment of
               yaml_path to evaluate; default=0

        Returns:  (Generator[Any, None, None]) Each node as they are matched

        Raises:
            - `YAMLPathException` when the YAML Path is invalid.
            - `NotImplementedError` when a segment of the YAML Path indicates
              an element that does not exist in data and this code isn't
              yet prepared to add it.
        """
        if data is None:
            self.logger.debug(
                "Processor::_get_optional_nodes:  Bailing out on None"
                + " data/path!"
            )
            return

        segments = yaml_path.escaped
        if segments and len(segments) > depth:
            (segment_type, unstripped_attrs) = yaml_path.unescaped[depth]
            stripped_attrs = segments[depth][1]
            except_segment = str(unstripped_attrs)

            self.logger.debug(
                ("Processor::_get_optional_nodes:  Seeking element <{}>{} in"
                 + " data of type {}:"
                ).format(segment_type, except_segment, type(data))
            )
            self.logger.debug(data)
            self.logger.debug("")

            # The next element may not exist; this method ensures that it does
            matched_nodes = 0
            for node in self._get_nodes_by_path_segment(
                    data, yaml_path, depth
            ):
                matched_nodes += 1
                self.logger.debug(
                    ("Processor::_get_optional_nodes:  Found element <{}>{} in"
                     + " the data; recursing into it..."
                    ).format(segment_type, except_segment)
                )
                for epn in self._get_optional_nodes(
                        node, yaml_path, value, depth + 1
                ):
                    yield epn

            if (
                    matched_nodes < 1
                    and segment_type is not PathSegmentTypes.SEARCH
            ):
                # Add the missing element
                self.logger.debug(
                    ("Processor::_get_optional_nodes:  Element <{}>{} is"
                     + " unknown in the data!"
                    ).format(segment_type, except_segment)
                )
                if isinstance(data, list):
                    self.logger.debug(
                        "Processor::_get_optional_nodes:  Dealing with a list"
                    )
                    if (
                            segment_type is PathSegmentTypes.ANCHOR
                            and isinstance(stripped_attrs, str)
                    ):
                        new_val = self.default_for_child(
                            yaml_path, depth + 1, value
                        )
                        new_ele = self.append_list_element(
                            data, new_val, stripped_attrs
                        )
                        for node in self._get_optional_nodes(
                                new_ele, yaml_path, value, depth + 1
                        ):
                            matched_nodes += 1
                            yield node
                    elif (
                            segment_type in [
                                PathSegmentTypes.INDEX,
                                PathSegmentTypes.KEY]
                    ):
                        if isinstance(stripped_attrs, int):
                            newidx = stripped_attrs
                        else:
                            try:
                                newidx = int(str(stripped_attrs))
                            except ValueError:
                                raise YAMLPathException(
                                    ("Cannot add non-integer {} subreference"
                                     + " to lists")
                                    .format(str(segment_type))
                                    , yaml_path
                                    , except_segment
                                )
                        for _ in range(len(data) - 1, newidx):
                            new_val = self.default_for_child(
                                yaml_path, depth + 1, value
                            )
                            self.append_list_element(data, new_val)
                        for node in self._get_optional_nodes(
                                data[newidx], yaml_path, value,
                                depth + 1
                        ):
                            matched_nodes += 1
                            yield node
                    else:
                        raise YAMLPathException(
                            "Cannot add {} subreference to lists"
                            .format(str(segment_type))
                            , yaml_path
                            , except_segment
                        )
                elif isinstance(data, dict):
                    self.logger.debug(
                        "Processor::_get_optional_nodes:  Dealing with a"
                        + " dictionary"
                    )
                    if segment_type is PathSegmentTypes.ANCHOR:
                        raise NotImplementedError

                    if segment_type is PathSegmentTypes.KEY:
                        data[stripped_attrs] = self.default_for_child(
                            yaml_path, depth + 1, value
                        )
                        for node in self._get_optional_nodes(
                                data[stripped_attrs], yaml_path, value,
                                depth + 1
                        ):
                            matched_nodes += 1
                            yield node
                    else:
                        raise YAMLPathException(
                            "Cannot add {} subreference to dictionaries"
                            .format(str(segment_type)),
                            yaml_path,
                            except_segment
                        )
                else:
                    raise YAMLPathException(
                        "Cannot add {} subreference to scalars".format(
                            str(segment_type)
                        ),
                        yaml_path,
                        except_segment
                    )

        else:
            self.logger.debug(
                ("Processor::_get_optional_nodes:  Finally returning data of"
                 + " type {}:"
                ).format(type(data))
            )
            self.logger.debug(data)

            yield data

    def _update_node(self, source_node: Any, value: Any,
                     value_format: YAMLValueFormats) -> None:
        """
        Recursively updates the value of a YAML Node and any references to it
        within the entire YAML data structure (Anchors and Aliases, if any).

        Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. source_node (object) The YAML Node to update
          3. value (any) The new value to assign to the source_node and
             its references
          4. value_format (YAMLValueFormats) the YAML representation of the
             value

        Returns: N/A

        Raises: N/A
        """
        # Change replacement_node has already been made to reference_node in
        # data.  When reference_node is either an Anchor or an Alias, all other
        # references to it must also receive an identical update so they are
        # kept in synchronization.
        def update_refs(data: Any, reference_node: Any,
                        replacement_node: Any) -> None:
            if isinstance(data, CommentedMap):
                for i, k in [
                        (idx, key) for idx, key in
                        enumerate(data.keys()) if key is reference_node
                ]:
                    data.insert(i, replacement_node, data.pop(k))
                for k, val in data.non_merged_items():
                    if val is reference_node:
                        data[k] = replacement_node
                    else:
                        update_refs(val, reference_node, replacement_node)
            elif isinstance(data, CommentedSeq):
                for idx, item in enumerate(data):
                    if item is reference_node:
                        data[idx] = replacement_node
                    else:
                        update_refs(item, reference_node, replacement_node)

        new_node = Processor.make_new_node(source_node, value, value_format)
        update_refs(self.data, source_node, new_node)

    @staticmethod
    def default_for_child(yaml_path: YAMLPath, depth: int,
                          value: Any = None) -> Any:
        """
        Identifies and returns the most appropriate default value for the next
        entry in a YAML Path, should it not already exist.

        Parameters:
            1. yaml_path (deque) The pre-parsed YAML Path to follow
            2. depth (int) Index of the YAML Path segment to evaluate
            3. value (Any) The expected value for the final YAML Path entry

        Returns:  (Any) The most appropriate default value

        Raises:  N/A
        """
        default_value = value
        segments = yaml_path.escaped
        if not (segments and len(segments) > depth):
            return default_value

        typ = segments[depth][0]
        if typ == PathSegmentTypes.INDEX:
            default_value = CommentedSeq()
        elif typ == PathSegmentTypes.KEY:
            default_value = CommentedMap()
        elif isinstance(value, str):
            default_value = PlainScalarString("")
        elif isinstance(value, bool):
            default_value = ScalarBoolean(False)
        elif isinstance(value, int):
            default_value = ScalarInt(maxsize)
        elif isinstance(value, float):
            default_value = ScalarFloat("inf")

        return default_value

    @staticmethod
    def append_list_element(data: Any, value: Any = None,
                            anchor: str = None) -> Any:
        """
        Appends a new element to an ruamel.yaml presented list, preserving any
        tailing comment for the former last element of the same list.

        Parameters:
            1. data (Any) The parsed YAML data to process
            2. value (Any) The value of the element to append
            3. anchor (str) An Anchor or Alias name for the new element

        Returns:  (Any) The newly appended element node

        Raises:  N/A
        """
        if anchor is not None and value is not None:
            value = Processor.wrap_type(value)
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

    @staticmethod
    def wrap_type(value: Any) -> Any:
        """
        Wraps a value in one of the ruamel.yaml wrapper types.

        Parameters:
            1. value (Any) The value to wrap.

        Returns: (Any) The wrapped value or the original value when a better
            wrapper could not be identified.

        Raises:  N/A
        """
        wrapped_value = value
        typ = type(value)
        if typ is list:
            wrapped_value = CommentedSeq(value)
        elif typ is dict:
            wrapped_value = CommentedMap(value)
        elif typ is str:
            wrapped_value = PlainScalarString(value)
        elif typ is int:
            wrapped_value = ScalarInt(value)
        elif typ is float:
            wrapped_value = ScalarFloat(value)
        elif typ is bool:
            wrapped_value = ScalarBoolean(value)

        return wrapped_value

    @staticmethod
    def clone_node(node: Any) -> Any:
        """
        Duplicates a YAML Data node.  This is necessary because otherwise,
        Python would treat any copies of a value as references to each other
        such that changes to one automatically affect all copies.  This is not
        desired when an original value must be duplicated elsewhere in the data
        and then the original changed without impacting the copy.

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

    @staticmethod
    def make_new_node(source_node: Any, value: Any,
                      value_format: YAMLValueFormats) -> Any:
        """
        Creates a new data node based on a sample node, effectively duplicaing
        the type and anchor of the node but giving it a different value.

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
            except NameError:
                raise NameError(
                    "Unknown YAML Value Format:  {}".format(strform)
                    + ".  Please specify one of:  "
                    + ", ".join(
                        [l.lower() for l in YAMLValueFormats.get_names()]
                    )
                )

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
            except ValueError:
                raise ValueError(
                    ("The requested value format is {}, but '{}' cannot be"
                     + " cast to a floating-point number.")
                    .format(valform, value)
                )

            strval = str(value)
            precision = 0
            width = len(strval)
            lastdot = strval.rfind(".")
            if -1 < lastdot:
                precision = strval.rfind(".")

            if hasattr(source_node, "anchor"):
                new_node = ScalarFloat(
                    new_value
                    , anchor=source_node.anchor.value
                    , prec=precision
                    , width=width
                )
            else:
                new_node = ScalarFloat(new_value, prec=precision, width=width)
        elif valform == YAMLValueFormats.INT:
            new_type = ScalarInt

            try:
                new_value = int(value)
            except ValueError:
                raise ValueError(
                    ("The requested value format is {}, but '{}' cannot be"
                     + " cast to an integer number.")
                    .format(valform, value)
                )
        else:
            # Punt to whatever the best type may be
            new_type = type(Processor.wrap_type(value))

        if new_node is None:
            if hasattr(source_node, "anchor"):
                new_node = new_type(new_value, anchor=source_node.anchor.value)
            else:
                new_node = new_type(new_value)

        return new_node
