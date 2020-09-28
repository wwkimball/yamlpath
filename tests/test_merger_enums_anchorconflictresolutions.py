import pytest

from yamlpath.merger.enums.anchorconflictresolutions import (
	AnchorConflictResolutions)


class Test_merger_enum_anchorconflictresolutions():
	"""Tests for the AnchorConflictResolutions enumeration."""

	def test_get_names(self):
		assert AnchorConflictResolutions.get_names() == [
			"STOP",
			"LEFT",
			"RIGHT",
			"RENAME",
		]

	def test_get_choices(self):
		assert AnchorConflictResolutions.get_choices() == [
			"left",
			"rename",
			"right",
			"stop",
		]

	@pytest.mark.parametrize("input,output", [
		("STOP", AnchorConflictResolutions.STOP),
		("LEFT", AnchorConflictResolutions.LEFT),
		("RIGHT", AnchorConflictResolutions.RIGHT),
		("RENAME", AnchorConflictResolutions.RENAME),
	])
	def test_from_str(self, input, output):
		assert output == AnchorConflictResolutions.from_str(input)

	def test_from_str_nameerror(self):
		with pytest.raises(NameError):
			AnchorConflictResolutions.from_str("NO SUCH NAME")
