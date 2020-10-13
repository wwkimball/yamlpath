import pytest

from yamlpath.wrappers import NodeCoords

class Test_wrappers_NodeCoords():
	"""Tests for the NodeCoords class."""

	def test_generic(self):
		node_coord = NodeCoords([], None, None)

	def test_repr(self):
		node_coord = NodeCoords([], None, None)
		assert repr(node_coord) == "NodeCoords('[]', 'None', 'None')"

	def test_str(self):
		node_coord = NodeCoords([], None, None)
		assert str(node_coord) == "[]"
