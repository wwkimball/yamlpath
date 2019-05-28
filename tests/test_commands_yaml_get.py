import pytest

class Test_yaml_get():
	"""Tests for the yaml-get command-line interface."""
	def test_bad_options(script_runner):
		ret = script_runner.run("yaml-get")
		assert ret.error
		assert -1 < ret.stderr.find("ERROR")
