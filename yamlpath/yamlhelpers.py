"""Reusable YAML helpers.

Copyright 2018, 2019 William W. Kimball, Jr. MBA MSIS
"""
from sys import maxsize
from collections import deque
from distutils.util import strtobool

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

from .exceptions import YAMLPathException
from .enums import YAMLValueFormats, PathSearchMethods, PathSegmentTypes

class YAMLHelpers:
    """Collection of generally-useful YAML processing methods based on
    ruamel.yaml."""

    # Cache parsed YAML Path results across instances to avoid repeated parsing
    _static_parsings = {}

    def __init__(self, logger):
        """Init this class.

        Positional Parameters:
          1. logger (ConsoleWriter) Instance of ConsoleWriter

        Returns:  N/A

        Raises:  N/A
        """
        self.log = logger

    def get_nodes(self, data, yaml_path, mustexist=False, default_value=None):
        """Retrieves zero or more node at YAML Path in YAML data.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (any) The YAML Path to evaluate
          3. mustexist (Boolean) Indicate whether yaml_path must exist
             in data prior to this query (lest an Exception be raised);
             default=False
          4. default_value (any) The value to set at yaml_path should
             it not already exist in data and mustexist is False;
             default=None

        Returns:  (object) The requested YAML nodes as they are matched

        Raises:
            YAMLPathException when YAML Path is invalid
        """
        path = self._parse_path(yaml_path)
        if mustexist:
            matched_nodes = 0
            for node in self._get_nodes(data, path):
                if node is not None:
                    matched_nodes += 1
                    self.log.debug(
                        "YAMLHelpers::get_nodes:  Relaying required node:"
                    )
                    yield node

            if 1 > matched_nodes:
                raise YAMLPathException(
                    "Required YAML Path does not match any nodes",
                    self.str_path(yaml_path),
                    self.str_path(path)
                )
        else:
            for node in self._ensure_path(data, path, default_value):
                if node is not None:
                    self.log.debug(
                        "YAMLHelpers::get_nodes:  Relaying optional node:"
                    )
                    yield node

    def set_value(self, data, yaml_path, value, mustexist=False,
                  format=YAMLValueFormats.DEFAULT
    ):
        """Sets the value of zero or more nodes at YAML Path in YAML data.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (any) The YAML Path to evaluate
          3. value (any) The value to set
          4. mustexist (Boolean) Indicate whether yaml_path must exist
             in data prior to this query (lest an Exception be raised);
             default=False
          5. format (YAMLValueFormats) The demarcation or visual
             representation to use when writing the data;
             default=YAMLValueFormats.DEFAULT

        Returns:  N/A

        Raises:
            YAMLPathException when YAML Path is invalid
        """
        if data is None or yaml_path is None:
            return

        path = self._parse_path(yaml_path)
        if mustexist:
            self.log.debug(
                "YAMLHelpers::set_value:  Seeking required node at {}."
                    .format(self.str_path(path))
            )
            found_nodes = 0
            for node in self._get_nodes(data, path):
                if node is None:
                    continue

                found_nodes += 1
                self._update_value(data, node, value, format)

            if 1 > found_nodes:
                raise YAMLPathException(
                    "No nodes matched required YAML Path",
                    self.str_path(path)
                )
        else:
            self.log.debug(
                "YAMLHelpers::set_value:  Seeking optional node at {}."
                    .format(self.str_path(path))
            )
            for node in self._ensure_path(data, path, value):
                if node is None:
                    continue
                self._update_value(data, node, value, format)

    @staticmethod
    def clone_node(node):
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

    def str_path(self, yaml_path):
        """Returns the printable, user-friendly version of a YAML Path.

        Positional Parameters:
          1. yaml_path (any) The YAML Path to convert

        Returns:  (str) The stringified YAML Path

        Raises:  N/A
        """
        parsed_path = self._parse_path(yaml_path)
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

    def _parse_path(self, yaml_path):
        r"""Breaks apart a stringified YAML Path into component elements, each
        identified by its type.  Some non-exhaustive examples of valid YAML
        Paths include:

           1. bare_top_level_key
           2. namespaced::top_level_key
           3. dictionary.key
           4. dictionary.sub.key
           5. top_level_list[element_index]
           6. &top_level_anchor
           7. aliases[&anchored_element]
           8. dictionary.'with.dotted.subkey'
           9. dictionary."with.dotted.subkey"
          10. dictionary.with\.dottet\.subkey
          11. complex.structures.with[&many].nested."elements.in.any"[form]
          12. sensitive::accounts.application.db.users[name=admin].password.encrypted
          13. sensitive::accounts.application.db.users[name^adm].password.encrypted
          14. sensitive::accounts.application.db.users[name$in].password.encrypted
          15. sensitive::accounts.application.db.users[name%dmi].password.encrypted
          16. sensitive::accounts.application.db.users[name!=admin].password.encrypted
          17. sensitive::accounts.application.db.users[access_level>3].password.enabled
          18. sensitive::accounts.application.db.users[access_level<6].password.enabled
          19. sensitive::accounts.application.db.users[access_level<=5].password.enabled
          20. sensitive::accounts.application.db.users[access_level<=5].password.[encrypted!^ENC\[]

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
            "YAMLHelpers::_parse_path:  Evaluating {}...".format(yaml_path)
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
        if yaml_path in YAMLHelpers._static_parsings:
            return YAMLHelpers._static_parsings[yaml_path].copy()

        element_id = ""
        demarc_stack = []
        seeking_anchor_mark = "&" == yaml_path[0]
        escape_next = False
        element_type = PathSegmentTypes.KEY
        search_inverted = False
        search_method = PathSearchMethods.EQUALS
        search_attr = ""

        for c in yaml_path:
            demarc_count = len(demarc_stack)

            if not escape_next and "\\" == c:
                # Escape the next character
                escape_next = True
                continue

            elif (
                not escape_next
                and " " == c
                and ((1 > demarc_count) or (not demarc_stack[-1] in ["'", '"']))
            ):
                # Ignore unescaped, non-demarcated whitespace
                continue

            elif not escape_next and seeking_anchor_mark and "&" == c:
                # Found an expected (permissible) ANCHOR mark
                seeking_anchor_mark = False
                element_type = PathSegmentTypes.ANCHOR
                continue

            elif not escape_next and c in ['"', "'"]:
                # Found a string demarcation mark
                if 0 < demarc_count:
                    # Already appending to an ongoing demarcated value
                    if c == demarc_stack[-1]:
                        # Close a matching pair
                        demarc_stack.pop()
                        demarc_count -= 1

                        # Record the element_id when all pairs have closed
                        if 1 > demarc_count:
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

            elif not escape_next and "[" == c:
                if 0 < len(element_id):
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
                and 0 < demarc_count
                and "[" == demarc_stack[-1]
                and c in ["=", "^", "$", "%", "!", ">", "<"]
            ):
                # Hash attribute search
                if "=" == c:
                    # Exact value match OR >=|<=
                    element_type = PathSegmentTypes.SEARCH

                    if search_method is PathSearchMethods.LESS_THAN:
                        search_method = PathSearchMethods.LESS_THAN_OR_EQUAL
                    elif search_method is PathSearchMethods.GREATER_THAN:
                        search_method = PathSearchMethods.GREATER_THAN_OR_EQUAL
                    else:
                        search_method = PathSearchMethods.EQUALS
                        search_attr = element_id
                        element_id = ""

                    continue

                elif "^" == c:
                    # Value starts with
                    element_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.STARTS_WITH
                    search_attr = element_id
                    element_id = ""
                    continue

                elif "$" == c:
                    # Value ends with
                    element_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.ENDS_WITH
                    search_attr = element_id
                    element_id = ""
                    continue

                elif "%" == c:
                    # Value contains
                    element_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.CONTAINS
                    search_attr = element_id
                    element_id = ""
                    continue

                elif ">" == c:
                    # Value greater than
                    element_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.GREATER_THAN
                    search_attr = element_id
                    element_id = ""
                    continue

                elif "<" == c:
                    # Value less than
                    element_type = PathSegmentTypes.SEARCH
                    search_method = PathSearchMethods.LESS_THAN
                    search_attr = element_id
                    element_id = ""
                    continue

                elif "!" == c:
                    # Invert the search
                    search_inverted = True
                    continue

            elif (
                not escape_next
                and 0 < demarc_count
                and "[" == demarc_stack[-1]
                and "]" == c
            ):
                # Store the INDEX or SEARCH parameters
                if element_type is PathSegmentTypes.INDEX:
                    path_elements.append((element_type, int(element_id)))
                elif element_type is PathSegmentTypes.SEARCH:
                    # Undemarcate the search term, if it is so
                    if 0 < len(element_id) and element_id[0] in ["'", '"']:
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

            elif not escape_next and 1 > demarc_count and "." == c:
                # Do not store empty elements
                if 0 < len(element_id):
                    path_elements.append((element_type, element_id))
                    element_id = ""

                element_type = PathSegmentTypes.KEY
                continue

            element_id += c
            seeking_anchor_mark = False
            escape_next = False

        # Check for mismatched demarcations
        if 0 < demarc_count:
            raise YAMLPathException(
                "YAML path contains at least one unmatched demarcation mark",
                yaml_path
            )

        # Store the final element_id
        if 0 < len(element_id):
            path_elements.append((element_type, element_id))

        self.log.debug(
            "YAMLHelpers::_parse_path:  Parsed {} into:".format(yaml_path)
        )
        self.log.debug(path_elements)

        # Cache the parsed results
        YAMLHelpers._static_parsings[yaml_path] = path_elements
        str_path = self.str_path(path_elements)
        if not str_path == yaml_path:
            # The stringified YAML Path differs from the user version but has
            # exactly the same parsed result, so cache it, too
            YAMLHelpers._static_parsings[str_path] = path_elements

        return path_elements.copy()

    def _get_nodes(self, data, yaml_path):
        """Generates zero or more matching, pre-existing nodes from YAML data
        matching a YAML Path.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (deque) The pre-parsed YAML Path to follow

        Returns:  (object) The requested YAML nodes as they are matched or None

        Raises:  N/A
        """
        if data is None or yaml_path is None:
            return None

        if 0 < len(yaml_path):
            (typ, ele) = yaml_path.popleft()

            self.log.debug(
                ("YAMLHelpers::_get_nodes:  Peeking at element {} of type {} in"
                    + " data of type {}:"
                ).format(ele, typ, type(data))
            )
            self.log.debug(data)
            self.log.debug("")

            if PathSegmentTypes.KEY == typ:
                self.log.debug(
                    "YAMLHelpers::_get_nodes:  Drilling into the present"
                    + " dictionary KEY..."
                )
                if ele in data:
                    for node in self._get_nodes(data[ele], yaml_path):
                        if node is not None:
                            yield node
                else:
                    return None
            elif PathSegmentTypes.INDEX == typ:
                self.log.debug(
                    "YAMLHelpers::_get_nodes:  Drilling into the present list"
                     + " INDEX..."
                )
                if ele < len(data):
                    for node in self._get_nodes(data[ele], yaml_path):
                        if node is not None:
                            yield node
                else:
                    return None
            elif PathSegmentTypes.ANCHOR == typ:
                if isinstance(data, list):
                    self.log.debug(
                        "YAMLHelpers::_get_nodes:  Searching for an ANCHOR in"
                        + " a list..."
                    )
                    for e in data:
                        if hasattr(e, "anchor") and ele == e.anchor.value:
                            for node in self._get_nodes(e, yaml_path):
                                if node is not None:
                                    yield node
                elif isinstance(data, dict):
                    self.log.debug(
                        "YAMLHelpers::_get_nodes:  Searching for an ANCHOR in a"
                        + " dictionary..."
                    )
                    for _,v in data:
                        if hasattr(v, "anchor") and ele == v.anchor.value:
                            for node in self._get_nodes(v, yaml_path):
                                if node is not None:
                                    yield node
                return None
            elif PathSegmentTypes.SEARCH == typ:
                self.log.debug(
                    "YAMLHelpers::_get_nodes:  Performing an attribute"
                    + " SEARCH..."
                )
                for match in self._search(data, ele):
                    if match is None:
                        continue
                    else:
                        for node in self._get_nodes(match, yaml_path):
                            if node is not None:
                                yield node
                return None
            else:
                raise NotImplementedError

        self.log.debug(
            "YAMLHelpers::_get_nodes:  Finally returning data of type {}:"
                .format(type(data))
        )
        self.log.debug(data)
        self.log.debug("")

        yield data

    def _update_value(self, data, source_node, value, format):
        """Recursively updates the value of a YAML Node and any references to it
        within the entire YAML data structure (Anchors and Aliases, if any).

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. source_node (object) The YAML Node to update
          3. value (any) The new value to assign to the source_node and
             its references
          4. format (YAMLValueFormats) the YAML representation of the
             value

        Returns: N/A

        Raises:
          No Exception but it will terminate the program after printing
          a console error when format is illegal for the given value or
          is unknown.
        """
        # Change val has already been made to obj in data.  When obj is either
        # an Anchor or an Alias, all other references to it must also receive
        # an identical update so they are kept in synchronization.  In addition,
        # if obj is a child of a parent that is an Anchor or Alias, all
        # references to that parent must also be updated.
        def update_refs(data, reference_node, replacement_node):
            if isinstance(data, dict):
                for i, k in [
                    (idx, key) for idx, key in
                        enumerate(data.keys()) if key is reference_node
                ]:
                    data.insert(i, replacement_node, data.pop(k))
                for k, v in data.non_merged_items():
                    if v is reference_node:
                        data[k] = replacement_node
                    else:
                        update_refs(v, reference_node, replacement_node)
            elif isinstance(data, list):
                for idx, item in enumerate(data):
                    if item is reference_node:
                        data[idx] = replacement_node
                    else:
                        update_refs(item, reference_node, replacement_node)

        newtype = type(source_node)
        newval = value
        new_node = None
        valform = YAMLValueFormats.DEFAULT

        if isinstance(format, YAMLValueFormats):
            valform = format
        else:
            strform = str(format)
            try:
                valform = YAMLValueFormats.from_str(strform)
            except NameError:
                self.log.error(
                    "Unknown YAML value format:  {}".format(strform)
                    , 1
                )

        if valform == YAMLValueFormats.BARE:
            newtype = PlainScalarString
            newval = str(value)
        elif valform == YAMLValueFormats.DQUOTE:
            newtype = DoubleQuotedScalarString
            newval = str(value)
        elif valform == YAMLValueFormats.SQUOTE:
            newtype = SingleQuotedScalarString
            newval = str(value)
        elif valform == YAMLValueFormats.FOLDED:
            newtype = FoldedScalarString
            newval = str(value)
        elif valform == YAMLValueFormats.LITERAL:
            newtype = LiteralScalarString
            newval = str(value)
        elif valform == YAMLValueFormats.BOOLEAN:
            newtype = ScalarBoolean
            newval = strtobool(value)
        elif valform == YAMLValueFormats.FLOAT:
            try:
                newval = float(value)
            except ValueError:
                self.log.error(
                    "Not a floating-point precision number:  {}".format(value)
                    , 1
                )

            strval = str(value)
            precision = 0
            width = len(strval)
            lastdot = strval.rfind(".")
            if -1 < lastdot:
                precision = strval.rfind(".")

            if hasattr(source_node, "anchor"):
                new_node = ScalarFloat(
                    newval
                    , anchor=source_node.anchor.value
                    , prec=precision
                    , width=width
                )
            else:
                new_node = ScalarFloat(newval, prec=precision, width=width)
        elif valform == YAMLValueFormats.INT:
            newtype = ScalarInt

            try:
                newval = int(value)
            except ValueError:
                self.log.error("Not an integer:  {}".format(value), 1)

        if new_node is None:
            if hasattr(source_node, "anchor"):
                new_node = newtype(newval, anchor=source_node.anchor.value)
            else:
                new_node = newtype(newval)

        update_refs(data, source_node, new_node)

    def _get_elements_by_ref(self, data, ref):
        """Returns zero or more referenced YALM Nodes or None when the given
        reference points nowhere.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. ref (tuple(PathSegmentTypes,any)) A YAML Path segment

        Returns:  (object) At least one YAML Node or None

        Raises:
          NotImplementedError when ref indicates an unknown
          PathSegmentTypes value.
        """
        if data is None or ref is None:
            return None

        reftyp = ref[0]
        refele = ref[1]

        if reftyp == PathSegmentTypes.ANCHOR:
            if isinstance(data, list):
                for e in data:
                    if hasattr(e, "anchor") and refele == e.anchor.value:
                        yield e
            elif isinstance(data, dict):
                for _,v in data:
                    if hasattr(v, "anchor") and refele == v.anchor.value:
                        yield v
            else:
                return None
        elif reftyp == PathSegmentTypes.INDEX:
            try:
                intele = int(refele)
            except ValueError:
                raise YAMLPathException(
                    "{} is not an integer array index".format(str(refele))
                    , str(ref)
                )

            if isinstance(data, list) and len(data) > intele:
                yield data[intele]
            else:
                return None
        elif reftyp == PathSegmentTypes.KEY:
            if isinstance(data, dict) and refele in data:
                yield data[refele]
            else:
                return None
        elif reftyp == PathSegmentTypes.SEARCH:
            for match in self._search(data, refele):
                if match is None:
                    continue
                else:
                    yield match
            return None
        else:
            raise NotImplementedError

    def _default_for_child(self, yaml_path, value=None):
        """Identifies and returns the most appropriate default value for the
        next entry in a YAML Path, should it not already exist.

        Positional Parameters:
          1. yaml_path (deque) The pre-parsed YAML Path to follow
          2. value (any) The final expected value for the final YAML Path entry

        Returns:  (any) The most appropriate default value

        Raises:  N/A
        """
        if yaml_path is None or 1 > len(yaml_path):
            return value

        (typ, _) = yaml_path[0]
        if typ == PathSegmentTypes.INDEX:
            return CommentedSeq()
        elif typ == PathSegmentTypes.KEY:
            return CommentedMap()
        else:
            if isinstance(value, str):
                return PlainScalarString("")
            elif isinstance(value, int):
                return ScalarInt(maxsize)
            elif isinstance(value, float):
                return ScalarFloat("inf")
            else:
                return value

    def _append_list_element(self, data, value=None, anchor=None):
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
            self.log.debug(
                ("YAMLHelpers::_append_list_element:  Ensuring {}{} is a"
                    + " PlainScalarString."
                ).format(type(value), value)
            )
            if type(value) is str:
                value = PlainScalarString(value)
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

    def _search(self, data, terms):
        """Searches the top level of given YAML data for all matching dictionary
        entries.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. terms (list) A list with these elements:
             0 = invert result (Boolean) true = Return a NON-matching node
             1 = search method (PathSearchMethods) the search
                 method
             2 = attribute name (str) the dictionary key to the value to check
             3 = search phrase (any) the value to match
        """

        def search_matches(method, needle, haystack):
            self.log.debug(
                ("YAMLHelpers::_search::search_matches:  Searching for {}"
                    + " using {} against:"
                ).format(needle, method)
            )
            self.log.debug(haystack)
            matches = None

            if method is PathSearchMethods.EQUALS:
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
                    except:
                        matches = False
                elif isinstance(haystack, float):
                    try:
                        matches = haystack > float(needle)
                    except:
                        matches = False
                else:
                    matches = haystack > needle
            elif method is PathSearchMethods.LESS_THAN:
                if isinstance(haystack, int):
                    try:
                        matches = haystack < int(needle)
                    except:
                        matches = False
                elif isinstance(haystack, float):
                    try:
                        matches = haystack < float(needle)
                    except:
                        matches = False
                else:
                    matches = haystack < needle
            elif method is PathSearchMethods.GREATER_THAN_OR_EQUAL:
                if isinstance(haystack, int):
                    try:
                        matches = haystack >= int(needle)
                    except:
                        matches = False
                elif isinstance(haystack, float):
                    try:
                        matches = haystack >= float(needle)
                    except:
                        matches = False
                else:
                    matches = haystack >= needle
            elif method is PathSearchMethods.LESS_THAN_OR_EQUAL:
                if isinstance(haystack, int):
                    try:
                        matches = haystack <= int(needle)
                    except:
                        matches = False
                elif isinstance(haystack, float):
                    try:
                        matches = haystack <= float(needle)
                    except:
                        matches = False
                else:
                    matches = haystack <= needle
            else:
                raise NotImplementedError

            return matches

        invert, method, attr, term = terms
        if isinstance(data, list):
            for e in data:
                if isinstance(e, dict) and attr in e:
                    matches = search_matches(method, term, e[attr])
                    if (matches and not invert) or (invert and not matches):
                        yield e

        elif isinstance(data, dict):
            if attr in data:
                value = data[attr]
                matches = search_matches(method, term, value)
                if (matches and not invert) or (invert and not matches):
                    yield value

        else:
            # Check the passed data itself for a match
            matches = search_matches(method, term, data)
            if (matches and not invert) or (invert and not matches):
                yield data

        yield None

    def _ensure_path(self, data, path, value=None):
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
        if data is None or path is None:
            self.log.debug(
                "YAMLHelpers::_ensure_path:  Bailing out on None data/path!"
            )
            return data

        if 0 < len(path):
            (curtyp, curele) = curref = path.popleft()

            self.log.debug(
                ("YAMLHelpers::_ensure_path:  Seeking element <{}>{} in data of"
                    + " type {}:"
                ).format(curtyp, curele, type(data))
            )
            self.log.debug(data)
            self.log.debug("")

            # The next element may not exist; this method ensures that it does
            matched_nodes = 0
            for node in self._get_elements_by_ref(data, curref):
                if node is None:
                    continue

                matched_nodes += 1
                self.log.debug(
                    ("YAMLHelpers::_ensure_path:  Found element {} in the data;"
                        + " recursing into it..."
                    ).format(curele)
                )
                for node in self._ensure_path(node, path.copy(), value):
                    if node is not None:
                        yield node

            if (
                1 > matched_nodes
                and curtyp is not PathSegmentTypes.SEARCH
            ):
                # Add the missing element
                self.log.debug(
                    ("YAMLHelpers::_ensure_path:  Element {} is unknown in the"
                        + " data!"
                    ).format(curele)
                )
                if isinstance(data, list):
                    self.log.debug(
                        "YAMLHelpers::_ensure_path:  Dealing with a list"
                    )
                    if curtyp is PathSegmentTypes.ANCHOR:
                        new_val = self._default_for_child(path, value)
                        new_ele = self._append_list_element(
                            data, new_val, curele
                        )
                        for node in self._ensure_path(new_ele, path, value):
                            if node is None:
                                continue
                            matched_nodes += 1
                            yield node
                    elif curtyp is PathSegmentTypes.INDEX:
                        for _ in range(len(data) - 1, curele):
                            new_val = self._default_for_child(path, value)
                            self._append_list_element(data, new_val)
                        for node in self._ensure_path(
                            data[curele], path, value
                        ):
                            if node is None:
                                continue
                            matched_nodes += 1
                            yield node
                    else:
                        restore_path = path.copy()
                        restore_path.appendleft(curref)
                        restore_path = self.str_path(restore_path)
                        throw_element = deque()
                        throw_element.append(curref)
                        throw_element = self.str_path(throw_element)
                        raise YAMLPathException(
                            "Cannot add {} subreference to lists"
                                .format(str(curtyp))
                            , restore_path
                            , throw_element
                        )
                elif isinstance(data, dict):
                    self.log.debug(
                        "YAMLHelpers::_ensure_path:  Dealing with a dictionary"
                    )
                    if curtyp is PathSegmentTypes.ANCHOR:
                        raise NotImplementedError
                    elif curtyp is PathSegmentTypes.KEY:
                        data[curele] = self._default_for_child(path, value)
                        for node in self._ensure_path(data[curele], path, value):
                            if node is None:
                                continue
                            matched_nodes += 1
                            yield node
                    else:
                        restore_path = path.copy()
                        restore_path.appendleft(curref)
                        restore_path = self.str_path(restore_path)
                        throw_element = deque()
                        throw_element.append(curref)
                        throw_element = self.str_path(throw_element)
                        raise YAMLPathException(
                            "Cannot add {} subreference to dictionaries".format(
                                str(curtyp)
                            ),
                            restore_path,
                            throw_element
                        )
                else:
                    restore_path = path.copy()
                    restore_path.appendleft(curref)
                    restore_path = self.str_path(restore_path)
                    throw_element = deque()
                    throw_element.append(curref)
                    throw_element = self.str_path(throw_element)
                    raise YAMLPathException(
                        "Cannot add {} subreference to scalars".format(
                            str(curtyp)
                        ),
                        restore_path,
                        throw_element
                    )

        else:
            self.log.debug(
                ("YAMLHelpers::_ensure_path:  Finally returning data of type"
                    + " {}:"
                ).format(type(data))
            )
            self.log.debug(data)

            yield data
