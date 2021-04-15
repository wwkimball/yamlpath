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
		(False, PathSearchKeywords.HAS_CHILD, "abc,' def'", "[has_child(abc,\\ def)]"),
	])
	def test_str(self, invert, keyword, parameters, output):
		assert output == str(SearchKeywordTerms(invert, keyword, parameters))
