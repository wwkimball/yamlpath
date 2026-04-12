"""Implement LinePathSearch, a static helper for line-to-path lookups."""

from typing import Any, Generator, List, Optional, Set

from ruamel.yaml.comments import CommentedMap, CommentedSeq, CommentedSet

from yamlpath import YAMLPath
from yamlpath.enums import PathSeparators


class LinePathSearch:
    """Helper methods for source line number to YAML Path searches."""

    @staticmethod
    def line_is_match(line_data: Any, line_number: int) -> bool:
        """Indicate whether ruamel line metadata matches a requested line."""
        if line_data is None:
            return False

        # ruamel.yaml line data are zero-based; CLI line numbers are one-based.
        return len(line_data) > 0 and line_data[0] == line_number - 1

    @staticmethod
    def join_map_key_path(
        base_path: str, key: Any, pathsep: PathSeparators
    ) -> str:
        """Create a child map/set path for a key from a parent path."""
        path_key = YAMLPath.escape_path_section(key, pathsep)
        join_mark = "/" if pathsep is PathSeparators.FSLASH else "."

        if base_path:
            return "{}{}{}".format(base_path, join_mark, path_key)

        if pathsep is PathSeparators.FSLASH:
            return "/{}".format(path_key)

        return "{}".format(path_key)

    @staticmethod
    def join_sequence_index_path(
        base_path: str, idx: int, pathsep: PathSeparators
    ) -> str:
        """Create a child sequence path for an index from a parent path."""
        if base_path:
            return "{}[{}]".format(base_path, idx)

        if pathsep is PathSeparators.FSLASH:
            return "/[{}]".format(idx)

        return "[{}]".format(idx)

    @staticmethod
    def collect_line_paths(
        data: Any,
        pathsep: PathSeparators,
        line_number: int,
        build_path: str = "",
        matched_paths: Optional[Set[str]] = None,
    ) -> Set[str]:
        """Recursively collect YAML Paths for a source line number."""
        if matched_paths is None:
            matched_paths = set()

        if isinstance(data, CommentedMap):
            for key, val in data.items():
                key_path = LinePathSearch.join_map_key_path(
                    build_path, key, pathsep
                )
                key_line = data.lc.key(key)
                val_line = data.lc.value(key)
                if LinePathSearch.line_is_match(key_line, line_number):
                    matched_paths.add(key_path)
                if LinePathSearch.line_is_match(val_line, line_number):
                    matched_paths.add(key_path)

                LinePathSearch.collect_line_paths(
                    val,
                    pathsep,
                    line_number,
                    build_path=key_path,
                    matched_paths=matched_paths,
                )

        elif isinstance(data, CommentedSeq):
            for idx, ele in enumerate(data):
                ele_path = LinePathSearch.join_sequence_index_path(
                    build_path, idx, pathsep
                )
                ele_line = data.lc.item(idx)
                if LinePathSearch.line_is_match(ele_line, line_number):
                    matched_paths.add(ele_path)

                LinePathSearch.collect_line_paths(
                    ele,
                    pathsep,
                    line_number,
                    build_path=ele_path,
                    matched_paths=matched_paths,
                )

        elif isinstance(data, CommentedSet):
            for key in data:
                key_path = LinePathSearch.join_map_key_path(
                    build_path, key, pathsep
                )
                key_line = data.lc.key(key)
                if LinePathSearch.line_is_match(key_line, line_number):
                    matched_paths.add(key_path)

        return matched_paths

    @staticmethod
    def path_is_ancestor(
        ancestor: str, descendant: str, pathsep: PathSeparators
    ) -> bool:
        """Indicate whether one YAML Path is ancestor of another."""
        if ancestor == descendant or not descendant.startswith(ancestor):
            return False

        boundary = descendant[len(ancestor):len(ancestor) + 1]
        join_mark = "/" if pathsep is PathSeparators.FSLASH else "."
        return boundary in ["[", join_mark]

    @staticmethod
    def prune_to_deepest_paths(
        paths: Set[str], pathsep: PathSeparators
    ) -> List[str]:
        """Remove ancestor paths when deeper descendent paths match."""
        keep_paths: List[str] = []
        for check_path in sorted(paths, key=len, reverse=True):
            is_ancestor = False
            for keep_path in keep_paths:
                if LinePathSearch.path_is_ancestor(
                    check_path, keep_path, pathsep
                ):
                    is_ancestor = True
                    break

            if not is_ancestor:
                keep_paths.append(check_path)

        return sorted(keep_paths)

    @staticmethod
    def search_for_paths_by_line(
        data: Any, pathsep: PathSeparators, line_number: int
    ) -> Generator[YAMLPath, None, None]:
        """Yield YAML Paths whose key/value/index metadata matches a line."""
        raw_paths = LinePathSearch.collect_line_paths(
            data, pathsep, line_number
        )
        paths = LinePathSearch.prune_to_deepest_paths(raw_paths, pathsep)
        for path in paths:
            yield YAMLPath(path)
