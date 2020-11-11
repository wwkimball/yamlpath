"""Wrap a node along with its relative coordinates within its DOM."""
from typing import Any

from yamlpath import YAMLPath

class NodeCoords:
    """
    Initialize a new NodeCoords.

    A node's coordinates track these properties:
    1. Reference-to-the-Node-Itself,
    2. Immediate-Parent-Node-of-the-Node,
    3. Index-or-Key-of-the-Node-Within-Its-Immediate-Parent
    """

    def __init__(
        self, node: Any, parent: Any, parentref: Any, path: YAMLPath = None
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

        Returns: N/A

        Raises:  N/A
        """
        self.node = node
        self.parent = parent
        self.parentref = parentref
        self.path = path

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
