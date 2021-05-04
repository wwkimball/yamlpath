"""
Implement NodeCoords.

Copyright 2020, 2021 William W. Kimball, Jr. MBA MSIS
"""
from typing import Any, List, Optional, Type

from yamlpath.types import AncestryEntry, PathSegment
from yamlpath import YAMLPath

class NodeCoords:
    """
    Wrap a node's data along with its relative coordinates within its DOM.

    A node's "coordinates" includes these properties:
    1. Reference to the node itself,
    2. Immediate parent node of the wrapped node,
    3. Index or Key of the node within its immediate parent

    Additional, optional data can be wrapped along with the node's coordinates
    to facilitate other specific operations upon the node/DOM.  See the
    `__init__` method for details.
    """

    # pylint: disable=locally-disabled,too-many-arguments
    def __init__(
        self, node: Any, parent: Any, parentref: Any,
        path: Optional[YAMLPath] = None,
        ancestry: Optional[List[AncestryEntry]] = None,
        path_segment: Optional[PathSegment] = None
    ) -> None:
        """
        Initialize a new NodeCoords.

        Positional Parameters:
        1. node (Any) Reference to the ruamel.yaml DOM data element
        2. parent (Any) Reference to `node`'s immediate DOM parent
        3. parentref (Any) The `list` index or `dict` key which indicates where
           within `parent` the `node` is located
        4. path (YAMLPath) The YAML Path for this node, as reported by its
           creator process
        5. ancestry (List[AncestryEntry]) Stack of AncestryEntry (parent,
           parentref) tracking the hierarchical ancestry of this node through
           its parent document
        6. path_segment (PathSegment) The YAML Path segment which most directly
           caused the generation of this NodeCoords

        Returns: N/A

        Raises:  N/A
        """
        self.node: Any = node
        self.parent: Any = parent
        self.parentref: Any = parentref
        self.path: Optional[YAMLPath] = path
        self.ancestry: List[AncestryEntry] = ([]
                                              if ancestry is None
                                              else ancestry)
        self.path_segment: Optional[PathSegment] = path_segment

    def __str__(self) -> str:
        """Get a String representation of this object."""
        return str(self.node)

    def __repr__(self) -> str:
        """
        Generate an eval()-safe representation of this object.

        Assumes all of the ruamel.yaml components are similarly safe.
        """
        return ("{}('{}', '{}', '{}')".format(
            self.__class__.__name__, self.node, self.parent,
            self.parentref))

    def __gt__(self, rhs: "NodeCoords") -> Any:
        """Indicate whether this node's data is greater-than another's."""
        if self.node is None or rhs.node is None:
            return False
        return self.node > rhs.node

    def __lt__(self, rhs: "NodeCoords") -> Any:
        """Indicate whether this node's data is less-than another's."""
        if self.node is None or rhs.node is None:
            return False
        return self.node < rhs.node

    @property
    def unwrapped_node(self) -> Any:
        """Unwrap the data, no matter how deeply nested it may be."""
        return NodeCoords.unwrap_node_coords(self)

    @property
    def deepest_node_coord(self) -> "NodeCoords":
        """Get the deepest wrapped NodeCoord contained within."""
        return NodeCoords._deepest_node_coord(self)

    def wraps_a(self, compare_type: Type) -> bool:
        """Indicate whether the wrapped node is of a given data-type."""
        if compare_type is None:
            return self.unwrapped_node is None
        return isinstance(self.unwrapped_node, compare_type)

    @staticmethod
    def _deepest_node_coord(node: "NodeCoords") -> "NodeCoords":
        """Get the deepest nested NodeCoord."""
        if (not isinstance(node, NodeCoords)
            or not isinstance(node.node, NodeCoords)
        ):
            return node

        return NodeCoords._deepest_node_coord(node.node)

    @staticmethod
    def unwrap_node_coords(data: Any) -> Any:
        """
        Recursively strips all DOM tracking data off of a NodeCoords wrapper.

        Parameters:
        1. data (Any) the source data to strip.

        Returns:  (Any) the stripped data.
        """
        if isinstance(data, NodeCoords):
            return NodeCoords.unwrap_node_coords(data.node)

        if isinstance(data, list):
            stripped_nodes = []
            for ele in data:
                stripped_nodes.append(NodeCoords.unwrap_node_coords(ele))
            return stripped_nodes

        return data
