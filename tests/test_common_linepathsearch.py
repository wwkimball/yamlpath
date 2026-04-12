import ruamel.yaml as ry

from yamlpath.enums import PathSeparators
from yamlpath.common import LinePathSearch


class Test_common_linepathsearch():
    """Tests for the LinePathSearch helper class."""

    def test_line_is_match_none(self):
        assert LinePathSearch.line_is_match(None, 1) is False

    def test_join_map_key_path_root_dot(self):
        assert LinePathSearch.join_map_key_path(
            "", "key", PathSeparators.DOT
        ) == "key"

    def test_join_sequence_index_path_root(self):
        assert LinePathSearch.join_sequence_index_path(
            "", 1, PathSeparators.FSLASH
        ) == "/[1]"
        assert LinePathSearch.join_sequence_index_path(
            "", 1, PathSeparators.DOT
        ) == "[1]"

    def test_collect_line_paths_set(self):
        yaml = ry.YAML()
        data = yaml.load("""--- !!set
? V
? VI
""")
        paths = LinePathSearch.collect_line_paths(
            data, PathSeparators.DOT, 1
        )
        assert paths == set()

    def test_collect_line_paths_set_with_linecol(self):
        data = ry.comments.CommentedSet(["V", "VI"])
        data.lc.add_kv_line_col("V", [0, 0, 0, 0])
        data.lc.add_kv_line_col("VI", [1, 0, 1, 0])

        paths = LinePathSearch.collect_line_paths(
            data, PathSeparators.DOT, 1
        )

        assert "V" in paths

    def test_path_is_ancestor_false(self):
        assert LinePathSearch.path_is_ancestor(
            "/same", "/same", PathSeparators.FSLASH
        ) is False
        assert LinePathSearch.path_is_ancestor(
            "/one", "/two", PathSeparators.FSLASH
        ) is False

    def test_search_for_paths_by_line(self):
        yaml = ry.YAML()
        data = yaml.load("""---
key: value
""")

        value_line = data.lc.value("key")
        assert value_line is not None

        paths = [
            str(path)
            for path in LinePathSearch.search_for_paths_by_line(
                data, PathSeparators.DOT, value_line[0] + 1
            )
        ]

        assert paths == ["key"]