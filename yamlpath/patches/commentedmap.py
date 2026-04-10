# pylint: skip-file
"""
Fix incorrect comment preservation when deleting keys from CommentedMap.

When a key is deleted from a ruamel.yaml CommentedMap, the library leaves
stale comment entries in ca.items and fails to transfer the deleted key's
"between-items" comment (ca.items[key][2]) to the preceding key's slot.  As
a result, the pre-comment of the deleted key is incorrectly kept and associated
with the next key, while the comment that *should* precede that next key is
lost.

This helper must be called BEFORE the actual deletion so that comments can be
inspected and relocated.  Call fix_comment_for_deleted_key(parent, key) right
before executing ``del parent[key]`` on a CommentedMap.

This must be removed once incorporated into ruamel.yaml.

See: https://github.com/wwkimball/yamlpath/issues/170
Copyright 2026 William W. Kimball Jr. MBA MSIS
"""
from typing import Any

from ruamel.yaml.comments import CommentedMap


def fix_comment_for_deleted_key(parent: Any, key: Any) -> None:
    """
    Relocate comments so that key deletion preserves the correct comments.

    In ruamel.yaml, ``ca.items[k][2]`` holds the blank-lines-and-comment that
    appears *after* key ``k``'s value and *before* the next key -- i.e. the
    pre-comment for whatever comes after ``k``.  When ``k`` is deleted:

    * ``ca.items[prev_key][2]`` was the pre-comment for ``k`` and should be
      **dropped** (because ``k`` is gone).
    * ``ca.items[k][2]`` was the pre-comment for the key that follows ``k``
      and should be **kept** -- specifically, transferred to become
      ``ca.items[prev_key][2]`` so the emitter will still emit it.

    For the special case where ``k`` is the first key in the mapping, its
    successor comment is promoted to the mapping's document-level pre-comment
    (``ca.comment[1]``), replacing the existing doc-level comment that belonged
    to the now-deleted first key.

    Parameters:
    1. parent (Any) The parent container; must be a CommentedMap for the fix
       to apply -- any other type is silently ignored.
    2. key (Any) The key about to be deleted from ``parent``.

    Returns:  N/A
    """
    if not isinstance(parent, CommentedMap):
        return
    if key not in parent:
        return

    keys = list(parent.keys())
    try:
        del_idx = keys.index(key)
    except ValueError:  # pragma: no cover
        return

    # ca.items[key][2] is the "between-items" comment -- the blank lines and
    # comment that appear after this key's value and before the next key.
    del_comment = parent.ca.items.get(key)
    successor_comment = del_comment[2] if del_comment else None

    if del_idx > 0:
        prev_key = keys[del_idx - 1]
        # Replace the pre-comment for `key` (which lives in prev_key's slot)
        # with the comment that should precede the key after `key`.
        if prev_key in parent.ca.items:
            parent.ca.items[prev_key][2] = successor_comment
        elif successor_comment is not None:
            parent.ca.items[prev_key] = [None, None, successor_comment, None]
    else:
        # The deleted key is the first key in the mapping.  Its successor
        # comment should become the document-level pre-comment so it still
        # appears before whichever key is now first.
        if successor_comment is not None:
            if (parent.ca.comment is not None
                    and isinstance(parent.ca.comment, list)
                    and len(parent.ca.comment) > 1):
                parent.ca.comment[1] = [successor_comment]
            else:
                parent.ca.comment = [None, [successor_comment]]
        else:
            # No successor comment; drop the existing doc-level pre-comment
            # because it belonged to the key being deleted.
            if (parent.ca.comment is not None
                    and isinstance(parent.ca.comment, list)
                    and len(parent.ca.comment) > 1):
                parent.ca.comment[1] = None

    # Remove the now-stale ca.items entry for the deleted key.
    if key in parent.ca.items:
        del parent.ca.items[key]
