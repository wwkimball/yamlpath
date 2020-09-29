import pytest

from yamlpath.merger.enums.aohmergeopts import (
	AoHMergeOpts)


class Test_merger_enums_aohmergeopts():
	"""Tests for the AoHMergeOpts enumeration."""

	def test_get_names(self):
		assert AoHMergeOpts.get_names() == [
			"ALL",
			"DEEP",
			"LEFT",
			"RIGHT",
			"UNIQUE",
		]

	def test_get_choices(self):
		assert AoHMergeOpts.get_choices() == [
			"all",
			"deep",
			"left",
			"right",
			"unique",
		]

	@pytest.mark.parametrize("input,output", [
		("ALL", AoHMergeOpts.ALL),
		("DEEP", AoHMergeOpts.DEEP),
		("LEFT", AoHMergeOpts.LEFT),
		("RIGHT", AoHMergeOpts.RIGHT),
		("UNIQUE", AoHMergeOpts.UNIQUE),
	])
	def test_from_str(self, input, output):
		assert output == AoHMergeOpts.from_str(input)

	def test_from_str_nameerror(self):
		with pytest.raises(NameError):
			AoHMergeOpts.from_str("NO SUCH NAME")
