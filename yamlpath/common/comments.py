"""
Implement Comments, a static lib of generally-useful code for YAML Comments.

Copyright 2022 William W. Kimball, Jr. MBA MSIS
"""
from typing import Any, Iterable, Tuple

# from ruamel.yaml.comments import CommentToken


class Comments:
    """Helper methods for common YAML Comment operations."""

    # @staticmethod
    # def find_comment_token(ca_items: Iterable) -> Tuple[int, int]:
    #     """Scans a ca object for the index of the first CommentToken."""
    #     slot_idx: int = -1
    #     sub_idx: int = -1
    #     for i, item in enumerate(ca_items):
    #         if item is None:
    #             continue

    #         slot_idx = i
    #         if item is CommentToken:
    #             break

    #         if item is Iterable:
    #             for j, _ in enumerate(item):
    #                 if item is CommentToken:
    #                     sub_idx = j
    #                     break

    #     return slot_idx, sub_idx

    @staticmethod
    def _get_comment_parts(comment_text: str) -> Tuple[str, str]:
        """Parse a ruamel.yaml comment into its EOL and after parts."""
        return (
            comment_text.partition("\n")[0],
            comment_text.partition("\n")[2])

    @staticmethod
    def _strip_next_node_comment(pnode_post_eol_comment: str) -> str:
        """Strip text of content that is likely meant for the next node."""
        if pnode_post_eol_comment is None:
            return None

        # Remove the target node's pre-node comment from the
        # predecessor node's post-eol comment.  Stop removing lines
        # when an empty-line or possible commented YAML is detected.
        pnode_comment_lines = pnode_post_eol_comment.split("\n")
        line_count = len(pnode_comment_lines)
        preserve_to = line_count
        keep_lines = 0
        for pre_index, pre_line in enumerate(
            reversed(pnode_comment_lines)
        ):
            keep_lines = pre_index
            pre_content = pre_line.partition("#")[2].lstrip()

            # Stop preserving lines at the first (last) blank line
            if len(pre_content) < 1:
                break

            # Check for possible YAML markup
            if pre_content[0] == '-' or ':' in pre_content:
                # May be YAML; there's room here for deeper testing...
                break

        preserve_to = line_count - keep_lines - 2
        return (
            "\n".join(pnode_comment_lines[0:preserve_to]) +
            ("\n" if preserve_to >= 0 else ""))

    # def merge_with_parent_having_eolc(parent, post_comment) -> None:
    #     # Pull the pre node comment from the node's parent; it will be in
    #     # one of multiple possible subscripts.
    #     print(f"Attempting to pull parent comment for parentref, {parentref}.")
    #     pnode_comment = (parent.ca.items[parentref][2].value
    #                     if parentref is not None
    #                     else None)

    #     # Strip the preceding node's post-eol-comment of content that is
    #     # likely meant for the to-be-deleted node.
    #     pnode_eol_comment, pnode_post_eol_comment = get_comment_parts(
    #         pnode_comment)
    #     pnode_eol_comment += "\n"
    #     stripped_pnode_post_eol_comment = (
    #         strip_next_node_comment(pnode_post_eol_comment)
    #         if pnode_post_eol_comment is not None
    #         else "")
    #     parent.ca.items[parentref][2].value = (
    #         pnode_eol_comment +
    #         stripped_pnode_post_eol_comment)

    #     # DEBUG
    #     dbg_pnode_comment = pnode_comment.replace("\n", "\\n")
    #     dbg_pnode_eol_comment = pnode_eol_comment.replace("\n", "\\n")
    #     dbg_pnode_post_eol_comment = pnode_post_eol_comment.replace("\n", "\\n")
    #     dbg_stripped_pnode_post_eol_comment = stripped_pnode_post_eol_comment.replace("\n", "\\n")
    #     dbg_new_comment = parent.ca.items[parentref][2].value.replace("\n", "\\n")
    #     print(f"                  pnode_comment: {dbg_pnode_comment}")
    #     print(f"              pnode_eol_comment: {dbg_pnode_eol_comment}")
    #     print(f"         pnode_post_eol_comment: {dbg_pnode_post_eol_comment}")
    #     print(f"stripped_pnode_post_eol_comment: {dbg_stripped_pnode_post_eol_comment}")
    #     print(f"                    new_comment: {dbg_new_comment}")

    #     # Check for any comment after an end-of-line comment of the target
    #     # node.  If present, move it to the end of the predecessor node's
    #     # post-eol comment.
    #     preserve_comment = post_comment.partition("\n")[2]
    #     if preserve_comment is not None:
    #         parent.ca.items[parentref][2].value = (
    #             pnode_comment + preserve_comment)

    # def merge_with_parent_without_eolc(parent, post_comment) -> None:
    #     # Pull the pre node comment from the node's parent; it will be in
    #     # one of multiple possible subscripts.
    #     print(f"Attempting to pull parent comment for parentref, {parentref}.")
    #     pnode_comment = (parent.ca.items[parentref][3][0].value
    #                     if parentref is not None
    #                     else None)

    #     # Strip the preceding node's post-eol-comment of content that is
    #     # likely meant for the to-be-deleted node.
    #     pnode_eol_comment, pnode_post_eol_comment = get_comment_parts(
    #         pnode_comment)
    #     pnode_eol_comment += "\n"
    #     stripped_pnode_post_eol_comment = (
    #         strip_next_node_comment(pnode_post_eol_comment)
    #         if pnode_post_eol_comment is not None
    #         else "")
    #     parent.ca.items[parentref][3][0].value = (
    #         pnode_eol_comment +
    #         stripped_pnode_post_eol_comment)

    #     # DEBUG
    #     dbg_pnode_comment = pnode_comment.replace("\n", "\\n")
    #     dbg_pnode_eol_comment = pnode_eol_comment.replace("\n", "\\n")
    #     dbg_pnode_post_eol_comment = pnode_post_eol_comment.replace("\n", "\\n")
    #     dbg_stripped_pnode_post_eol_comment = stripped_pnode_post_eol_comment.replace("\n", "\\n")
    #     dbg_new_comment = parent.ca.items[parentref][3][0].value.replace("\n", "\\n")
    #     print(f"                  pnode_comment: {dbg_pnode_comment}")
    #     print(f"              pnode_eol_comment: {dbg_pnode_eol_comment}")
    #     print(f"         pnode_post_eol_comment: {dbg_pnode_post_eol_comment}")
    #     print(f"stripped_pnode_post_eol_comment: {dbg_stripped_pnode_post_eol_comment}")
    #     print(f"                    new_comment: {dbg_new_comment}")

    #     # Check for any comment after an end-of-line comment of the target
    #     # node.  If present, move it to the end of the predecessor node's
    #     # post-eol comment.
    #     preserve_comment = post_comment.partition("\n")[2]
    #     if preserve_comment is not None:
    #         parent.ca.items[parentref][3][0].value = (
    #             pnode_comment + preserve_comment)

    @staticmethod
    def _merge_with_map_parent(parent, parentref, post_comment) -> None:
        # Merging with the parent is more complicated than merging with a
        # preceding peer node.  The comment token appears in a different
        # subscript of the parent ca container based on whether there is
        # end-of-line comment text.  ruamel.yaml unfortunately does not
        # keep that end-of-line comment at one subscript and the following
        # comment lines in another subscript.  Worse, the comment text will
        # be either in a CommentToken or a list of CommentTokens that only
        # ever has a length of one.  This is very confusing, so my code
        # must be sensitive to both cases.
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        print("The ca items for parent:")
        pp.pprint(parent.ca.items if hasattr(parent, "ca") else "PARENT HAS NO COMMENTS!")
        print("All parent keys:")
        pp.pprint(list(parent.keys()) if hasattr(parent, "keys") else "NO KEYS!")

        if parentref is None:
            return None

        if parent.ca.items[parentref][3] is None:
            #merge_with_parent_having_eolc(parent, post_comment)
            exit(86)
        else:
            #merge_with_parent_without_eolc(parent, post_comment)
            exit(42)

    @staticmethod
    def _merge_with_preceding_map_peer(data, post_comment, prekey) -> None:
        pnode_comment = data.ca.items[prekey][2].value

        # Strip the preceding node's post-eol-comment of content that is
        # likely meant for the to-be-deleted node.
        pnode_eol_comment, pnode_post_eol_comment = Comments._get_comment_parts(
            pnode_comment)
        pnode_eol_comment += "\n"
        stripped_pnode_post_eol_comment = (
            Comments._strip_next_node_comment(pnode_post_eol_comment)
            if pnode_post_eol_comment is not None
            else "")
        pnode_comment = (
            pnode_eol_comment +
            stripped_pnode_post_eol_comment)
        data.ca.items[prekey][2].value = pnode_comment

        # Check for any comment after an end-of-line comment of the target
        # node.  If present, move it to the end of the predecessor node's
        # post-eol comment.
        preserve_comment = post_comment.partition("\n")[2]
        if preserve_comment is not None:
            data.ca.items[prekey][2].value = (
                pnode_comment + preserve_comment)

    @staticmethod
    def del_map_comment_for_entry(
        data: Any, key: Any, parent: Any, parentref: Any
    ) -> None:
        """
        Delete comments for a key-value pair from a map.

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

        # In order to preserve the post-node comment, omiting any end-of-line
        # comment, it must be appended/moved to the node preceding the deleted
        # node.  That preceding node will be either an immediate peer or the
        # parent.  If however the target node has no post-comment -- even if it
        # does have an EOL comment -- there will be nothing to preserve.
        if hasattr(data, "ca") and key in data.ca.items:
            # There is an end-of-line comment, post-eol-comment (i.e. a comment
            # after this node's EOL comment that is preceding the NEXT node
            # which must be attached to the end of the PRECEDING node's
            # comment), or both.  A comment merge is necessary only when there
            # is a post-eol-comment.  So, is there a post-eol-comment?
            keylist: list[Any] = list(data.keys())
            keydex: int = keylist.index(key)
            predex: int = keydex - 1
            node_comment = data.ca.items[key][2].value
            node_post_eol_comment = node_comment.partition("\n")[2]

            if node_post_eol_comment is not None:
                # There is a post-eol-comment that must be preserved
                if predex < 0:
                    Comments._merge_with_map_parent(
                        parent, parentref, node_comment)
                else:
                    preceding_key: Any = keylist[predex]
                    Comments._merge_with_preceding_map_peer(
                        data, node_comment, preceding_key)
