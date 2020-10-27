import pytest

from yamlpath.differ.enums.arraydiffopts import ArrayDiffOpts


class Test_differ_enums_arraydiffopts():
	"""Tests for the ArrayDiffOpts enumeration."""

	def test_get_names(self):
		assert ArrayDiffOpts.get_names() == [
			"POSITION",
			"VALUE",
		]

	def test_get_choices(self):
		assert ArrayDiffOpts.get_choices() == [
			"position",
			"value",
		]

	@pytest.mark.parametrize("input,output", [
		("POSITION", ArrayDiffOpts.POSITION),
		("VALUE", ArrayDiffOpts.VALUE),
	])
	def test_from_str(self, input, output):
		assert output == ArrayDiffOpts.from_str(input)

	def test_from_str_nameerror(self):
		with pytest.raises(NameError):
			ArrayDiffOpts.from_str("NO SUCH NAME")
