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

	def test_gt(self):
		lhs_nc = NodeCoords(5, None, None)
		rhs_nc = NodeCoords(3, None, None)
		assert lhs_nc > rhs_nc

	def test_null_gt(self):
		lhs_nc = NodeCoords(5, None, None)
		rhs_nc = NodeCoords(None, None, None)
		assert not lhs_nc > rhs_nc

	def test_lt(self):
		lhs_nc = NodeCoords(5, None, None)
		rhs_nc = NodeCoords(7, None, None)
		assert lhs_nc < rhs_nc

	def test_null_lt(self):
		lhs_nc = NodeCoords(5, None, None)
		rhs_nc = NodeCoords(None, None, None)
		assert not lhs_nc < rhs_nc

	def test_isa_null(self):
		nc = NodeCoords(None, None, None)
		assert nc.wraps_a(None)
