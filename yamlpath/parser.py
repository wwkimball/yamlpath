"""YAML Path parser.

Copyright 2018, 2019 William W. Kimball, Jr. MBA MSIS
"""
from collections import deque

from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import (
    PathSegmentTypes,
    PathSearchMethods,
    PathSeperators,
)


class Parser:
    """Parse YAML Paths into iterable queue components."""

    # Cache parsed YAML Path results across instances to avoid repeated parsing
    _static_parsings = {}

    def __init__(self, logger, **kwargs):
        """Init this class.

        Positional Parameters:
          1. logger (ConsoleWriter) Instance of ConsoleWriter or any similar
             wrapper (say, around stdlib logging modules)

        Optional Parameters:
          1. pathsep (string) A PathSeperators value for controlling the YAML
             Path seperator

        Returns:  N/A

        Raises:  N/A
        """
        self.log = logger

        pathsep = kwargs.pop("pathsep", "auto")
        if isinstance(pathsep, PathSeperators):
            self.pathsep = pathsep
        else:
            try:
                self.pathsep = PathSeperators.from_str(pathsep)
            except NameError:
                raise YAMLPathException(
                    "Unknown YAML Path seperator, {}.".format(pathsep)
                    , pathsep
                )

    def _infer_pathsep(self, yaml_path):
        """Gets the most likely YAML Path seperator to use based on whether one
        has already been manually specified or from what can be inferred from a
        sample.

        Positional Parameters:
          1. yaml_path (any) The YAML Path to evaluate

        Returns:  (str) The stringified YAML Path seperator

        Raises:  N/A
        """
        seperator = '.'
        if self.pathsep is not PathSeperators.AUTO:
            seperator = PathSeperators.to_seperator(self.pathsep)
        elif not yaml_path:
            self.pathsep = PathSeperators.DOT
            seperator = '.'
        elif '/' == yaml_path[0]:
            self.pathsep = PathSeperators.FSLASH
            seperator = '/'

        return seperator

    def str_path(self, yaml_path, **kwargs):
        """Returns the printable, user-friendly version of a YAML Path.

        Positional Parameters:
          1. yaml_path (any) The YAML Path to convert

        Optional Parameters:
          1. pathsep (string) A PathSeperators value for controlling the YAML
             Path seperator

        Returns:  (str) The stringified YAML Path

        Raises:  N/A
        """
        parsed_path = self.parse_path(yaml_path)
        add_sep = False
        ppath = ""
        pathsep = kwargs.pop("pathsep", self._infer_pathsep(yaml_path))

        # FSLASH pathsep requires a path starting with a /
        if pathsep == '/':
            ppath = "/"

        for (ptype, element_id) in parsed_path:
            if ptype == PathSegmentTypes.KEY:
                if add_sep:
                    ppath += pathsep

                ppath += (
                    element_id
                    .replace(pathsep, "\\{}".format(pathsep))
                    .replace("&", r"\&")
                    .replace("[", r"\[")
                    .replace("]", r"\]")
                )
            elif ptype == PathSegmentTypes.INDEX:
                ppath += "[{}]".format(element_id)
            elif ptype == PathSegmentTypes.ANCHOR:
                if add_sep:
                    ppath += "[&{}]".format(element_id)
                else:
                    ppath += "&{}".format(element_id)
            elif ptype == PathSegmentTypes.SEARCH:
                invert, method, attr, term = element_id
                if method == PathSearchMethods.REGEX:
                    safe_term = "/{}/".format(term.replace("/", r"\/"))
                else:
                    safe_term = str(term).replace(" ", r"\ ")
                ppath += (
                    "["
                    + str(attr)
                    + ("!" if invert else "")
                    + PathSearchMethods.to_operator(method)
                    + safe_term
                    + "]"
                )

            add_sep = True

        return ppath

    def parse_path(self, yaml_path):
        r"""Breaks apart a stringified YAML Path into component elements, each
        identified by its type.  See README.md for sample YAML Paths.

        Positional Parameters:
          1. yaml_path (any) The stringified YAML Path to parse

        Returns:  (deque) an empty queue or a queue of tuples, each identifying
        (type, element) unless yaml_path is already a list or a deque.  If
        yaml_path is already a list, it is blindly converted into a deque and
        returned.  If yaml_path is already a deque, it is blindly returned
        as-is.

        Raises:
          YAMLPathException when yaml_path is invalid
        """
        self.log.debug(
            "Parser::parse_path:  Evaluating {}...".format(yaml_path)
        )

        path_elements = deque()

        if yaml_path is None:
            return path_elements
        elif isinstance(yaml_path, deque):
            return yaml_path
        elif isinstance(yaml_path, list):
            return deque(yaml_path)
        elif isinstance(yaml_path, dict):
            raise YAMLPathException(
                "YAML paths must be strings, queues, or lists",
                yaml_path
            )

        # Check for empty paths
        if not str(yaml_path).strip():
            return path_elements

        # Don't parse a path that has already been seen
        if yaml_path in Parser._static_parsings:
            return Parser._static_parsings[yaml_path].copy()

        # Infer the path seperator
        pathsep = self._infer_pathsep(yaml_path)
        first_anchor_pos = 0
        if pathsep == '/':
            first_anchor_pos = 1

        element_id = ""
        demarc_stack = []
        seeking_anchor_mark = yaml_path[first_anchor_pos] == "&"
        escape_next = False
        element_type = None
        search_inverted = False
        search_method = None
        search_attr = ""
        seeking_regex_delim = False
        capturing_regex = False

        for c in yaml_path:
            demarc_count = len(demarc_stack)

            if escape_next:
                # Pass-through; capture this escaped character
                pass

            elif capturing_regex:
                if c == demarc_stack[-1]:
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
            elif c == "\\":
                # Escape the next character
                escape_next = True
                continue

            elif (
                c == " "
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
                demarc_stack.append(c)
                demarc_count += 1
                continue

            elif seeking_anchor_mark and c == "&":
                # Found an expected (permissible) ANCHOR mark
                seeking_anchor_mark = False
                element_type = PathSegmentTypes.ANCHOR
                continue

            elif c in ['"', "'"]:
                # Found a string demarcation mark
                if demarc_count > 0:
                    # Already appending to an ongoing demarcated value
                    if c == demarc_stack[-1]:
                        # Close a matching pair
                        demarc_stack.pop()
                        demarc_count -= 1

                        # Record the element_id when all pairs have closed
                        # unless there is no element_id.
                        if demarc_count < 1:
                            if element_id:
                                # Unless the element has already been
                                # identified as a special type, assume it is a
                                # KEY.
                                if element_type is None:
                                    element_type = PathSegmentTypes.KEY
                                path_elements.append((element_type, element_id))

                            element_id = ""
                            element_type = None
                            continue
                    else:
                        # Embed a nested, demarcated component
                        demarc_stack.append(c)
                        demarc_count += 1
                else:
                    # Fresh demarcated value
                    demarc_stack.append(c)
                    demarc_count += 1
                    continue

            elif demarc_count == 0 and c == "[":
                # Array INDEX/SLICE or SEARCH
                if element_id:
                    # Record its predecessor element; unless it has already
                    # been identified as a special type, assume it is a KEY.
                    if element_type is None:
                        element_type = PathSegmentTypes.KEY
                    path_elements.append((element_type, element_id))
                    element_id = ""

                demarc_stack.append(c)
                demarc_count += 1
                element_type = PathSegmentTypes.INDEX
                seeking_anchor_mark = True
                search_inverted = False
                search_method = None
                search_attr = ""
                continue

            elif (
                demarc_count > 0
                and demarc_stack[-1] == "["
                and c in ["=", "^", "$", "%", "!", ">", "<", "~"]
            ):
                # Hash attribute search
                if c == "!":
                    if search_inverted:
                        raise YAMLPathException(
                            "Double search inversion is meaningless at {}"
                            .format(c)
                            , yaml_path
                        )

                    # Invert the search
                    search_inverted = True
                    continue

                elif c == "=":
                    # Exact value match OR >=|<=
                    element_type = PathSegmentTypes.SEARCH

                    if search_method is PathSearchMethods.LESS_THAN:
                        search_method = PathSearchMethods.LESS_THAN_OR_EQUAL
                    elif search_method is PathSearchMethods.GREATER_THAN:
                        search_method = PathSearchMethods.GREATER_THAN_OR_EQUAL
                    elif search_method is PathSearchMethods.EQUALS:
                        # Allow ==
                        continue
                    elif search_method is None:
                        search_method = PathSearchMethods.EQUALS

                        if element_id:
                            search_attr = element_id
                            element_id = ""
                        else:
                            raise YAMLPathException(
                                "Missing search operand before operator, {}"
                                .format(c)
                                , yaml_path
                            )
                    else:
                        raise YAMLPathException(
                            "Unsupported search operator combination at {}"
                            .format(c)
                            , yaml_path
                        )

                    continue  # pragma: no cover

                elif c == "~":
                    if search_method == PathSearchMethods.EQUALS:
                        search_method = PathSearchMethods.REGEX
                        seeking_regex_delim = True
                    else:
                        raise YAMLPathException(
                            ("Unexpected use of {} operator.  Please try =~ if"
                                + " you mean to search with a Regular"
                                + " Expression."
                            ).format(c)
                            , yaml_path
                        )

                    continue  # pragma: no cover

                elif not element_id:
                    # All tests beyond this point require an operand
                    raise YAMLPathException(
                        "Missing search operand before operator, {}".format(c)
                        , yaml_path
                    )

                elif c == "^":
                    # Value starts with
                    element_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.STARTS_WITH
                    if element_id:
                        search_attr = element_id
                        element_id = ""
                    continue

                elif c == "$":
                    # Value ends with
                    element_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.ENDS_WITH
                    if element_id:
                        search_attr = element_id
                        element_id = ""
                    continue

                elif c == "%":
                    # Value contains
                    element_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.CONTAINS
                    if element_id:
                        search_attr = element_id
                        element_id = ""
                    continue

                elif c == ">":
                    # Value greater than
                    element_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.GREATER_THAN
                    if element_id:
                        search_attr = element_id
                        element_id = ""
                    continue

                elif c == "<":
                    # Value less than
                    element_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.LESS_THAN
                    if element_id:
                        search_attr = element_id
                        element_id = ""
                    continue

            elif (
                demarc_count > 0
                and c == "]"
                and demarc_stack[-1] == "["
            ):
                # Store the INDEX, SLICE, or SEARCH parameters
                if (
                    element_type is PathSegmentTypes.INDEX
                    and ':' not in element_id
                ):
                    try:
                        idx = int(element_id)
                    except ValueError:
                        raise YAMLPathException(
                            "Not an integer index:  {}".format(element_id)
                            , yaml_path
                        )
                    path_elements.append((element_type, idx))
                elif element_type is PathSegmentTypes.SEARCH:
                    # Undemarcate the search term, if it is so
                    if element_id and element_id[0] in ["'", '"']:
                        leading_mark = element_id[0]
                        if element_id[-1] == leading_mark:
                            element_id = element_id[1:-1]

                    path_elements.append((
                        element_type,
                        [search_inverted,
                         search_method,
                         search_attr,
                         element_id]
                    ))
                else:
                    path_elements.append((element_type, element_id))

                element_id = ""
                element_type = None
                demarc_stack.pop()
                demarc_count -= 1
                search_method = None
                continue

            elif demarc_count < 1 and c == pathsep:
                # Do not store empty elements
                if element_id:
                    # Unless its type has already been identified as a special
                    # type, assume it is a KEY.
                    if element_type is None:
                        element_type = PathSegmentTypes.KEY
                    path_elements.append((element_type, element_id))
                    element_id = ""

                element_type = None
                continue

            element_id += c
            seeking_anchor_mark = False
            escape_next = False

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
        if element_id:
            # Unless its type has already been identified as a special
            # type, assume it is a KEY.
            if element_type is None:
                element_type = PathSegmentTypes.KEY
            path_elements.append((element_type, element_id))

        self.log.debug(
            "Parser::parse_path:  Parsed {} into:".format(yaml_path)
        )
        self.log.debug(path_elements)

        # Cache the parsed results
        Parser._static_parsings[yaml_path] = path_elements
        str_path = self.str_path(path_elements)
        if not str_path == yaml_path:
            # The stringified YAML Path differs from the user version but has
            # exactly the same parsed result, so cache it, too
            Parser._static_parsings[str_path] = path_elements

        return path_elements.copy()
