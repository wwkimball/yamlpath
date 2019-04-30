#!/usr/bin/env python3
################################################################################
# Reusable YAML helpers.
#
# Copyright 2018, 2019 William W. Kimball, Jr. MBA MSIS
################################################################################
from enum import Enum, auto
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

from yamlexceptions import YAMLPathException

class YAMLValueFormats(Enum):
    """Supported representation formats for YAML values."""
    BARE = auto()
    BOOLEAN = auto()
    DEFAULT = auto()
    DQUOTE = auto()
    FLOAT = auto()
    FOLDED = auto()
    INT = auto()
    LITERAL = auto()
    SQUOTE = auto()

    @staticmethod
    def get_names():
        """Returns all entry names for this enumeration.

        Positional Parameters:  N/A

        Returns:  (list) Upper-case names from this enumeration

        Raises:  N/A
        """
        return [entry.name.upper() for entry in YAMLValueFormats]

    @staticmethod
    def from_str(name):
        """Converts a string value to a value of this enumeration, if valid.

        Positional Parameters:
          1. name (str) The name to convert

        Returns:  (YAMLValueFormats) the converted enumeration value

        Raises:
          NameError when name doesn't match any enumeration values.
        """
        check = str(name).upper()
        if check in YAMLValueFormats.get_names():
            return YAMLValueFormats[check]
        else:
            raise NameError("YAMLValueFormats has no such item, " + check)

