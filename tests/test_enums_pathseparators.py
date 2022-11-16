import pytest

from yamlpath.enums import PathSeparators

# Legacy spelling compatibility:
from yamlpath.enums import PathSeperators


class Test_enums_PathSeparators():
	"""Tests for the PathSeparators enumeration."""
	@pytest.mark.parametrize("pathsep_module", [PathSeparators, PathSeperators])
	def test_get_names(self, pathsep_module):
		assert pathsep_module.get_names() == [
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
	@pytest.mark.parametrize("pathsep_module", [PathSeparators, PathSeperators])
	def test_from_str(self, input, output, pathsep_module):
		assert output == pathsep_module.from_str(input)

	@pytest.mark.parametrize("pathsep_module", [PathSeparators, PathSeperators])
	def test_from_str_nameerror(self, pathsep_module):
		with pytest.raises(NameError):
			pathsep_module.from_str("NO SUCH NAME")

	@pytest.mark.parametrize("input,output", [
		("abc", PathSeparators.DOT),
		("abc.123", PathSeparators.DOT),
		("/abc", PathSeparators.FSLASH),
		("/abc/123", PathSeparators.FSLASH),
	])
	@pytest.mark.parametrize("pathsep_module", [PathSeparators, PathSeperators])
	@pytest.mark.parametrize("func_name", ["infer_separator", "infer_seperator"])
	def test_infer_separator(self, input, output, pathsep_module, func_name):
		assert output == getattr(pathsep_module, func_name)(input)
