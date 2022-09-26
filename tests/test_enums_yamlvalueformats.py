import pytest
from datetime import datetime, date

from ruamel.yaml.scalarstring import (
    PlainScalarString,
    DoubleQuotedScalarString,
    SingleQuotedScalarString,
    FoldedScalarString,
    LiteralScalarString,
)
from ruamel.yaml.scalarbool import ScalarBoolean
from ruamel.yaml.scalarfloat import ScalarFloat
from ruamel.yaml.scalarint import ScalarInt
from ruamel.yaml import version_info as ryversion
if ryversion < (0, 17, 22):                   # pragma: no cover
    from yamlpath.patches.timestamp import (
        AnchoredTimeStamp,
    )  # type: ignore
else:
    # Temporarily fool MYPY into resolving the future-case imports
    from ruamel.yaml.timestamp import TimeStamp as AnchoredTimeStamp
    #from ruamel.yaml.timestamp import AnchoredTimeStamp

from yamlpath.enums import YAMLValueFormats


class Test_enums_YAMLValueFormats():
	"""Tests for the YAMLValueFormats enumeration."""
	def test_get_names(self):
		assert YAMLValueFormats.get_names() == [
			"BARE",
			"BOOLEAN",
			"DATE",
			"DEFAULT",
			"DQUOTE",
			"FLOAT",
			"FOLDED",
			"INT",
			"LITERAL",
			"SQUOTE",
			"TIMESTAMP",
		]

	@pytest.mark.parametrize("input,output", [
		("BARE", YAMLValueFormats.BARE),
		("BOOLEAN", YAMLValueFormats.BOOLEAN),
		("DATE", YAMLValueFormats.DATE),
		("DEFAULT", YAMLValueFormats.DEFAULT),
		("DQUOTE", YAMLValueFormats.DQUOTE),
		("FLOAT", YAMLValueFormats.FLOAT),
		("FOLDED", YAMLValueFormats.FOLDED),
		("INT", YAMLValueFormats.INT),
		("LITERAL", YAMLValueFormats.LITERAL),
		("SQUOTE", YAMLValueFormats.SQUOTE),
		("TIMESTAMP", YAMLValueFormats.TIMESTAMP),
	])
	def test_from_str(self, input, output):
		assert output == YAMLValueFormats.from_str(input)

	def test_from_str_nameerror(self):
		with pytest.raises(NameError):
			YAMLValueFormats.from_str("NO SUCH NAME")

	@pytest.mark.parametrize("input,output", [
		(FoldedScalarString(""), YAMLValueFormats.FOLDED),
		(LiteralScalarString(""), YAMLValueFormats.LITERAL),
		(date(2022, 9, 24), YAMLValueFormats.DATE),
		(DoubleQuotedScalarString(''), YAMLValueFormats.DQUOTE),
		(SingleQuotedScalarString(""), YAMLValueFormats.SQUOTE),
		(PlainScalarString(""), YAMLValueFormats.BARE),
		(ScalarBoolean(False), YAMLValueFormats.BOOLEAN),
		(ScalarFloat(1.01), YAMLValueFormats.FLOAT),
		(ScalarInt(10), YAMLValueFormats.INT),
		(AnchoredTimeStamp(2022, 9, 24, 7, 42, 38), YAMLValueFormats.TIMESTAMP),
		(None, YAMLValueFormats.DEFAULT),
	])
	def test_from_node(self, input, output):
		assert output == YAMLValueFormats.from_node(input)
