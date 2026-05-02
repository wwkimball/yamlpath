"""
Fix dropped spacing before commented aliased parent hash keys.

ruamel.yaml can drop the separator blank line or comment between a sequence and
the following aliased mapping key when that child mapping has its own comment.
Older ruamel.yaml releases could also assert while dumping the same shape.

This must be removed once incorporated into ruamel.yaml.

See:  https://sourceforge.net/p/ruamel-yaml/tickets/351/
Copyright 2026 William W. Kimball Jr. MBA MSIS
"""
from typing import Any

from ruamel.yaml.comments import CommentedMap, CommentedSeq


class CommentedAliasedParentHashPatch:
    """Patch ruamel.yaml aliased parent hash comment emission."""

    @staticmethod
    def _relocate_seq_comment_before_alias_key(
        parent: CommentedMap, previous_value: Any, next_key: Any, next_value: Any
    ) -> None:
        """
        Reattach dropped separator comments before aliased mapping keys.

        ruamel.yaml stores blank lines and full-line comments that appear after
        the final item of a sequence in that item's ``ca.items[idx][0]`` slot.
        When the next mapping key is emitted as an alias and its value carries
        its own comment, ruamel.yaml can either drop that separator comment or,
        on older releases, assert while dumping.  Moving that separator comment
        to the following aliased key's own comment slot preserves output and
        sidesteps the old assertion path.

        Parameters:
        1. parent (CommentedMap) Mapping containing the affected nodes.
        2. previous_value (Any) Value preceding the aliased key.
        3. next_key (Any) Candidate aliased mapping key.
        4. next_value (Any) Value associated with ``next_key``.

        Returns:  N/A
        """
        if not isinstance(previous_value, CommentedSeq) or len(previous_value) < 1:
            return

        if not isinstance(next_value, CommentedMap):
            return

        if next_key not in parent.ca.items:
            return

        next_key_comments = parent.ca.items[next_key]
        if not next_key_comments or next_key_comments[0] is not None:
            return

        if not next_key_comments[3]:
            return

        if not hasattr(next_key, "yaml_anchor"):
            return

        anchor = next_key.yaml_anchor()
        if anchor is None or not getattr(anchor, "always_dump", False):
            return

        last_seq_comments = previous_value.ca.items.get(len(previous_value) - 1)
        if not last_seq_comments or last_seq_comments[0] is None:
            return

        next_key_comments[0] = last_seq_comments[0]
        last_seq_comments[0] = None

    @staticmethod
    def restore_dropped_alias_key_spacing(dom: Any) -> None:
        """
        Fix ruamel.yaml alias-key separator comments before dumping.

        This is a compatibility workaround for ruamel.yaml ticket 351 and the
        still-related spacing loss that can occur when a sequence is followed by
        an aliased mapping key whose child mapping has its own comment.

        Parameters:
        1. dom (Any) The document or node to normalize before dumping.

        Returns:  N/A
        """
        if dom is None:
            return

        if isinstance(dom, CommentedMap):
            keys = list(dom.keys())
            for idx, key in enumerate(keys):
                value = dom[key]
                if idx + 1 < len(keys):
                    CommentedAliasedParentHashPatch._relocate_seq_comment_before_alias_key(
                        dom, value, keys[idx + 1], dom[keys[idx + 1]])
                CommentedAliasedParentHashPatch.restore_dropped_alias_key_spacing(key)
                CommentedAliasedParentHashPatch.restore_dropped_alias_key_spacing(value)
        elif isinstance(dom, CommentedSeq):
            for ele in dom:
                CommentedAliasedParentHashPatch.restore_dropped_alias_key_spacing(ele)
