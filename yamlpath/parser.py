"""YAML Path parser.

Copyright 2018, 2019 William W. Kimball, Jr. MBA MSIS
"""
from collections import deque

from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import (
    PathSegmentTypes,
    PathSearchMethods,
)


class Parser:
    """Parse YAML Paths into iterable queue components."""

    # Cache parsed YAML Path results across instances to avoid repeated parsing
    _static_parsings = {}

    def __init__(self, logger):
        """Init this class.

        Positional Parameters:
          1. logger (ConsoleWriter) Instance of ConsoleWriter or any similar
             wrapper (say, around stdlib logging modules)

        Returns:  N/A

        Raises:  N/A
        """
        self.log = logger

    def str_path(self, yaml_path):
        """Returns the printable, user-friendly version of a YAML Path.

        Positional Parameters:
          1. yaml_path (any) The YAML Path to convert

        Returns:  (str) The stringified YAML Path

        Raises:  N/A
        """
        parsed_path = self.parse_path(yaml_path)
        add_dot = False
        ppath = ""

        for (ptype, element_id) in parsed_path:
            if ptype == PathSegmentTypes.KEY:
                if add_dot:
                    ppath += "."
                ppath += element_id.replace(".", "\\.")
            elif ptype == PathSegmentTypes.INDEX:
                ppath += "[" + str(element_id) + "]"
            elif ptype == PathSegmentTypes.ANCHOR:
                ppath += "[&" + element_id + "]"
            elif ptype == PathSegmentTypes.SEARCH:
                invert, method, attr, term = element_id
                ppath += (
                    "["
                    + str(attr)
                    + ("!" if invert else "")
                    + PathSearchMethods.to_operator(method)
                    + str(term).replace(" ", "\\ ")
                    + "]"
                )

            add_dot = True

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

        element_id = ""
        demarc_stack = []
        seeking_anchor_mark = yaml_path[0] == "&"
        escape_next = False
        element_type = PathSegmentTypes.KEY
        search_inverted = False
        search_method = None
        search_attr = ""

        for c in yaml_path:
            demarc_count = len(demarc_stack)

            if not escape_next and c == "\\":
                # Escape the next character
                escape_next = True
                continue

            elif (
                not escape_next
                and c == " "
                and ((demarc_count < 1) or (not demarc_stack[-1] in ["'", '"']))
            ):
                # Ignore unescaped, non-demarcated whitespace
                continue

            elif not escape_next and seeking_anchor_mark and c == "&":
                # Found an expected (permissible) ANCHOR mark
                seeking_anchor_mark = False
                element_type = PathSegmentTypes.ANCHOR
                continue

            elif not escape_next and c in ['"', "'"]:
                # Found a string demarcation mark
                if demarc_count > 0:
                    # Already appending to an ongoing demarcated value
                    if c == demarc_stack[-1]:
                        # Close a matching pair
                        demarc_stack.pop()
                        demarc_count -= 1

                        # Record the element_id when all pairs have closed
                        if demarc_count < 1:
                            path_elements.append((element_type, element_id))
                            element_id = ""
                            element_type = PathSegmentTypes.KEY
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

            elif not escape_next and c == "[":
                if element_id:
                    # Named list INDEX; record its predecessor element
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
                not escape_next
                and demarc_count > 0
                and demarc_stack[-1] == "["
                and c in ["=", "^", "$", "%", "!", ">", "<"]
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

                    continue

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
                not escape_next
                and demarc_count > 0
                and demarc_stack[-1] == "["
                and c == "]"
            ):
                # Store the INDEX or SEARCH parameters
                if element_type is PathSegmentTypes.INDEX:
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
                demarc_stack.pop()
                demarc_count -= 1
                continue

            elif not escape_next and demarc_count < 1 and c == ".":
                # Do not store empty elements
                if element_id:
                    path_elements.append((element_type, element_id))
                    element_id = ""

                element_type = PathSegmentTypes.KEY
                continue

            element_id += c
            seeking_anchor_mark = False
            escape_next = False

        # Check for mismatched demarcations
        if demarc_count > 0:
            raise YAMLPathException(
                "YAML path contains at least one unmatched demarcation mark",
                yaml_path
            )

        # Store the final element_id
        if element_id:
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
