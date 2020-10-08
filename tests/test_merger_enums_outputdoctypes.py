import pytest

from yamlpath.merger.enums.outputdoctypes import (
	OutputDocTypes)


class Test_merger_enums_outputdoctypes():
	"""Tests for the OutputDocTypes enumeration."""

	def test_get_names(self):
		assert OutputDocTypes.get_names() == [
			"AUTO",
			"JSON",
			"YAML",
		]

	def test_get_choices(self):
		assert OutputDocTypes.get_choices() == [
			"auto",
			"json",
			"yaml",
		]

	@pytest.mark.parametrize("input,output", [
		("AUTO", OutputDocTypes.AUTO),
		("JSON", OutputDocTypes.JSON),
		("YAML", OutputDocTypes.YAML),
	])
	def test_from_str(self, input, output):
		assert output == OutputDocTypes.from_str(input)

	def test_from_str_nameerror(self):
		with pytest.raises(NameError):
			OutputDocTypes.from_str("NO SUCH NAME")
