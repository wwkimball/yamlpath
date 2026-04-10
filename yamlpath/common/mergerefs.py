"""
Implement MergeRefs, a static library for YAML Merge Key operations.

Copyright 2026 William W. Kimball, Jr. MBA MSIS
"""
from typing import Any, Generator, List, Union

from ruamel.yaml.comments import CommentedSeq, merge_attrib
from ruamel.yaml.mergevalue import MergeValue


class MergeRefs:
    """Helper methods for YAML merge reference operations."""

    @staticmethod
    def iter_nodes(
        data: Any,
    ) -> Generator[Any, None, None]:
        """
        Generate merge-reference nodes from a CommentedMap-like node.

        Parameters:
        1. data (Any) A node which may contain YAML merge references.

        Returns:  (Generator[Any, None, None]) Tuples of:
          * int: 0-based merge reference position
          * Any: The merge reference node at that position

        Raises:  N/A
        """
        refs = data.merge if hasattr(data, "merge") else []
        for idx, merge_item in enumerate(refs):
            if isinstance(merge_item, tuple) and len(merge_item) > 1:
                yield idx, merge_item[1]
            else:
                yield idx, merge_item

    @staticmethod
    def replace_node(
        data: Any, idx: int, new_node: Any
    ) -> None:
        """
        Replace one YAML merge reference node in-place.

        Parameters:
        1. data (Any) Node containing merge references.
        2. idx (int) 0-based merge reference index to replace.
        3. new_node (Any) Replacement merge reference node.

        Returns:  N/A

        Raises:  N/A
        """
        refs = data.merge if hasattr(data, "merge") else []
        if isinstance(refs, MergeValue):
            ref_store = refs.value  # type: ignore[attr-defined]
        else:
            ref_store = refs
        current = ref_store[idx]
        if isinstance(current, tuple) and len(current) > 1:
            ref_store[idx] = (current[0], new_node)
        else:
            ref_store[idx] = new_node

    @staticmethod
    def remove_node(data: Any, idx: int) -> None:
        """
        Delete one YAML merge reference by index.

        Parameters:
        1. data (Any) Node containing merge references.
        2. idx (int) 0-based merge reference index to remove.

        Returns:  N/A

        Raises:  N/A
        """
        refs = data.merge if hasattr(data, "merge") else []
        if isinstance(refs, MergeValue):
            ref_store = refs.value  # type: ignore[attr-defined]
        else:
            ref_store = refs
        del ref_store[idx]

    @staticmethod
    def add_node(
        data: Any, merge_node: Any, materialize_keys: bool = False
    ) -> None:
        """
        Append one YAML merge reference to a node.

        Parameters:
        1. data (Any) Node receiving the merge reference.
        2. merge_node (Any) Node to be merged into data.
        3. materialize_keys (bool) True to concretely copy missing keys from
           merge_node into data; False to keep only merge references.

        Returns:  N/A

        Raises:  N/A
        """
        refs: Union[MergeValue, List[Any], None]
        refs = getattr(data, merge_attrib, None)
        if isinstance(refs, MergeValue):
            refs.append(merge_node)  # type: ignore[union-attr]
            if refs.merge_pos is None:  # type: ignore[union-attr]
                refs.merge_pos = 0  # type: ignore[union-attr]
            MergeRefs._sync_sequence(refs)
        else:
            merge_value = MergeValue()
            if isinstance(refs, list):
                merge_value.extend(refs)
            merge_value.append(merge_node)
            merge_value.merge_pos = 0
            MergeRefs._sync_sequence(merge_value)
            setattr(data, merge_attrib, merge_value)

        if hasattr(merge_node, "add_referent"):
            merge_node.add_referent(data)

        if materialize_keys:
            for key, val in merge_node.items():
                if key not in data:
                    data[key] = val

    @staticmethod
    def _sync_sequence(merge_value: MergeValue) -> None:
        """Synchronize MergeValue.sequence with MergeValue.value."""
        if len(merge_value.value) <= 1:
            merge_value.set_sequence(None)
            return

        sequence = CommentedSeq(merge_value.value)
        sequence.fa.set_flow_style()
        merge_value.set_sequence(sequence)
