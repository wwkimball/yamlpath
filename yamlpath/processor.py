"""YAML Path processor based on ruamel.yaml.

Copyright 2018, 2019 William W. Kimball, Jr. MBA MSIS
"""
from sys import maxsize
import re
from distutils.util import strtobool
from typing import Any, Generator, Union

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

from yamlpath import Path
from yamlpath.wrappers import ConsolePrinter
from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import (
    YAMLValueFormats,
    PathSegmentTypes,
    PathSearchMethods,
    CollectorOperators,
)
from yamlpath.types import SearchTerms, CollectorTerms


class Processor:
    """Query and update YAML data via robust YAML Paths."""

    def __init__(self, logger: ConsolePrinter, data: Any) -> None:
        """Init this class.

        Positional Parameters:
          1. logger (ConsoleWriter) Instance of ConsoleWriter or any similar
             wrapper (say, around stdlib logging modules)
          2. data (any) Parsed YAML data

        Returns:  N/A

        Raises:  N/A
        """
        self.logger: ConsolePrinter = logger
        self.data: Any = data

    def get_nodes(self, yaml_path: Union[Path, str],
                  **kwargs) -> Generator[Any, None, None]:
        """Retrieves zero or more node at YAML Path in YAML data.

        Positional Parameters:
          1. yaml_path (yamlpath.Path) The YAML Path to evaluate

        Optional Parameters:
          1. mustexist (Boolean) Indicate whether yaml_path must exist
             in data prior to this query (lest an Exception be raised);
             default=False
          2. default_value (any) The value to set at yaml_path should
             it not already exist in data and mustexist is False;
             default=None

        Returns:  (Generator) The requested YAML nodes as they are matched

        Raises:
            YAMLPathException when YAML Path is invalid
        """
        mustexist: bool = kwargs.pop("mustexist", False)
        default_value: Any = kwargs.pop("default_value", None)
        node: Any

        if self.data is None:
            return

        if isinstance(yaml_path, str):
            yaml_path = Path(yaml_path, **kwargs)

        if mustexist:
            matched_nodes = 0
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
            for node in self._get_optional_nodes(self.data, yaml_path, default_value):
                self.logger.debug(
                    "Processor::get_nodes:  Relaying optional node <{}>:"
                    .format(type(node))
                )
                self.logger.debug(node)
                yield node

    def set_value(self, yaml_path: Union[Path, str],
                  value: Any, **kwargs) -> None:
        """Sets the value of zero or more nodes at YAML Path in YAML data.

        Positional Parameters:
          1. yaml_path (yamlpath.Path) The YAML Path to evaluate
          2. value (any) The value to set

        Optional Parameters:
          1. mustexist (Boolean) Indicate whether yaml_path must exist
             in data prior to this query (lest an Exception be raised);
             default=False
          2. value_format (YAMLValueFormats) The demarcation or visual
             representation to use when writing the data;
             default=YAMLValueFormats.DEFAULT

        Returns:  N/A

        Raises:
            YAMLPathException when YAML Path is invalid
        """
        if self.data is None:
            return

        if isinstance(yaml_path, str):
            yaml_path = Path(yaml_path, **kwargs)

        mustexist: bool = kwargs.pop("mustexist", False)
        value_format: YAMLValueFormats = kwargs.pop("value_format",
                                                    YAMLValueFormats.DEFAULT)
        node: Any

        if mustexist:
            self.logger.debug(
                "Processor::set_value:  Seeking required node at {}."
                .format(yaml_path)
            )
            found_nodes = 0
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

    def _get_nodes_by_path_segment(self, data: Any,
                                   yaml_path: Path, segment_index: int,
                                  ) -> Generator[Any, None, None]:
        """Returns zero or more referenced YALM Nodes.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (yamlpath.Path) THe YAML Path being processed
          3. path_index (int) Segment index of the YAML Path to process

        Returns:  (any) At least one YAML Node

        Raises:
          NotImplementedError when ref indicates an unknown
          PathSegmentTypes value.
        """
        if data is None:
            return

        segments = yaml_path.escaped
        segment_len = len(segments)
        if not (segments and segment_len > segment_index):
            return

        segment = segments[segment_index]
        (segment_type, stripped_attrs) = segment
        (_, unstripped_attrs) = yaml_path.unescaped[segment_index]

        if segment_type == PathSegmentTypes.KEY:
            if isinstance(data, dict) and stripped_attrs in data:
                yield data[stripped_attrs]
            elif isinstance(data, list):
                try:
                    # Try using the ref as a bare Array index
                    idx = int(stripped_attrs)
                    if len(data) > idx:
                        yield data[idx]
                except ValueError:
                    # Pass-through search against possible Array-of-Hashes
                    for element in data:
                        for node in self._get_nodes_by_path_segment(
                                element, yaml_path, segment_index):
                            yield node
        elif (
            segment_type == PathSegmentTypes.INDEX
            and isinstance(stripped_attrs, str)
            and ':' in stripped_attrs
        ):
            # Array index or Hash key slice
            slice_parts = stripped_attrs.split(':', 1)
            min_match = slice_parts[0]
            max_match = slice_parts[1]
            if isinstance(data, list):
                try:
                    intmin = int(min_match)
                    intmax = int(max_match)
                except ValueError:
                    raise YAMLPathException(
                        "{} is not an integer array slice"
                        .format(str(stripped_attrs))
                        , yaml_path
                        , unstripped_attrs
                    )

                if intmin == intmax and len(data) > intmin:
                    yield data[intmin]
                else:
                    yield data[intmin:intmax]

            elif isinstance(data, dict):
                for key, val in data.items():
                    if min_match <= key <= max_match:
                        yield val
        elif segment_type == PathSegmentTypes.INDEX:
            try:
                idx = int(stripped_attrs)
            except ValueError:
                raise YAMLPathException(
                    "{} is not an integer array index"
                    .format(str(stripped_attrs))
                    , yaml_path
                    , unstripped_attrs
                )

            if isinstance(data, list) and len(data) > idx:
                yield data[idx]
        elif segment_type == PathSegmentTypes.ANCHOR:
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
        elif segment_type == PathSegmentTypes.SEARCH:
            for match in self._search(data, stripped_attrs):
                yield match
        elif segment_type == PathSegmentTypes.COLLECTOR:
            terms: CollectorTerms = stripped_attrs
            operation = terms.operation
            if not operation is CollectorOperators.NONE:
                yield data
                return

            expression = terms.expression
            subpath = Path(expression)
            results = []
            for node in self._get_required_nodes(data, subpath):
                results.append(node)

            # As long as each next segment is an ADDITION or SUBTRACTION
            # COLLECTOR, keep combining the results.
            next_segment_idx = segment_index + 1
            while next_segment_idx < segment_len:
                (peek_type, peek_attrs) = segments[next_segment_idx]
                if peek_type == PathSegmentTypes.COLLECTOR:
                    peek_terms: CollectorTerms = peek_attrs
                    peek_operation: CollectorOperators = peek_terms.operation
                    peek_path: Path = Path(peek_terms.expression)
                    if peek_operation == CollectorOperators.ADDITION:
                        add_results = []
                        for node in self._get_required_nodes(data, peek_path):
                            add_results.append(node)
                        results += add_results
                    elif peek_operation == CollectorOperators.SUBTRACTION:
                        rem_results = []
                        for node in self._get_required_nodes(data, peek_path):
                            rem_results.append(node)
                        results = [e for e in results if e not in rem_results]
                    else:
                        break
                else:
                    break

                next_segment_idx += 1

            # Don't unnecessarily wrap single-match results within lists
            if len(results) == 1:
                results = results[0]

            yield results
        else:
            raise NotImplementedError

    def _search(self, data: Any,
                terms: SearchTerms) -> Generator[Any, None, None]:
        """Searches the top level of given YAML data for all matching dictionary
        entries.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. terms (SearchTerms) A SearchTerms with these properties:
             * inverted (Boolean) true = Return a NON-matching node
             * method (PathSearchMethods) the search method
             * attribute (str) the dictionary key to the value to check
             * term (any) the term to match
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

    def _get_required_nodes(self, data: Any, yaml_path: Path,
                            depth: int = 0) -> Generator[Any, None, None]:
        """Generates zero or more pre-existing nodes from YAML data matching a
        YAML Path.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (yamlpath.Path) The pre-parsed YAML Path to follow
          3. depth (int) Index within yaml_path to process

        Returns:  (any) The requested YAML nodes as they are matched or None

        Raises:  N/A
        """
        if data is None:
            return

        segments = yaml_path.escaped
        if segments and len(segments) > depth:
            (segment_type, unstripped_attrs) = yaml_path.unescaped[depth]
            self.logger.debug(
                ("Processor::_get_required_nodes:  Seeking segment <{}>{} in data of"
                 + " type {}:")
                 .format(segment_type, unstripped_attrs, type(data))
            )
            self.logger.debug(data)
            self.logger.debug("")

            for node in self._get_nodes_by_path_segment(
                    data, yaml_path, depth):
                self.logger.debug(
                    ("Processor::_get_required_nodes:  Found node <{}>{} in the"
                        + " data and recursing into it...")
                    .format(segment_type, unstripped_attrs)
                )
                for subnode in self._get_required_nodes(
                        node, yaml_path, depth + 1):
                    yield subnode
        else:
            self.logger.debug(
                "Processor::_get_required_nodes:  Finally returning data of type {}:"
                .format(type(data))
            )
            self.logger.debug(data)
            self.logger.debug("")

            yield data

    def _get_optional_nodes(self, data: Any, yaml_path: Path,
                            value: Any = None,
                            depth: int = 0) -> Generator[Any, None, None]:
        """Returns zero or more pre-existing nodes matching a YAML Path, or
        exactly one new node at the end of the YAML Path if it had to be
        created.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. path (deque) The pre-parsed YAML Path to follow
          3. value (any) The value to assign to the element

        Returns:  (object) The specified node(s)

        Raises:
          YAMLPathException when the YAML Path is invalid.
          NotImplementedError when a segment of the YAML Path indicates
            an element that does not exist in data and this code isn't
            yet prepared to add it.
        """
        if data is None:
            self.logger.debug(
                "Processor::_get_optional_nodes:  Bailing out on None data/path!"
            )
            return

        segments = yaml_path.escaped
        if segments and len(segments) > depth:
            (segment_type, unstripped_attrs) = yaml_path.unescaped[depth]
            stripped_attrs = segments[depth][1]

            self.logger.debug(
                ("Processor::_get_optional_nodes:  Seeking element <{}>{} in data of"
                 + " type {}:"
                ).format(segment_type, unstripped_attrs, type(data))
            )
            self.logger.debug(data)
            self.logger.debug("")

            # The next element may not exist; this method ensures that it does
            matched_nodes = 0
            for node in self._get_nodes_by_path_segment(data, yaml_path,
                    depth):
                matched_nodes += 1
                self.logger.debug(
                    ("Processor::_get_optional_nodes:  Found element <{}>{} in the"
                        + " data; recursing into it..."
                    ).format(segment_type, unstripped_attrs)
                )
                for epn in self._get_optional_nodes(node, yaml_path, value,
                        depth + 1):
                    yield epn

            if (matched_nodes < 1
                    and segment_type is not PathSegmentTypes.SEARCH):
                # Add the missing element
                self.logger.debug(
                    ("Processor::_get_optional_nodes:  Element <{}>{} is unknown in"
                     + " the data!"
                    ).format(segment_type, unstripped_attrs)
                )
                if isinstance(data, list):
                    self.logger.debug(
                        "Processor::_get_optional_nodes:  Dealing with a list"
                    )
                    if segment_type is PathSegmentTypes.ANCHOR:
                        new_val = self.default_for_child(yaml_path, depth + 1,
                            value)
                        new_ele = self.append_list_element(data, new_val,
                            stripped_attrs)
                        for node in self._get_optional_nodes(new_ele,
                                yaml_path, value, depth + 1):
                            matched_nodes += 1
                            yield node
                    elif (
                        segment_type is PathSegmentTypes.INDEX
                        and isinstance(stripped_attrs, int)
                    ):
                        for _ in range(len(data) - 1, stripped_attrs):
                            new_val = self.default_for_child(yaml_path,
                                depth + 1, value)
                            self.append_list_element(data, new_val)
                        for node in self._get_optional_nodes(
                            data[stripped_attrs], yaml_path, value, depth + 1
                        ):
                            matched_nodes += 1
                            yield node
                    else:
                        raise YAMLPathException(
                            "Cannot add {} subreference to lists"
                            .format(str(segment_type))
                            , yaml_path
                            , unstripped_attrs
                        )
                elif isinstance(data, dict):
                    self.logger.debug(
                        "Processor::_get_optional_nodes:  Dealing with a dictionary"
                    )
                    if segment_type is PathSegmentTypes.ANCHOR:
                        raise NotImplementedError

                    if segment_type is PathSegmentTypes.KEY:
                        data[stripped_attrs] = self.default_for_child(
                            yaml_path, depth + 1, value
                        )
                        for node in self._get_optional_nodes(
                            data[stripped_attrs], yaml_path, value, depth + 1
                        ):
                            matched_nodes += 1
                            yield node
                    else:
                        raise YAMLPathException(
                            "Cannot add {} subreference to dictionaries"
                            .format(str(segment_type)),
                            yaml_path,
                            unstripped_attrs
                        )
                else:
                    raise YAMLPathException(
                        "Cannot add {} subreference to scalars".format(
                            str(segment_type)
                        ),
                        yaml_path,
                        unstripped_attrs
                    )

        else:
            self.logger.debug(
                ("Processor::_get_optional_nodes:  Finally returning data of type"
                 + " {}:"
                ).format(type(data))
            )
            self.logger.debug(data)

            yield data

    def _update_node(self, source_node: Any, value: Any,
                     value_format: YAMLValueFormats) -> None:
        """Recursively updates the value of a YAML Node and any references to it
        within the entire YAML data structure (Anchors and Aliases, if any).

        Positional Parameters:
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
    def default_for_child(yaml_path: Path, depth: int,
                          value: Any = None) -> Any:
        """Identifies and returns the most appropriate default value for the
        next entry in a YAML Path, should it not already exist.

        Positional Parameters:
          1. yaml_path (deque) The pre-parsed YAML Path to follow
          2. value (any) The final expected value for the final YAML Path entry

        Returns:  (any) The most appropriate default value

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
        """Appends a new element to an ruamel.yaml presented list, preserving
        any tailing comment for the former last element of the same list.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. value (any) The value of the element to append
          3. anchor (str) An Anchor or Alias name for the new element

        Returns:  (object) The newly appended element node

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
        """Wraps a value in one of the ruamel.yaml wrapper types.

        Positional Parameters:
          1. value (any) The value to wrap.

        Returns: (any) The wrapped value or the original value when a better
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
        """Duplicates a YAML Data node.

        Positional Parameters:
          1. node (object) The node to clone.

        Returns: (object) Clone of the given node
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
        """Creates a new data node given a value and its presumed format."""
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
                    "The requested value format is {}, but '{}' cannot be cast\
                     to a floating-point number.".format(valform, value)
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
                    "The requested value format is {}, but '{}' cannot be cast\
                     to an integer number.".format(valform, value)
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
