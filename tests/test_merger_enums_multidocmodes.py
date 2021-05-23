import pytest

from yamlpath.merger.enums.multidocmodes import MultiDocModes


class Test_merger_enums_multidocmodes():
	"""Tests for the MultiDocModes enumeration."""

	def test_get_names(self):
		assert MultiDocModes.get_names() == [
			"CONDENSE_ALL",
			"MERGE_ACROSS",
			"MATRIX_MERGE",
		]

	def test_get_choices(self):
		assert MultiDocModes.get_choices() == [
			"condense_all",
			"matrix_merge",
			"merge_across",
		]

	@pytest.mark.parametrize("input,output", [
		("CONDENSE_ALL", MultiDocModes.CONDENSE_ALL),
		("MERGE_ACROSS", MultiDocModes.MERGE_ACROSS),
		("MATRIX_MERGE", MultiDocModes.MATRIX_MERGE),
	])
	def test_from_str(self, input, output):
		assert output == MultiDocModes.from_str(input)

	def test_from_str_nameerror(self):
		with pytest.raises(NameError):
			MultiDocModes.from_str("NO SUCH NAME")
