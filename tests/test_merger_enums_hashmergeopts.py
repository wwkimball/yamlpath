import pytest

from yamlpath.merger.enums.hashmergeopts import (
	HashMergeOpts)


class Test_merger_enums_hashmergeopts():
	"""Tests for the HashMergeOpts enumeration."""

	def test_get_names(self):
		assert HashMergeOpts.get_names() == [
			"DEEP",
			"LEFT",
			"RIGHT",
		]

	def test_get_choices(self):
		assert HashMergeOpts.get_choices() == [
			"deep",
			"left",
			"right",
		]

	@pytest.mark.parametrize("input,output", [
		("DEEP", HashMergeOpts.DEEP),
		("LEFT", HashMergeOpts.LEFT),
		("RIGHT", HashMergeOpts.RIGHT),
	])
	def test_from_str(self, input, output):
		assert output == HashMergeOpts.from_str(input)

	def test_from_str_nameerror(self):
		with pytest.raises(NameError):
			HashMergeOpts.from_str("NO SUCH NAME")
