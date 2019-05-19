"""YAML Path.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from collections import deque
from typing import List, Optional, Union

from yamlpath.wrappers import ConsolePrinter
from yamlpath.enums import (
    PathSegmentTypes,
    PathSearchMethods,
    PathSeperators,
)
from yamlpath.types import SearchTerms


class Path:
    """Encapsulate a YAML Path and its parsing logic.  This will keep track of:
      * the original, unparsed, and unmodified YAML Path;
      * its path seperator;
      * the unescaped, parsed representation of the YAML Path; and
      * the escaped, parsed representation of the YAML Path.

    Parsing operations are lazy and property setting smartly tiggers re-parsing
    only when necessary.
    """

    def __init__(self, logger: ConsolePrinter,
                 yaml_path: Union["Path", str] = "", **kwargs) -> None:
        """Init this class.

        Positional Parameters:
          1. logger (ConsolePrinter) Instance of ConsolePrinter or any subclass
             wrapper (say, around stdlib logging modules)

        Returns:  N/A

        Raises:  N/A
        """
        self.logger: ConsolePrinter = logger
        self._seperator: PathSeperators = kwargs.pop("pathsep",
                                                     PathSeperators.AUTO)
        self._original: str = ""
        self._unescaped: deque = deque()
        self._escaped: deque = deque()
        self._stringified: str = ""

        if isinstance(yaml_path, Path):
            self.original = yaml_path.original
        else:
            self.original = yaml_path

    def __str__(self) -> str:
        """Returns the printable, user-friendly version of a YAML Path.

        Positional Parameters:
          1. yaml_path (any) The YAML Path to convert

        Optional Parameters:
          1. pathsep (string) A PathSeperators value for controlling the YAML
             Path seperator

        Returns:  (str) The stringified YAML Path

        Raises:  N/A
        """
        if self._stringified:
            return self._stringified

        segments = self.unescaped
        pathsep = PathSeperators.to_seperator(self.seperator)
        add_sep = False
        ppath = ""

        # FSLASH seperator requires a path starting with a /
        if self.seperator is PathSeperators.FSLASH:
            ppath = "/"

        for (segment_type, segment_attrs) in segments:
            if segment_type == PathSegmentTypes.KEY:
                if add_sep:
                    ppath += pathsep

                ppath += (
                    segment_attrs
                    .replace(pathsep, "\\{}".format(pathsep))
                    .replace("&", r"\&")
                    .replace("[", r"\[")
                    .replace("]", r"\]")
                )
            elif segment_type == PathSegmentTypes.INDEX:
                ppath += "[{}]".format(segment_attrs)
            elif segment_type == PathSegmentTypes.ANCHOR:
                if add_sep:
                    ppath += "[&{}]".format(segment_attrs)
                else:
                    ppath += "&{}".format(segment_attrs)
            elif segment_type == PathSegmentTypes.SEARCH:
                ppath += str(segment_attrs)

            add_sep = True

        self._stringified = ppath
        return ppath

    def __repr__(self) -> str:
        """Generates an eval()-safe representation of this object."""
        return "{}('{}')".format(self.__class__.__name__, self._original)

    @property
    def original(self) -> str:
        """Original YAML Path accesor.

        Positional Parameters:  N/A

        Returns:  (str) The original, unparsed, unmodified YAML Path

        Raises:  N/A
        """
        return self._original

    @original.setter
    def original(self, value: str) -> None:
        """Original YAML Path mutator.

        Positional Parameters:
          1. value (str) A YAML Path in string form

        Returns:  N/A

        Raises:  N/A
        """
        # Check for empty paths
        if not str(value).strip():
            value = ""

        self._original = value
        self._seperator = PathSeperators.AUTO
        self._unescaped = deque()
        self._escaped = deque()
        self._stringified = ""

    @property
    def seperator(self) -> PathSeperators:
        """Accessor for the seperator used to demarcate YAML Path segments.

        Positional Parameters:  N/A

        Returns:  (PathSeperators) The segment demarcation symbol

        Raises:  N/A
        """
        if (self._seperator is PathSeperators.AUTO
                and self._original):
            if self._original[0] == '/':
                self._seperator = PathSeperators.FSLASH
            else:
                self._seperator = PathSeperators.DOT

        return self._seperator

    @seperator.setter
    def seperator(self, value: PathSeperators) -> None:
        """Mutator for the seperator used to demarcate YAML Path segments.
        This only affects __str__ and only when the new value differs from the
        seperator already inferred from the original YAML Path.

        Positional Parameters:
          1. value (PathSeperators) The segment demarcation symbol

        Returns:  N/A

        Raises:  N/A
        """
        old_value = self._seperator

        # Only build a new stringified version when this value changes
        if not value == old_value:
            self._seperator = value
            self._stringified = ""

    @property
    def escaped(self) -> deque:
        r"""Accessor for the escaped, parsed version of this YAML Path.  Any
        leading \ symbols are stripped out.  This is the parsed YAML Path used
        for processing YAML data.

        Positional Parameters:  N/A

        Returns:  (deque) The escaped, parsed version of this YAML Path

        Raises:  N/A
        """
        if not self._escaped:
            self._escaped = self._parse_path(True)

        return self._escaped.copy()

    @property
    def unescaped(self) -> deque:
        r"""Accessor for the unescaped, parsed version of this YAML Path.  Any
        leading \ symbols are preserved.  This is the print and log friendly
        version of the parsed YAML Path.

        Positional Parameters:  N/A

        Returns:  (deque) The unescaped, parsed version of this YAML Path

        Raises:  N/A
        """
        if not self._unescaped:
            self._unescaped = self._parse_path(False)

        return self._unescaped.copy()

    def _parse_path(self, strip_escapes: bool = True) -> deque:
        r"""Breaks apart a stringified YAML Path into component segments, each
        identified by its type.  See README.md for sample YAML Paths.

        Positional Parameters:
          1. strip_escapes (bool) True = Remove leading \ symbols, leaving only
             the "escaped" symbol.  False = Leave all leading \ symbols intact.

        Returns:  (deque) an empty queue or a queue of tuples, each identifying
          (PathSegmentTypes, segment_attributes).

        Raises:
          YAMLPathException when yaml_path is invalid
        """
        from yamlpath.exceptions import YAMLPathException

        yaml_path: str = self.original
        path_segments: deque = deque()
        segment_id: str = ""
        segment_type: Optional[PathSegmentTypes] = None
        demarc_stack: List[str] = []
        escape_next: bool = False
        search_inverted: bool = False
        search_method: Optional[PathSearchMethods] = None
        search_attr: str = ""
        seeking_regex_delim: bool = False
        capturing_regex: bool = False
        pathsep: str = PathSeperators.to_seperator(self.seperator)

        self.logger.debug(
            "Path::_parse_path:  Evaluating {}...".format(yaml_path)
        )

        # Empty paths yield empty queues
        if not yaml_path:
            return path_segments

        # Infer the first possible position for a top-level Anchor mark
        first_anchor_pos = 0
        if self.seperator is PathSeperators.FSLASH:
            first_anchor_pos = 1
        seeking_anchor_mark = yaml_path[first_anchor_pos] == "&"

        # Parse the YAML Path
        for char in yaml_path:
            demarc_count = len(demarc_stack)

            if escape_next:
                # Pass-through; capture this escaped character
                escape_next = False

            elif capturing_regex:
                if char == demarc_stack[-1]:
                    # Stop the RegEx capture
                    capturing_regex = False
                    demarc_stack.pop()
                    continue
                else:
                    # Pass-through; capture everything that isn't the present
                    # RegEx delimiter.  This deliberately means users cannot
                    # escape the RegEx delimiter itself should it occur within
                    # the RegEx; thus, users must select a delimiter that won't
                    # appear within the RegEx (which is exactly why the user
                    # gets to choose the delimiter).
                    pass  # pragma: no cover

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
                and (
                    (demarc_count < 1)
                    or (not demarc_stack[-1] in ["'", '"'])
                )
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

            elif demarc_count == 0 and char == "[":
                # Array INDEX/SLICE or SEARCH
                if segment_id:
                    # Record its predecessor element; unless it has already
                    # been identified as a special type, assume it is a KEY.
                    if segment_type is None:
                        segment_type = PathSegmentTypes.KEY
                    path_segments.append((segment_type, segment_id))
                    segment_id = ""

                demarc_stack.append(char)
                demarc_count += 1
                segment_type = PathSegmentTypes.INDEX
                seeking_anchor_mark = True
                search_inverted = False
                search_method = None
                search_attr = ""
                continue

            elif (
                demarc_count > 0
                and demarc_stack[-1] == "["
                and char in ["=", "^", "$", "%", "!", ">", "<", "~"]
            ):
                # Hash attribute search
                if char == "!":
                    if search_inverted:
                        raise YAMLPathException(
                            "Double search inversion is meaningless at {}"
                            .format(char)
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
                            raise YAMLPathException(
                                "Missing search operand before operator, {}"
                                .format(char)
                                , yaml_path
                            )
                    else:
                        raise YAMLPathException(
                            "Unsupported search operator combination at {}"
                            .format(char)
                            , yaml_path
                        )

                    continue  # pragma: no cover

                elif char == "~":
                    if search_method == PathSearchMethods.EQUALS:
                        search_method = PathSearchMethods.REGEX
                        seeking_regex_delim = True
                    else:
                        raise YAMLPathException(
                            ("Unexpected use of {} operator.  Please try =~ if"
                                + " you mean to search with a Regular"
                                + " Expression."
                            ).format(char)
                            , yaml_path
                        )

                    continue  # pragma: no cover

                elif not segment_id:
                    # All tests beyond this point require an operand
                    raise YAMLPathException(
                        "Missing search operand before operator, {}"
                        .format(char)
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

            elif (
                demarc_count > 0
                and char == "]"
                and demarc_stack[-1] == "["
            ):
                # Store the INDEX, SLICE, or SEARCH parameters
                if (
                    segment_type is PathSegmentTypes.INDEX
                    and ':' not in segment_id
                ):
                    try:
                        idx = int(segment_id)
                    except ValueError:
                        raise YAMLPathException(
                            "Not an integer index:  {}".format(segment_id)
                            , yaml_path
                        )
                    path_segments.append((segment_type, idx))
                elif (segment_type is PathSegmentTypes.SEARCH
                        and search_method is not None):
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
                else:
                    path_segments.append((segment_type, segment_id))

                segment_id = ""
                segment_type = None
                demarc_stack.pop()
                demarc_count -= 1
                search_method = None
                continue

            elif demarc_count < 1 and char == pathsep:
                # Do not store empty elements
                if segment_id:
                    # Unless its type has already been identified as a special
                    # type, assume it is a KEY.
                    if segment_type is None:
                        segment_type = PathSegmentTypes.KEY
                    path_segments.append((segment_type, segment_id))
                    segment_id = ""

                segment_type = None
                continue

            segment_id += char
            seeking_anchor_mark = False

        # Check for unterminated RegExes
        if capturing_regex:
            raise YAMLPathException(
                "YAML Path contains an unterminated Regular Expression.",
                yaml_path
            )

        # Check for mismatched demarcations
        if demarc_count > 0:
            raise YAMLPathException(
                "YAML Path contains at least one unmatched demarcation mark",
                yaml_path
            )

        # Store the final element_id, which must have been a KEY
        if segment_id:
            # Unless its type has already been identified as a special
            # type, assume it is a KEY.
            if segment_type is None:
                segment_type = PathSegmentTypes.KEY
            path_segments.append((segment_type, segment_id))

        self.logger.debug(
            "Path::_parse_path:  Parsed {} into:".format(yaml_path)
        )
        self.logger.debug(path_segments)

        return path_segments