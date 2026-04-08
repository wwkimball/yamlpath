"""Compatibility helpers for ruamel.yaml API changes."""
from typing import Any, Iterator, Optional, Tuple

from ruamel.yaml.comments import (
    CommentedMap,
    CommentedSeq,
    CommentedSet,
    TaggedScalar,
    merge_attrib,
)
from ruamel.yaml.mergevalue import MergeValue
from ruamel.yaml.tag import Tag


def get_yaml_tag(node: Any) -> Optional[str]:  # pragma: no cover
    """Get a node tag as a plain string or None."""
    if not hasattr(node, "tag"):
        return None

    node_tag = node.tag
    if node_tag is None:
        return None

    if isinstance(node_tag, str):
        return node_tag or None

    has_value = hasattr(node_tag, "value")
    tag_value = getattr(node_tag, "value", None)
    if has_value:
        return str(tag_value) if tag_value else None

    return str(node_tag) or None


def set_yaml_tag(  # pragma: no cover
    node: Any,
    value_tag: Optional[str],
    *,
    clear_on_none: bool = False,
) -> None:
    """Set a YAML tag on a node across ruamel.yaml API generations."""
    if value_tag is None:
        if not clear_on_none:
            # Preserve existing tag when no new tag is provided.
            return
        value_tag = ""

    if hasattr(node, "yaml_set_ctag"):
        node.yaml_set_ctag(Tag(handle=None, suffix=value_tag))
        return

    if hasattr(node, "yaml_set_tag"):
        node.yaml_set_tag(value_tag)


def iter_merge_nodes(
    data: Any,
) -> Iterator[Tuple[int, Any]]:  # pragma: no cover
    """Yield merge references as (index, node) across ruamel versions."""
    refs = data.merge if hasattr(data, "merge") else []
    for idx, merge_item in enumerate(refs):
        if isinstance(merge_item, tuple) and len(merge_item) > 1:
            yield idx, merge_item[1]
        else:
            yield idx, merge_item


def replace_merge_node(
    data: Any, idx: int, new_node: Any
) -> None:  # pragma: no cover
    """Replace one merge reference node in-place."""
    refs = data.merge if hasattr(data, "merge") else []
    ref_store = refs.value if hasattr(refs, "value") else refs
    current = ref_store[idx]
    if isinstance(current, tuple) and len(current) > 1:
        ref_store[idx] = (current[0], new_node)
    else:
        ref_store[idx] = new_node


def remove_merge_node(data: Any, idx: int) -> None:  # pragma: no cover
    """Delete one merge reference by index."""
    refs = data.merge if hasattr(data, "merge") else []
    ref_store = refs.value if hasattr(refs, "value") else refs
    del ref_store[idx]


def _sync_merge_sequence(merge_value: MergeValue) -> None:  # pragma: no cover
    """Keep MergeValue.sequence in sync and force compact flow-style output."""
    if len(merge_value.value) <= 1:
        merge_value.set_sequence(None)
        return

    sequence = CommentedSeq(merge_value.value)
    sequence.fa.set_flow_style()
    merge_value.set_sequence(sequence)


def add_merge_node(  # pragma: no cover
    data: Any,
    merge_node: Any,
    *,
    materialize_keys: bool = False,
) -> None:
    """Append one merge reference while preserving ruamel internals."""
    # Pre-0.18/0.19 legacy API expected list-of-tuples; try first for safety.
    if hasattr(data, "add_yaml_merge"):
        try:
            data.add_yaml_merge([(len(data.merge), merge_node)])
            return
        except (AssertionError, AttributeError, TypeError):
            pass

    refs = getattr(data, merge_attrib, None)
    if isinstance(refs, MergeValue):
        refs.append(merge_node)
        if refs.merge_pos is None:
            refs.merge_pos = 0
        _sync_merge_sequence(refs)
    else:
        merge_value = MergeValue()
        if isinstance(refs, list):
            merge_value.extend(refs)
        merge_value.append(merge_node)
        merge_value.merge_pos = 0
        _sync_merge_sequence(merge_value)
        setattr(data, merge_attrib, merge_value)

    if hasattr(merge_node, "add_referent"):
        merge_node.add_referent(data)

    if materialize_keys:
        for key, val in merge_node.items():
            if key in data:
                continue
            data[key] = val


def _patch_yaml_set_tag_alias() -> None:  # pragma: no cover
    """Restore yaml_set_tag compatibility on ruamel 0.19+ node classes."""
    def _alias_set_tag(self: Any, value_tag: Optional[str]) -> None:
        set_yaml_tag(self, value_tag)

    for node_type in (CommentedMap, CommentedSeq, CommentedSet, TaggedScalar):
        if (
            not hasattr(node_type, "yaml_set_tag")
            and hasattr(node_type, "yaml_set_ctag")
        ):
            setattr(node_type, "yaml_set_tag", _alias_set_tag)


_patch_yaml_set_tag_alias()
