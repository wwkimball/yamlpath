"""
Implement YAML Path.

Copyright 2019, 2020, 2021 William W. Kimball, Jr. MBA MSIS
"""
from collections import deque
from typing import Deque, List, Optional, Union

from yamlpath.types import PathAttributes, PathSegment
from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import (
    PathSegmentTypes,
    PathSearchKeywords,
    PathSearchMethods,
    PathSeperators,
    CollectorOperators,
)
from yamlpath.path import SearchKeywordTerms, SearchTerms, CollectorTerms


class YAMLPath:
    """
    Encapsulate a YAML Path and its parsing logic.

    This will keep track of:
      * the original, unparsed, and unmodified YAML Path;
      * its segment seperator (inferred or manually specified);
      * the unescaped, parsed representation of the YAML Path; and
      * the escaped, parsed representation of the YAML Path.

    Parsing operations are lazy and property setting smartly tiggers re-parsing
    only when necessary.
    """

    def __init__(self, yaml_path: Union["YAMLPath", str, None] = "",
                 pathsep: PathSeperators = PathSeperators.AUTO) -> None:
        """
        Instantiate this class into an object.

        Parameters:
        1. yaml_path (Union["YAMLPath", str, None]) The YAML Path to parse or
           copy
        2. pathsep (PathSeperators) Forced YAML Path segment separator; set
           only when automatic inference fails

        Returns:  N/A

        Raises:  N/A
        """
        self._seperator: PathSeperators = pathsep
        self._original: str = ""
        self._unescaped: deque = deque()
        self._escaped: deque = deque()
        self._stringified: str = ""

        if isinstance(yaml_path, YAMLPath):
            self.original = yaml_path.original
        else:
            self.original = "" if yaml_path is None else yaml_path

    def __str__(self) -> str:
        """Get a stringified version of this object."""
        if self._stringified:
            return self._stringified

        self._stringified = YAMLPath._stringify_yamlpath_segments(
            self.unescaped, self.seperator)
        return self._stringified

    def __repr__(self) -> str:
        """Generate an eval()-safe representation of this object."""
        return ("{}('{}', '{}')".format(self.__class__.__name__,
                                        self.original, self.seperator))

    def __len__(self) -> int:
        """Indicate how many segments comprise this YAML Path."""
        return len(self.escaped)

    def __eq__(self, other: object) -> bool:
        """
        Indicate equivalence of two YAMLPaths.

        The path seperator is ignored for this comparison.  This is deliberate
        and allows "some.path[1]" == "/some/path[1]" because both forms of the
        same path yield exactly the same data.

        Parameters:
        1. other (object) The other YAMLPath to compare against.

        Returns:  (bool) true = Both are identical; false, otherwise
        """
        if not isinstance(other, (YAMLPath, str)):
            return False

        equiv_this = YAMLPath(self)
        equiv_this.seperator = PathSeperators.FSLASH
        cmp_this = str(equiv_this)

        equiv_that = YAMLPath(other)
        equiv_that.seperator = PathSeperators.FSLASH
        cmp_that = str(equiv_that)

        return cmp_this == cmp_that

    def __ne__(self, other: object) -> bool:
        """Indicate non-equivalence of two YAMLPaths."""
        return not self == other

    def __add__(self, other: object) -> "YAMLPath":
        """Add a nonmutating -- pre-escaped -- path segment."""
        next_segment = str(other) if not isinstance(other, str) else other
        return YAMLPath(self).append(next_segment)

    def append(self, segment: str) -> "YAMLPath":
        """
        Append a new -- pre-escaped -- segment to this YAML Path.

        Parameters:
        1. segment (str) The new -- pre-escaped -- segment to append to this
           YAML Path.  Do NOT include any seperator with this value; it will be
           added for you.

        Returns:  (YAMLPath) The adjusted YAMLPath
        """
        seperator = (
            PathSeperators.FSLASH
            if self.seperator is PathSeperators.AUTO
            else self.seperator)
        if len(self._original) < 1:
            self.original = segment
        else:
            self.original += "{}{}".format(seperator, segment)
        return self

    def pop(self) -> PathSegment:
        """
        Pop the last segment off this YAML Path.

        This mutates the YAML Path and returns the removed segment PathSegment.

        Returns:  (PathSegment) The removed segment
        """
        segments: Deque[PathSegment] = self.unescaped
        if len(segments) < 1:
            raise YAMLPathException(
                "Cannot pop when there are no segments to pop from",
                str(self))

        popped_queue: Deque = deque()
        popped_segment: PathSegment = segments.pop()
        popped_queue.append(popped_segment)
        removable_segment = YAMLPath._stringify_yamlpath_segments(
            popped_queue, self.seperator)
        prefixed_segment = "{}{}".format(self.seperator, removable_segment)
        path_now = self.original

        if path_now.endswith(prefixed_segment):
            self.original = path_now[0:len(path_now) - len(prefixed_segment)]
        elif path_now.endswith(removable_segment):
            self.original = path_now[0:len(path_now) - len(removable_segment)]
        elif (
            self.seperator == PathSeperators.FSLASH
            and path_now.endswith(removable_segment[1:])
        ):
            self.original = path_now[
                0:len(path_now) - len(removable_segment) + 1]

        return popped_segment

    @property
    def is_root(self) -> bool:
        """Indicate whether this YAML Path points at the document root."""
        return len(self.escaped) == 0

    @property
    def original(self) -> str:
        """
        Original YAML Path accessor.

        Positional Parameters:  N/A

        Returns:  (str) The original, unparsed, unmodified YAML Path

        Raises:  N/A
        """
        return self._original

    @original.setter
    def original(self, value: str) -> None:
        """
        Original YAML Path mutator.

        Parameters:
        1. value (str) A YAML Path in string form

        Returns:  N/A

        Raises:  N/A
        """
        str_val = str(value)

        # Check for empty paths
        if not str_val.strip():
            str_val = ""

        self._original = str_val
        self._seperator = PathSeperators.AUTO
        self._unescaped = deque()
        self._escaped = deque()
        self._stringified = ""

    @property
    def seperator(self) -> PathSeperators:
        """
        Get the seperator used to demarcate YAML Path segments.

        Parameters:  N/A

        Returns:  (PathSeperators) The segment demarcation symbol

        Raises:  N/A
        """
        if self._seperator is PathSeperators.AUTO:
            self._seperator = PathSeperators.infer_seperator(self._original)

        return self._seperator

    @seperator.setter
    def seperator(self, value: PathSeperators) -> None:
        """
        Set the seperator used to demarcate YAML Path segments.

        This only affects __str__ and only when the new value differs from the
        seperator already inferred from the original YAML Path.

        Parameters:
        1. value (PathSeperators) The segment demarcation symbol

        Returns:  N/A

        Raises:  N/A
        """
        old_value: PathSeperators = self._seperator

        # This changes only the stringified representation
        if not value == old_value:
            self._stringified = YAMLPath._stringify_yamlpath_segments(
                self.unescaped, value)
            self._seperator = value

    @property
    def escaped(self) -> Deque[PathSegment]:
        r"""
        Get the escaped, parsed version of this YAML Path.

        Any leading \ symbols are stripped out.  This is the parsed YAML Path
        used for processing YAML data.

        Parameters:  N/A

        Returns:  (deque) The escaped, parsed version of this YAML Path

        Raises:  N/A
        """
        if not self._escaped:
            self._escaped = self._parse_path(True)

        return self._escaped.copy()

    @property
    def unescaped(self) -> Deque[PathSegment]:
        r"""
        Get the unescaped, parsed version of this YAML Path.

        Any leading \ symbols are preserved.  This is the print and log
        friendly version of the parsed YAML Path.

        Parameters:  N/A

        Returns:  (deque) The unescaped, parsed version of this YAML Path

        Raises:  N/A
        """
        if not self._unescaped:
            self._unescaped = self._parse_path(False)

        return self._unescaped.copy()

    # pylint: disable=locally-disabled,too-many-locals,too-many-branches,too-many-statements
    def _parse_path(self,
                    strip_escapes: bool = True
                   ) -> Deque[PathSegment]:
        r"""
        Parse the YAML Path into its component PathSegment tuples.

        Breaks apart a stringified YAML Path into component segments, each
        identified by its type.  See README.md for sample YAML Paths.

        Parameters:
        1. strip_escapes (bool) True = Remove leading \ symbols, leaving
           only the "escaped" symbol.  False = Leave all leading \ symbols
           intact.

        Returns:  (Deque[PathSegment]) an empty queue or a queue of
            PathSegments.

        Raises:
            - `YAMLPathException` when the YAML Path is invalid
        """
        yaml_path: str = self.original
        path_segments: deque = deque()
        segment_id: str = ""
        segment_type: Optional[PathSegmentTypes] = None
        demarc_stack: List[str] = []
        escape_next: bool = False
        search_inverted: bool = False
        search_method: Optional[PathSearchMethods] = None
        search_attr: str = ""
        search_keyword: Optional[PathSearchKeywords] = None
        seeking_regex_delim: bool = False
        capturing_regex: bool = False
        pathsep: str = str(self.seperator)
        collector_level: int = 0
        collector_operator: CollectorOperators = CollectorOperators.NONE
        seeking_collector_operator: bool = False
        next_char_must_be: Optional[str] = None

        # Empty paths yield empty queues
        if not yaml_path:
            return path_segments

        # Infer the first possible position for a top-level Anchor mark
        first_anchor_pos = 0
        if self.seperator is PathSeperators.FSLASH and len(yaml_path) > 1:
            first_anchor_pos = 1
        seeking_anchor_mark = yaml_path[first_anchor_pos] == "&"

        # Parse the YAML Path
        # pylint: disable=locally-disabled,too-many-nested-blocks
        for char_idx, char in enumerate(yaml_path):
            demarc_count = len(demarc_stack)
            if next_char_must_be and char == next_char_must_be:
                next_char_must_be = None

            if escape_next:
                # Pass-through; capture this escaped character
                escape_next = False

            elif capturing_regex:
                # Pass-through; capture everything that isn't the present
                # RegEx delimiter.  This deliberately means users cannot
                # escape the RegEx delimiter itself should it occur within
                # the RegEx; thus, users must select a delimiter that won't
                # appear within the RegEx (which is exactly why the user
                # gets to choose the delimiter).
                if char == demarc_stack[-1]:
                    # Stop the RegEx capture
                    capturing_regex = False
                    demarc_stack.pop()
                    continue

            # The escape test MUST come AFTER the RegEx capture test so users
            # won't be forced into "The Backslash Plague".
            # (https://docs.python.org/3/howto/regex.html#the-backslash-plague)
            elif char == "\\":
                # Escape the next character
                escape_next = True
                if strip_escapes:
                    continue

            elif (
                    char == " "
                    and (demarc_count < 1
                         or demarc_stack[-1] not in ["'", '"'])
            ):
                # Ignore unescaped, non-demarcated whitespace
                continue

            elif seeking_regex_delim:
                # This first non-space symbol is now the RegEx delimiter
                seeking_regex_delim = False
                capturing_regex = True
                demarc_stack.append(char)
                demarc_count += 1
                continue

            elif seeking_anchor_mark and char == "&":
                # Found an expected (permissible) ANCHOR mark
                seeking_anchor_mark = False
                segment_type = PathSegmentTypes.ANCHOR
                continue

            elif seeking_collector_operator and char in ['+', '-']:
                seeking_collector_operator = False
                next_char_must_be = '('
                if char == '+':
                    collector_operator = CollectorOperators.ADDITION
                elif char == '-':
                    collector_operator = CollectorOperators.SUBTRACTION
                continue

            elif next_char_must_be and char != next_char_must_be:
                raise YAMLPathException((
                    "Invalid YAML Path at character index {}, \"{}\", which"
                    " must be \"{}\" in YAML Path")
                    .format(char_idx, char, next_char_must_be), yaml_path)

            elif char in ['"', "'"]:
                # Found a string demarcation mark
                if demarc_count > 0:
                    # Already appending to an ongoing demarcated value
                    if char == demarc_stack[-1]:
                        # Close a matching pair
                        demarc_stack.pop()
                        demarc_count -= 1

                        # Record the element_id when all pairs have closed
                        # unless there is no element_id.
                        if demarc_count < 1:
                            if segment_id:
                                # Unless the element has already been
                                # identified as a special type, assume it is a
                                # KEY.
                                if segment_type is None:
                                    segment_type = PathSegmentTypes.KEY
                                path_segments.append(
                                    (segment_type, segment_id))

                            segment_id = ""
                            segment_type = None
                            continue
                    else:
                        # Embed a nested, demarcated component
                        demarc_stack.append(char)
                        demarc_count += 1
                else:
                    # Fresh demarcated value
                    demarc_stack.append(char)
                    demarc_count += 1
                    continue

            elif char == "(":
                if (demarc_count == 1
                    and demarc_stack[-1] == "["
                    and segment_id
                ):
                    if PathSearchKeywords.is_keyword(segment_id):
                        demarc_stack.append(char)
                        demarc_count += 1
                        segment_type = PathSegmentTypes.KEYWORD_SEARCH
                        search_keyword = PathSearchKeywords[segment_id.upper()]
                        segment_id = ""
                        continue

                    raise YAMLPathException((
                        "Unknown Search Keyword at character index {},"
                        " \"{}\"; allowed: {}.  Encountered in YAML Path")
                        .format(char_idx - len(segment_id), segment_id,
                            ', '.join(PathSearchKeywords.get_keywords())
                        )
                        , yaml_path
                    )

                if collector_level == 0 and segment_id:
                    # Record its predecessor element; unless it has already
                    # been identified as a special type, assume it is a KEY.
                    if segment_type is None:
                        segment_type = PathSegmentTypes.KEY
                    path_segments.append(self._expand_splats(
                        yaml_path, segment_id, segment_type))
                    segment_id = ""

                seeking_collector_operator = False
                collector_level += 1
                demarc_stack.append(char)
                demarc_count += 1
                segment_type = PathSegmentTypes.COLLECTOR

                # Preserve nested collectors
                if collector_level == 1:
                    continue

            elif (
                    demarc_count > 0
                    and char == ")"
                    and segment_type is PathSegmentTypes.KEYWORD_SEARCH
            ):
                demarc_count -= 1
                demarc_stack.pop()
                next_char_must_be = "]"
                seeking_collector_operator = False
                continue

            elif (
                    demarc_count > 0
                    and char == ")"
                    and demarc_stack[-1] == "("
                    and collector_level > 0
            ):
                collector_level -= 1
                demarc_count -= 1
                demarc_stack.pop()

                if collector_level < 1:
                    path_segments.append(
                        (segment_type,
                            CollectorTerms(segment_id, collector_operator)))
                    segment_id = ""
                    collector_operator = CollectorOperators.NONE
                    seeking_collector_operator = True
                    continue

            elif demarc_count == 0 and char == "[":
                # Array INDEX/SLICE or SEARCH
                if segment_id:
                    # Record its predecessor element; unless it has already
                    # been identified as a special type, assume it is a KEY.
                    if segment_type is None:
                        segment_type = PathSegmentTypes.KEY
                    path_segments.append(self._expand_splats(
                        yaml_path, segment_id, segment_type))
                    segment_id = ""

                demarc_stack.append(char)
                demarc_count += 1
                segment_type = PathSegmentTypes.INDEX
                seeking_collector_operator = False
                seeking_anchor_mark = True
                search_inverted = False
                search_method = None
                search_attr = ""
                continue

            elif (
                    demarc_count == 1
                    and demarc_stack[-1] == "["
                    and char in ["=", "^", "$", "%", "!", ">", "<", "~"]
            ):
                # Hash attribute search
                # pylint: disable=no-else-continue
                if char == "!":
                    if search_inverted:
                        raise YAMLPathException((
                            "Double search inversion is meaningless at"
                            " character index {}, {}")
                            .format(char_idx, char)
                            , yaml_path
                        )

                    # Invert the search
                    search_inverted = True
                    continue

                elif char == "=":
                    # Exact value match OR >=|<=
                    segment_type = PathSegmentTypes.SEARCH

                    if search_method is PathSearchMethods.LESS_THAN:
                        search_method = PathSearchMethods.LESS_THAN_OR_EQUAL
                    elif search_method is PathSearchMethods.GREATER_THAN:
                        search_method = PathSearchMethods.GREATER_THAN_OR_EQUAL
                    elif search_method is PathSearchMethods.EQUALS:
                        # Allow ==
                        continue
                    elif search_method is None:
                        search_method = PathSearchMethods.EQUALS

                        if segment_id:
                            search_attr = segment_id
                            segment_id = ""
                        else:
                            raise YAMLPathException((
                                "Missing search operand before operator at"
                                " character index {}, \"{}\"")
                                .format(char_idx, char)
                                , yaml_path
                            )
                    else:
                        raise YAMLPathException((
                            "Unsupported search operator combination at"
                            " character index {}, \"{}\"")
                            .format(char_idx, char)
                            , yaml_path
                        )

                    continue  # pragma: no cover

                elif char == "~":
                    if search_method == PathSearchMethods.EQUALS:
                        search_method = PathSearchMethods.REGEX
                        seeking_regex_delim = True
                    else:
                        raise YAMLPathException((
                            "Unexpected use of \"{}\" operator at character"
                            " index {}.  Please try =~ if you mean to search"
                            " with a Regular Expression."
                            ).format(char, char_idx)
                            , yaml_path
                        )

                    continue  # pragma: no cover

                elif not segment_id:
                    # All tests beyond this point require an operand
                    raise YAMLPathException((
                        "Missing search operand before operator, \"{}\" at"
                        " character index, {}")
                        .format(char, char_idx)
                        , yaml_path
                    )

                elif char == "^":
                    # Value starts with
                    segment_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.STARTS_WITH
                    if segment_id:
                        search_attr = segment_id
                        segment_id = ""
                    continue

                elif char == "$":
                    # Value ends with
                    segment_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.ENDS_WITH
                    if segment_id:
                        search_attr = segment_id
                        segment_id = ""
                    continue

                elif char == "%":
                    # Value contains
                    segment_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.CONTAINS
                    if segment_id:
                        search_attr = segment_id
                        segment_id = ""
                    continue

                elif char == ">":
                    # Value greater than
                    segment_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.GREATER_THAN
                    if segment_id:
                        search_attr = segment_id
                        segment_id = ""
                    continue

                elif char == "<":
                    # Value less than
                    segment_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.LESS_THAN
                    if segment_id:
                        search_attr = segment_id
                        segment_id = ""
                    continue

            elif char == "[":
                # Track bracket nesting
                demarc_stack.append(char)
                demarc_count += 1

            elif (
                    demarc_count == 1
                    and char == "]"
                    and demarc_stack[-1] == "["
            ):
                # Store the INDEX, SLICE, SEARCH, or KEYWORD_SEARCH parameters
                if (
                        segment_type is PathSegmentTypes.INDEX
                        and ':' not in segment_id
                ):
                    try:
                        idx = int(segment_id)
                    except ValueError as wrap_ex:
                        raise YAMLPathException((
                            "Not an integer index at character index {}:  {}")
                            .format(char_idx, segment_id)
                            , yaml_path
                            , segment_id
                        ) from wrap_ex
                    path_segments.append((segment_type, idx))
                elif (
                        segment_type is PathSegmentTypes.SEARCH
                        and search_method is not None
                ):
                    # Undemarcate the search term, if it is so
                    if segment_id and segment_id[0] in ["'", '"']:
                        leading_mark = segment_id[0]
                        if segment_id[-1] == leading_mark:
                            segment_id = segment_id[1:-1]

                    path_segments.append((
                        segment_type,
                        SearchTerms(search_inverted, search_method,
                                    search_attr, segment_id)
                    ))
                elif (
                    segment_type is PathSegmentTypes.KEYWORD_SEARCH
                    and search_keyword
                ):
                    path_segments.append((
                        segment_type,
                        SearchKeywordTerms(search_inverted, search_keyword,
                                           segment_id)
                    ))
                else:
                    path_segments.append((segment_type, segment_id))

                segment_id = ""
                segment_type = None
                demarc_stack.pop()
                demarc_count -= 1
                search_method = None
                search_inverted = False
                search_keyword = None
                continue

            elif char == "]":
                # Track bracket de-nesting
                demarc_stack.pop()
                demarc_count -= 1

            elif demarc_count < 1 and char == pathsep:
                # Do not store empty elements
                if segment_id:
                    # Unless its type has already been identified as a special
                    # type, assume it is a KEY.
                    if segment_type is None:
                        segment_type = PathSegmentTypes.KEY
                    path_segments.append(self._expand_splats(
                        yaml_path, segment_id, segment_type))
                    segment_id = ""

                segment_type = None
                seeking_anchor_mark = True
                continue

            segment_id += char
            seeking_anchor_mark = False
            seeking_collector_operator = False

        # Check for unmatched subpath demarcations
        if collector_level > 0:
            raise YAMLPathException(
                "YAML Path contains an unmatched () collector pair",
                yaml_path
            )

        # Check for unterminated RegExes
        if capturing_regex:
            raise YAMLPathException(
                "YAML Path contains an unterminated Regular Expression",
                yaml_path
            )

        # Check for mismatched demarcations
        if demarc_count > 0:
            raise YAMLPathException((
                "YAML Path contains at least one unmatched demarcation mark"
                " with remaining open marks, {} in"
                ).format(", ".join(demarc_stack)),
                yaml_path
            )

        # Store the final element_id, which must have been a KEY
        if segment_id:
            # Unless its type has already been identified as a special
            # type, assume it is a KEY.
            if segment_type is None:
                segment_type = PathSegmentTypes.KEY
            path_segments.append(self._expand_splats(
                yaml_path, segment_id, segment_type))

        return path_segments

    @staticmethod
    def _expand_splats(
        yaml_path: str, segment_id: PathAttributes,
        segment_type: PathSegmentTypes
    ) -> PathSegment:
        """
        Replace segment IDs with search operators when * is present.

        Parameters:
        1. yaml_path (str) The full YAML Path being processed.
        2. segment_id (str) The segment identifier to parse.
        3. segment_type (Optional[PathSegmentTypes]) Pending predetermined type
           of the segment under evaluation.

        Returns:  (PathSegment) Coallesced YAML Path segment.
        """
        coal_type: PathSegmentTypes = segment_type
        coal_value: PathAttributes = segment_id

        if isinstance(segment_id, str) and  '*' in segment_id:
            splat_count = segment_id.count("*")
            splat_pos = segment_id.index("*")
            segment_len = len(segment_id)
            if splat_count == 1:
                if segment_len == 1:
                    # /*/ -> [.=~/.*/]
                    coal_type = PathSegmentTypes.SEARCH
                    coal_value = SearchTerms(
                        False, PathSearchMethods.REGEX, ".", ".*")
                elif splat_pos == 0:
                    # /*text/ -> [.$text]
                    coal_type = PathSegmentTypes.SEARCH
                    coal_value = SearchTerms(
                        False, PathSearchMethods.ENDS_WITH, ".",
                        segment_id[1:])
                elif splat_pos == segment_len - 1:
                    # /text*/ -> [.^text]
                    coal_type = PathSegmentTypes.SEARCH
                    coal_value = SearchTerms(
                        False, PathSearchMethods.STARTS_WITH, ".",
                        segment_id[0:splat_pos])
                else:
                    # /te*xt/ -> [.=~/^te.*xt$/]
                    coal_type = PathSegmentTypes.SEARCH
                    coal_value = SearchTerms(
                        False, PathSearchMethods.REGEX, ".",
                        "^{}.*{}$".format(
                            segment_id[0:splat_pos],
                            segment_id[splat_pos + 1:]))
            elif splat_count == 2 and segment_len == 2:
                # Traversal operator
                coal_type = PathSegmentTypes.TRAVERSE
                coal_value = None
            elif splat_count > 1:
                # Multi-wildcard search
                search_term = "^"
                was_splat = False
                for char in segment_id:
                    if char == "*":
                        if was_splat:
                            raise YAMLPathException(
                                "The ** traversal operator has no meaning when"
                                " combined with other characters", yaml_path,
                                segment_id)
                        was_splat = True
                        search_term += ".*"
                    else:
                        was_splat = False
                        search_term += char
                search_term += "$"

                coal_type = PathSegmentTypes.SEARCH
                coal_value = SearchTerms(
                    False, PathSearchMethods.REGEX, ".", search_term)

        return (coal_type, coal_value)

    @staticmethod
    def _stringify_yamlpath_segments(
        segments: Deque[PathSegment], seperator: PathSeperators
    ) -> str:
        """Stringify segments of a YAMLPath."""
        pathsep: str = str(seperator)
        add_sep: bool = False
        ppath: str = ""

        # FSLASH seperator requires a path starting with a /
        if seperator is PathSeperators.FSLASH:
            ppath = pathsep

        for (segment_type, segment_attrs) in segments:
            if segment_type == PathSegmentTypes.KEY:
                if add_sep:
                    ppath += pathsep

                # Replace a subset of special characters to alert users to
                # potentially unintentional demarcation.
                ppath += YAMLPath.ensure_escaped(
                    str(segment_attrs),
                    pathsep,
                    '(', ')', '[', ']', '^', '$', '%', ' ', "'", '"'
                )
            elif segment_type == PathSegmentTypes.INDEX:
                ppath += "[{}]".format(segment_attrs)
            elif segment_type == PathSegmentTypes.ANCHOR:
                if add_sep:
                    ppath += "[&{}]".format(segment_attrs)
                else:
                    ppath += "&{}".format(segment_attrs)
            elif segment_type == PathSegmentTypes.KEYWORD_SEARCH:
                ppath += str(segment_attrs)
            elif (segment_type == PathSegmentTypes.SEARCH
                  and isinstance(segment_attrs, SearchTerms)):
                terms: SearchTerms = segment_attrs
                if (terms.method == PathSearchMethods.REGEX
                    and terms.attribute == "."
                    and terms.term == ".*"
                    and not terms.inverted
                ):
                    if add_sep:
                        ppath += pathsep
                    ppath += "*"
                else:
                    ppath += str(segment_attrs)
            elif segment_type == PathSegmentTypes.COLLECTOR:
                ppath += str(segment_attrs)
            elif segment_type == PathSegmentTypes.TRAVERSE:
                if add_sep:
                    ppath += pathsep
                ppath += "**"

            add_sep = True

        return ppath

    @staticmethod
    def strip_path_prefix(path: "YAMLPath", prefix: "YAMLPath") -> "YAMLPath":
        """
        Remove a prefix from a YAML Path.

        Parameters:
        1. path (YAMLPath) The path from which to remove the prefix.
        2. prefix (YAMLPath) The prefix to remove (except "/").

        Returns:  (YAMLPath) The trimmed YAML Path.
        """
        if prefix is None:
            return path

        prefix.seperator = PathSeperators.FSLASH
        if str(prefix) == "/":
            return path

        path.seperator = PathSeperators.FSLASH
        prefix_str = str(prefix)
        path_str = str(path)
        if path_str.startswith(prefix_str):
            path_str = path_str[len(prefix_str):]
            return YAMLPath(path_str)

        return path

    @staticmethod
    def ensure_escaped(value: str, *symbols: str) -> str:
        r"""
        Escape all instances of a symbol within a value.

        Ensures all instances of a symbol are escaped (via \) within a value.
        Multiple symbols can be processed at once.

        Parameters:
        1. value (str) The String in which to escape special characters
        2. *symbols (str) List of special characters to escape

        Returns:  (str) `value` with all `symbols` escaped
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

    @staticmethod
    def escape_path_section(section: str, pathsep: PathSeperators) -> str:
        """
        Escape all special symbols present within a YAML Path segment.

        Renders inert via escaping all symbols within a string which have
        special meaning to YAML Path.  The resulting string can be consumed as
        a YAML Path section without triggering unwanted additional processing.

        Parameters:
        1. section (str) The portion of a YAML Path segment to escape
        2. pathsep (PathSeperators) The YAML Path segment seperator symbol to
           also escape, when present

        Returns:  (str) `section` with all special symbols escaped
        """
        return YAMLPath.ensure_escaped(
            section,
            '\\', str(pathsep), '(', ')', '[', ']', '^', '$', '%',
            ' ', "'", '"'
        )
