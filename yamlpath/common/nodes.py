"""
Implement Nodes, a static library of generally-useful code for data nodes.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
import re
from datetime import datetime, date, timedelta, timezone
from ast import literal_eval
from typing import Any, Optional

from dateutil import parser

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
from yamlpath.patches.timestamp import (
    AnchoredTimeStamp,
    AnchoredDate,
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
        new_node: Any = None
        new_type: Any = type(source_node)
        new_value: Any = value
        valform: YAMLValueFormats = YAMLValueFormats.DEFAULT

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
                allowed_vals = ["true", "false", "yes", "no", "y", "n",
                                "t", "f", "1", "0"]
                str_val = str(value).lower()
                if str_val not in allowed_vals:
                    raise ValueError("Boolean values must be one of " +
                                     ", ".join(allowed_vals))
                new_value = str(value).lower() in (
                    "true", "yes", "y", "t", "1")
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
        elif valform == YAMLValueFormats.DATE:
            new_type = AnchoredDate

            if isinstance(value, (AnchoredDate, date, datetime)):
                new_value = value
            else:
                # Enforce matches against http://yaml.org/type/timestamp.html
                yaml_spec_re = re.compile(r"""(?x)
                    ^
                    [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] # (ymd)
                    $""")
                dt_matches = yaml_spec_re.match(value)
                if not dt_matches:
                    raise ValueError(
                        f"The requested value format is {valform}, but"
                        + f" '{value}' is not a YAML-compatible ISO8601 date"
                        + " per http://yaml.org/type/timestamp.html")

                try:
                    new_value = parser.parse(value)
                except ValueError as wrap_ex:
                    raise ValueError(
                        f"The requested value format is {valform}, but "
                        + f" {value}' cannot be cast to an ISO8601 date."
                    ) from wrap_ex

            anchor_val = None
            if hasattr(source_node, "anchor"):
                anchor_val = source_node.anchor.value

            new_node = Nodes.make_date_node(new_value, anchor_val)
        elif valform == YAMLValueFormats.TIMESTAMP:
            new_type = AnchoredTimeStamp
            t_sep = ' '

            if isinstance(value, (datetime, AnchoredTimeStamp)):
                new_value = value
            else:
                # Enforce matches against http://yaml.org/type/timestamp.html
                yaml_spec_re = re.compile(r"""(?x)
                    ^
                    [0-9][0-9][0-9][0-9] # (year)
                    -[0-9][0-9]? # (month)
                    -[0-9][0-9]? # (day)
                    ([Tt]|[ \t]+)[0-9][0-9]? # (hour)
                    :[0-9][0-9] # (minute)
                    :[0-9][0-9] # (second)
                    (\.[0-9]*)? # (fraction)
                    (([ \t]*)Z|[-+][0-9][0-9]?(:[0-9][0-9])?)? # (time zone)
                    $""")
                dt_matches = yaml_spec_re.match(value)
                if not dt_matches:
                    raise ValueError(
                        f"The requested value format is {valform}, but"
                        + f" '{value}' is not a YAML-compatible ISO8601"
                        + " timestamp per http://yaml.org/type/timestamp.html")

                t_sep = dt_matches.group(1)

                try:
                    new_value = parser.parse(value)
                except ValueError as wrap_ex:
                    raise ValueError(
                        f"The requested value format is {valform}, but"
                        + f" '{value}' cannot be cast to an ISO8601 timestamp."
                    ) from wrap_ex

            anchor_val = None
            if hasattr(source_node, "anchor"):
                anchor_val = source_node.anchor.value

            new_node = Nodes.make_timestamp_node(
                new_value, t_sep, anchor_val)
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
    def make_date_node(
        value: date, anchor: Optional[str] = None
    ) -> AnchoredDate:
        r"""
        Create a new AnchoredDate data node from a bare date.

        An optional anchor may be attached.

        Parameters:
        1. value (date) The bare date to wrap.
        2. anchor (str) OPTIONAL anchor to add.

        Returns: (AnchoredDate) The new node
        """
        if anchor is None:
            new_node = AnchoredDate(
                value.year
                , value.month
                , value.day
            )
        else:
            new_node = AnchoredDate(
                value.year
                , value.month
                , value.day
                , anchor=anchor
            )

        return new_node

    @staticmethod
    def make_timestamp_node(
        value: datetime, t_separator: str, anchor: Optional[str] = None
    ) -> AnchoredTimeStamp:
        r"""
        Create a new AnchoredTimeStamp data node from a bare datetime.

        An optional anchor may be attached.

        Parameters:
        1. value (datetime) The bare datetime to wrap.
        2. t_separator (str) One of [Tt\s] to separate date from time
        3. anchor (str) OPTIONAL anchor to add.

        Returns: (AnchoredTimeStamp) The new node
        """
        if anchor is None:
            new_node = AnchoredTimeStamp(
                value.year
                , value.month
                , value.day
                , value.hour
                , value.minute
                , value.second
                , value.microsecond
                , value.tzinfo
            )
        else:
            new_node = AnchoredTimeStamp(
                value.year
                , value.month
                , value.day
                , value.hour
                , value.minute
                , value.second
                , value.microsecond
                , value.tzinfo
                , anchor=anchor
            )

        # Add a T separator only when set
        if t_separator in ['T', 't']:
            # Ignore W0212 here because there is literally no other way to tell
            # ruamel.yaml to preserve the T separator for this timestamp at the
            # time of this writing.  This code is indeed therefore fragile.
            # pylint: disable=protected-access
            new_node._yaml['t'] = t_separator

        return new_node

    @staticmethod
    def make_float_node(value: float, anchor: Optional[str] = None):
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
        elif typ is date:
            wrapped_value = AnchoredDate(
                value.year, value.month, value.day)
        elif typ is datetime:
            wrapped_value = AnchoredTimeStamp(
                value.year, value.month, value.day,
                value.hour, value.minute, value.second, value.microsecond,
                value.tzinfo)

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
        data: Any, value: Any = None, anchor: Optional[str] = None
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

    @staticmethod
    def get_timestamp_with_tzinfo(data: AnchoredTimeStamp) -> Any:
        """
        Get an AnchoredTimeStamp with time-zone info correctly applied.

        For whatever reason, ruamel.yaml hides time-zone data in a private
        dict rather than as a manifest property of the wrapped datetime value.
        Doing so causes the datetime value to be pre-calculated when emitted,
        with the time-zone delta applied to the original value.  The net effect
        is users get a different value out than they put in.  This method
        rewinds the pre-calculation and combines the time-zone with the
        original data as befits a complete datetime value.

        Parameters:
        1. value (AnchoredTimeStamp) the value to correct

        Returns:  One of:
          * (datetime) time-zone aware non-pre-calculated value
          * (AnchoredTimeStamp) original value when it had no time-zone data
        """
        # As stated in the method comments, ruamel.yaml hides the time-zone
        # details in a private dict after forcibly normalizing the datetime;
        # there is no public accessor for this.  Also ignoring the mypy type
        # check on the various returns because ruamel.yaml defines TimeStamp
        # as an 'Any' type rather than a 'TimeStamp' or even its superclass of
        # 'datetime'.  It is perfectly accurate to assert that this method is
        # correctly returning a 'datetime' despite the ruamel.yaml type
        # annotation error.
        # pylint: disable=protected-access
        tzinfo_raw = (data._yaml['tz']
                        if hasattr(data, "_yaml") and 'tz' in data._yaml
                        else None)
        if tzinfo_raw:
            tzre = re.compile(r'([+\-]?)(\d{1,2}):?(\d{2})')
            tzmatches = tzre.match(tzinfo_raw)
            if tzmatches:
                sign_mark, hours, minutes = tzmatches.groups()
                sign = -1 if sign_mark == '-' else 1
                tdelta = timedelta(hours=int(hours), minutes=int(minutes))
                tzinfo = timezone(sign * tdelta)
                return ((data + tdelta * sign).replace(
                    tzinfo=tzinfo))
        return data
