import pytest
import io

from yamlpath.common import Parsers
from yamlpath import Processor


class Test_common_comments():
    """Tests for the Comments helper class."""

    @staticmethod
    def compare_yaml(dom_data, expected_str):
        """Dumps a DOM to text and compares against an expected string."""
        buf = io.StringIO()
        yaml = Parsers.get_yaml_editor()
        yaml.dump(dom_data, stream=buf)
        assert buf.getvalue() == expected_str

    def delete_from(self, logger, yaml_str, delete_yamlpath):
        """Deletes at delete_path from yaml_str, returning the result."""
        yaml = Parsers.get_yaml_editor()
        (data, loaded) = Parsers.get_yaml_data(
            yaml, logger, yaml_str,
            literal=True)
        assert loaded == True

        processor = Processor(logger, data)
        deleted_nodes = list(processor.delete_nodes(delete_yamlpath))

        return data

    ###
    # del_map_comment_for_entry
    ###
    def test_simple_delete_hkv_uncommented(self, quiet_logger):
        src = """---
key1: value1
key2: value2
"""
        cmp = """---
key2: value2
"""
        Test_common_comments.compare_yaml(
            self.delete_from(quiet_logger, src, "key1"),
            cmp
        )

    def test_simple_delete_hkv_1_comment(self, quiet_logger):
        src = """---
# Comment on key1
key1: value1
key2: value2
"""
        cmp = """---
key2: value2
"""
        Test_common_comments.compare_yaml(
            self.delete_from(quiet_logger, src, "key1"),
            cmp
        )
