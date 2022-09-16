"""
Implement Nodes, a static library of generally-useful code for data nodes.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
import re
from ast import literal_eval
from distutils.util import strtobool
from typing import Any

from ruamel.yaml.comments import CommentedSeq, CommentedMap, TaggedScalar
from ruamel.yaml.scalarbool import ScalarBoolean
from ruamel.yaml.scalarfloat import ScalarFloat
from ruamel.yaml.scalarint import ScalarInt
from ruamel.yaml.scalarstring import (
    PlainScalarString,
    DoubleQuotedScalarString,
    SingleQuotedScalarString,
    FoldedScalarString,
    LiteralScalarString,
)

from yamlpath.enums import (
    PathSegmentTypes,
    YAMLValueFormats,
)
from yamlpath.wrappers import NodeCoords
from yamlpath import YAMLPath


class Nodes:
    """Helper methods for common data node operations."""

    @staticmethod
    # pylint: disable=too-many-branches,too-many-statements,too-many-locals
    def make_new_node(
        source_node: Any, value: Any, value_format: YAMLValueFormats, **kwargs
    ) -> Any:
        """
        Create a new data node based on a sample node.

        This is achieved by effectively duplicaing the type and anchor of the
        node but giving it a different value.

        Parameters:
        1. source_node (Any) The node from which to copy type
        2. value (Any) The value to assign to the new node
        3. value_format (YAMLValueFormats) The YAML presentation format to
           apply to value when it is dumped

        Keyword Arguments:
        * tag (str) Custom data-type tag to apply to this node

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

            if hasattr(source_node, "anchor") and source_node.anchor.value:
                new_node = new_type(new_value, anchor=source_node.anchor.value)
            else:
                new_node = new_type(new_value)

            fold_at = [x.start() for x in re.finditer(' ', new_node)]
            new_node.fold_pos = fold_at # type: ignore

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
            new_node = Nodes.make_float_node(new_value, anchor_val)
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
            # Punt to whatever the best Scalar type may be
            try:
                wrapped_value = Nodes.wrap_type(value)
            except ValueError:
                # Value cannot be safely converted to any native type
                new_type = PlainScalarString
                wrapped_value = PlainScalarString(value)

            if Nodes.node_is_leaf(wrapped_value):
                new_type = type(wrapped_value)
            else:
                # Disallow conversions to complex types
                new_type = PlainScalarString
                wrapped_value = PlainScalarString(value)

            new_format = YAMLValueFormats.from_node(wrapped_value)
            if new_format is not YAMLValueFormats.DEFAULT:
                new_node = Nodes.make_new_node(
                    source_node, value, new_format, **kwargs)

        if new_node is None:
            if hasattr(source_node, "anchor") and source_node.anchor.value:
                new_node = new_type(new_value, anchor=source_node.anchor.value)
            elif new_type is not type(None):
                new_node = new_type(new_value)

        # Apply a custom tag, if provided
        if "tag" in kwargs:
            new_node = Nodes.apply_yaml_tag(new_node, kwargs.pop("tag"))

        return new_node

    @staticmethod
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

    @staticmethod
    def clone_node(node: Any) -> Any:
        """
        Duplicate a YAML Data node.

        This is necessary because otherwise, Python would treat any copies of a
        value as references to each other such that changes to one
        automatically affect all copies.  This is not desired when an original
        value must be duplicated elsewhere in the data and then the original
        changed without impacting the copy.

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
        ast_value = Nodes.typed_value(value)
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
            wrapped_value = Nodes.make_float_node(ast_value)
        elif typ is bool:
            wrapped_value = ScalarBoolean(bool(value))

        return wrapped_value

    @staticmethod
    def build_next_node(
        yaml_path: YAMLPath, depth: int, value: Any = None
    ) -> Any:
        """
        Get the best default value for the next entry in a YAML Path.

        Parameters:
        1. yaml_path (deque) The pre-parsed YAML Path to follow
        2. depth (int) Index of the YAML Path segment to evaluate
        3. value (Any) The expected value for the final YAML Path entry

        Returns:  (Any) The most appropriate default value

        Raises:  N/A
        """
        default_value = Nodes.wrap_type(value)
        segments = yaml_path.escaped
        if not (segments and len(segments) > depth):
            return default_value

        typ = segments[depth][0]
        if typ == PathSegmentTypes.INDEX:
            default_value = CommentedSeq()
        elif typ == PathSegmentTypes.KEY:
            default_value = CommentedMap()

        return default_value

    @staticmethod
    def append_list_element(
        data: Any, value: Any = None, anchor: str = None
    ) -> Any:
        """
        Append a new element to an ruamel.yaml List.

        This method preserves any tailing comment for the former last element
        of the same list.

        Parameters:
        1. data (Any) The parsed YAML data to process
        2. value (Any) The value of the element to append
        3. anchor (str) An Anchor or Alias name for the new element

        Returns:  (Any) The newly appended element node

        Raises:  N/A
        """
        if anchor is not None and value is not None:
            value = Nodes.wrap_type(value)
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
    def delete_from_dict_with_comments(data, key, parent, parentref):
        """
        Delete a key-value pair from a dict, correctly removing its comment.

        Because ruamel.yaml only associates comments with the node BEFORE them,
        deleting nodes causes unwanted comment removal behavior:  the node,
        any end-of-line comment obviously for it, and all whitespace and other
        comments on lines AFTER the node are destroyed.  Because most comments
        PRECEDE the node they are intended for, this is almost exactly the
        opposite of the expected behavior except for correctly removing any
        end-of-line comment.

        This static method attempts to correct for this unwanted behavior by
        treating the pre-node comment, the end-of-line comment, and any post-
        node comments as discrete entities which must be separately handled.
        This is complex.  While it is obvious that any end-of-line comment must
        be deleted with the node and any post-node comment must be PRESERVED,
        the pre-node comment may or may not be related to the deleted node.
        Some checks will be performed to determine whether or not to delete the
        pre-node comment or a part of it.  If it is commented YAML, it will be
        kept.  If there is an empty-line (handled as a comment by ruamel.yaml)
        as the last line of the preceding comment, the entire preceding comment
        will be preserved.  Otherwise, the preceding comment will be destroyed
        from the end up to the first newline or non-commented YAML.

        This is fragile code.  The ruamel.yaml project is subject to change how
        it handles comments.  Using this method as a central means of treating
        comment removal from dicts will limit scope of such fagility to this
        method alone.
        """
        # DEBUG
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        print("The ca items for data:")
        pp.pprint(data.ca.items if hasattr(data, "ca") else "DATA HAS NO COMMENTS!")
        print("All data keys:")
        pp.pprint(list(data.keys()))
        print("The ca items for parent:")
        pp.pprint(parent.ca.items if hasattr(parent, "ca") else "PARENT HAS NO COMMENTS!")
        print("All parent keys:")
        pp.pprint(list(parent.keys()) if hasattr(parent, "keys") else "NO KEYS!")

        # In order to preserve the post-node comment, omiting any end-of-line
        # comment, it must be appended/moved to the node preceding the deleted
        # node.
        if hasattr(data, "ca") and key in data.ca.items:
            # There is an end-of-line comment, post-comment (i.e. comment for
            # the NEXT node which must be attached to the end of the PRECEDING
            # node's comment), or both.
            keylist: list[Any] = list(data.keys())
            keydex: int = keylist.index(key)
            predex: int = keydex - 1
            prekey: Any = (None if predex < 0
                          else keylist[predex])
            pre_comment = (data.ca.items[prekey][2].value
                           if prekey is not None
                           else None)
            post_comment = data.ca.items[key][2].value

            if pre_comment is None:
                # Pull the pre node comment from the node's parent
                print(f"Attempting to pull parent comment for parentref, {parentref}.")
                pre_comment = (parent.ca.items[parentref][3][0].value
                               if parentref is not None
                               else None)

            # DEBUG
            debug_pre = pre_comment.replace('\n', '\\n') if pre_comment is not None else "NO PRE COMMENT"
            debug_post = post_comment.replace('\n', '\\n')
            print(f"Target object with key, {key}, has:")
            print(f"  pre  comment:  {debug_pre}" )
            print(f"  post comment:  {debug_post}")

            # Check the preceding node's post-comment for content that is
            # likely meant for the to-be-deleted node.  First, exclude any
            # end-of-line comment.
            pre_eol_comment = pre_comment.partition("\n")[0] + "\n"
            post_eol_comment = pre_comment.partition("\n")[2]

            # DEBUG
            debug_pre_eol_comment = pre_eol_comment.replace('\n', '\\n')
            debug_post_eol_comment = post_eol_comment.replace('\n', '\\n')
            print(f"  pre_eol_comment:  {debug_pre_eol_comment}" )
            print(f"  post_eol_comment:  {debug_post_eol_comment}")

            if post_eol_comment is not None:
                pre_lines = post_eol_comment.split("\n")
                line_count = len(pre_lines)
                preserve_to = line_count
                keep_lines = 0
                for pre_index, pre_line in enumerate(reversed(pre_lines)):
                    keep_lines = pre_index
                    pre_content = pre_line.partition("#")[2].lstrip()

                    # DEBUG
                    print(f"Evaluating:  {pre_content}")

                    # Stop preserving lines at the first (last) blank line
                    if len(pre_content) < 1:
                        print(f"EVALUATION HIT AN EMPTY LINE AT {pre_index}")
                        break

                    # Check for possible YAML markup
                    if pre_content[0] == '-' or ':' in pre_content:
                        # May be YAML
                        print(f"EVALUATION HIT POSSIBLE YAML AT {pre_index}")
                        break

                preserve_to = line_count - keep_lines - 2
                pre_comment = pre_eol_comment + "\n".join(pre_lines[0:preserve_to]) + ("\n" if preserve_to >= 0 else "")

                # DEBUG
                debug_lines = pre_comment.replace("\n", "\\n")
                print(f"EVALUATION WOULD PRESERVE TO {preserve_to} LINES: {debug_lines}")

                data.ca.items[prekey][2].value = pre_comment

            # Check for any comment after an end-of-line comment
            preserve_comment = post_comment.partition("\n")[2]
            if len(preserve_comment) > 0:
                # There's something to preserve; move it to the preceding
                # node's post-comment.
                new_pre_comment = pre_comment + preserve_comment

                # DEBUG
                debug_new_pre_comment = new_pre_comment.replace('\n', '\\n') if new_pre_comment is not None else "NO NEW PRE COMMENT"
                print(f"With a preserve_comment lenght of {len(preserve_comment)}, the new pre_comment:  {debug_new_pre_comment}")

                data.ca.items[prekey][2].value = new_pre_comment

        del data[key]

    @staticmethod
    def apply_yaml_tag(node: Any, value_tag: str) -> Any:
        """
        Apply a YAML Tag (AKA Schema) to a node or remove one.

        Using None for the tag simply preserves the existing tag.  To delete a
        tag, it must be set to an empty-string.

        Parameters:
        1. document (Any) the document in which the node exists
        2. node (Any) the node to update
        3. value_tag (str) Tag to apply (or None to remove)

        Returns: (Any) the updated node; may be new data, so replace your node
            with this returned value!
        """
        if value_tag is None:
            return node

        new_node = node
        if Nodes.node_is_leaf(new_node):
            if isinstance(new_node, TaggedScalar):
                if value_tag:
                    new_node.yaml_set_tag(value_tag)
                else:
                    # Strip off the tag
                    new_node = node.value
            elif value_tag:
                new_node = TaggedScalar(value=node, tag=value_tag)
                if hasattr(node, "anchor") and node.anchor.value:
                    new_node.yaml_set_anchor(node.anchor.value)
        else:
            new_node.yaml_set_tag(value_tag)

        return new_node

    @staticmethod
    def node_is_leaf(node: Any) -> bool:
        """
        Indicate whether a node is a leaf (Scalar data).

        Parameters:
        1. node (Any) The node to evaluate

        Returns:  (bool) True = node is a leaf; False, otherwise
        """
        return not isinstance(node, (dict, list, set))

    @staticmethod
    def node_is_aoh(node: Any, **kwargs) -> bool:
        """
        Indicate whether a node is an Array-of-Hashes (List of Dicts).

        Parameters:
        1. node (Any) The node under evaluation

        Keyword Arguments:
        * accept_nulls (bool) When node is enumerable, True = allow elements to
          be None; False, otherwise; default=False

        Returns:  (bool) True = node is a `list` comprised **only** of `dict`s
        """
        accept_nulls: bool = kwargs.pop("accept_nulls", False)
        if node is None:
            return False

        if not isinstance(node, (list, set)):
            return False

        for ele in node:
            if accept_nulls and ele is None:
                continue
            if not isinstance(ele, dict):
                return False

        return True

    @staticmethod
    def tagless_elements(data: list) -> list:
        """
        Get a copy of a list with all elements stripped of YAML Tags.

        Parameters:
        1. data (list) The list to strip of YAML Tags

        Returns:  (list) De-tagged version of `data`
        """
        detagged = []
        for ele in data:
            if isinstance(ele, TaggedScalar):
                detagged.append(ele.value)
            else:
                detagged.append(ele)
        return detagged

    @staticmethod
    def tagless_value(value: Any) -> Any:
        """
        Get a value in its true data-type, stripped of any YAML Tag.

        Parameters:
        1. value (Any) The value to de-tag

        Returns:  (Any) The de-tagged value
        """
        evalue = value
        if isinstance(value, TaggedScalar):
            evalue = value.value
        return Nodes.typed_value(evalue)

    @staticmethod
    def typed_value(value: str) -> Any:
        """
        Safely convert a String value to its intrinsic Python data type.

        Parameters:
        1. value (Any) the value to convert
        """
        if value is None:
            return value

        if isinstance(value, NodeCoords):
            return Nodes.typed_value(value.node)

        cased_value = value
        lower_value = str(value).lower()

        try:
            # Booleans require special handling
            if lower_value in ("true", "false"):
                cased_value = str(value).title()
            typed_value = literal_eval(cased_value)
        except ValueError:
            typed_value = value
        except SyntaxError:
            typed_value = value
        return typed_value
