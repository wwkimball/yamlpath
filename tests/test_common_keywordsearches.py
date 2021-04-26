import pytest

import ruamel.yaml as ry

from yamlpath.enums import PathSearchKeywords
from yamlpath.path import SearchKeywordTerms
from yamlpath.common import KeywordSearches
from yamlpath.exceptions import YAMLPathException
from yamlpath import YAMLPath

class Test_common_keywordsearches():
    """Tests for the KeywordSearches helper class."""

    ###
    # search_matches
    ###
    def test_unknown_search_keyword(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.search_matches(
                SearchKeywordTerms(False, None, ""),
                {},
                YAMLPath("/")
            ))
        assert -1 < str(ex.value).find("Unsupported search keyword")


    ###
    # has_child
    ###
    def test_has_child_invalid_param_count(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.search_matches(
                SearchKeywordTerms(False, PathSearchKeywords.HAS_CHILD, []),
                {},
                YAMLPath("/")
            ))
        assert -1 < str(ex.value).find("Invalid parameter count to ")

    def test_has_child_invalid_node(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.has_child(
                "abc: xyz",
                False,
                ["wwk"],
                YAMLPath("")
            ))
        assert -1 < str(ex.value).find("has no child nodes")


    ###
    # name
    ###
    def test_name_invalid_param_count(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.name(
                False,
                ["1", "2"],
                YAMLPath("/")
            ))
        assert -1 < str(ex.value).find("Invalid parameter count to ")

    def test_name_invalid_inversion(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.name(
                True,
                [],
                YAMLPath("/")
            ))
        assert -1 < str(ex.value).find("Inversion is meaningless to ")


    ###
    # max
    ###
    def test_max_invalid_param_count(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.max(
                {},
                False,
                ["1", "2"],
                YAMLPath("/")
            ))
        assert -1 < str(ex.value).find("Invalid parameter count to ")

    def test_max_missing_aoh_param(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.max(
                [{'a': 1},{'a': 2}],
                False,
                [],
                YAMLPath("/")
            ))
        assert -1 < str(ex.value).find("when evaluating an Array-of-Hashes")

    def test_max_missing_hash_param(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.max(
                {'a': {'b': 1}, 'c': {'d': 2}},
                False,
                [],
                YAMLPath("/")
            ))
        assert -1 < str(ex.value).find("when comparing Hash/map/dict children")

    def test_max_invalid_array_param(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.max(
                [1, 2, 3],
                False,
                ['3'],
                YAMLPath("/")
            ))
        assert -1 < str(ex.value).find("when comparing Array/sequence/list elements to one another")

    def test_max_incorrect_node(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.max(
                {'b': 2},
                False,
                ['b'],
                YAMLPath("/*[max(b)]")
            ))
        assert -1 < str(ex.value).find("operates against collections of data")


    ###
    # min
    ###
    def test_min_invalid_param_count(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.min(
                {},
                False,
                ["1", "2"],
                YAMLPath("/")
            ))
        assert -1 < str(ex.value).find("Invalid parameter count to ")

    def test_min_missing_aoh_param(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.min(
                [{'a': 1},{'a': 2}],
                False,
                [],
                YAMLPath("/")
            ))
        assert -1 < str(ex.value).find("when evaluating an Array-of-Hashes")

    def test_min_missing_hash_param(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.min(
                {'a': {'b': 1}, 'c': {'d': 2}},
                False,
                [],
                YAMLPath("/")
            ))
        assert -1 < str(ex.value).find("when comparing Hash/map/dict children")

    def test_min_invalid_array_param(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.min(
                [1, 2, 3],
                False,
                ['3'],
                YAMLPath("/")
            ))
        assert -1 < str(ex.value).find("when comparing Array/sequence/list elements to one another")

    def test_min_incorrect_node(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.min(
                {'b': 2},
                False,
                ['b'],
                YAMLPath("/*[max(b)]")
            ))
        assert -1 < str(ex.value).find("operates against collections of data")


    ###
    # parent
    ###
    def test_parent_invalid_param_count(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.parent(
                {},
                False,
                ["1", "2"],
                YAMLPath("/")
            ))
        assert -1 < str(ex.value).find("Invalid parameter count to ")

    def test_parent_invalid_inversion(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.parent(
                {},
                True,
                [],
                YAMLPath("/")
            ))
        assert -1 < str(ex.value).find("Inversion is meaningless to ")

    def test_parent_invalid_parameter(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.parent(
                {},
                False,
                ["abc"],
                YAMLPath("/")
            ))
        assert -1 < str(ex.value).find("Invalid parameter passed to ")

    def test_parent_invalid_step_count(self):
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(KeywordSearches.parent(
                {},
                False,
                ["5"],
                YAMLPath("/")
            ))
        assert -1 < str(ex.value).find("higher than the document root")
