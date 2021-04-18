import pytest

from yamlpath.enums import PathSearchKeywords
from yamlpath.path import SearchKeywordTerms

class Test_path_SearchKeywordTerms():
    """Tests for the SearchKeywordTerms class."""

    @pytest.mark.parametrize("invert,keyword,parameters,output", [
        (True, PathSearchKeywords.HAS_CHILD, "abc", "[!has_child(abc)]"),
        (False, PathSearchKeywords.HAS_CHILD, "abc", "[has_child(abc)]"),
        (False, PathSearchKeywords.HAS_CHILD, "abc\\,def", "[has_child(abc\\,def)]"),
        (False, PathSearchKeywords.HAS_CHILD, "abc, def", "[has_child(abc, def)]"),
        (False, PathSearchKeywords.HAS_CHILD, "abc,' def'", "[has_child(abc,' def')]"),
    ])
    def test_str(self, invert, keyword, parameters, output):
        assert output == str(SearchKeywordTerms(invert, keyword, parameters))

    @pytest.mark.parametrize("parameters,output", [
        ("abc", ["abc"]),
        ("abc\\,def", ["abc,def"]),
        ("abc, def", ["abc", "def"]),
        ("abc,' def'", ["abc", " def"]),
        ("1,'1', 1, '1', 1 , ' 1', '1 ', ' 1 '", ["1", "1", "1", "1", "1", " 1", "1 ", " 1 "]),
        ("true, False,'True','false'", ["true", "False", "True", "false"]),
        ("'',,\"\", '', ,,\"\\'\",'\\\"'", ["", "", "", "", "", "", "'", "\""]),
        ("'And then, she said, \"Quote!\"'", ["And then, she said, \"Quote!\""]),
        (None, []),
    ])
    def test_parameter_parsing(self, parameters, output):
        skt = SearchKeywordTerms(False, PathSearchKeywords.HAS_CHILD, parameters)
        assert output == skt.parameters

    @pytest.mark.parametrize("parameters", [
        ("','a'"),
        ("a,\"b,"),
    ])
    def test_unmatched_demarcation(self, parameters):
        skt = SearchKeywordTerms(False, PathSearchKeywords.HAS_CHILD, parameters)
        with pytest.raises(ValueError) as ex:
            parmlist = skt.parameters
        assert -1 < str(ex.value).find("one or more unmatched demarcation symbol")
