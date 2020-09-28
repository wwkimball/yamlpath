import pytest

from yamlpath.merger.enums.arraymergeopts import (
	ArrayMergeOpts)


class Test_merger_enums_arraymergeopts():
	"""Tests for the ArrayMergeOpts enumeration."""

	def test_get_names(self):
		assert ArrayMergeOpts.get_names() == [
			"ALL",
			"LEFT",
			"RIGHT",
			"UNIQUE",
		]

	def test_get_choices(self):
		assert ArrayMergeOpts.get_choices() == [
			"all",
			"left",
			"right",
			"unique",
		]

	@pytest.mark.parametrize("input,output", [
		("ALL", ArrayMergeOpts.ALL),
		("LEFT", ArrayMergeOpts.LEFT),
		("RIGHT", ArrayMergeOpts.RIGHT),
		("UNIQUE", ArrayMergeOpts.UNIQUE),
	])
	def test_from_str(self, input, output):
		assert output == ArrayMergeOpts.from_str(input)

	def test_from_str_nameerror(self):
		with pytest.raises(NameError):
			ArrayMergeOpts.from_str("NO SUCH NAME")
