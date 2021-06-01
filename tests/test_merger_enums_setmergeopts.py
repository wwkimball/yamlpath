import pytest

from yamlpath.merger.enums.setmergeopts import SetMergeOpts


class Test_merger_enums_setmergeopts():
	"""Tests for the SetMergeOpts enumeration."""

	def test_get_names(self):
		assert SetMergeOpts.get_names() == [
			"LEFT",
			"RIGHT",
			"UNIQUE",
		]

	def test_get_choices(self):
		assert SetMergeOpts.get_choices() == [
			"left",
			"right",
			"unique",
		]

	@pytest.mark.parametrize("input,output", [
		("LEFT", SetMergeOpts.LEFT),
		("RIGHT", SetMergeOpts.RIGHT),
		("UNIQUE", SetMergeOpts.UNIQUE),
	])
	def test_from_str(self, input, output):
		assert output == SetMergeOpts.from_str(input)

	def test_from_str_nameerror(self):
		with pytest.raises(NameError):
			SetMergeOpts.from_str("NO SUCH NAME")
