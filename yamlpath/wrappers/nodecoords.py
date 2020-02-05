"""
Wraps a ruamel.yaml data element along with its relative coordinates
within its DOM.

A node's coordinates track these properties:
    1. Reference-to-the-Node-Itself,
    2. Immediate-Parent-Node-of-the-Node,
    3. Index-or-Key-of-the-Node-Within-Its-Immediate-Parent
"""
from typing import Any


class NodeCoords:
    """
    Initialize a new NodeCoords.

    Positional Parameters:
        1. node (Any) Reference to the ruamel.yaml DOM data element
        2. parent (Any) Reference to `node`'s immediate DOM parent
        3. parentref (Any) The `list` index or `dict` key which indicates
           where within `parent` the `node` is located

    Returns: N/A

    Raises:  N/A
    """

    def __init__(self, node: Any, parent: Any, parentref: Any) -> None:
        self.node = node
        self.parent = parent
        self.parentref = parentref

    def __str__(self) -> str:
        return str(self.node)

    def __repr__(self) -> str:
        """
        Generates an eval()-safe representation of this object,
        assuming all of the ruamel.yaml components are similarly safe.
        """
        return ("{}('{}', '{}', '{}')".format(
            self.__class__.__name__, self.node, self.parent,
            self.parentref))
