import pytest

from yamlpath.differ.enums.aohdiffopts import AoHDiffOpts


class Test_differ_enums_aohdiffopts():
	"""Tests for the AoHDiffOpts enumeration."""

	def test_get_names(self):
		assert AoHDiffOpts.get_names() == [
			"DEEP",
			"DPOS",
			"KEY",
			"POSITION",
			"VALUE",
		]

	def test_get_choices(self):
		assert AoHDiffOpts.get_choices() == [
			"deep",
			"dpos",
			"key",
			"position",
			"value",
		]

	@pytest.mark.parametrize("input,output", [
		("DEEP", AoHDiffOpts.DEEP),
		("DPOS", AoHDiffOpts.DPOS),
		("KEY", AoHDiffOpts.KEY),
		("POSITION", AoHDiffOpts.POSITION),
		("VALUE", AoHDiffOpts.VALUE),
	])
	def test_from_str(self, input, output):
		assert output == AoHDiffOpts.from_str(input)

	def test_from_str_nameerror(self):
		with pytest.raises(NameError):
			AoHDiffOpts.from_str("NO SUCH NAME")
