"""
Implement Comments, a static lib of generally-useful code for YAML Comments.

Copyright 2022 William W. Kimball, Jr. MBA MSIS
"""
from typing import Any, Iterable, List, Sequence, Tuple, Union
from charset_normalizer import from_bytes

from ruamel.yaml.comments import CommentedMap, CommentedSeq, CommentedSet
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

    # Define constants used to track whether a comment is in a ca.comment or
    # the ca map.
    IN_CA_COMMENT = 0
    IN_CA_MAP = 1

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

    # @staticmethod
    # def _interrogate_1d_ca(
    #     items: Iterable, ref: Any, index: int
    # ) -> Union[str, None]:
    #     """Get comment text from a ruamel.yaml ca's items or None."""
    #     if (ref in items
    #         and isinstance(items[ref], list)
    #         and len(items[ref]) >= index
    #         and items[ref] is not None
    #     ):
    #         return items[ref][index].value

    #     return None

    # @staticmethod
    # def _get_comment_parts(comment_text: str) -> Tuple[str, str]:
    #     """Parse a ruamel.yaml comment into its EOL and after parts."""
    #     return (
    #         comment_text.partition("\n")[0],
    #         comment_text.partition("\n")[2])

    @staticmethod
    def _strip_next_node_comment(
        comment: Union[None, CommentToken, List[CommentToken]]
    ) -> Union[None, CommentToken, List[CommentToken]]:
        """
        Strip comment text that is likely meant for the next node.
        """
        # Delete any obvious comment meant for the target node.  Such
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
        if comment is None:
            return None

        if isinstance(comment, CommentToken):
            # Got an all-in-one comment:
            # Remove the target node's pre-node comment from the
            # predecessor node's post-eol comment.  Stop removing lines
            # when an empty-line or possible commented YAML is detected.
            comment_lines = comment.value.split("\n")
            line_count = len(comment_lines)
            preserve_to = line_count
            keep_lines = 0
            for line_index, comment_line in enumerate(
                reversed(comment_lines)
            ):
                keep_lines = line_index
                pre_content = comment_line.partition("#")[2].lstrip()

                # Stop preserving lines at the first (last) blank line
                if len(pre_content) < 1:
                    break

                # Check for possible YAML markup
                if pre_content[0] == '-' or ':' in pre_content:
                    # May be YAML; there's room here for deeper testing...
                    break

            preserve_to = line_count - keep_lines - 2
            return CommentToken(
                ("\n".join(comment_lines[0:preserve_to]) +
                 ("\n" if preserve_to >= 0 else "")),
                comment.start_mark,
                comment.end_mark,
                comment.column)

        if len(comment) > 1:
            # Got a list of comments:
            # Process the lines from bottom-up, removing them until an empty-
            # line or possible commented YAML is detected.
            line_count = len(comment)
            preserve_to = line_count
            keep_lines = 0
            for line_index, comment_line in enumerate(
                reversed(comment)
            ):
                keep_lines = line_index
                pre_content = comment_line.value.partition("#")[2].lstrip() if comment_line is not None else ""

                # Stop preserving lines at the first (last) blank line
                if len(pre_content) < 1:
                    break

                # Check for possible YAML markup
                if pre_content[0] == '-' or ':' in pre_content:
                    # May be YAML; there's room here for deeper testing...
                    break

            return comment[0:preserve_to]
        return []

    # # def merge_with_parent_having_eolc(parent, post_comment) -> None:
    # #     # Pull the pre node comment from the node's parent; it will be in
    # #     # one of multiple possible subscripts.
    # #     print(f"Attempting to pull parent comment for parentref, {parentref}.")
    # #     pnode_comment = (parent.ca.items[parentref][Comments.RYCA_DICT_POST_VALUE].value
    # #                     if parentref is not None
    # #                     else None)

    # #     # Strip the preceding node's post-eol-comment of content that is
    # #     # likely meant for the to-be-deleted node.
    # #     pnode_eol_comment, pnode_post_eol_comment = get_comment_parts(
    # #         pnode_comment)
    # #     pnode_eol_comment += "\n"
    # #     stripped_pnode_post_eol_comment = (
    # #         strip_next_node_comment(pnode_post_eol_comment)
    # #         if pnode_post_eol_comment is not None
    # #         else "")
    # #     parent.ca.items[parentref][Comments.RYCA_DICT_POST_VALUE].value = (
    # #         pnode_eol_comment +
    # #         stripped_pnode_post_eol_comment)

    # #     # DEBUG
    # #     dbg_pnode_comment = pnode_comment.replace("\n", "\\n")
    # #     dbg_pnode_eol_comment = pnode_eol_comment.replace("\n", "\\n")
    # #     dbg_pnode_post_eol_comment = pnode_post_eol_comment.replace("\n", "\\n")
    # #     dbg_stripped_pnode_post_eol_comment = stripped_pnode_post_eol_comment.replace("\n", "\\n")
    # #     dbg_new_comment = parent.ca.items[parentref][Comments.RYCA_DICT_POST_VALUE].value.replace("\n", "\\n")
    # #     print(f"                  pnode_comment: {dbg_pnode_comment}")
    # #     print(f"              pnode_eol_comment: {dbg_pnode_eol_comment}")
    # #     print(f"         pnode_post_eol_comment: {dbg_pnode_post_eol_comment}")
    # #     print(f"stripped_pnode_post_eol_comment: {dbg_stripped_pnode_post_eol_comment}")
    # #     print(f"                    new_comment: {dbg_new_comment}")

    # #     # Check for any comment after an end-of-line comment of the target
    # #     # node.  If present, move it to the end of the predecessor node's
    # #     # post-eol comment.
    # #     preserve_comment = post_comment.partition("\n")[2]
    # #     if preserve_comment is not None:
    # #         parent.ca.items[parentref][Comments.RYCA_DICT_POST_VALUE].value = (
    # #             pnode_comment + preserve_comment)

    # # def merge_with_parent_without_eolc(parent, post_comment) -> None:
    # #     # Pull the pre node comment from the node's parent; it will be in
    # #     # one of multiple possible subscripts.
    # #     print(f"Attempting to pull parent comment for parentref, {parentref}.")
    # #     pnode_comment = (parent.ca.items[parentref][Comments.RYCA_DICT_PRE_VALUE_L][0].value
    # #                     if parentref is not None
    # #                     else None)

    # #     # Strip the preceding node's post-eol-comment of content that is
    # #     # likely meant for the to-be-deleted node.
    # #     pnode_eol_comment, pnode_post_eol_comment = get_comment_parts(
    # #         pnode_comment)
    # #     pnode_eol_comment += "\n"
    # #     stripped_pnode_post_eol_comment = (
    # #         strip_next_node_comment(pnode_post_eol_comment)
    # #         if pnode_post_eol_comment is not None
    # #         else "")
    # #     parent.ca.items[parentref][Comments.RYCA_DICT_PRE_VALUE_L][0].value = (
    # #         pnode_eol_comment +
    # #         stripped_pnode_post_eol_comment)

    # #     # DEBUG
    # #     dbg_pnode_comment = pnode_comment.replace("\n", "\\n")
    # #     dbg_pnode_eol_comment = pnode_eol_comment.replace("\n", "\\n")
    # #     dbg_pnode_post_eol_comment = pnode_post_eol_comment.replace("\n", "\\n")
    # #     dbg_stripped_pnode_post_eol_comment = stripped_pnode_post_eol_comment.replace("\n", "\\n")
    # #     dbg_new_comment = parent.ca.items[parentref][Comments.RYCA_DICT_PRE_VALUE_L][0].value.replace("\n", "\\n")
    # #     print(f"                  pnode_comment: {dbg_pnode_comment}")
    # #     print(f"              pnode_eol_comment: {dbg_pnode_eol_comment}")
    # #     print(f"         pnode_post_eol_comment: {dbg_pnode_post_eol_comment}")
    # #     print(f"stripped_pnode_post_eol_comment: {dbg_stripped_pnode_post_eol_comment}")
    # #     print(f"                    new_comment: {dbg_new_comment}")

    # #     # Check for any comment after an end-of-line comment of the target
    # #     # node.  If present, move it to the end of the predecessor node's
    # #     # post-eol comment.
    # #     preserve_comment = post_comment.partition("\n")[2]
    # #     if preserve_comment is not None:
    # #         parent.ca.items[parentref][Comments.RYCA_DICT_PRE_VALUE_L][0].value = (
    # #             pnode_comment + preserve_comment)

    # @staticmethod
    # def _merge_with_map_parent(parent, parentref, post_comment) -> None:
    #     # Merging with the parent is more complicated than merging with a
    #     # preceding peer node.  The comment token appears in a different
    #     # subscript of the parent ca container based on whether there is
    #     # end-of-line comment text.  ruamel.yaml unfortunately does not
    #     # keep that end-of-line comment at one subscript and the following
    #     # comment lines in another subscript.  Worse, the comment text will
    #     # be either in a CommentToken or a list of CommentTokens that only
    #     # ever has a length of one.  This is very confusing, so my code
    #     # must be sensitive to both cases.
    #     import pprint
    #     pp = pprint.PrettyPrinter(indent=4)
    #     print("*" * 80 + "\n" + "The ca items for parent:")
    #     pp.pprint(parent.ca.items if hasattr(parent, "ca") else "PARENT HAS NO COMMENTS!")
    #     print("The ca comment for parent:")
    #     pp.pprint(parent.ca.comment if hasattr(parent, "ca") else "PARENT HAS NO COMMENTS!")
    #     print("All parent keys:")
    #     pp.pprint(list(parent.keys()) if hasattr(parent, "keys") else "NO KEYS!")

    #     if parentref is None:
    #         return None

    #     if parent.ca.items[parentref][Comments.RYCA_DICT_PRE_VALUE_L] is None:
    #         #merge_with_parent_having_eolc(parent, post_comment)
    #         exit(86)
    #     else:
    #         #merge_with_parent_without_eolc(parent, post_comment)
    #         exit(42)

    # @staticmethod
    # def _merge_with_preceding_map_peer(data, post_comment, prekey) -> None:
    #     pnode_comment = data.ca.items[prekey][Comments.RYCA_DICT_POST_VALUE].value

    #     # Strip the preceding node's post-eol-comment of content that is
    #     # likely meant for the to-be-deleted node.
    #     pnode_eol_comment, pnode_post_eol_comment = Comments._get_comment_parts(
    #         pnode_comment)
    #     pnode_eol_comment += "\n"
    #     stripped_pnode_post_eol_comment = (
    #         Comments._strip_next_node_comment(pnode_post_eol_comment)
    #         if pnode_post_eol_comment is not None
    #         else "")
    #     pnode_comment = (
    #         pnode_eol_comment +
    #         stripped_pnode_post_eol_comment)
    #     data.ca.items[prekey][Comments.RYCA_DICT_POST_VALUE].value = pnode_comment

    #     # Check for any comment after an end-of-line comment of the target
    #     # node.  If present, move it to the end of the predecessor node's
    #     # post-eol comment.
    #     preserve_comment = post_comment.partition("\n")[2]
    #     if preserve_comment is not None:
    #         data.ca.items[prekey][Comments.RYCA_DICT_POST_VALUE].value = (
    #             pnode_comment + preserve_comment)

    # @staticmethod
    # def _strip_next_node_comment_from_aio(
    #     pnode_post_eol_comment: CommentToken
    # ) -> None:
    #     """Strip text of content that is likely meant for the next node."""
    #     if (pnode_post_eol_comment is None
    #         or not isinstance(pnode_post_eol_comment, CommentToken)
    #         or pnode_post_eol_comment.value is None
    #     ):
    #         # DEBUG
    #         print("!" * 160 + "_strip_next_node_comment_from_aio BAIL OUT ON FAILED PRECONDITIONS!")
    #         return None

    #     # Remove the target node's pre-node comment from the predecessor node's
    #     # post-eol comment.  Stop removing lines when an empty-line or possible
    #     # commented YAML is detected.  There is always a stray \n on the final
    #     # line.
    #     pnode_comment_lines = pnode_post_eol_comment.value[:-1].split("\n")
    #     eol_comment = pnode_comment_lines.pop(0)
    #     line_count = len(pnode_comment_lines)
    #     preserve_to = line_count
    #     keep_lines = 0

    #     # DEBUG
    #     import pprint
    #     pp = pprint.PrettyPrinter(indent=4)
    #     print("/" * 80 + "\n" + "The lines being evaluated:")
    #     pp.pprint(pnode_comment_lines)

    #     for pre_index, pre_line in enumerate(
    #         reversed(pnode_comment_lines)
    #     ):
    #         pre_content = pre_line.partition("#")[2].lstrip()
    #         print("/" * 5 + f"EVALUATING: {pre_content}({len(pre_content)})")

    #         # Stop preserving lines at the first (last) blank line
    #         if len(pre_content) < 1:
    #             break

    #         # Check for possible YAML markup
    #         if pre_content[0] == '-' or ':' in pre_content:
    #             # May be YAML; there's room here for deeper testing...
    #             break

    #         keep_lines = pre_index

    #     preserve_to = line_count - keep_lines - 1
    #     pnode_post_eol_comment.value = (
    #          eol_comment +
    #         "\n".join(pnode_comment_lines[0:preserve_to]) +
    #         ("\n" if preserve_to >= 0 else ""))

    # @staticmethod
    # def _strip_next_node_comment_from_lst(
    #     pnode_post_eol_comments: List[CommentToken]
    # ) -> None:
    #     """Strip text of content that is likely meant for the next node."""
    #     # DEBUG
    #     import pprint
    #     pp = pprint.PrettyPrinter(indent=4)

    #     line_count = len(pnode_post_eol_comments)
    #     preserve_to = line_count
    #     keep_lines = 0
    #     for pre_index, ct in enumerate(reversed(pnode_post_eol_comments)):
    #         pre_line = ct.value
    #         pre_content = pre_line.partition("#")[2].lstrip()

    #         dbg_pre_content = pre_content.replace("\n", "\\n")
    #         print("\\" * 5 + f"l_EVALUATING CommentToken@{pre_index}:{dbg_pre_content}({len(pre_content)})")
    #         pp.pprint(ct)

    #         # Stop preserving lines at the first (last) blank line; but there's
    #         # a trick.  Blank lines are hidden at the end of the preceding
    #         # CommentToken as a double new-line marker.
    #         if len(pre_content) < 1:
    #             print("\\" * 5 + f"l_STOPPING on an empty line!")
    #             break

    #         if len(pre_content) >= 2 and "\n\n" == pre_content[-2:]:
    #             print("\\" * 5 + f"l_STOPPING on an empty line!")
    #             break

    #         # Check for possible YAML markup
    #         if pre_content[0] == '-' or ':' in pre_content:
    #             # May be YAML; there's room here for deeper testing...
    #             print("\\" * 5 + f"l_STOPPING on potential YAML!")
    #             break

    #         print("\\" * 5 + f"l_TARGETTING CommentToken@{pre_index} for deletion!")
    #         keep_lines = pre_index

    #     preserve_to = line_count - keep_lines - 2
    #     print("\\" * 5 + f"l_PREPARING TO DESTROY from index {line_count} to {preserve_to}!")
    #     for idx in range(line_count - 1, preserve_to, -1):
    #         print("\\" * 5 + f"l_DESTROYING CommentToken@{idx}!")
    #         del pnode_post_eol_comments[idx]

    @staticmethod
    def _get_map_node_comment(
        data: CommentedMap,
        key: Any
    ) -> Union[None, CommentToken, List[CommentToken]]:
        r"""
        Get the comment(s) for a given map node, if any exist.

        Remember that the comment -- when not None -- will include any EOL
        comment *and* all commented lines following the node, if any.  You will
        get either a single CommentToken (an all-in-one comment value where
        each line of the commented text is terminated with a \n) or a list of
        CommentTokens where each CommentToken's value is terminated with a \n
        mark.
        """
        node_comment: Union[
            None, CommentToken, List[CommentToken]] = None
        if hasattr(data, "ca") and key in data.ca.items:
            # There is an end-of-line comment, post-eol-comment (i.e. a comment
            # after this node's EOL comment that is preceding the NEXT node's
            # comment), or both.
            ca_item = data.ca.items[key]
            if ca_item[Comments.RYCA_DICT_POST_VALUE] is not None:
                # There is an all-in-one comment
                # node_comment = ca_item[Comments.RYCA_DICT_POST_VALUE].value
                # node_post_eol_comment = node_comment.partition("\n")[2]
                node_comment = ca_item[Comments.RYCA_DICT_POST_VALUE]
            else:
                # There MAY BE a list of comment tokens (while not likely,
                # it could still be None).
                # node_comment = ca_item[Comments.RYCA_DICT_PRE_VALUE_L][-1].value
                # node_post_eol_comment = node_comment.partition("\n")[2]
                node_comment = ca_item[Comments.RYCA_DICT_PRE_VALUE_L]

        return node_comment

    @staticmethod
    def _find_tail_comment_in_map(
        data: CommentedMap
    ) -> Tuple[Any, Any, int]:
        """
        Find the last, deepest comment ref in a map.
        """
        tail_comment: Tuple[Any, Any, int] = (
            None, None, Comments.IN_CA_MAP)
        key_list: list[Any] = list(data.keys())
        last_key: Any = key_list[-1]
        last_data = data[last_key]

        # Recursively find the last, deepest child's ref.  If and only
        # if it is in the container's ca, then and only then will there
        # be a tail comment to return.
        if isinstance(last_data, CommentedMap):
            tail_comment = Comments._find_tail_comment_in_map(last_data)
        # TODO
        # elif isinstance(last_data, CommentedSeq):
        #     tail_comment = Comments._find_tail_comment_in_seq(last_data)
        # elif isinstance(last_data, CommentedSet):
        #     tail_comment = Comments._find_tail_comment_in_set(last_data)
        elif last_key in data.ca.items:
            tail_comment = (data.ca, last_key, Comments.IN_CA_MAP)

        return tail_comment

    @staticmethod
    def _find_preceding_map_node_comment(
        # parent: Union[CommentedMap, CommentedSeq, CommentedSet],
        # parentref: Any,
        data: CommentedMap,
        key: Any
    ) -> Tuple[Any, Any, int]:
        """
        Find the comment container and ref for the comment preceding key node.

        The result may be a reference to the comment of the key node's
        preceding peer node, immediate parent, or the very last node in a
        preceding container (map, sequence, or set).
        """
        node_comment: Tuple[Any, Any, int] = (None, None, Comments.IN_CA_MAP)
        keylist: list[Any] = list(data.keys())
        keydex: int = keylist.index(key)
        predex: int = keydex - 1
        if 0 == keydex:
            # The target node is the first child of its container, which means
            # its predecessor comment -- if there is one -- is to be found in
            # the container's ca.comment property.
            if data.ca.comment is None:
                # Signal with a None ref that the container's comment is unset
                node_comment = (data.ca, None, Comments.IN_CA_COMMENT)

            # The target key is the first child; delete any obvious comment
            # meant for the target node from the node's container's post-EOL
            # comment and merge any post-EOL comment of the target node
            # with the remainder of the container's post-EOL comment.
            elif data.ca.comment[Comments.RYCA_COMMENT_POST] is None:
                # The container does NOT have an EOL comment; each pre-node
                # comment line is in its own CommentToken.
                node_comment = (
                    data.ca,
                    Comments.RYCA_COMMENT_PRE_L,
                    Comments.IN_CA_COMMENT)
                # print("?1" * 40 + "Need to parse a list of PARENT CommentTokens because this FIRST node's PARENT does /NOT/ have an EOL comment...")
                # Comments._strip_next_node_comment_from_lst(
                #     data.ca.comment[Comments.RYCA_COMMENT_PRE_L])
            else:
                # The container HAS an EOL comment; all pre-node comment
                # lines are crammed into a single CommentToken.
                node_comment = (
                    data.ca,
                    Comments.RYCA_COMMENT_POST,
                    Comments.IN_CA_COMMENT)
                # print("?2" * 40 + "Need to parse a multi-line single token because this FIRST node's PARENT /HAS/ an EOL comment...")
                # Comments._strip_next_node_comment_from_aio(
                #     data.ca.comment[Comments.RYCA_COMMENT_POST])
        else:
            # The target key is any child except the first; delete any
            # obvious comment meant for the target node from the
            # predecessor peer node's post-EOL comment and merge any post-
            # EOL comment of the target node with the remainder of its
            # predecessor peer node's post-EOL comment.
            #
            # If the predecessor peer node is another container (map, sequence,
            # or set), then this node's pre-comment will be hidden in the post-
            # EOL comment of the container's last, deepest child.
            prekey: Any = keylist[predex]
            predata: Any = data[prekey]
            if isinstance(predata, CommentedMap):
                node_comment = Comments._find_tail_comment_in_map(predata)
            # TODO
            # elif isinstance(predata, CommentedSeq):
            #     node_comment = Comments._find_tail_comment_in_seq(predata)
            # elif isinstance(predata, CommentedSet):
            #     node_comment = Comments._find_tail_comment_in_set(predata)

            #     # prekeylist: list[Any] = list(predata.keys())
            #     # prelastkey: Any = prekeylist[-1] if len(prekeylist) > 0 else None
            #     # prelastcr: Any = predata.ca.items[prelastkey] if prelastkey is not None and prelastkey in predata.ca.items else None

            #     # # print("^" * 80 + "\n" + "The ca items for predata:")
            #     # # pp.pprint(predata.ca.items if hasattr(predata, "ca") else "predata HAS NO COMMENTS!")
            #     # # print("^-" * 40 + "The ca comment for predata:")
            #     # # pp.pprint(predata.ca.comment if hasattr(predata, "ca") else "predata HAS NO COMMENTS!")
            #     # # print("^=" * 40 + "All predata keys:")
            #     # # pp.pprint(list(predata.keys()) if hasattr(predata, "keys") and callable(getattr(predata, "keys")) else "predata HAS NO KEYS METHOD")
            #     # # print("^_" * 40 + f"Identified last key: {prelastkey}")
            #     # # print("^." * 40 + "Got comment record from prelastkey:")
            #     # # pp.pprint(prelastcr)

            #     # if prelastcr is not None:
            #     #     # There is a predecessor comment to parse
            #     #     if prelastcr[Comments.RYCA_DICT_POST_VALUE] is None:
            #     #         print("?3" * 40 + "Need to parse a list of CommentTokens...")
            #     #         exit(43)
            #     #     else:
            #     #         print("?4" * 40 + "Need to parse a multi-line single token...")
            #     #         Comments._strip_next_node_comment_from_aio(
            #     #             prelastcr[Comments.RYCA_DICT_POST_VALUE])
            elif prekey in data.ca.items:
                if data.ca.items[prekey][Comments.RYCA_DICT_POST_VALUE] is None:
                    # print("?5" * 40 + "Need to parse a list of CommentTokens...")
                    # exit(44)
                    node_comment = (
                        data.ca.items[prekey],
                        Comments.RYCA_DICT_PRE_VALUE_L,
                        Comments.IN_CA_MAP)
                else:
                    # print("?6" * 40 + "Need to parse a multi-line single token...")
                    # Comments._strip_next_node_comment_from_aio(
                    #     data.ca.items[prekey][Comments.RYCA_DICT_POST_VALUE])
                    node_comment = (
                        data.ca.items[prekey],
                        Comments.RYCA_DICT_POST_VALUE,
                        Comments.IN_CA_MAP)

        return node_comment

    @staticmethod
    def _strip_eol_comment(
        comment: Union[None, CommentToken, List[CommentToken]]
    ) -> Union[None, CommentToken, List[CommentToken]]:
        """
        Delete an EOL comment from a given comment.
        """
        if comment is None:
            return None

        if isinstance(comment, CommentToken):
            # Got an all-in-one comment
            return CommentToken(
                comment.value.partition("\n")[2],
                comment.start_mark,
                comment.end_mark,
                comment.column)

        # Got a list of comments; preserve all but the first
        if len(comment) > 1:
            return comment[1:]
        return []

    @staticmethod
    def _merge_comments(
        from_cmt: Union[None, CommentToken, List[CommentToken]],
        into_cmt: Union[None, CommentToken, List[CommentToken]]
    ) -> Union[None, CommentToken, List[CommentToken]]:
        """
        Merge comment text together, if possible.
        """
        if from_cmt is None:
            return into_cmt
        if into_cmt is None:
            return from_cmt

        if isinstance(into_cmt, list):
            if len(into_cmt) < 1:
                return from_cmt

            if isinstance(from_cmt, list):
                if len(from_cmt) < 1:
                    return into_cmt
                return [*into_cmt, *from_cmt]
            else:
                # INTO is a list while FROM is not
                return into_cmt.append(from_cmt)
        else:
            if isinstance(from_cmt, list):
                if len(from_cmt) < 1:
                    return into_cmt

                into_cmt.value += "\n".join(item.value for item in from_cmt)
                return

        # Both are strings
        into_cmt.value += from_cmt.value
        return into_cmt

    @staticmethod
    def del_map_comment_for_entry(
        data: CommentedMap, key: Any, parent: Any, parentref: Any
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
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)
        # print("*" * 80 + "\n" + "The ca items for data:")
        # pp.pprint(data.ca.items if hasattr(data, "ca") else "DATA HAS NO CA ITEMS!")
        # print("*-" * 40 + "The ca comment for data:")
        # pp.pprint(data.ca.comment if hasattr(data, "ca") else "DATA HAS NO CA COMMENTS!")
        # print("*=" * 40 + "All data keys:")
        # pp.pprint(list(data.keys()))

        # print("+" * 80 + "\n" + "The ca items for parent:")
        # pp.pprint(parent.ca.items if hasattr(parent, "ca") else "PARENT HAS NO CA ITEMS!")
        # print("+-" * 40 + "The ca comment for parent:")
        # pp.pprint(parent.ca.comment if hasattr(parent, "ca") else "PARENT HAS NO CA COMMENTS!")
        # print("+=" * 40 + "All parent keys:")
        # pp.pprint(list(parent.keys()) if hasattr(parent, "keys") and callable(getattr(parent, "keys")) else "PARENT HAS NO KEYS METHOD")

        # print("@" * 80 + "\n" + "The ca items for data[key]:")
        # pp.pprint(data[key].ca.items if hasattr(data[key], "ca") else "data[key] HAS NO CA ITEMS!")
        # print("@-" * 40 + "The ca comment for data[key]:")
        # pp.pprint(data[key].ca.comment if hasattr(data[key], "ca") else "data[key] HAS NO CA COMMENTS!")
        # print("@=" * 40 + "All data[key] keys:")
        # pp.pprint(list(data[key].keys()) if hasattr(data[key], "keys") and callable(getattr(data[key], "keys")) else "data[key] HAS NO KEYS METHOD")

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
        # node_post_eol_comment = None
        # if hasattr(data, "ca") and key in data.ca.items:
        #     # There is an end-of-line comment, post-eol-comment (i.e. a comment
        #     # after this node's EOL comment that is preceding the NEXT node
        #     # which must be attached to the end of the PRECEDING node's
        #     # comment), or both.  A comment merge is necessary only when there
        #     # is a post-eol-comment.  So, is there a post-eol-comment?

        #     # Merge any target node post-EOL comment with the predecessor
        #     # node's post-EOL comment.
        #     if data.ca.items[key][Comments.RYCA_DICT_POST_VALUE] is not None:
        #         node_comment = data.ca.items[key][Comments.RYCA_DICT_POST_VALUE].value
        #         node_post_eol_comment = node_comment.partition("\n")[2]
        #     else:
        #         node_comment = data.ca.items[key][Comments.RYCA_DICT_PRE_VALUE_L][-1].value
        #         node_post_eol_comment = node_comment.partition("\n")[2]

            # if node_post_eol_comment is not None:
            #     # There is a post-eol-comment that must be preserved
            #     if predex < 0:
            #         Comments._merge_with_map_parent(
            #             parent, parentref, node_comment)
            #     else:
            #         preceding_key: Any = keylist[predex]
            #         Comments._merge_with_preceding_map_peer(
            #             data, node_comment, preceding_key)

        node_comment: Union[
            None, CommentToken, List[CommentToken]
        ] = Comments._get_map_node_comment(data, key)
        node_post_eol_comment = Comments._strip_eol_comment(node_comment)

        # # DEBUG
        # if isinstance(node_comment, list):
        #     print("X1"*40)
        #     for dbg_comment in node_comment:
        #         print(type(dbg_comment.value) if dbg_comment and dbg_comment.value else "type(None)")
        #         dbg_node_comment = dbg_comment.value.replace("\n", "\\n") if dbg_comment and dbg_comment.value else None
        #         print(f"Got LIST comment: {dbg_node_comment}" if dbg_node_comment else "NO COMMENT TO EVALUATE!")
        #     print("X1"*40)
        # else:
        #     print("X2"*40)
        #     print(type(node_comment.value) if node_comment and node_comment.value else "type(None)")
        #     dbg_node_comment = node_comment.value.replace("\n", "\\n") if node_comment and node_comment.value else None
        #     print(f"Got scalar comment: {dbg_node_comment}" if dbg_node_comment else "NO COMMENT TO EVALUATE!")
        #     print("X2"*40)

        # if isinstance(node_post_eol_comment, list):
        #     print("Y1"*40)
        #     for dbg_comment in node_post_eol_comment:
        #         dbg_node_post_eol_comment = dbg_comment.value.replace("\n", "\\n") if dbg_comment and dbg_comment.value else None
        #         print(f"Preserving LIST comment: {dbg_node_post_eol_comment}" if dbg_node_post_eol_comment else "NO POST-EOL COMMENT TO PRESERVE!")
        #     print("Y2"*40)
        # else:
        #     print("Y2"*40)
        #     dbg_node_post_eol_comment = node_post_eol_comment.value.replace("\n", "\\n") if node_post_eol_comment and node_post_eol_comment.value else None
        #     print(f"Preserving scalar comment: {dbg_node_post_eol_comment}" if dbg_node_post_eol_comment else "NO POST-EOL COMMENT TO PRESERVE!")
        #     print("Y2"*40)

        # Next, get a ref to the preceding node's comment, if there is one
        pre_cmt: Tuple[
            Any, Any, int
        ] = Comments._find_preceding_map_node_comment(
            data, key)
        old_pre_comment: Union[None, CommentToken, List[CommentToken]] = None
        if pre_cmt[2] == Comments.IN_CA_COMMENT:
            old_pre_comment = (pre_cmt[0].comment[pre_cmt[1]]
                               if pre_cmt[0] is not None
                               and pre_cmt[1] is not None
                               else None)
        else:
            old_pre_comment = pre_cmt[0].items[pre_cmt[1]]

        # Then, from the preceding comment, remove any comment text that is
        # obviously the preceding comment for the target node.
        new_pre_comment = Comments._strip_next_node_comment(old_pre_comment)

        # Finally, merge the preserved comment with the preceding node's
        # remaining comment.
        merged_comment = Comments._merge_comments(
            node_post_eol_comment, new_pre_comment)
        # if merged_comment is None:
        #     return

        if pre_cmt[2] == Comments.IN_CA_COMMENT:
            # Any pre-existing EOL comment would survive this operation, so
            # whether the new comment must be a list or not depends on
            # pre_cmt[1].
            if pre_cmt[1] in [None, Comments.RYCA_COMMENT_PRE_L]:
                if not isinstance(merged_comment, list):
                    merged_comment = [merged_comment]
            else:
                # Must NOT be a list
                if isinstance(merged_comment, list):
                    merged_comment = "\n" + "\n".join(
                        item.value for item in merged_comment)

            if pre_cmt[1] is None:
                # Must create a new comment property for a CommentedMap which
                # has no leading EOL or "pre" (confusingly-named) comments.  As
                # such, the merged comment must be a list of CommentTokens stored
                # at ca.comment[RYCA_COMMENT_PRE_L], which is assignable via the
                # add_pre_comments method (which is NOT additive).
                print("-=\n"*25)
                print(repr(pre_cmt[0]))
                print("-=\n"*25)
                exit(1)
                pre_cmt[0].add_pre_comments(merged_comment)

                # For ruamel.yaml > 0.17.x, where add_comment_pre replaces
                # add_pre_comments -- writing to RYCA_COMMENT_POST rather than
                # RYCA_COMMENT_PRE_L -- and IS additive, so the list must first be
                # purged.
                # pre_cmt[0].comment[0] = []
                # for comment in merged_comment:
                #     pre_cmt[0].add_comment_pre(comment)
            else:
                pre_cmt[0].comment[pre_cmt[1]] = merged_comment

        else:
            # When pre_cmt[1] is RYCA_COMMENT_PRE_L, RYCA_DICT_PRE_KEY_L, or
            # RYCA_LIST_POST_ITEM_L, merged_comment MUST be a list.
            requires_list = pre_cmt[1] in [
                Comments.RYCA_DICT_PRE_KEY_L,
                Comments.RYCA_LIST_POST_ITEM_L
            ]
            cmt_is_list = isinstance(merged_comment, list)
            if cmt_is_list and not requires_list:
                merged_comment = "\n"*2 + "Kiss my ass!\n" + "\n".join(
                    item.value for item in merged_comment if item is not None)
            elif requires_list and not cmt_is_list:
                merged_comment = [merged_comment]

            # pre_cmt[0].items[pre_cmt[1]] = merged_comment
            pre_cmt[0].end = merged_comment
