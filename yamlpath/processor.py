#pylint: disable=too-many-lines
"""
YAML Path processor based on ruamel.yaml.

Copyright 2018, 2019, 2020, 2021 William W. Kimball, Jr. MBA MSIS
"""
from collections import OrderedDict
from typing import Any, Dict, Generator, List, Union

from ruamel.yaml.comments import (
    CommentedMap,
    CommentedSeq,
    CommentedSet,
    TaggedScalar,
)

from yamlpath.types import AncestryEntry, PathAttributes, PathSegment
from yamlpath.common import Anchors, KeywordSearches, Nodes, Searches
from yamlpath import YAMLPath
from yamlpath.path import SearchKeywordTerms, SearchTerms, CollectorTerms
from yamlpath.wrappers import ConsolePrinter, NodeCoords
from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import (
    YAMLValueFormats,
    PathSegmentTypes,
    PathSearchKeywords,
    CollectorOperators,
    PathSeperators,
)


class Processor:
    """Query and update YAML data via robust YAML Paths."""

    def __init__(self, logger: ConsolePrinter, data: Any) -> None:
        """
        Instantiate this class into an object.

        Parameters:
        1. logger (ConsolePrinter) Instance of ConsoleWriter or subclass
        2. data (Any) Parsed YAML data

        Returns:  N/A

        Raises:  N/A
        """
        self.logger: ConsolePrinter = logger
        self.data: Any = data

    def get_nodes(
        self, yaml_path: Union[YAMLPath, str], **kwargs: Any
    ) -> Generator[Any, None, None]:
        """
        Get nodes at YAML Path in data.

        Parameters:
        1. yaml_path (Union[YAMLPath, str]) The YAML Path to evaluate

        Keyword Arguments:
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

        if self.data is None:
            self.logger.debug(
                "Refusing to get nodes from a null document!",
                prefix="Processor::get_nodes:  ", data=self.data)
            return

        if isinstance(yaml_path, str):
            yaml_path = YAMLPath(yaml_path, pathsep)
        elif pathsep is not PathSeperators.AUTO:
            yaml_path.seperator = pathsep

        self.logger.debug(
            "Processing YAML Path:",
            prefix="Processor::get_nodes:  ", data={
                'path': yaml_path,
                'segments': yaml_path.escaped
            })

        if mustexist:
            matched_nodes: int = 0
            for node_coords in self._get_required_nodes(self.data, yaml_path):
                matched_nodes += 1
                self.logger.debug(
                    "Relaying required node:",
                    prefix="Processor::get_nodes:  ", data=node_coords)
                yield node_coords

            if matched_nodes < 1:
                raise YAMLPathException(
                    "Required YAML Path does not match any nodes",
                    str(yaml_path)
                )
        else:
            for opt_node in self._get_optional_nodes(
                self.data, yaml_path, default_value
            ):
                self.logger.debug(
                    "Relaying optional node:",
                    prefix="Processor::get_nodes:  ", data=opt_node)
                yield opt_node

    def set_value(
        self, yaml_path: Union[YAMLPath, str], value: Any, **kwargs
    ) -> None:
        """
        Set the value of zero or more nodes at YAML Path in YAML data.

        Parameters:
        1. yaml_path (Union[Path, str]) The YAML Path to evaluate
        2. value (Any) The value to set

        Keyword Arguments:
        * mustexist (bool) Indicate whether yaml_path must exist
          in data prior to this query (lest an Exception be raised);
          default=False
        * value_format (YAMLValueFormats) The demarcation or visual
          representation to use when writing the data;
          default=YAMLValueFormats.DEFAULT
        * pathsep (PathSeperators) Forced YAML Path segment seperator; set
          only when automatic inference fails;
          default = PathSeperators.AUTO
        * tag (str) Custom data-type tag to assign

        Returns:  N/A

        Raises:
            - `YAMLPathException` when YAML Path is invalid
        """
        if self.data is None:
            self.logger.debug(
                "Refusing to set nodes of a null document!",
                prefix="Processor::set_nodes:  ", data=self.data)
            return

        mustexist: bool = kwargs.pop("mustexist", False)
        value_format: YAMLValueFormats = kwargs.pop("value_format",
                                                    YAMLValueFormats.DEFAULT)
        pathsep: PathSeperators = kwargs.pop("pathsep", PathSeperators.AUTO)
        tag: str = kwargs.pop("tag", None)

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
            for req_node in self._get_required_nodes(self.data, yaml_path):
                found_nodes += 1
                self._apply_change(yaml_path, req_node, value,
                    value_format=value_format, tag=tag)

            if found_nodes < 1:
                raise YAMLPathException(
                    "No nodes matched required YAML Path",
                    str(yaml_path)
                )
        else:
            self.logger.debug(
                "Processor::set_value:  Seeking optional node at {}."
                .format(yaml_path)
            )
            for node_coord in self._get_optional_nodes(
                self.data, yaml_path, value
            ):
                self._apply_change(yaml_path, node_coord, value,
                    value_format=value_format, tag=tag)

    # pylint: disable=locally-disabled,too-many-locals,too-many-branches
    def _apply_change(
        self, yaml_path: YAMLPath, node_coord: NodeCoords, value: Any,
        **kwargs: Any
    ) -> None:
        """
        Apply a controlled change to the document via gathered NodeCoords.

        Parameters:
        1. yaml_path (YAMLPath) The YAML Path causing this change.
        2. node_coord (NodeCoords) The data node to affect.
        3. value (Any) The value to apply.

        Keyword Arguments:
        * value_format (YAMLValueFormats) The demarcation or visual
          representation to use when writing the data;
          default=YAMLValueFormats.DEFAULT
        * tag (str) Custom data-type tag to assign

        Returns: N/A

        Raises:
        - YAMLPathException when the attempted change is impossible
        """
        value_format: YAMLValueFormats = kwargs.pop("value_format",
                                                    YAMLValueFormats.DEFAULT)
        tag: str = kwargs.pop("tag", None)

        self.logger.debug((
            "Attempting to change a node coordinate of type {} to value with"
            " format <{}>:"
            ).format(type(node_coord), value_format),
            data={
                "value": value,
                "node_coord": node_coord
            }, prefix="Processor::_apply_change:  ")

        if isinstance(node_coord.node, NodeCoords):
            self.logger.debug(
                "Unpacked Collector results to apply change:"
                , data=node_coord.node
                , prefix="Processor::_apply_change:  ")
            self._apply_change(yaml_path, node_coord.node, value, **kwargs)

        if (isinstance(node_coord.node, list)
            and len(node_coord.node) > 0
            and isinstance(node_coord.node[0], NodeCoords)
        ):
            for collector_node in node_coord.node:
                self.logger.debug(
                    "Expanded collected Collector results to apply change:"
                    , data=collector_node
                    , prefix="Processor::_apply_change:  ")
                self._apply_change(yaml_path, collector_node, value, **kwargs)
            return

        last_segment = node_coord.path_segment
        if last_segment is not None:
            (_, segment_value) = last_segment
            if (
                isinstance(segment_value, SearchKeywordTerms)
                and segment_value.keyword is PathSearchKeywords.NAME
            ):
                # Rename a key; the new name must not already exist in its
                # parent.
                parent = node_coord.parent
                parentref = node_coord.parentref
                if isinstance(parent, CommentedMap):
                    if value in parent:
                        raise YAMLPathException((
                            "Key, {}, already exists at the same document"
                            " level in YAML Path"
                            ).format(value), str(yaml_path))

                    for i, k in [
                        (idx, key) for idx, key
                        in enumerate(parent.keys())
                        if key == parentref
                    ]:
                        parent.insert(i, value, parent.pop(k))
                        break
                elif isinstance(parent, dict):
                    if value in parent:
                        raise YAMLPathException((
                            "Key, {}, already exists at the same document"
                            " level in YAML Path"
                            ).format(value), str(yaml_path))

                    parent[value] = parent[parentref]
                    del parent[parentref]
                else:
                    raise YAMLPathException((
                        "Keys can be renamed only in Hash/map/dict"
                        " data; got a {}, instead."
                        ).format(type(parent)), str(yaml_path))
                return

        try:
            self._update_node(
                node_coord.parent, node_coord.parentref, value,
                value_format, tag)
        except ValueError as vex:
            raise YAMLPathException(
                "Impossible to write '{}' as {}.  The error was:  {}"
                .format(value, value_format, str(vex))
                , str(yaml_path)) from vex

    def _get_anchor_node(
        self, anchor_path: Union[YAMLPath, str], **kwargs: Any
    ) -> Any:
        """
        Gather the source YAML Anchor node for an Aliasing operation.

        Parameters:
        1. anchor_path (Union[YAMLPath, str]) The YAML Path to a single source
           anchor node; specifying any path which points to more than one node
           will result in a YAMLPathException because YAML does not define
           Aliases for more than one Anchor.

        Keyword Arguments:
        * anchor_name (str) Alternate name to use for the YAML Anchor and its
          Aliases.

        Returns: (Any) The source node

        Raises:
            - `YAMLPathException` when YAML Path is invalid or a supplied
               anchor_name is illegal
        """
        pathsep: PathSeperators = kwargs.pop("pathsep", PathSeperators.AUTO)
        anchor_name: str = kwargs.pop("anchor_name", "")

        if isinstance(anchor_path, str):
            anchor_path = YAMLPath(anchor_path, pathsep)
        elif pathsep is not PathSeperators.AUTO:
            anchor_path.seperator = pathsep

        anchor_node_coordinates: List[NodeCoords] = []
        for node_coords in self._get_required_nodes(self.data, anchor_path):
            self.logger.debug(
                "Gathered YAML Anchor node:",
                prefix="Processor::_get_anchor_node:  ", data=node_coords)
            anchor_node_coordinates.append(node_coords)
        if len(anchor_node_coordinates) > 1:
            raise YAMLPathException(
                "It is impossible to Alias more than one Anchor at a time!",
                str(anchor_path))

        anchor_coord = anchor_node_coordinates[0]
        anchor_node = anchor_coord.node
        if not hasattr(anchor_node, "anchor"):
            anchor_coord.parent[anchor_coord.parentref] = Nodes.wrap_type(
                anchor_node)
            anchor_node = anchor_coord.parent[anchor_coord.parentref]

        known_anchors: Dict[str, Any] = {}
        Anchors.scan_for_anchors(self.data, known_anchors)

        if anchor_name:
            # Rename any pre-existing anchor or set an original anchor name;
            # the assigned name must be unique!
            if anchor_name in known_anchors:
                raise YAMLPathException(
                    "Anchor names must be unique within YAML documents."
                    "  Anchor name, {}, is already used."
                    .format(anchor_name), str(anchor_path))
            anchor_node.yaml_set_anchor(anchor_name, always_dump=True)
        elif anchor_node.anchor.value:
            # The source node already has an anchor name
            anchor_name = anchor_node.anchor.value
        else:
            # An orignial, unique-to-the-document anchor name must be generated
            new_anchor = Anchors.generate_unique_anchor_name(
                self.data, anchor_coord, known_anchors)
            anchor_node.yaml_set_anchor(new_anchor, always_dump=True)

        return anchor_node

    def ymk_nodes(
        self, yaml_path: Union[YAMLPath, str],
        anchor_path: Union[YAMLPath, str], **kwargs: Any
    ) -> None:
        """Add a YAML Merge Key to YAML Path specified nodes."""
        pathsep: PathSeperators = kwargs.pop("pathsep", PathSeperators.AUTO)
        anchor_name: str = kwargs.pop("anchor_name", "")

        if self.data is None:
            self.logger.debug(
                "Refusing to set a YAML Merge Key to nodes in a null"
                " document!",
                prefix="Processor::ymk_nodes:  ", data=self.data)
            return

        if isinstance(yaml_path, str):
            yaml_path = YAMLPath(yaml_path, pathsep)
        elif pathsep is not PathSeperators.AUTO:
            yaml_path.seperator = pathsep

        anchor_node = self._get_anchor_node(
            anchor_path, pathsep=pathsep, anchor_name=anchor_name)

        gathered_nodes: List[NodeCoords] = []
        for node_coords in self._get_required_nodes(self.data, yaml_path):
            self.logger.debug(
                "Gathered node for YAML Merge Key assignment:",
                prefix="Processor::ymk_nodes:  ", data=node_coords)
            gathered_nodes.append(node_coords)

        if len(gathered_nodes) > 0:
            self._ymk_nodes(gathered_nodes, anchor_node, yaml_path)

    def ymk_gathered_nodes(
        self, gathered_nodes: List[NodeCoords],
        anchor_path: Union[YAMLPath, str], target_path: Union[YAMLPath, str],
        **kwargs: Any
    ) -> None:
        """Add a YAML Merge Key to pre-gathered nodes."""
        pathsep: PathSeperators = kwargs.pop("pathsep", PathSeperators.AUTO)
        anchor_name: str = kwargs.pop("anchor_name", "")

        if self.data is None:
            self.logger.debug(
                "Refusing to set a YAML Merge Key to nodes in a null"
                " document!",
                prefix="Processor::ymk_gathered_nodes:  ", data=self.data)
            return

        anchor_node = self._get_anchor_node(
            anchor_path, pathsep=pathsep, anchor_name=anchor_name)

        if gathered_nodes:
            self._ymk_nodes(gathered_nodes, anchor_node, target_path)

    def _ymk_nodes(
        self, gathered_nodes: List[NodeCoords], anchor_node: Any,
        target_path: Union[YAMLPath, str]
    ) -> None:
        """Add a YAML Merge Key to nodes."""
        anchor_name = anchor_node.anchor.value
        for node_coord in gathered_nodes:
            self.logger.debug(
                "Attempting to add YAML Merge Key for node to {}:"
                .format(anchor_name),
                data=node_coord,
                prefix="yaml_set::_ymk_nodes:  ")
            node = node_coord.node
            if not isinstance(node, CommentedMap):
                raise YAMLPathException(
                    "Cannot add YAML Merge Keys to non-Hash nodes specified"
                    " by",
                    str(target_path))

            refs = node.merge if hasattr(node, "merge") else []
            already_refed = False
            for (_, ref_node) in refs:
                if ref_node == anchor_node:
                    already_refed = True
                    break
            if already_refed:
                continue

            node_coord.node.add_yaml_merge([(len(refs), anchor_node)])

    def alias_nodes(
        self, yaml_path: Union[YAMLPath, str],
        anchor_path: Union[YAMLPath, str], **kwargs: Any
    ) -> None:
        """
        Gather and assign YAML Aliases to nodes at YAML Path in data.

        Parameters:
        1. yaml_path (Union[YAMLPath, str]) The YAML Path to all target nodes
           which will become Aliases to the Anchor node specified via
           `anchor_path`.
        2. anchor_path (Union[YAMLPath, str]) The YAML Path to a single source
           anchor node; specifying any path which points to more than one node
           will result in a YAMLPathException because YAML does not define
           Aliases for more than one Anchor.

        Keyword Arguments:
        * pathsep (PathSeperators) Forced YAML Path segment seperator; set
          only when automatic inference fails;
          default = PathSeperators.AUTO
        * anchor_name (str) Override the Alias name to any non-empty name you
          set; attempts to re-use an existing Anchor name will result in a
          YAMLPathException.

        Returns:  N/A

        Raises:
            - `YAMLPathException` when YAML Path is invalid
        """
        pathsep: PathSeperators = kwargs.pop("pathsep", PathSeperators.AUTO)
        anchor_name: str = kwargs.pop("anchor_name", "")

        if self.data is None:
            self.logger.debug(
                "Refusing to alias nodes in a null document!",
                prefix="Processor::alias_nodes:  ", data=self.data)
            return

        if isinstance(yaml_path, str):
            yaml_path = YAMLPath(yaml_path, pathsep)
        elif pathsep is not PathSeperators.AUTO:
            yaml_path.seperator = pathsep

        anchor_node = self._get_anchor_node(
            anchor_path, pathsep=pathsep, anchor_name=anchor_name)

        gathered_nodes: List[NodeCoords] = []
        for node_coords in self._get_required_nodes(self.data, yaml_path):
            self.logger.debug(
                "Gathered node for YAML Alias assignment:",
                prefix="Processor::alias_nodes:  ", data=node_coords)
            gathered_nodes.append(node_coords)

        if len(gathered_nodes) > 0:
            self._alias_nodes(gathered_nodes, anchor_node)

    def alias_gathered_nodes(
        self, gathered_nodes: List[NodeCoords],
        anchor_path: Union[YAMLPath, str], **kwargs: Any
    ) -> None:
        """
        Assign a YAML Anchor to zero or more YAML Alias nodes.

        Parameters:
        1. gathered_nodes (List[NodeCoords]) The pre-gathered nodes to assign
        2. anchor_path (Union[YAMLPath, str]) YAML Path to the source Anchor

        Keyword Arguments:
        * pathsep (PathSeperators) Forced YAML Path segment seperator; set
          only when automatic inference fails;
          default = PathSeperators.AUTO
        * anchor_name (str) Override automatic anchor name; use this, instead

        Returns:  N/A

        Raises:  N/A
        """
        pathsep: PathSeperators = kwargs.pop("pathsep", PathSeperators.AUTO)
        anchor_name: str = kwargs.pop("anchor_name", "")

        if self.data is None:
            self.logger.debug(
                "Refusing to alias nodes in a null document!",
                prefix="Processor::alias_gathered_nodes:  ", data=self.data)
            return

        anchor_node = self._get_anchor_node(
            anchor_path, pathsep=pathsep, anchor_name=anchor_name)

        if gathered_nodes:
            self._alias_nodes(gathered_nodes, anchor_node)

    def _alias_nodes(
        self, gathered_nodes: List[NodeCoords], anchor_node: Any
    ) -> None:
        """
        Assign a YAML Anchor to its various YAML Alias nodes.

        Parameters:
        1. gathered_nodes (List[NodeCoords]) The pre-gathered nodes to assign.
        2. anchor_node (Any) The source YAML Anchor node.

        Returns:  N/A
        """
        anchor_name = anchor_node.anchor.value
        for node_coord in gathered_nodes:
            self.logger.debug(
                "Attempting to set the anchor name for node to {}:"
                .format(anchor_name),
                data=node_coord,
                prefix="yaml_set::_alias_nodes:  ")
            node_coord.parent[node_coord.parentref] = anchor_node

    def tag_nodes(
        self, yaml_path: Union[YAMLPath, str], tag: str, **kwargs: Any
    ) -> None:
        """
        Gather and assign a data-type tag to nodes at YAML Path in data.

        Parameters:
        1. yaml_path (Union[YAMLPath, str]) The YAML Path to evaluate
        2. tag (str) The tag to assign

        Keyword Arguments:
        * pathsep (PathSeperators) Forced YAML Path segment seperator; set
          only when automatic inference fails;
          default = PathSeperators.AUTO

        Returns:  N/A

        Raises:
        - `YAMLPathException` when YAML Path is invalid
        """
        pathsep: PathSeperators = kwargs.pop("pathsep", PathSeperators.AUTO)

        if self.data is None:
            self.logger.debug(
                "Refusing to tag nodes from a null document!",
                prefix="Processor::tag_nodes:  ", data=self.data)
            return

        if isinstance(yaml_path, str):
            yaml_path = YAMLPath(yaml_path, pathsep)
        elif pathsep is not PathSeperators.AUTO:
            yaml_path.seperator = pathsep

        gathered_nodes: List[NodeCoords] = []
        for node_coords in self._get_required_nodes(self.data, yaml_path):
            self.logger.debug(
                "Gathered node for tagging:",
                prefix="Processor::tag_nodes:  ", data=node_coords)
            gathered_nodes.append(node_coords)

        if len(gathered_nodes) > 0:
            self.tag_gathered_nodes(gathered_nodes, tag)

    def tag_gathered_nodes(
        self, gathered_nodes: List[NodeCoords], tag: str
    ) -> None:
        """
        Assign a data-type tag to a set of nodes.

        Parameters:
        1. gathered_nodes (List[NodeCoords]) The nodes to affect
        2. tag (str) The tag to assign

        Returns:  N/A
        """
        # A YAML tag must be prefixed via at least one bang (!)
        if tag and not tag[0] == "!":
            tag = "!{}".format(tag)

        for node_coord in gathered_nodes:
            old_node = node_coord.node
            if node_coord.parent is None:
                node_coord.node.yaml_set_tag(tag)
            else:
                node_coord.parent[node_coord.parentref] = Nodes.apply_yaml_tag(
                    node_coord.node, tag)
                if Anchors.get_node_anchor(old_node) is not None:
                    Anchors.replace_anchor(
                        self.data, old_node,
                        node_coord.parent[node_coord.parentref])

    def delete_nodes(
        self, yaml_path: Union[YAMLPath, str], **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """
        Gather and delete nodes at YAML Path in data.

        Parameters:
        1. yaml_path (Union[YAMLPath, str]) The YAML Path to evaluate

        Keyword Arguments:
        * pathsep (PathSeperators) Forced YAML Path segment seperator; set
          only when automatic inference fails;
          default = PathSeperators.AUTO

        Returns:  (Generator) Affected NodeCoords before they are deleted

        Raises:
            - `YAMLPathException` when YAML Path is invalid
        """
        pathsep: PathSeperators = kwargs.pop("pathsep", PathSeperators.AUTO)

        if self.data is None:
            self.logger.debug(
                "Refusing to delete nodes from a null document!",
                prefix="Processor::delete_nodes:  ", data=self.data)
            return

        if isinstance(yaml_path, str):
            yaml_path = YAMLPath(yaml_path, pathsep)
        elif pathsep is not PathSeperators.AUTO:
            yaml_path.seperator = pathsep

        # Nodes must be processed in reverse order while deleting them to avoid
        # corrupting list element indecies, thereby deleting the wrong nodes.
        # As such, the intended nodes must be first gathered into a list.
        gathered_nodes: List[NodeCoords] = []
        for node_coords in self._get_required_nodes(self.data, yaml_path):
            self.logger.debug(
                "Gathered node for deletion:",
                prefix="Processor::delete_nodes:  ", data=node_coords)
            gathered_nodes.append(node_coords)
            yield node_coords

        if len(gathered_nodes) > 0:
            self._delete_nodes(gathered_nodes)

    def delete_gathered_nodes(self, gathered_nodes: List[NodeCoords]) -> None:
        """
        Delete pre-gathered nodes.

        Parameters:
        1. gathered_nodes (List[NodeCoords]) The pre-gathered nodes to delete.
        """
        self._delete_nodes(gathered_nodes)

    def _delete_nodes(self, delete_nodes: List[NodeCoords]) -> None:
        """
        Recursively delete specified nodes.

        Parameters:
        1. delete_nodes (List[NodeCoords]) The nodes to delete.

        Raises:
        - `YAMLPathException` when the operation would destroy the entire
           document
        """
        # pylint: disable=locally-disabled,too-many-nested-blocks
        for delete_nc in reversed(delete_nodes):
            node = delete_nc.node
            parent = delete_nc.parent
            parentref = delete_nc.parentref
            ancestry = delete_nc.ancestry
            self.logger.debug(
                "Deleting node:",
                prefix="yaml_set::delete_nodes:  ",
                data_header="!" * 80,
                footer="!" * 80,
                data=delete_nc)

            # Ensure the reference exists before attempting to delete it
            if isinstance(node, list) and isinstance(node[0], NodeCoords):
                self._delete_nodes(node)
            elif isinstance(node, NodeCoords):
                self._delete_nodes([node])
            elif isinstance(parent, (CommentedMap, dict)):
                all_data = ancestry[0][0] if len(ancestry) > 0 else parent
                all_anchors: Dict[str, Any] = {}
                Anchors.scan_for_anchors(all_data, all_anchors)
                compare_node = (all_anchors[parentref]
                                if parentref in all_anchors
                                else None)
                is_ymk_anchor = (
                    compare_node is not None
                    and isinstance(compare_node, dict))

                if (is_ymk_anchor
                    and isinstance(parent, CommentedMap)
                    and hasattr(parent, "merge")
                    and len(parent.merge) > 0
                ):
                    for (midx, merge_node) in parent.merge:
                        if merge_node == compare_node:
                            for (key, val) in merge_node.items():
                                if key in parent and parent[key] == val:
                                    del parent[key]
                            del parent.merge[midx]
                            break
                elif parentref in parent:
                    del parent[parentref]
            elif isinstance(parent, (CommentedSeq, list)):
                if len(parent) > parentref:
                    del parent[parentref]
            elif isinstance(parent, (CommentedSet, set)):
                parent.discard(parentref)
            else:
                # Edge-case:  Attempt to delete from a document which is
                # entirely one Scalar value OR user is deleting the entire
                # document.
                raise YAMLPathException(
                    "Refusing to delete the entire document!  Ensure the"
                    " source document is YAML, JSON, or compatible and the"
                    " target nodes do not include the document root.",
                    str(delete_nc.path)
                )

    # pylint: disable=locally-disabled,too-many-branches,too-many-locals
    def _get_nodes_by_path_segment(
        self, data: Any, yaml_path: YAMLPath, segment_index: int, **kwargs: Any
    ) -> Generator[Any, None, None]:
        """
        Get nodes identified by their YAML Path segment.

        Returns zero or more NodeCoords *or* List[NodeCoords] identified by one
        segment of a YAML Path within the present data context.

        Parameters:
        1. data (ruamel.yaml data) The parsed YAML data to process
        2. yaml_path (yamlpath.Path) The YAML Path being processed
        3. segment_index (int) Segment index of the YAML Path to process

        Keyword Arguments:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent
        * traverse_lists (Boolean) Indicate whether KEY searches against lists
          are permitted to automatically traverse into the list; Default=True
        * translated_path (YAMLPath) YAML Path indicating precisely which node
          is being evaluated
        * ancestry (List[AncestryEntry]) Stack of ancestors preceding the
          present node under evaluation

        Returns:  (Generator[Any, None, None]) Each node coordinate or list of
        node coordinates as they are matched.  You must check with isinstance()
        to determine whether you have received a NodeCoords or a
        List[NodeCoords].

        Raises:
        - `NotImplementedError` when the segment indicates an unknown
          PathSegmentTypes value.
        """
        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        traverse_lists: bool = kwargs.pop("traverse_lists", True)
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))
        ancestry: List[AncestryEntry] = kwargs.pop("ancestry", [])
        segments = yaml_path.escaped
        if not (segments and len(segments) > segment_index):
            self.logger.debug(
                "Bailing out because there are not {} segments in:"
                .format(segment_index),
                prefix="Processor::_get_nodes_by_path_segment:  ",
                data=segments)
            return

        pathseg: PathSegment = yaml_path.unescaped[segment_index]
        (unesc_type, unesc_attrs) = pathseg
        (segment_type, stripped_attrs) = segments[segment_index]

        # Disallow traversal recursion (because it creates a denial-of-service)
        if segment_index > 0 and segment_type == PathSegmentTypes.TRAVERSE:
            (prior_segment_type, _) = segments[segment_index - 1]
            if prior_segment_type == PathSegmentTypes.TRAVERSE:
                raise YAMLPathException(
                    "Repeating traversals are not allowed because they cause"
                    " recursion which leads to excessive CPU and RAM"
                    " consumption while yielding no additional useful data",
                    str(yaml_path), "**")

        # NodeCoords cannot be directly evaluated as data, so pull out their
        # wrapped data for evaluation.
        if isinstance(data, NodeCoords):
            ancestry = data.ancestry
            translated_path = YAMLPath(data.path)
            parent = data.parent
            parentref = data.parentref
            data = data.node

        node_coords: Any = None
        if segment_type == PathSegmentTypes.KEY:
            node_coords = self._get_nodes_by_key(
                data, yaml_path, segment_index, traverse_lists=traverse_lists,
                translated_path=translated_path, ancestry=ancestry)
        elif segment_type == PathSegmentTypes.INDEX:
            node_coords = self._get_nodes_by_index(
                data, yaml_path, segment_index,
                translated_path=translated_path, ancestry=ancestry)
        elif segment_type == PathSegmentTypes.ANCHOR:
            node_coords = self._get_nodes_by_anchor(
                data, yaml_path, segment_index,
                translated_path=translated_path, ancestry=ancestry)
        elif (
                segment_type == PathSegmentTypes.KEYWORD_SEARCH
                and isinstance(stripped_attrs, SearchKeywordTerms)
        ):
            node_coords = self._get_nodes_by_keyword_search(
                data, yaml_path, stripped_attrs, parent=parent,
                parentref=parentref, traverse_lists=traverse_lists,
                translated_path=translated_path, ancestry=ancestry,
                relay_segment=pathseg)
        elif (
                segment_type == PathSegmentTypes.SEARCH
                and isinstance(stripped_attrs, SearchTerms)
        ):
            node_coords = self._get_nodes_by_search(
                data, stripped_attrs, parent=parent, parentref=parentref,
                traverse_lists=traverse_lists, translated_path=translated_path,
                ancestry=ancestry)
        elif (
                unesc_type == PathSegmentTypes.COLLECTOR
                and isinstance(unesc_attrs, CollectorTerms)
        ):
            node_coords = self._get_nodes_by_collector(
                data, yaml_path, segment_index, unesc_attrs, parent=parent,
                parentref=parentref, translated_path=translated_path,
                ancestry=ancestry)
        elif segment_type == PathSegmentTypes.TRAVERSE:
            node_coords = self._get_nodes_by_traversal(
                data, yaml_path, segment_index, parent=parent,
                parentref=parentref, translated_path=translated_path,
                ancestry=ancestry)
        else:
            raise NotImplementedError

        for node_coord in node_coords:
            yield node_coord

    def _get_nodes_by_key(
        self, data: Any, yaml_path: YAMLPath, segment_index: int, **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """
        Get nodes from a Hash by their unique key name.

        Returns zero or more NodeCoords identified by a dict key found at a
        specific segment of a YAML Path within the present data context.

        Parameters:
        1. data (ruamel.yaml data) The parsed YAML data to process
        2. yaml_path (yamlpath.Path) The YAML Path being processed
        3. segment_index (int) Segment index of the YAML Path to process

        Keyword Arguments:
        * traverse_lists (Boolean) Indicate whether KEY searches against lists
          are permitted to automatically traverse into the list; Default=True
        * translated_path (YAMLPath) YAML Path indicating precisely which node
          is being evaluated
        * ancestry (List[AncestryEntry]) Stack of ancestors preceding the
          present node under evaluation

        Returns:  (Generator[NodeCoords, None, None]) Each NodeCoords as they
        are matched

        Raises:  N/A
        """
        traverse_lists: bool = kwargs.pop("traverse_lists", True)
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))
        ancestry: List[AncestryEntry] = kwargs.pop("ancestry", [])

        pathseg: PathSegment = yaml_path.escaped[segment_index]
        (_, stripped_attrs) = pathseg
        str_stripped = str(stripped_attrs)
        next_ancestry: List[AncestryEntry] = []

        self.logger.debug((
            "Seeking KEY node, {}, in data:"
            ).format(str_stripped),
            prefix="Processor::_get_nodes_by_key:  ",
            data={"KEY": stripped_attrs,
                  "DATA": data})

        if isinstance(data, dict):
            next_translated_path = (translated_path +
                YAMLPath.escape_path_section(
                    str_stripped, translated_path.seperator))
            next_ancestry = ancestry + [(data, stripped_attrs)]
            if stripped_attrs in data:
                self.logger.debug(
                    "Processor::_get_nodes_by_key:  FOUND key node by name at"
                    " {}."
                    .format(str_stripped))
                yield NodeCoords(
                    data[stripped_attrs], data, stripped_attrs,
                    next_translated_path, next_ancestry, pathseg)
            else:
                # Check for a string/int type mismatch
                try:
                    intkey = int(str_stripped)
                    if intkey in data:
                        yield NodeCoords(
                            data[intkey], data, intkey, next_translated_path,
                            ancestry + [(data, intkey)], pathseg)
                except ValueError:
                    pass

        elif isinstance(data, list):
            try:
                # Try using the ref as a bare Array index
                idx = int(str_stripped)
                if len(data) > idx:
                    self.logger.debug(
                        "Processor::_get_nodes_by_key:  FOUND key node as a"
                        " bare Array index at [{}]."
                        .format(str_stripped))
                    next_translated_path = translated_path + "[{}]".format(idx)
                    next_ancestry = ancestry + [(data, idx)]
                    yield NodeCoords(
                        data[idx], data, idx,
                        next_translated_path, next_ancestry, pathseg)
            except ValueError:
                # Pass-through search against possible Array-of-Hashes, if
                # allowed.
                if not traverse_lists:
                    self.logger.debug(
                        "Processor::_get_nodes_by_key:  Refusing to traverse a"
                        " list.")
                    return

                for eleidx, element in enumerate(data):
                    next_translated_path = translated_path + "[{}]".format(
                        eleidx)
                    next_ancestry = ancestry + [(data, stripped_attrs)]
                    for node_coord in self._get_nodes_by_path_segment(
                            element, yaml_path, segment_index, parent=data,
                            parentref=eleidx, traverse_lists=traverse_lists,
                            translated_path=next_translated_path,
                            ancestry=next_ancestry):
                        self.logger.debug(
                            "Processor::_get_nodes_by_key:  FOUND key node "
                            " via pass-through Array-of-Hashes search at {}."
                            .format(next_translated_path))
                        yield node_coord

        elif isinstance(data, (set, CommentedSet)):
            for ele in data:
                if ele == stripped_attrs or (
                    isinstance(ele, TaggedScalar)
                    and ele.value == stripped_attrs
                ):
                    self.logger.debug((
                        "Processor::_get_nodes_by_key:  FOUND set node by"
                        " name at {}."
                        ).format(str_stripped))
                    next_translated_path = (translated_path +
                        YAMLPath.escape_path_section(
                            ele, translated_path.seperator))
                    next_ancestry = ancestry + [(data, ele)]
                    yield NodeCoords(
                        ele, data, stripped_attrs,
                        next_translated_path, next_ancestry, pathseg)
                    break

    # pylint: disable=locally-disabled,too-many-locals
    def _get_nodes_by_index(
        self, data: Any, yaml_path: YAMLPath, segment_index: int, **kwargs
    ) -> Generator[NodeCoords, None, None]:
        """
        Get nodes from a List by their index.

        Returns zero or more NodeCoords identified by a list element index
        found at a specific segment of a YAML Path within the present data
        context.

        Parameters:
        1. data (Any) The parsed YAML data to process
        2. yaml_path (YAMLPath) The YAML Path being processed
        3. segment_index (int) Segment index of the YAML Path to process

        Keyword Arguments:
        * translated_path (YAMLPath) YAML Path indicating precisely which node
          is being evaluated
        * ancestry (List[AncestryEntry]) Stack of ancestors preceding the
          present node under evaluation

        Returns:  (Generator[NodeCoords, None, None]) Each NodeCoords as they
            are matched

        Raises:  N/A
        """
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))
        ancestry: List[AncestryEntry] = kwargs.pop("ancestry", [])

        pathseg: PathSegment = yaml_path.escaped[segment_index]
        (_, stripped_attrs) = pathseg
        (_, unstripped_attrs) = yaml_path.unescaped[segment_index]
        str_stripped = str(stripped_attrs)

        self.logger.debug(
            "Processor::_get_nodes_by_index:  Seeking INDEX node at {}."
            .format(str_stripped))

        if ':' in str_stripped:
            # Array index or Hash key slice
            slice_parts: List[str] = str_stripped.split(':', 1)
            min_match: str = slice_parts[0]
            max_match: str = slice_parts[1]
            if isinstance(data, list):
                try:
                    intmin: int = int(min_match)
                    intmax: int = int(max_match)
                except ValueError as wrap_ex:
                    raise YAMLPathException(
                        "{} is not an integer array slice"
                        .format(str_stripped),
                        str(yaml_path),
                        str(unstripped_attrs)
                    ) from wrap_ex

                if intmin == intmax and len(data) > intmin:
                    yield NodeCoords(
                        [data[intmin]], data, intmin,
                        translated_path + "[{}]".format(intmin),
                        ancestry + [(data, intmin)], pathseg)
                else:
                    sliced_elements = []
                    for slice_index in range(intmin, intmax):
                        sliced_elements.append(NodeCoords(
                            data[slice_index], data, intmin,
                            translated_path + "[{}]".format(slice_index),
                            ancestry + [(data, slice_index)], pathseg))
                    yield NodeCoords(
                        sliced_elements, data, intmin,
                        translated_path + "[{}:{}]".format(intmin, intmax),
                        ancestry + [(data, intmin)], pathseg)

            elif isinstance(data, dict):
                for key, val in data.items():
                    if min_match <= key <= max_match:
                        yield NodeCoords(
                            val, data, key,
                            translated_path + YAMLPath.escape_path_section(
                                key, translated_path.seperator),
                            ancestry + [(data, key)], pathseg)

            elif isinstance(data, (CommentedSet, set)):
                for ele in data:
                    if min_match <= ele <= max_match:
                        yield NodeCoords(
                            ele, data, ele,
                            translated_path + YAMLPath.escape_path_section(
                                ele, translated_path.seperator),
                            ancestry + [(data, ele)], pathseg)
        else:
            try:
                idx: int = int(str_stripped)
            except ValueError as wrap_ex:
                raise YAMLPathException(
                    "{} is not an integer array index"
                    .format(str_stripped),
                    str(yaml_path),
                    str(unstripped_attrs)
                ) from wrap_ex

            if isinstance(data, list) and len(data) > idx:
                yield NodeCoords(
                    data[idx], data, idx, translated_path + "[{}]".format(idx),
                    ancestry + [(data, idx)], pathseg)

            elif isinstance(data, (CommentedSet, set)):
                raise YAMLPathException(
                    "Array indexing is invalid against unordered set data"
                    " because element positioning is not guaranteed in"
                    " unordered data; rather, match set entries by their"
                    " actual values.  This error was encountered",
                    str(yaml_path),
                    str(unstripped_attrs)
                )

    def _get_nodes_by_anchor(
        self, data: Any, yaml_path: YAMLPath, segment_index: int, **kwargs
    ) -> Generator[NodeCoords, None, None]:
        """
        Get nodes matching an Anchor name.

        Returns zero or more NodeCoords identified by an Anchor name found at a
        specific segment of a YAML Path within the present data context.

        Parameters:
        1. data (Any) The parsed YAML data to process
        2. yaml_path (YAMLPath) The YAML Path being processed
        3. segment_index (int) Segment index of the YAML Path to process

        Keyword Arguments:
        * translated_path (YAMLPath) YAML Path indicating precisely which node
          is being evaluated
        * ancestry (List[AncestryEntry]) Stack of ancestors preceding the
          present node under evaluation

        Returns:  (Generator[NodeCoords, None, None]) Each NodeCoords as they
        are matched

        Raises:  N/A
        """
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))
        ancestry: List[AncestryEntry] = kwargs.pop("ancestry", [])

        pathseg: PathSegment = yaml_path.escaped[segment_index]
        (_, stripped_attrs) = pathseg
        next_translated_path = translated_path + "[&{}]".format(
            YAMLPath.escape_path_section(
                str(stripped_attrs), translated_path.seperator))

        self.logger.debug(
            "Processor::_get_nodes_by_anchor:  Seeking ANCHOR node at {}."
            .format(stripped_attrs))

        if isinstance(data, list):
            for lstidx, ele in enumerate(data):
                if (hasattr(ele, "anchor")
                        and stripped_attrs == ele.anchor.value):
                    yield NodeCoords(ele, data, lstidx, next_translated_path,
                        ancestry + [(data, lstidx)], pathseg)
        elif isinstance(data, (CommentedMap, dict)):
            if (isinstance(data, CommentedMap)
                and hasattr(data, "merge")
                and len(data.merge) > 0
            ):
                all_anchors: Dict[str, Any] = {}
                Anchors.scan_for_anchors(self.data, all_anchors)
                compare_node = (all_anchors[str(stripped_attrs)]
                                if stripped_attrs in all_anchors
                                else None)
                if compare_node:
                    for merge_tuple in data.merge:
                        merge_node = merge_tuple[1]
                        self.logger.debug((
                            "Comparing YAML Merge Key against ANCHOR node {}:"
                            ).format(stripped_attrs),
                            prefix="Processor::_get_nodes_by_anchor:  ",
                            data={
                                "merge_node": merge_node,
                                "anchor_node": compare_node
                            })
                        if merge_node == compare_node:
                            next_ancestry = ancestry + [(data, merge_node)]
                            yield NodeCoords(
                                compare_node, data,
                                stripped_attrs, next_translated_path,
                                next_ancestry, pathseg)
                            break

            for key, val in data.items():
                next_ancestry = ancestry + [(data, key)]
                if (hasattr(key, "anchor")
                        and stripped_attrs == key.anchor.value):
                    yield NodeCoords(
                        val, data, key, next_translated_path,
                        next_ancestry, pathseg)
                elif (hasattr(val, "anchor")
                      and stripped_attrs == val.anchor.value):
                    yield NodeCoords(
                        val, data, key, next_translated_path,
                        next_ancestry, pathseg)
        elif isinstance(data, (CommentedSet, set)):
            for ele in data:
                if (hasattr(ele, "anchor")
                        and stripped_attrs == ele.anchor.value):
                    yield NodeCoords(ele, data, ele, next_translated_path,
                        ancestry + [(data, ele)], pathseg)

    def _get_nodes_by_keyword_search(
        self, data: Any, yaml_path: YAMLPath, terms: SearchKeywordTerms,
        **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """
        Perform a search identified by a keyword and its parameters.

        Parameters:
        1. data (Any) The parsed YAML data to process
        2. yaml_path (YAMLPath) The YAML Path being processed
        3. terms (SearchKeywordTerms) The keyword search terms

        Keyword Arguments:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent
        * traverse_lists (Boolean) Indicate whether searches against lists are
          permitted to automatically traverse into the list; Default=True
        * translated_path (YAMLPath) YAML Path indicating precisely which node
          is being evaluated
        * ancestry (List[AncestryEntry]) Stack of ancestors preceding the
          present node under evaluation

        Returns:  (Generator[NodeCoords, None, None]) Each NodeCoords as they
            are matched

        Raises:  N/A
        """
        self.logger.debug(
            "Seeking KEYWORD_SEARCH nodes matching {} in data:".format(terms),
            data=data,
            prefix="Processor::_get_nodes_by_keyword_search:  ")

        for res_nc in KeywordSearches.search_matches(
            terms, data, yaml_path, **kwargs
        ):
            self.logger.debug(
                "Yielding keyword search match:",
                data=res_nc,
                prefix="Processor::_get_nodes_by_keyword_search:  ")
            yield res_nc

    # pylint: disable=too-many-statements
    def _get_nodes_by_search(
        self, data: Any, terms: SearchTerms, **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """
        Get nodes matching a search expression.

        Searches the the current data context for all NodeCoords matching a
        search expression.

        Parameters:
        1. data (Any) The parsed YAML data to process
        2. terms (SearchTerms) The search terms

        Keyword Arguments:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent
        * traverse_lists (Boolean) Indicate whether searches against lists are
          permitted to automatically traverse into the list; Default=True
        * translated_path (YAMLPath) YAML Path indicating precisely which node
          is being evaluated
        * ancestry (List[AncestryEntry]) Stack of ancestors preceding the
          present node under evaluation

        Returns:  (Generator[NodeCoords, None, None]) Each NodeCoords as they
        are matched

        Raises:  N/A
        """
        self.logger.debug(
            "Seeking SEARCH nodes matching {} in data:".format(terms),
            data=data,
            prefix="Processor::_get_nodes_by_search:  ")

        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        traverse_lists: bool = kwargs.pop("traverse_lists", True)
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))
        pathseg: PathSegment = (PathSegmentTypes.SEARCH, terms)
        ancestry: List[AncestryEntry] = kwargs.pop("ancestry", [])

        invert = terms.inverted
        method = terms.method
        attr = terms.attribute
        term = terms.term
        matches = False
        desc_path = YAMLPath(attr)
        debug_matched = "NO MATCHES YIELDED"
        if isinstance(data, list):
            if not traverse_lists:
                self.logger.debug(
                    "Processor::_get_nodes_by_search:  Refusing to traverse a"
                    " list.")
                return

            is_aoh = Nodes.node_is_aoh(data, accept_nulls=True)
            search_keys = attr == '.'
            for lstidx, ele in enumerate(data):
                if search_keys:
                    # pylint: disable=locally-disabled,consider-using-ternary
                    matches = ((is_aoh and term in ele)
                        or Searches.search_matches(method, term, ele))
                elif isinstance(ele, dict) and attr in ele:
                    matches = Searches.search_matches(method, term, ele[attr])
                else:
                    # Attempt a descendant search
                    next_translated_path = translated_path + "[{}]".format(
                        lstidx)
                    next_ancestry = ancestry + [(data, lstidx)]
                    for desc_node in self._get_required_nodes(
                        ele, desc_path, 0,
                        translated_path=next_translated_path,
                        ancestry=next_ancestry, relay_segment=pathseg
                    ):
                        matches = Searches.search_matches(
                            method, term, desc_node.node)
                        break

                if (matches and not invert) or (invert and not matches):
                    debug_matched = "one list match yielded"
                    self.logger.debug(
                        "Yielding list match at index {}:".format(lstidx),
                        data=ele,
                        prefix="Processor::_get_nodes_by_search:  ")
                    yield NodeCoords(
                        ele, data, lstidx,
                        translated_path + "[{}]".format(lstidx),
                        ancestry + [(data, lstidx)], pathseg)

        elif isinstance(data, dict):
            # Allow . to mean "each key's name"
            if attr == '.':
                self.logger.debug(
                    "Scanning every key's name...",
                    prefix="Processor::_get_nodes_by_search:  ")
                for key, val in data.items():
                    matches = Searches.search_matches(method, term, key)
                    if (matches and not invert) or (invert and not matches):
                        debug_matched = "one dictionary key name match yielded"
                        self.logger.debug(
                            "Yielding dictionary key name match against '{}':"
                            .format(key),
                            data=val,
                            prefix="Processor::_get_nodes_by_search:  ")
                        yield NodeCoords(
                            val, data, key,
                            translated_path + YAMLPath.escape_path_section(
                                key, translated_path.seperator),
                            ancestry + [(data, key)], pathseg)

            elif attr in data:
                value = data[attr]
                matches = Searches.search_matches(method, term, value)
                self.logger.debug(
                    "Scanning for an attribute match against {}, which {}."
                    .format(attr, "matches" if matches else "does not match"),
                    prefix="Processor::_get_nodes_by_search:  ")
                if (matches and not invert) or (invert and not matches):
                    debug_matched = "one dictionary attribute match yielded"
                    self.logger.debug(
                        "Yielding dictionary attribute match against '{}':"
                        .format(attr),
                        data=value,
                        prefix="Processor::_get_nodes_by_search:  ")
                    yield NodeCoords(
                        value, data, attr,
                        translated_path + YAMLPath.escape_path_section(
                            attr, translated_path.seperator),
                        ancestry + [(data, attr)], pathseg)

            else:
                # Attempt a descendant search; return every node which has ANY
                # descendent matching the search expression.
                self.logger.debug((
                    "Attempting a descendant search against data at"
                    " desc_path={}, translated_path={}:"
                    ).format(desc_path, translated_path),
                    prefix="Processor::_get_nodes_by_search:  ",
                    data=data)
                for desc_node in self._get_required_nodes(
                    data, desc_path, 0, parent=parent, parentref=parentref,
                    translated_path=translated_path, ancestry=ancestry,
                    relay_segment=pathseg
                ):
                    matches = Searches.search_matches(
                        method, term, desc_node.node)

                    if (matches and not invert) or (invert and not matches):
                        # Search no further because the parent node of this
                        # search has at least one matching descendent.
                        self.logger.debug((
                            "BREAKING OUT of descendent search with matches={}"
                            " and invert={}").format(
                                "matching" if matches else "NOT matching",
                                "yes" if invert else "no"),
                            prefix="Processor::_get_nodes_by_search:  ")
                        break

                if (matches and not invert) or (invert and not matches):
                    debug_matched = "one descendant search match yielded"
                    self.logger.debug(
                        "Yielding descendant match against '{}':"
                        .format(attr),
                        data=data,
                        prefix="Processor::_get_nodes_by_search:  ")
                    yield NodeCoords(
                        data, parent, parentref, translated_path, ancestry,
                        pathseg)

        elif isinstance(data, (CommentedSet, set)):
            for ele in data:
                matches = Searches.search_matches(method, term, ele)

                if (matches and not invert) or (invert and not matches):
                    debug_matched = "one set match yielded"
                    self.logger.debug(
                        "Yielding set match at value {}:".format(ele),
                        prefix="Processor::_get_nodes_by_search:  ")
                    yield NodeCoords(
                        ele, data, ele,
                        translated_path + YAMLPath.escape_path_section(
                            ele, translated_path.seperator),
                        ancestry + [(data, ele)], pathseg)

        else:
            # Check the passed data itself for a match
            matches = Searches.search_matches(method, term, data)
            if (matches and not invert) or (invert and not matches):
                debug_matched = "query source data itself yielded"
                self.logger.debug(
                    "Yielding the queried data itself because it matches.",
                    prefix="Processor::_get_nodes_by_search:  ")
                yield NodeCoords(
                    data, parent, parentref, translated_path, ancestry,
                    pathseg)

        self.logger.debug(
            "Finished seeking SEARCH nodes matching {} in data with {}:"
            .format(terms, debug_matched),
            data=data,
            prefix="Processor::_get_nodes_by_search:  ")

    def _collector_addition(
        self, data: Any, peek_path: YAMLPath, node_coords: List[NodeCoords],
        **kwargs
    ) -> List[NodeCoords]:
        """Helper for _get_nodes_by_collector."""
        updated_coords = node_coords
        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))
        ancestry: List[AncestryEntry] = kwargs.pop("ancestry", [])
        relay_segment: PathSegment = kwargs.pop("relay_segment")

        for node_coord in self._get_required_nodes(
            data, peek_path, 0, parent=parent, parentref=parentref,
            translated_path=translated_path, ancestry=ancestry,
            relay_segment=relay_segment
        ):
            if (isinstance(node_coord, NodeCoords)
                    and isinstance(node_coord.node, list)):
                for coord_idx, coord in enumerate(node_coord.node):
                    if not isinstance(coord, NodeCoords):
                        next_translated_path = node_coord.path
                        if next_translated_path is not None:
                            next_translated_path = (
                                next_translated_path +
                                "[{}]".format(coord_idx))
                        next_ancestry = ancestry + [(
                            node_coord.node, coord_idx)]
                        coord = NodeCoords(
                            coord, node_coord.node, coord_idx,
                            next_translated_path,
                            next_ancestry, relay_segment)
                    updated_coords.append(coord)
            else:
                updated_coords.append(node_coord)

        return updated_coords

    def _collector_subtraction(
        self, data: Any, peek_path: YAMLPath, collected_ncs: List[NodeCoords],
        **kwargs
    ) -> List[NodeCoords]:
        """Helper for _get_nodes_by_collector."""
        def get_del_nodes(
            del_nodes: List[Any], node_coord: NodeCoords
        ) -> None:
            unwrapped_node = NodeCoords.unwrap_node_coords(node_coord)
            if isinstance(unwrapped_node, (list, CommentedSet, set)):
                for ele in unwrapped_node:
                    del_nodes.append(ele)
            elif isinstance(node_coord.parent, dict):
                del_nodes.append(
                    {node_coord.parentref: unwrapped_node})
            else:
                del_nodes.append(unwrapped_node)


        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))
        ancestry: List[AncestryEntry] = kwargs.pop("ancestry", [])
        relay_segment: PathSegment = kwargs.pop("relay_segment")

        expression_path = YAMLPath(peek_path)

        self.logger.debug((
            "Getting required nodes matching collector sub-path, {}, from:"
            ).format(peek_path),
            prefix="Processor::_collector_subtraction:  ",
            data={
                "segments": expression_path.unescaped,
                "data": data})

        rem_data: List[Any] = []
        for node_coord in self._get_required_nodes(
            data, expression_path, 0, parent=parent, parentref=parentref,
            translated_path=translated_path, ancestry=ancestry,
            relay_segment=relay_segment
        ):
            self.logger.debug((
                "Extracting node(s) for deletion from collected result:"
                ),
                prefix="Processor::_collector_subtraction:  ",
                data=node_coord)
            get_del_nodes(rem_data, node_coord)

        self.logger.debug((
            "Removing the following nodes from pre-gathered data:"),
            prefix="Processor::_collector_subtraction:  REMOVAL NODES->",
            data={
                "REMOVING": rem_data,
                "FROM": collected_ncs,
            })

        # If LHS in RHS, delete it
        rem_dels = []
        rem_idx = 0
        updated_coords: List[NodeCoords] = []
        for lhs in collected_ncs:
            unwrapped_lhs = lhs.unwrapped_node
            deepest_lhs = lhs.deepest_node_coord
            append_node = True

            if lhs.wraps_a(dict):
                if unwrapped_lhs in rem_data:
                    continue
                for rhs in rem_data:
                    if lhs.parentref in rhs:
                        append_node = False
                    if isinstance(rhs, OrderedDict):
                        # Do not drill into OrderedDict results because such
                        # wrapping means the user intends for the ENTIRE dict
                        # to be matched, not its individual key-value pairs.
                        continue
                    for key, val in rhs.items():
                        if key in unwrapped_lhs and unwrapped_lhs[key] == val:
                            rem_dels.append((rem_idx, key))
            elif lhs.wraps_a(list):
                if unwrapped_lhs in rem_data or rem_data == unwrapped_lhs:
                    continue
            else:
                if unwrapped_lhs in rem_data:
                    continue

            if append_node:
                updated_coords.append(deepest_lhs)
                rem_idx += 1
        for idx, key in rem_dels:
            del updated_coords[idx].deepest_node_coord.node[key]

        self.logger.debug((
            "Resulting data:"),
            prefix="Processor::_collector_subtraction:  DONE->",
            data=updated_coords
        )
        return updated_coords

    def _get_nodes_by_collector(
        self, data: Any, yaml_path: YAMLPath, segment_index: int,
        terms: CollectorTerms, **kwargs: Any
    ) -> Generator[List[NodeCoords], None, None]:
        """
        Generate List of nodes gathered via a Collector.

        Returns a list of zero or more NodeCoords within a given data context
        that match an inner YAML Path found at a specific segment of an outer
        YAML Path.

        Parameters:
        1. data (ruamel.yaml data) The parsed YAML data to process
        2. yaml_path (YAMLPath) The YAML Path being processed
        3. segment_index (int) Segment index of the YAML Path to process
        4. terms (CollectorTerms) The collector terms

        Keyword Arguments:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent
        * translated_path (YAMLPath) YAML Path indicating precisely which node
          is being evaluated
        * ancestry (List[AncestryEntry]) Stack of ancestors preceding the
          present node under evaluation

        Returns:  (Generator[List[NodeCoords], None, None]) Each list of
        NodeCoords as they are matched (the result is always a list)

        Raises:  N/A
        """
        if not terms.operation is CollectorOperators.NONE:
            self.logger.debug((
                "Processor::_get_nodes_by_collector:  Bailing out -- yielding"
                " the input data -- because the operation is {}"
                ).format(terms.operation))
            yield data
            return

        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))
        ancestry: List[AncestryEntry] = kwargs.pop("ancestry", [])

        node_coords: List[NodeCoords] = []
        segments = yaml_path.escaped
        next_segment_idx = segment_index + 1
        pathseg: PathSegment = segments[segment_index]
        expression_path = YAMLPath(terms.expression)

        self.logger.debug((
            "Getting required nodes matching collector sub-path, {}, from:"
            ).format(terms.expression),
            prefix="Processor::_get_nodes_by_collector:  ",
            data={
                "segments": expression_path.unescaped,
                "data": data})
        for node_coord in self._get_required_nodes(
            data, expression_path, 0, parent=parent,
            parentref=parentref, translated_path=translated_path,
            ancestry=ancestry, relay_segment=pathseg
        ):
            node_coords.append(node_coord)

        # This may end up being a bad idea for some cases, but this method will
        # unwrap all lists that look like `[[value]]` into just `[value]`.
        # When this isn't done, Collector syntax gets burdensome because
        # `(...)[0]` becomes necessary in too many use-cases.  This will be an
        # issue when the user actually expects a list-of-lists as output,
        # though I haven't yet come up with any use-case where a
        # list-of-only-one-list-result is what I really wanted to get from the
        # query.
        if (len(node_coords) == 1
            and isinstance(node_coords[0], NodeCoords)
            and isinstance(node_coords[0].node, list)
        ):
            # Give each element the same parent and its relative index
            node_coord = node_coords[0]
            flat_nodes = []
            for flatten_idx, flatten_node in enumerate(node_coord.node):
                flat_nodes.append(
                    NodeCoords(
                        flatten_node, node_coord.parent, flatten_idx,
                        node_coord.path, node_coord.ancestry, pathseg))
            node_coords = flat_nodes

        # As long as each next segment is an ADDITION or SUBTRACTION
        # COLLECTOR, keep combining the results.
        while next_segment_idx < len(segments):
            peekseg: PathSegment = segments[next_segment_idx]
            (peek_type, peek_attrs) = peekseg
            if (
                peek_type is PathSegmentTypes.COLLECTOR
                and isinstance(peek_attrs, CollectorTerms)
            ):
                peek_path: YAMLPath = YAMLPath(peek_attrs.expression)
                if peek_attrs.operation == CollectorOperators.ADDITION:
                    node_coords = self._collector_addition(
                        data, peek_path, node_coords,
                        parent=parent, parentref=parentref,
                        translated_path=translated_path, ancestry=ancestry,
                        relay_segment=peekseg)
                elif peek_attrs.operation == CollectorOperators.SUBTRACTION:
                    node_coords = self._collector_subtraction(
                        data, peek_path, node_coords,
                        parent=parent, parentref=parentref,
                        translated_path=translated_path, ancestry=ancestry,
                        relay_segment=peekseg)
                else:
                    raise YAMLPathException(
                        "Adjoining Collectors without an operator has no"
                        + " meaning; try + or - between them",
                        str(yaml_path),
                        str(peek_path)
                    )
            else:
                break  # pragma: no cover

            next_segment_idx += 1

        # yield only when there are results
        if node_coords:
            self.logger.debug((
                "Yielding collected node list:"),
                prefix="Processor::_get_nodes_by_collector:  ",
                data=node_coords)
            yield node_coords

    # pylint: disable=locally-disabled,too-many-branches
    def _get_nodes_by_traversal(
        self, data: Any, yaml_path: YAMLPath, segment_index: int, **kwargs: Any
    ) -> Generator[Any, None, None]:
        """
        Deeply traverse the document tree, returning all or filtered nodes.

        Parameters:
        1. data (ruamel.yaml data) The parsed YAML data to process
        2. yaml_path (yamlpath.Path) The YAML Path being processed
        3. segment_index (int) Segment index of the YAML Path to process

        Keyword Arguments:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent
        * translated_path (YAMLPath) YAML Path indicating precisely which node
          is being evaluated
        * ancestry (List[AncestryEntry]) Stack of ancestors preceding the
          present node under evaluation

        Returns:  (Generator[Any, None, None]) Each node coordinate as they are
        matched.
        """
        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))
        ancestry: List[AncestryEntry] = kwargs.pop("ancestry", [])

        segments = yaml_path.escaped
        pathseg: PathSegment = segments[segment_index]
        next_segment_idx: int = segment_index + 1

        self.logger.debug(
            "TRAVERSING the tree at parentref:",
            prefix="Processor::_get_nodes_by_traversal:  ", data=parentref)

        # Is there a next segment?
        if next_segment_idx == len(segments):
            # This traversal is gathering every leaf node
            if data is None:
                self.logger.debug((
                    "Yielding a None node."),
                    prefix="Processor::_get_nodes_by_traversal:  ")
                yield NodeCoords(None, parent, parentref, translated_path,
                    ancestry, pathseg)
                return

            if isinstance(data, (CommentedMap, dict)):
                for key, val in data.items():
                    next_translated_path = (
                        translated_path + YAMLPath.escape_path_section(
                            key, translated_path.seperator))
                    next_ancestry = ancestry + [(data, key)]
                    for node_coord in self._get_nodes_by_traversal(
                        val, yaml_path, segment_index,
                        parent=data, parentref=key,
                        translated_path=next_translated_path,
                        ancestry=next_ancestry
                    ):
                        self.logger.debug(
                            "Yielding unfiltered Hash value:",
                            prefix="Processor::_get_nodes_by_traversal:  ",
                            data=node_coord)
                        yield node_coord
            elif isinstance(data, (CommentedSeq, list)):
                for idx, ele in enumerate(data):
                    next_translated_path = translated_path + "[{}]".format(idx)
                    for node_coord in self._get_nodes_by_traversal(
                        ele, yaml_path, segment_index,
                        parent=data, parentref=idx,
                        translated_path=next_translated_path
                    ):
                        self.logger.debug(
                            "Yielding unfiltered Array value:",
                            prefix="Processor::_get_nodes_by_traversal:  ",
                            data=node_coord)
                        yield node_coord
            elif isinstance(data, (CommentedSet, set)):
                # Sets cannot be traversed; they cannot have complex children
                for ele in data:
                    next_translated_path = (
                        translated_path + YAMLPath.escape_path_section(
                            ele, translated_path.seperator))
                    self.logger.debug(
                        "Yielding unfiltered Set value:",
                        prefix="Processor::_get_nodes_by_traversal:  ",
                        data=ele)
                    yield NodeCoords(
                        ele, parent, ele, next_translated_path, ancestry,
                        pathseg)
            else:
                self.logger.debug(
                    "Yielding unfiltered Scalar value:",
                    prefix="Processor::_get_nodes_by_traversal:  ", data=data)
                yield NodeCoords(
                    data, parent, parentref, translated_path, ancestry,
                    pathseg)
        else:
            # There is a filter in the next segment; recurse data, comparing
            # every child against the following segment until there are no more
            # nodes.  For each match, resume normal path function against the
            # matching node(s).
            peekseg: PathSegment = segments[next_segment_idx]

            # Because the calling code will continue to process the remainder
            # of the YAML Path, only the parent of the matched node(s) can be
            # yielded.
            self.logger.debug((
                "Checking the DIRECT node for a next-segment match at"
                " parentref {} with next segment {} in data..."
                ).format(parentref, peekseg),
                prefix="Processor::_get_nodes_by_traversal:  ",
                data=data)

            for node_coord in self._get_nodes_by_path_segment(
                data, yaml_path, next_segment_idx, parent=parent,
                parentref=parentref, traverse_lists=False,
                translated_path=translated_path, ancestry=ancestry
            ):
                self.logger.debug(
                    "Yielding filtered DIRECT node at parentref {} of coord:"
                    .format(parentref),
                    prefix="Processor::_get_nodes_by_traversal:  ",
                    data=node_coord)
                yield NodeCoords(
                    data, parent, parentref, translated_path, ancestry,
                    peekseg)

            # Then, recurse into each child to perform the same test.
            if isinstance(data, dict):
                for key, val in data.items():
                    self.logger.debug(
                        "Processor::_get_nodes_by_traversal:  Recursing into"
                        " KEY '{}' at ref '{}' for next-segment matches..."
                        .format(key, parentref))
                    next_translated_path = (
                        translated_path + YAMLPath.escape_path_section(
                            key, translated_path.seperator))
                    next_ancestry = ancestry + [(data, key)]
                    for node_coord in self._get_nodes_by_traversal(
                        val, yaml_path, segment_index,
                        parent=data, parentref=key,
                        translated_path=next_translated_path,
                        ancestry=next_ancestry
                    ):
                        self.logger.debug(
                            "Yielding filtered indirect Hash value from KEY"
                            " '{}' at ref '{}':".format(key, parentref),
                            prefix="Processor::_get_nodes_by_traversal:  ",
                            data=node_coord.node)
                        yield node_coord
            elif isinstance(data, list):
                for idx, ele in enumerate(data):
                    self.logger.debug(
                        "Processor::_get_nodes_by_traversal:  Recursing into"
                        " INDEX '{}' at ref '{}' for next-segment matches..."
                        .format(idx, parentref))
                    next_translated_path = translated_path + "[{}]".format(idx)
                    next_ancestry = ancestry + [(data, idx)]
                    for node_coord in self._get_nodes_by_traversal(
                        ele, yaml_path, segment_index,
                        parent=data, parentref=idx,
                        translated_path=next_translated_path,
                        ancestry=next_ancestry
                    ):
                        self.logger.debug(
                            "Yielding filtered indirect Array value from INDEX"
                            " {} at {}:".format(idx, parentref),
                            prefix="Processor::_get_nodes_by_traversal:  ",
                            data=node_coord)
                        yield node_coord

    def _get_required_nodes(
        self, data: Any, yaml_path: YAMLPath, depth: int = 0, **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """
        Generate pre-existing NodeCoords from YAML data matching a YAML Path.

        Parameters:
        1. data (Any) The parsed YAML data to process
        2. yaml_path (YAMLPath) The pre-parsed YAML Path to follow
        3. depth (int) Index within yaml_path to process; default=0
        4. parent (ruamel.yaml node) The parent node from which this query
           originates
        5. parentref (Any) Key or Index of data within parent

        Keyword Arguments:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent
        * relay_segment (PathSegment) YAML Path segment presently under
          evaluation
        * translated_path (YAMLPath) YAML Path indicating precisely which node
          is being evaluated
        * ancestry (List[AncestryEntry]) Stack of ancestors preceding the
          present node under evaluation

        Returns:  (Generator[NodeCoords, None, None]) The requested NodeCoords
            as they are matched

        Raises:  N/A
        """
        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        relay_segment: PathSegment = kwargs.pop("relay_segment", None)
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))
        ancestry: List[AncestryEntry] = kwargs.pop("ancestry", [])

        segments = yaml_path.escaped
        if segments and len(segments) > depth:
            pathseg: PathSegment = yaml_path.unescaped[depth]
            (segment_type, unstripped_attrs) = pathseg
            except_segment = str(unstripped_attrs)
            self.logger.debug(
                "Seeking segment <{}>{} in data of type {}:"
                .format(segment_type, except_segment, type(data)),
                prefix="Processor::_get_required_nodes:  ",
                data=data, footer=" ")

            for segment_node_coords in self._get_nodes_by_path_segment(
                data, yaml_path, depth, parent=parent, parentref=parentref,
                translated_path=translated_path, ancestry=ancestry
            ):
                self.logger.debug(
                    "Got data of type {} at <{}>{} in the data."
                    .format(
                        type(segment_node_coords.node
                             if hasattr(segment_node_coords, "node")
                             else segment_node_coords),
                        segment_type,
                        except_segment),
                    prefix="Processor::_get_required_nodes:  ",
                    data=segment_node_coords)

                if isinstance(segment_node_coords, list):
                    # Most likely the output of a Collector, this list will be
                    # of NodeCoords rather than an actual DOM reference.  As
                    # such, it must be treated as a virtual DOM element that
                    # cannot itself be parented to the real DOM, though each
                    # of its elements has a real parent.
                    self.logger.debug(
                        "Got a list:",
                        prefix="Processor::_get_required_nodes:  ",
                        data=segment_node_coords)
                    for subnode_coord in self._get_required_nodes(
                            segment_node_coords, yaml_path, depth + 1,
                            parent=parent, parentref=parentref,
                            translated_path=translated_path,
                            ancestry=ancestry, relay_segment=pathseg):
                        yield subnode_coord
                else:
                    self.logger.debug(
                        "Recursing into the retrieved data...",
                        prefix="Processor::_get_required_nodes:  ")
                    for subnode_coord in self._get_required_nodes(
                            segment_node_coords.node, yaml_path, depth + 1,
                            parent=segment_node_coords.parent,
                            parentref=segment_node_coords.parentref,
                            translated_path=segment_node_coords.path,
                            ancestry=segment_node_coords.ancestry,
                            relay_segment=pathseg):
                        self.logger.debug(
                            "Finally returning segment data of type {} at"
                            " parentref {}:"
                            .format(type(subnode_coord.node),
                                    subnode_coord.parentref),
                            prefix="Processor::_get_required_nodes:  ",
                            data=subnode_coord, footer=" ")
                        yield subnode_coord
        else:
            self.logger.debug(
                "Finally returning data of type {} at parentref {}:"
                .format(type(data), parentref),
                prefix="Processor::_get_required_nodes:  ",
                data=data, footer=" ")
            yield NodeCoords(
                data, parent, parentref, translated_path, ancestry,
                relay_segment)

    # pylint: disable=locally-disabled,too-many-statements
    def _get_optional_nodes(
        self, data: Any, yaml_path: YAMLPath, value: Any = None,
        depth: int = 0, **kwargs: Any
    ) -> Generator[NodeCoords, None, None]:
        """
        Return zero or more pre-existing NodeCoords matching a YAML Path.

        Will create nodes that are missing, as long as any missing segments are
        deterministic (SEARCH and COLLECTOR segments are non-deterministic).

        Parameters:
        1. data (Any) The parsed YAML data to process
        2. yaml_path (YAMLPath) The pre-parsed YAML Path to follow
        3. value (Any) The value to assign to the element
        4. depth (int) For recursion, this identifies which segment of
           yaml_path to evaluate; default=0

        Keyword Arguments:
        * parent (ruamel.yaml node) The parent node from which this query
          originates
        * parentref (Any) The Index or Key of data within parent
        * relay_segment (PathSegment) YAML Path segment presently under
          evaluation
        * translated_path (YAMLPath) YAML Path indicating precisely which node
          is being evaluated
        * ancestry (List[AncestryEntry]) Stack of ancestors preceding the
          present node under evaluation

        Returns:  (Generator[NodeCoords, None, None]) The requested NodeCoords
        as they are matched

        Raises:
        - `YAMLPathException` when the YAML Path is invalid.
        - `NotImplementedError` when a segment of the YAML Path indicates
          an element that does not exist in data and this code isn't
          yet prepared to add it.
        """
        parent: Any = kwargs.pop("parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        relay_segment: PathSegment = kwargs.pop("relay_segment", None)
        translated_path: YAMLPath = kwargs.pop("translated_path", YAMLPath(""))
        ancestry: List[AncestryEntry] = kwargs.pop("ancestry", [])
        segments = yaml_path.escaped

        # pylint: disable=locally-disabled,too-many-nested-blocks
        if segments and len(segments) > depth:
            pathseg: PathSegment = yaml_path.unescaped[depth]
            (segment_type, unstripped_attrs) = pathseg
            stripped_attrs: PathAttributes = segments[depth][1]
            except_segment = str(unstripped_attrs)

            self.logger.debug(
                "Seeking element <{}>{} in data of type {}:"
                .format(segment_type, except_segment, type(data)),
                prefix="Processor::_get_optional_nodes:  ",
                data=data, footer=" ")

            # The next element may not exist; this method ensures that it does
            matched_nodes = 0
            for next_coord in self._get_nodes_by_path_segment(
                data, yaml_path, depth, parent=parent, parentref=parentref,
                translated_path=translated_path, ancestry=ancestry
            ):
                matched_nodes += 1
                if isinstance(next_coord, list):
                    # Drill into Collector results
                    for node_coord in self._get_optional_nodes(
                            next_coord, yaml_path, value, depth + 1,
                            parent=parent, parentref=parentref,
                            translated_path=translated_path,
                            ancestry=ancestry,
                            relay_segment=pathseg
                    ):
                        self.logger.debug((
                            "Relaying a drilled-into Collector node:"),
                            prefix="Processor::_get_optional_nodes:  ",
                            data={
                                "node": node_coord,
                                "parent": parent,
                                "parentref": parentref
                            }
                        )
                        yield node_coord
                    continue

                if next_coord.node is None:
                    self.logger.debug((
                        "Relaying a None element <{}>{} from the data."
                        ).format(segment_type, except_segment),
                        prefix="Processor::_get_optional_nodes:  ",
                        data=next_coord
                    )
                    yield next_coord
                    continue

                self.logger.debug((
                    "Found element <{}>{} in the data; recursing into it..."
                    ).format(segment_type, except_segment),
                    prefix="Processor::_get_optional_nodes:  ",
                    data=next_coord
                )

                for node_coord in self._get_optional_nodes(
                        next_coord.node, yaml_path, value, depth + 1,
                        parent=next_coord.parent,
                        parentref=next_coord.parentref,
                        translated_path=next_coord.path,
                        ancestry=next_coord.ancestry,
                        relay_segment=pathseg
                ):
                    yield node_coord

            if (
                    matched_nodes < 1
                    and segment_type is not PathSegmentTypes.SEARCH
                    and segment_type is not PathSegmentTypes.KEYWORD_SEARCH
            ):
                # Add the missing element
                self.logger.debug(
                    ("Processor::_get_optional_nodes:  Element <{}>{} is"
                     " unknown in the data!  Applying default, <{}>{} to"
                     " data:"
                    ).format(segment_type, except_segment, type(value), value),
                    data=data
                )
                if isinstance(data, list):
                    self.logger.debug(
                        "Processor::_get_optional_nodes:  Dealing with a list"
                    )
                    if (
                            segment_type is PathSegmentTypes.ANCHOR
                            and isinstance(stripped_attrs, str)
                    ):
                        next_node = Nodes.build_next_node(
                            yaml_path, depth + 1, value
                        )
                        new_ele = Nodes.append_list_element(
                            data, next_node, stripped_attrs
                        )
                        new_idx = len(data) - 1
                        next_translated_path = translated_path + "[{}]".format(
                            new_idx)
                        next_ancestry = ancestry + [(data, new_idx)]
                        for node_coord in self._get_optional_nodes(
                                new_ele, yaml_path, value, depth + 1,
                                parent=data, parentref=new_idx,
                                translated_path=next_translated_path,
                                ancestry=next_ancestry, relay_segment=pathseg
                        ):
                            matched_nodes += 1
                            yield node_coord
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
                            except ValueError as wrap_ex:
                                raise YAMLPathException(
                                    ("Cannot add non-integer {} subreference"
                                     + " to lists")
                                    .format(str(segment_type)),
                                    str(yaml_path),
                                    except_segment
                                ) from wrap_ex
                        for _ in range(len(data) - 1, newidx):
                            next_node = Nodes.build_next_node(
                                yaml_path, depth + 1, value
                            )
                            Nodes.append_list_element(data, next_node)
                        next_translated_path = translated_path + "[{}]".format(
                            newidx)
                        next_ancestry = ancestry + [(data, newidx)]
                        for node_coord in self._get_optional_nodes(
                                data[newidx], yaml_path, value,
                                depth + 1, parent=data, parentref=newidx,
                                translated_path=next_translated_path,
                                ancestry=next_ancestry, relay_segment=pathseg
                        ):
                            matched_nodes += 1
                            yield node_coord
                    else:
                        raise YAMLPathException(
                            "Cannot add {} subreference to lists"
                            .format(str(segment_type)),
                            str(yaml_path),
                            except_segment
                        )

                elif isinstance(data, dict):
                    self.logger.debug(
                        "Processor::_get_optional_nodes:  Dealing with a"
                        + " dictionary"
                    )
                    if segment_type is PathSegmentTypes.ANCHOR:
                        raise YAMLPathException(
                            "Cannot add ANCHOR keys",
                            str(yaml_path),
                            str(unstripped_attrs)
                        )
                    if segment_type is PathSegmentTypes.KEY:
                        data[stripped_attrs] = Nodes.build_next_node(
                            yaml_path, depth + 1, value
                        )
                        next_translated_path = (
                            translated_path + YAMLPath.escape_path_section(
                                str(stripped_attrs),
                                translated_path.seperator))
                        next_ancestry = ancestry + [(data, stripped_attrs)]
                        for node_coord in self._get_optional_nodes(
                                data[stripped_attrs], yaml_path, value,
                                depth + 1, parent=data,
                                parentref=stripped_attrs,
                                translated_path=next_translated_path,
                                ancestry=next_ancestry, relay_segment=pathseg
                        ):
                            matched_nodes += 1
                            yield node_coord
                    else:
                        raise YAMLPathException(
                            "Cannot add {} subreference to dictionaries"
                            .format(str(segment_type)),
                            str(yaml_path),
                            except_segment
                        )

                elif isinstance(data, (CommentedSet, set)):
                    self.logger.debug(
                        "Processor::_get_optional_nodes:  Dealing with a set"
                    )
                    if segment_type is not PathSegmentTypes.KEY:
                        raise YAMLPathException(
                            "Cannot add {} subreference to sets"
                            .format(str(segment_type)),
                            str(yaml_path),
                            except_segment
                        )

                    data.add(stripped_attrs)
                    yield NodeCoords(
                        data, parent, parentref,
                        translated_path, ancestry,
                        relay_segment)

                else:
                    self.logger.debug(
                        "Assuming data is scalar and cannot receive a {}"
                        " subreference at {} ({}/{}):".format(
                            str(segment_type), str(yaml_path), str(depth + 1),
                            str(len(yaml_path))),
                        prefix="Processor::_get_optional_nodes:  ",
                        data={"data": data, "parent": parent,
                            "parentref": parentref, "(default_)value": value})
                    raise YAMLPathException(
                        "Cannot add {} subreference to scalars".format(
                            str(segment_type)
                        ),
                        str(yaml_path),
                        except_segment
                    )

        else:
            self.logger.debug(
                "Finally returning data of type {}:"
                .format(type(data)),
                prefix="Processor::_get_optional_nodes:  ", data=data)
            yield NodeCoords(
                data, parent, parentref, translated_path, ancestry,
                relay_segment)

    # pylint: disable=too-many-arguments
    def _update_node(
        self, parent: Any, parentref: Any, value: Any,
        value_format: YAMLValueFormats, value_tag: str = None
    ) -> None:
        """
        Set the value of a data node.

        Recursively updates the value of a YAML Node and any references to it
        within the entire YAML data structure (Anchors and Aliases, if any).

        Parameters:
        1. parent (ruamel.yaml data) The parent of the node to change
        2. parent_ref (Any) Index or Key of the value within parent_node to
           change
        3. value (any) The new value to assign to the source_node and
           its references
        4. value_format (YAMLValueFormats) the YAML representation of the
           value
        5. value_tag (str) the custom YAML data-type tag of the value

        Returns: N/A

        Raises: N/A
        """
        if parent is None:
            # Empty document or the document root
            self.logger.debug(
                "Processor::_update_node:  Ignoring node with no parent!")
            return

        # This recurse function was contributed by Anthon van der Neut, the
        # author of ruamel.yaml, to resolve how to update all references to an
        # Anchor throughout the parsed data structure.
        def recurse(data, parent, parentref, reference_node, replacement_node):
            if isinstance(data, (CommentedMap, dict)):
                for i, k in [
                        (idx, key) for idx, key in enumerate(data.keys())
                        if key is reference_node
                ]:
                    data.insert(i, replacement_node, data.pop(k))
                for k, val in data.items():
                    if val is reference_node:
                        if (hasattr(val, "anchor") or
                                (data is parent and k == parentref)):
                            data[k] = replacement_node
                    else:
                        recurse(val, parent, parentref, reference_node,
                                replacement_node)
            elif isinstance(data, (CommentedSeq, list)):
                for idx, item in enumerate(data):
                    if data is parent and item is reference_node:
                        data[idx] = replacement_node
                    else:
                        recurse(item, parent, parentref, reference_node,
                                replacement_node)
            elif isinstance(data, (CommentedSet, set)):
                data.discard(reference_node)
                data.add(replacement_node)

        if isinstance(parent, (set, CommentedSet)):
            for ele in parent:
                if ele == parentref:
                    change_node = ele
                    break
        else:
            change_node = parent[parentref]
        new_node = Nodes.make_new_node(
            change_node, value, value_format, tag=value_tag)

        self.logger.debug(
            "Changing the following <{}> formatted node:".format(value_format),
            prefix="Processor::_update_node:  ",
            data={ "__FROM__": change_node, "___TO___": new_node })

        recurse(self.data, parent, parentref, change_node, new_node)

        self.logger.debug(
            "Parent after change:", prefix="Processor::_update_node:  ",
            data=parent)