class YAMLHelpers:
    """Collection of generally-useful YAML processing methods based on
    ruamel.yaml."""

    class ElementTypes(Enum):
        """Supported YAML Path elements"""
        ANCHOR = auto()
        INDEX = auto()
        KEY = auto()
        SEARCH = auto()

    class ElementSearchMethods(Enum):
        """Supported YAML Path Array-of-Hashes element search methods"""
        CONTAINS = auto()
        ENDS_WITH = auto()
        EQUALS = auto()
        STARTS_WITH = auto()
        # TODO:  GREATER_THAN = auto()
        # TODO:  LESS_THAN = auto()
        # TODO:  EQUAL_OR_GREATER_THAN = auto()
        # TODO:  EQUAL_OR_LESS_THAN = auto()

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

    def get_node(self, data, yaml_path, mustexist=False, default_value=None):
        """Retrieves a node at YAML Path from YAML data.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (any) The YAML Path to evaluate
          3. mustexist (Boolean) Indicate whether yaml_path must exist
             in data prior to this query (lest an Exception be raised);
             default=False
          4. default_value (any) The value to set at yaml_path should
             it not already exist in data and mustexist is False;
             default=None

        Returns:  (object) The requested YAML node

        Raises:
            AttributeError when YAML Path is invalid
        """
        self.log.debug("YAMLHelpers::get_node:  Getting parsed version of " + str(yaml_path))
        path = self._parse_path(yaml_path)
        if mustexist:
            return self._get_node(data, path)
        else:
            return self._ensure_path(data, path, default_value)

    def get_value(self, data, yaml_path, mustexist=False):
        """Retrieves the value of a node at YAML Path from YAML data.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (any) The YAML Path to evaluate
          3. mustexist (Boolean) Indicate whether yaml_path must exist
             in data prior to this query (lest an Exception be raised);
             default=False

        Returns:  (any) The value at YAML Path or None if YAML Path did not
        exist

        Raises:
            YAMLPathException when YAML Path is invalid
        """
        if data is None or yaml_path is None:
            return None

        self.log.debug("YAMLHelpers::get_value:  Getting parsed version of " + str(yaml_path))
        path = self._parse_path(yaml_path)
        node = self._get_node(data, path)
        if node is None and mustexist:
            raise YAMLPathException(
                "Required path does not exist",
                self.str_path(path)
            )
        return node

    def set_value(self, data, yaml_path, value, mustexist=False,
                  format=YAMLValueFormats.DEFAULT
    ):
        """Sets a value for a specific node at YAML Path in YAML data.

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

        Returns:  (object) The YAML node after its value has been set

        Raises:
            AttributeError when YAML Path is invalid
        """
        if data is None or yaml_path is None:
            return None

        self.log.debug("YAMLHelpers::set_value:  Getting parsed version of " + str(yaml_path))
        path = self._parse_path(yaml_path)
        if mustexist:
            self.log.debug("YAMLHelpers::set_value:  Seeking required node at " + self.str_path(path))
            node = self._get_node(data, path)

            if node is None:
                raise YAMLPathException(
                    "Required path does not exist",
                    self.str_path(path)
                )
        else:
            self.log.debug("YAMLHelpers::set_value:  Seeking optional node at " + self.str_path(path))
            node = self._ensure_path(data, path, value)

        self._update_value(data, node, value, format)

        return node

    def str_path(self, yaml_path):
        """Returns the printable, user-friendly version of a YAML Path.

        Positional Parameters:
          1. yaml_path (any) The YAML Path to convert

        Returns:  (str) The stringified YAML Path

        Raises:  N/A
        """
        self.log.debug("YAMLHelpers::str_path:  Getting parsed version of " + str(yaml_path))
        parsed_path = self._parse_path(yaml_path)
        add_dot = False
        ppath = ""

        for (ptype, element_id) in parsed_path:
            if ptype == YAMLHelpers.ElementTypes.KEY:
                if add_dot:
                    ppath += "."
                ppath += element_id.replace(".", "\\.")
            elif ptype == YAMLHelpers.ElementTypes.INDEX:
                ppath += "[" + str(element_id) + "]"
            elif ptype == YAMLHelpers.ElementTypes.ANCHOR:
                ppath += "[&" + element_id + "]"
            elif ptype == YAMLHelpers.ElementTypes.SEARCH:
                invert, method, attr, term = element_id
                pmethod = "???"
                if method == YAMLHelpers.ElementSearchMethods.EQUALS:
                    pmethod = "="
                elif method == YAMLHelpers.ElementSearchMethods.STARTS_WITH:
                    pmethod = "^"
                elif method == YAMLHelpers.ElementSearchMethods.ENDS_WITH:
                    pmethod = "$"
                elif method == YAMLHelpers.ElementSearchMethods.CONTAINS:
                    pmethod = "%"
                else:
                    raise NotImplementedError

                ppath += (
                    "["
                    + str(attr)
                    + ("!" if invert else "")
                    + pmethod
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

        Positional Parameters:
          1. yaml_path (any) The stringified YAML Path to parse

        Returns:  (deque) an empty queue or a queue of tuples, each identifying
        (type, element) unless yaml_path is already a list or a deque.  If
        yaml_path is already a list, it is blindly converted into a deque and
        returned.  If yaml_path is already a deque, it is blindly returned
        as-is.

        Raises:
          AttributeError when yaml_path is invalid
        """
        self.log.debug("YAMLHelpers::_parse_path:  Evaluating \"" + str(yaml_path) + "\"...")

        path_elements = deque()

        if yaml_path is None:
            self.log.debug("YAMLHelpers::_parse_path:  None path begets empty deque.")
            return path_elements
        elif isinstance(yaml_path, deque):
            self.log.debug("YAMLHelpers::_parse_path:  Sending deque back as-is.")
            return yaml_path
        elif isinstance(yaml_path, list):
            self.log.debug("YAMLHelpers::_parse_path:  Sending deque(list) back.")
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
            self.log.debug("YAMLHelpers::_parse_path:  Returning cached copy of pre-parsed path \"" + yaml_path + "\".")
            return YAMLHelpers._static_parsings[yaml_path].copy()

        element_id = ""
        demarc_stack = []
        seeking_anchor_mark = "&" == yaml_path[0]
        escape_next = False
        element_type = YAMLHelpers.ElementTypes.KEY
        search_inverted = False
        search_method = YAMLHelpers.ElementSearchMethods.EQUALS
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
                element_type = YAMLHelpers.ElementTypes.ANCHOR
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
                            element_type = YAMLHelpers.ElementTypes.KEY
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
                element_type = YAMLHelpers.ElementTypes.INDEX
                seeking_anchor_mark = True
                search_inverted = False
                search_method = YAMLHelpers.ElementSearchMethods.EQUALS
                search_attr = ""
                continue

            elif (
                not escape_next
                and 0 < demarc_count
                and "[" == demarc_stack[-1]
                and c in ["=", "^", "$", "%", "!"]
            ):
                # Hash attribute search
                if "=" == c:
                    # Exact value match
                    element_type = YAMLHelpers.ElementTypes.SEARCH
                    search_method = YAMLHelpers.ElementSearchMethods.EQUALS
                    search_attr = element_id
                    element_id = ""
                    continue

                elif "^" == c:
                    # Value starts with
                    element_type = YAMLHelpers.ElementTypes.SEARCH
                    search_method = YAMLHelpers.ElementSearchMethods.STARTS_WITH
                    search_attr = element_id
                    element_id = ""
                    continue

                elif "$" == c:
                    # Value ends with
                    element_type = YAMLHelpers.ElementTypes.SEARCH
                    search_method = YAMLHelpers.ElementSearchMethods.ENDS_WITH
                    search_attr = element_id
                    element_id = ""
                    continue

                elif "%" == c:
                    # Value contains
                    element_type = YAMLHelpers.ElementTypes.SEARCH
                    search_method = YAMLHelpers.ElementSearchMethods.CONTAINS
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
                if element_type is YAMLHelpers.ElementTypes.INDEX:
                    path_elements.append((element_type, int(element_id)))
                elif element_type is YAMLHelpers.ElementTypes.SEARCH:
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

                element_type = YAMLHelpers.ElementTypes.KEY
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

        self.log.debug("YAMLHelpers::_parse_path:  Parsed \"" + str(yaml_path) + "\" into:")
        self.log.debug(path_elements)

        # Cache the parsed results
        YAMLHelpers._static_parsings[yaml_path] = path_elements
        str_path = self.str_path(path_elements)
        if not str_path == yaml_path:
            # The stringified YAML Path differs from the user version but has
            # exactly the same parsed result, so cache it, too
            YAMLHelpers._static_parsings[str_path] = path_elements

        return path_elements.copy()

    def _get_node(self, data, yaml_path):
        """Returns a pre-existing node from YAML data or None if the given YAML
        Path fails to lead to a node.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. yaml_path (deque) The pre-parsed YAML Path to follow

        Returns:  (object) The requested YAML node or None

        Raises:  N/A
        """
        if data is None or yaml_path is None:
            return None

        if 0 < len(yaml_path):
            (typ, ele) = yaml_path.popleft()

            self.log.debug("YAMLHelpers::_get_node:  Peeking at element [" + str(ele) + "] of type [" + str(typ) + "] in data of type[" + str(type(data)) + "]:")
            self.log.debug(data)
            self.log.debug("")

            if YAMLHelpers.ElementTypes.KEY == typ:
                self.log.debug("YAMLHelpers::_get_node:  Drilling into the present dictionary KEY...")
                if ele in data:
                    return self._get_node(data[ele], yaml_path)
                else:
                    return None
            elif YAMLHelpers.ElementTypes.INDEX == typ:
                self.log.debug("YAMLHelpers::_get_node:  Drilling into the present list INDEX...")
                if ele < len(data):
                    return self._get_node(data[ele], yaml_path)
                else:
                    return None
            elif YAMLHelpers.ElementTypes.ANCHOR == typ:
                if isinstance(data, list):
                    self.log.debug("YAMLHelpers::_get_node:  Searching for an ANCHOR in a list...")
                    for e in data:
                        if hasattr(e, "anchor") and ele == e.anchor.value:
                            return self._get_node(e, yaml_path)
                elif isinstance(data, dict):
                    self.log.debug("YAMLHelpers::_get_node:  Searching for an ANCHOR in a dictionary...")
                    for _,v in data:
                        if hasattr(v, "anchor") and ele == v.anchor.value:
                            return self._get_node(v, yaml_path)
                return None
            elif YAMLHelpers.ElementTypes.SEARCH == typ:
                self.log.debug("YAMLHelpers::_get_node:  Performing an attribute SEARCH...")
                # Return only the first match
                for match in self._search(data, ele):
                    if match is None:
                        continue
                    else:
                        return self._get_node(match, yaml_path)
                return None
            else:
                raise NotImplementedError

        self.log.debug("YAMLHelpers::_get_node:  Finally returning data of type [" + str(type(data)) + "]:")
        self.log.debug(data)
        self.log.debug("")

        return data

    def clone_node(self, node):
        """Duplicates a YAML Data node.

        Positional Parameters:
          1. node (object) The node to clone.

        Returns: (object) Clone of the given node
        """
        if hasattr(node, "anchor"):
            return type(node)(node, anchor=node.anchor.value)
        else:
            return type(node)(node)

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
        def update_references(data, reference_node, replacement_node):
            if isinstance(data, dict):
                for i, k in [(idx, key) for idx, key in enumerate(data.keys()) if key is reference_node]:
                    data.insert(i, replacement_node, data.pop(k))
                for k, v in data.non_merged_items():
                    if v is reference_node:
                        data[k] = replacement_node
                    else:
                        update_references(v, reference_node, replacement_node)
            elif isinstance(data, list):
                for idx, item in enumerate(data):
                    if item is reference_node:
                        data[idx] = replacement_node
                    else:
                        update_references(item, reference_node, replacement_node)

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
                self.log.error("Unknown YAML value format, " + strform)

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
                self.log.error("Not a floating-point precision number: " + str(value), 1)

            strval = str(value)
            precision = 0
            width = len(strval)
            lastdot = strval.rfind(".")
            if -1 < lastdot:
                precision = strval.rfind(".")

            if hasattr(source_node, "anchor"):
                new_node = ScalarFloat(newval, anchor=source_node.anchor.value, prec=precision, width=width)
            else:
                new_node = ScalarFloat(newval, prec=precision, width=width)
        elif valform == YAMLValueFormats.INT:
            newtype = ScalarInt

            try:
                newval = int(value)
            except ValueError:
                self.log.error("Not an integer: " + str(value), 1)

        if new_node is None:
            if hasattr(source_node, "anchor"):
                new_node = newtype(newval, anchor=source_node.anchor.value)
            else:
                new_node = newtype(newval)

        update_references(data, source_node, new_node)

    def _get_element_by_ref(self, data, ref):
        """Returns the referenced YALM Node or None when the given reference
        points nowhere.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. ref (tuple(YAMLHelpers.ElementTypes,any)) A YAML Path segment

        Returns:  (object) A YAML Node or None

        Raises:
          NotImplementedError when ref indicates an unknown
          YAMLHelpers.ElementTypes value.
        """
        if data is None or ref is None:
            return None

        reftyp = ref[0]
        refele = ref[1]

        if reftyp == YAMLHelpers.ElementTypes.ANCHOR:
            if isinstance(data, list):
                for e in data:
                    if hasattr(e, "anchor") and refele == e.anchor.value:
                        return e
            elif isinstance(data, dict):
                for _,v in data:
                    if hasattr(v, "anchor") and refele == v.anchor.value:
                        return v
            else:
                return None
        elif reftyp == YAMLHelpers.ElementTypes.INDEX:
            if isinstance(data, list) and len(data) > refele:
                return data[refele]
            else:
                return None
        elif reftyp == YAMLHelpers.ElementTypes.KEY:
            if isinstance(data, dict) and refele in data:
                return data[refele]
            else:
                return None
        elif reftyp == YAMLHelpers.ElementTypes.SEARCH:
            # Return only the first match
            for match in self._search(data, refele):
                if match is None:
                    continue
                else:
                    return match
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
        if typ == YAMLHelpers.ElementTypes.INDEX:
            return CommentedSeq()
        elif typ == YAMLHelpers.ElementTypes.KEY:
            return CommentedMap()
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
        old_tail_pos = len(data) - 1
        data.append(value)
        new_element = data[-1]

        if anchor is not None:
            new_element.yaml_set_anchor(anchor)

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
             1 = search method (YAMLHelpers.ElementSearchMethods) the search
                 method
             2 = attribute name (str) the dictionary key to the value to check
             3 = search phrase (any) the value to match
        """

        def search_matches(method, needle, haystack):
            self.log.debug("Searching for '" + str(needle) + "' in:")
            self.log.debug(haystack)
            matches = None

            if YAMLHelpers.ElementSearchMethods.EQUALS == method:
                matches = haystack == needle
            elif YAMLHelpers.ElementSearchMethods.STARTS_WITH == method:
                matches = str(haystack).startswith(needle)
            elif YAMLHelpers.ElementSearchMethods.ENDS_WITH == method:
                matches = str(haystack).endswith(needle)
            elif YAMLHelpers.ElementSearchMethods.CONTAINS == method:
                matches = needle in str(haystack)
            else:
                raise NotImplementedError

            return matches

        self.log.debug("-\n--\n---")
        self.log.debug(terms)
        invert, method, attr, term = terms
        if isinstance(data, list):
            # Select only the first element which is a dict and matches
            # the search terms.
            self.log.debug("------ searching a list...")
            for e in data:
                if isinstance(e, dict) and attr in e:
                    matches = search_matches(method, term, e[attr])
                    if (matches and not invert) or (invert and not matches):
                        yield e

        elif isinstance(data, dict):
            # Select only the first value which is a dict and matches
            # the search terms.
            self.log.debug("------ searching a dictionary...")
            for _,v in data:
                if isinstance(v, dict) and attr in v:
                    matches = search_matches(method, term, v[attr])
                    if (matches and not invert) or (invert and not matches):
                        yield v

        else:
            # Check the passed data itself for a match
            self.log.debug("------ searching literal data...")
            matches = search_matches(method, term, data)
            if (matches and not invert) or (invert and not matches):
                yield v

        self.log.debug("---\n--\n-")
        yield None

    def _ensure_path(self, data, path, value=None):
        """Returns the YAML node at the end of a YAML Path, having created it if
        necessary and possible.

        Positional Parameters:
          1. data (ruamel.yaml data) The parsed YAML data to process
          2. path (deque) The pre-parsed YAML Path to follow
          3. value (any) The value to assign to the element

        Returns:  (object) The specified node

        Raises:
          AttributeError when the YAML Path is invalid.
          NotImplementedError when a segment of the YAML Path indicates
            an element that does not exist in data and this code isn't
            yet prepared to add it.
        """
        if data is None or path is None:
            return data

        if 0 < len(path):
            (curtyp, curele) = curref = path.popleft()

            self.log.debug("YAMLHelpers::_ensure_path:  Seeking element [" + str(curele) + "] of type [" + str(curtyp) + "] in data of type [" + str(type(data)) + "]:")
            self.log.debug(data)
            self.log.debug("")

            # The next element may not exist; this method ensures that it does
            node = self._get_element_by_ref(data, curref)
            if node is not None:
                self.log.debug("YAMLHelpers::_ensure_path:  Found element [" + str(curele) + "] in the data; recursing into it...")
                return self._ensure_path(node, path, value)
            else:
                # Add the missing element
                self.log.debug("YAMLHelpers::_ensure_path:  Element [" + str(curele) + "] is unknown in the data!")
                if isinstance(data, list):
                    self.log.debug("YAMLHelpers::_ensure_path:  Dealing with a list...")
                    if curtyp is YAMLHelpers.ElementTypes.ANCHOR:
                        new_val = self._default_for_child(path, value)
                        new_ele = self._append_list_element(data, new_val, curele)
                        return self._ensure_path(new_ele, path, value)
                    elif curtyp is YAMLHelpers.ElementTypes.INDEX:
                        for _ in range(len(data) - 1, curele):
                            new_val = self._default_for_child(path, value)
                            self._append_list_element(data, new_val)
                        return self._ensure_path(data[curele], path, value)
                    elif curtyp is YAMLHelpers.ElementTypes.SEARCH:
                        restore_path = path.copy()
                        restore_path.appendleft(curref)
                        restore_path = self.str_path(restore_path)
                        throw_element = deque()
                        throw_element.append(curref)
                        throw_element = self.str_path(throw_element)
                        raise YAMLPathException(
                            "Search criteria cannot be used to create missing YAML data",
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
                            "Cannot add {} subreference to lists".format(str(curtyp)),
                            restore_path,
                            throw_element
                        )
                elif isinstance(data, dict):
                    self.log.debug("YAMLHelpers::_ensure_path:  Dealing with a dictionary...")
                    if curtyp is YAMLHelpers.ElementTypes.ANCHOR:
                        raise NotImplementedError
                    elif curtyp is YAMLHelpers.ElementTypes.KEY:
                        data[curele] = self._default_for_child(path, value)
                        return self._ensure_path(data[curele], path, value)
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

        self.log.debug("YAMLHelpers::_ensure_path:  Returning data of type [" + str(type(data)) + "]:")
        self.log.debug(data)

        return data
