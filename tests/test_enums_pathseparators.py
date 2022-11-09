import pytest

from yamlpath.enums import PathSeparators


class Test_enums_PathSeparators():
	"""Tests for the PathSeparators enumeration."""
	def test_get_names(self):
		assert PathSeparators.get_names() == [
			"AUTO",
			"DOT",
			"FSLASH",
		]

	@pytest.mark.parametrize("input,output", [
		(PathSeparators.AUTO, '.'),
		(PathSeparators.DOT, '.'),
		(PathSeparators.FSLASH, '/'),
	])
	def test_str(self, input, output):
		assert output == str(input)

	@pytest.mark.parametrize("input,output", [
		(".", PathSeparators.DOT),
		("/", PathSeparators.FSLASH),
		("DOT", PathSeparators.DOT),
		("FSLASH", PathSeparators.FSLASH),
		(PathSeparators.DOT, PathSeparators.DOT),
		(PathSeparators.FSLASH, PathSeparators.FSLASH),
	])
	def test_from_str(self, input, output):
		assert output == PathSeparators.from_str(input)

	def test_from_str_nameerror(self):
		with pytest.raises(NameError):
			PathSeparators.from_str("NO SUCH NAME")

	@pytest.mark.parametrize("input,output", [
		("abc", PathSeparators.DOT),
		("abc.123", PathSeparators.DOT),
		("/abc", PathSeparators.FSLASH),
		("/abc/123", PathSeparators.FSLASH),
	])
	def test_infer_separator(self, input, output):
		assert output == PathSeparators.infer_separator(input)
