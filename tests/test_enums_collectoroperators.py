import pytest

from yamlpath.enums import CollectorOperators


class Test_enums_CollectorOperators():
	"""Tests for the CollectorOperators enumeration."""
	def test_get_names(self):
		assert CollectorOperators.get_names() == [
			"ADDITION",
			"NONE",
			"SUBTRACTION",
			"INTERSECTION",
		]

	@pytest.mark.parametrize("input,output", [
		(CollectorOperators.ADDITION, "+"),
		(CollectorOperators.NONE, ""),
		(CollectorOperators.SUBTRACTION, "-"),
		(CollectorOperators.INTERSECTION, "&"),
	])
	def test_str(self, input, output):
		assert output == str(input)

	@pytest.mark.parametrize("input,output", [
		("+", CollectorOperators.ADDITION),
		("-", CollectorOperators.SUBTRACTION),
		("&", CollectorOperators.INTERSECTION),
		("ADDITION", CollectorOperators.ADDITION),
		("NONE", CollectorOperators.NONE),
		("SUBTRACTION", CollectorOperators.SUBTRACTION),
		("INTERSECTION", CollectorOperators.INTERSECTION),
		(CollectorOperators.ADDITION, CollectorOperators.ADDITION),
		(CollectorOperators.SUBTRACTION, CollectorOperators.SUBTRACTION),
		(CollectorOperators.INTERSECTION, CollectorOperators.INTERSECTION),
		(CollectorOperators.NONE, CollectorOperators.NONE),
	])
	def test_from_operator(self, input, output):
		assert output == CollectorOperators.from_operator(input)

	def test_from_operator_nameerror(self):
		with pytest.raises(NameError):
			CollectorOperators.from_operator("NO SUCH NAME")
