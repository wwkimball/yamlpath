import pytest

from yamlpath.merger.exceptions import MergeException


class Test_exceptions_mergeexception():
	def test_str_pathless(self):
		message = "Test message"
		with pytest.raises(MergeException) as ex:
			raise MergeException(message)
		assert str(ex.value) == message

	def test_str_pathfull(self):
		message = "Test message"
		path = "/test"
		with pytest.raises(MergeException) as ex:
			raise MergeException(message, path)
		assert (str(ex.value) == "{}  This issue occurred at YAML Path:  {}"
			.format(message, path))
