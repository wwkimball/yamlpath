"""
Implement Comments, a static lib of generally-useful code for YAML Comments.

Copyright 2022 William W. Kimball, Jr. MBA MSIS
"""
from typing import Any, Iterable, List, Tuple, Union

from ruamel.yaml.tokens import CommentToken


class Comments:
    """Helper methods for common YAML Comment operations."""

    # Define some constants to keep track of how ruamel.yaml identifies where
    # within ca instances it stores comments.  The names for these positions
    # were found within the Comment class in comments.py:
    # *** For pre-comments(?) or non-dict entities (but also not lists?):
    RYCA_COMMENT_POST = 0
    RYCA_COMMENT_PRE_L = 1        # MUST be a list of CommentTokens
    # *** For dict containers:
    RYCA_DICT_POST_KEY = 0
    RYCA_DICT_PRE_KEY_L = 1       # MUST be a list of CommentTokens
    RYCA_DICT_POST_VALUE = 2
    RYCA_DICT_PRE_VALUE_L = 3     # MUST be a list of CommentTokens
    # *** For list containers (note the unexpected reversal of PRE|POST):
    RYCA_LIST_PRE_ITEM = 0
    RYCA_LIST_POST_ITEM_L = 1     # MUST be a list of CommentTokens

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
    def _interrogate_1d_ca(
        items: Iterable, ref: Any, index: int
    ) -> Union[str, None]:
        """Get comment text from a ruamel.yaml ca's items or None."""
        if (ref in items
            and isinstance(items[ref], list)
            and len(items[ref]) >= index
            and items[ref] is not None
        ):
            return items[ref][index].value

        return None

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
    #     pnode_comment = (parent.ca.items[parentref][Comments.RYCA_DICT_POST_VALUE].value
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
    #     parent.ca.items[parentref][Comments.RYCA_DICT_POST_VALUE].value = (
    #         pnode_eol_comment +
    #         stripped_pnode_post_eol_comment)

    #     # DEBUG
    #     dbg_pnode_comment = pnode_comment.replace("\n", "\\n")
    #     dbg_pnode_eol_comment = pnode_eol_comment.replace("\n", "\\n")
    #     dbg_pnode_post_eol_comment = pnode_post_eol_comment.replace("\n", "\\n")
    #     dbg_stripped_pnode_post_eol_comment = stripped_pnode_post_eol_comment.replace("\n", "\\n")
    #     dbg_new_comment = parent.ca.items[parentref][Comments.RYCA_DICT_POST_VALUE].value.replace("\n", "\\n")
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
    #         parent.ca.items[parentref][Comments.RYCA_DICT_POST_VALUE].value = (
    #             pnode_comment + preserve_comment)

    # def merge_with_parent_without_eolc(parent, post_comment) -> None:
    #     # Pull the pre node comment from the node's parent; it will be in
    #     # one of multiple possible subscripts.
    #     print(f"Attempting to pull parent comment for parentref, {parentref}.")
    #     pnode_comment = (parent.ca.items[parentref][Comments.RYCA_DICT_PRE_VALUE_L][0].value
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
    #     parent.ca.items[parentref][Comments.RYCA_DICT_PRE_VALUE_L][0].value = (
    #         pnode_eol_comment +
    #         stripped_pnode_post_eol_comment)

    #     # DEBUG
    #     dbg_pnode_comment = pnode_comment.replace("\n", "\\n")
    #     dbg_pnode_eol_comment = pnode_eol_comment.replace("\n", "\\n")
    #     dbg_pnode_post_eol_comment = pnode_post_eol_comment.replace("\n", "\\n")
    #     dbg_stripped_pnode_post_eol_comment = stripped_pnode_post_eol_comment.replace("\n", "\\n")
    #     dbg_new_comment = parent.ca.items[parentref][Comments.RYCA_DICT_PRE_VALUE_L][0].value.replace("\n", "\\n")
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
    #         parent.ca.items[parentref][Comments.RYCA_DICT_PRE_VALUE_L][0].value = (
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
        print("*" * 80 + "\n" + "The ca items for parent:")
        pp.pprint(parent.ca.items if hasattr(parent, "ca") else "PARENT HAS NO COMMENTS!")
        print("The ca comment for parent:")
        pp.pprint(parent.ca.comment if hasattr(parent, "ca") else "PARENT HAS NO COMMENTS!")
        print("All parent keys:")
        pp.pprint(list(parent.keys()) if hasattr(parent, "keys") else "NO KEYS!")

        if parentref is None:
            return None

        if parent.ca.items[parentref][Comments.RYCA_DICT_PRE_VALUE_L] is None:
            #merge_with_parent_having_eolc(parent, post_comment)
            exit(86)
        else:
            #merge_with_parent_without_eolc(parent, post_comment)
            exit(42)

    @staticmethod
    def _merge_with_preceding_map_peer(data, post_comment, prekey) -> None:
        pnode_comment = data.ca.items[prekey][Comments.RYCA_DICT_POST_VALUE].value

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
        data.ca.items[prekey][Comments.RYCA_DICT_POST_VALUE].value = pnode_comment

        # Check for any comment after an end-of-line comment of the target
        # node.  If present, move it to the end of the predecessor node's
        # post-eol comment.
        preserve_comment = post_comment.partition("\n")[2]
        if preserve_comment is not None:
            data.ca.items[prekey][Comments.RYCA_DICT_POST_VALUE].value = (
                pnode_comment + preserve_comment)

    @staticmethod
    def _strip_next_node_comment_from_aio(
        pnode_post_eol_comment: CommentToken
    ) -> None:
        """Strip text of content that is likely meant for the next node."""
        if (pnode_post_eol_comment is None
            or not isinstance(pnode_post_eol_comment, CommentToken)
            or pnode_post_eol_comment.value is None
        ):
            # DEBUG
            print("!" * 160 + "_strip_next_node_comment_from_aio BAIL OUT ON FAILED PRECONDITIONS!")
            return None

        # Remove the target node's pre-node comment from the predecessor node's
        # post-eol comment.  Stop removing lines when an empty-line or possible
        # commented YAML is detected.  There is always a stray \n on the final
        # line.
        pnode_comment_lines = pnode_post_eol_comment.value[:-1].split("\n")
        eol_comment = pnode_comment_lines.pop(0)
        line_count = len(pnode_comment_lines)
        preserve_to = line_count
        keep_lines = 0

        # DEBUG
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        print("/" * 80 + "\n" + "The lines being evaluated:")
        pp.pprint(pnode_comment_lines)

        for pre_index, pre_line in enumerate(
            reversed(pnode_comment_lines)
        ):
            pre_content = pre_line.partition("#")[2].lstrip()
            print("/" * 5 + f"EVALUATING: {pre_content}({len(pre_content)})")

            # Stop preserving lines at the first (last) blank line
            if len(pre_content) < 1:
                break

            # Check for possible YAML markup
            if pre_content[0] == '-' or ':' in pre_content:
                # May be YAML; there's room here for deeper testing...
                break

            keep_lines = pre_index

        preserve_to = line_count - keep_lines - 1
        pnode_post_eol_comment.value = (
             eol_comment +
            "\n".join(pnode_comment_lines[0:preserve_to]) +
            ("\n" if preserve_to >= 0 else ""))

    @staticmethod
    def _strip_next_node_comment_from_lst(
        pnode_post_eol_comments: List[CommentToken]
    ) -> None:
        """Strip text of content that is likely meant for the next node."""
        # DEBUG
        import pprint
        pp = pprint.PrettyPrinter(indent=4)

        line_count = len(pnode_post_eol_comments)
        preserve_to = line_count
        keep_lines = 0
        for pre_index, ct in enumerate(reversed(pnode_post_eol_comments)):
            pre_line = ct.value
            pre_content = pre_line.partition("#")[2].lstrip()

            dbg_pre_content = pre_content.replace("\n", "\\n")
            print("\\" * 5 + f"l_EVALUATING CommentToken@{pre_index}:{dbg_pre_content}({len(pre_content)})")
            pp.pprint(ct)

            # Stop preserving lines at the first (last) blank line; but there's
            # a trick.  Blank lines are hidden at the end of the preceding
            # CommentToken as a double new-line marker.
            if len(pre_content) < 1:
                print("\\" * 5 + f"l_STOPPING on an empty line!")
                break

            if len(pre_content) >= 2 and "\n\n" == pre_content[-2:]:
                print("\\" * 5 + f"l_STOPPING on an empty line!")
                break

            # Check for possible YAML markup
            if pre_content[0] == '-' or ':' in pre_content:
                # May be YAML; there's room here for deeper testing...
                print("\\" * 5 + f"l_STOPPING on potential YAML!")
                break

            print("\\" * 5 + f"l_TARGETTING CommentToken@{pre_index} for deletion!")
            keep_lines = pre_index

        preserve_to = line_count - keep_lines - 2
        print("\\" * 5 + f"l_PREPARING TO DESTROY from index {line_count} to {preserve_to}!")
        for idx in range(line_count - 1, preserve_to, -1):
            print("\\" * 5 + f"l_DESTROYING CommentToken@{idx}!")
            del pnode_post_eol_comments[idx]

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
        print("*" * 80 + "\n" + "The ca items for data:")
        pp.pprint(data.ca.items if hasattr(data, "ca") else "DATA HAS NO CA ITEMS!")
        print("*-" * 40 + "The ca comment for data:")
        pp.pprint(data.ca.comment if hasattr(data, "ca") else "DATA HAS NO CA COMMENTS!")
        print("*=" * 40 + "All data keys:")
        pp.pprint(list(data.keys()))

        print("+" * 80 + "\n" + "The ca items for parent:")
        pp.pprint(parent.ca.items if hasattr(parent, "ca") else "PARENT HAS NO CA ITEMS!")
        print("+-" * 40 + "The ca comment for parent:")
        pp.pprint(parent.ca.comment if hasattr(parent, "ca") else "PARENT HAS NO CA COMMENTS!")
        print("+=" * 40 + "All parent keys:")
        pp.pprint(list(parent.keys()) if hasattr(parent, "keys") and callable(getattr(parent, "keys")) else "PARENT HAS NO KEYS METHOD")

        print("@" * 80 + "\n" + "The ca items for data[key]:")
        pp.pprint(data[key].ca.items if hasattr(data[key], "ca") else "data[key] HAS NO CA ITEMS!")
        print("@-" * 40 + "The ca comment for data[key]:")
        pp.pprint(data[key].ca.comment if hasattr(data[key], "ca") else "data[key] HAS NO CA COMMENTS!")
        print("@=" * 40 + "All data[key] keys:")
        pp.pprint(list(data[key].keys()) if hasattr(data[key], "keys") and callable(getattr(data[key], "keys")) else "data[key] HAS NO KEYS METHOD")

        # In order to handle the comments just once on a single pass, these
        # steps will be taken:
        # 1. Gather up the post-node comment, discarding any EOL comment.  This
        #    may yield a single CommentToken or a list of CommentTokens.
        # 2. Remove obvious for-node pre-node comment line(s) or CommentTokens
        #    from the predecessor node's container's ca collection.
        # 3. Append the preserved post-node comment to the predecessor node's
        #    container's ca collection (which may require creation of a novel
        #    ca entry).

        # First, delete any EOL comment for the target node but PRESERVE any
        # post-EOL comment attached to it by merging that content to the node's
        # predecessor, which may be either a peer node or the node's parent.
        # Such additional text will be either:
        # 1. At [Comments.RYCA_DICT_POST_VALUE] and will have all lines of
        #    the post-value comment (end-of-line comment AND ALL FOLLOWING
        #    COMMENTED AND WHITESPACE LINES) in a single CommenToken,
        #    separated by \n markers.  This is most comments, excluding the
        #    first child of a dict.
        # 2. At [Comments.RYCA_DICT_PRE_VALUE_L] and will have a discrete
        #    CommentToken for each line of the comment text, each still
        #    terminated by \n markers.

        # In order to preserve the post-node comment, omiting any end-of-line
        # comment, it must be appended/moved to the node preceding the deleted
        # node.  That preceding node will be either an immediate peer or the
        # parent.  If however the target node has no post-comment -- even if it
        # does have an EOL comment -- there will be nothing to preserve.
        node_post_eol_comment = None
        if hasattr(data, "ca") and key in data.ca.items:
            # There is an end-of-line comment, post-eol-comment (i.e. a comment
            # after this node's EOL comment that is preceding the NEXT node
            # which must be attached to the end of the PRECEDING node's
            # comment), or both.  A comment merge is necessary only when there
            # is a post-eol-comment.  So, is there a post-eol-comment?

            # Merge any target node post-EOL comment with the predecessor
            # node's post-EOL comment.
            if data.ca.items[key][Comments.RYCA_DICT_POST_VALUE] is not None:
                node_comment = data.ca.items[key][Comments.RYCA_DICT_POST_VALUE].value
                node_post_eol_comment = node_comment.partition("\n")[2]
            else:
                node_comment = data.ca.items[key][Comments.RYCA_DICT_PRE_VALUE_L][-1].value
                node_post_eol_comment = node_comment.partition("\n")[2]

            # if node_post_eol_comment is not None:
            #     # There is a post-eol-comment that must be preserved
            #     if predex < 0:
            #         Comments._merge_with_map_parent(
            #             parent, parentref, node_comment)
            #     else:
            #         preceding_key: Any = keylist[predex]
            #         Comments._merge_with_preceding_map_peer(
            #             data, node_comment, preceding_key)

        dbg_node_post_eol_comment = node_post_eol_comment.replace("\n", "\\n") if node_post_eol_comment else None
        print("X"*80)
        print(f"Preserving: {dbg_node_post_eol_comment}" if node_post_eol_comment else "NO POST-EOL COMMENT TO PRESERVE!")
        print("X"*80)

        # Then, delete any obvious comment meant for the target node.  Such
        # a comment will be at any of:
        # 1. Any pre-comment for the FIRST child of a dict will have that
        #    comment stuffed in EITHER:
        #    1.1:  the ca's comment property at
        #          [Comments.RYCA_COMMENT_PRE_L] where each line is its own
        #          CommentToken ONLY WHEN THE PARENT DOES *NOT* HAVE AN EOL
        #          COMMENT; or
        #    1.2:  the ca's comment poperty at [Comments.RYCA_COMMENT_POST]
        #          where all lines are stored together in a single
        #          CommentToken separated by \n marks.
        # 2. A pre-comment for a node preceded by another dict will have its
        #    pre-comment in the post-EOL comment of the predecessor node's last
        #    child.
        keylist: list[Any] = list(data.keys())
        keydex: int = keylist.index(key)
        predex: int = keydex - 1
        if 0 == keydex:
            if data.ca.comment is None:
                if node_post_eol_comment:
                    # Add a novel comment to the node's container
                    data.ca.comment = CommentToken(node_post_eol_comment)

                # Nothing more to do; there are no comments in this dict
                return None

            # The target key is the first child; delete any obvious comment
            # meant for the target node from the node's container's post-EOL
            # comment and merge any post-EOL comment of the target node
            # with the remainder of the container's post-EOL comment.
            if data.ca.comment[Comments.RYCA_COMMENT_POST] is None:
                # The container does NOT have an EOL comment; each pre-node
                # comment line is in its own CommentToken.
                print("?1" * 40 + "Need to parse a list of PARENT CommentTokens because this FIRST node's PARENT does /NOT/ have an EOL comment...")
                Comments._strip_next_node_comment_from_lst(
                    data.ca.comment[Comments.RYCA_COMMENT_PRE_L])
            else:
                # The container HAS an EOL comment; all pre-node comment
                # lines are crammed into a single CommentToken.
                print("?2" * 40 + "Need to parse a multi-line single token because this FIRST node's PARENT /HAS/ an EOL comment...")
                Comments._strip_next_node_comment_from_aio(
                    data.ca.comment[Comments.RYCA_COMMENT_POST])
        else:
            # The target key is any child except the first; delete any
            # obvious comment meant for the target node from the
            # predecessor peer node's post-EOL comment and merge any post-
            # EOL comment of the target node with the remainder of its
            # predecessor peer node's post-EOL comment.
            #
            # If the predecessor peer node is another map, then this node's
            # pre-comment will be hidden in the post-EOL comment of the
            # predecessor node's last, deepest child.  Are we having fun, yet?
            prekey: Any = keylist[predex]
            predata: Any = data[prekey]
            if isinstance(predata, dict) and hasattr(predata, "ca"):
                prekeylist: list[Any] = list(predata.keys())
                prelastkey: int = prekeylist[-1] if len(prekeylist) > 0 else None
                prelastcr: Any = predata.ca.items[prelastkey] if prelastkey is not None and prelastkey in predata.ca.items else None

                print("^" * 80 + "\n" + "The ca items for predata:")
                pp.pprint(predata.ca.items if hasattr(predata, "ca") else "predata HAS NO COMMENTS!")
                print("^-" * 40 + "The ca comment for predata:")
                pp.pprint(predata.ca.comment if hasattr(predata, "ca") else "predata HAS NO COMMENTS!")
                print("^=" * 40 + "All predata keys:")
                pp.pprint(list(predata.keys()) if hasattr(predata, "keys") and callable(getattr(predata, "keys")) else "predata HAS NO KEYS METHOD")
                print("^_" * 40 + f"Identified last key: {prelastkey}")
                print("^." * 40 + "Got comment record from prelastkey:")
                pp.pprint(prelastcr)

                if prelastcr is not None:
                    # There is a predecessor comment to parse
                    if prelastcr[Comments.RYCA_DICT_POST_VALUE] is None:
                        print("?3" * 40 + "Need to parse a list of CommentTokens...")
                        exit(43)
                    else:
                        print("?4" * 40 + "Need to parse a multi-line single token...")
                        Comments._strip_next_node_comment_from_aio(
                            prelastcr[Comments.RYCA_DICT_POST_VALUE])
            elif prekey in data.ca.items:
                if data.ca.items[prekey][Comments.RYCA_DICT_POST_VALUE] is None:
                    print("?5" * 40 + "Need to parse a list of CommentTokens...")
                    exit(44)
                else:
                    print("?6" * 40 + "Need to parse a multi-line single token...")
                    Comments._strip_next_node_comment_from_aio(
                        data.ca.items[prekey][Comments.RYCA_DICT_POST_VALUE])
