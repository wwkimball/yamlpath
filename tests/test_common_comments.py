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

    def test_simple_delete_hkv_1_buffered_comment(self, quiet_logger):
        src = """---
# Unrelated comment buffered by an empty line

# Comment on key1
key1: value1
key2: value2
"""
        cmp = """---
# Unrelated comment buffered by an empty line

key2: value2
"""
        Test_common_comments.compare_yaml(
            self.delete_from(quiet_logger, src, "key1"),
            cmp
        )

    def test_simple_delete_hkv_2_comment(self, quiet_logger):
        src = """---
# Comment on key1
key1: value1
key2: value2
"""
        cmp = """---
# Comment on key1
key1: value1
"""
        Test_common_comments.compare_yaml(
            self.delete_from(quiet_logger, src, "key2"),
            cmp
        )

    def test_simple_delete_hkv_1_comment_eols(self, quiet_logger):
        src = """---
# Comment on key1
key1: value1  # With an EOL comment 1
key2: value2  # With an EOL comment 2
"""
        cmp = """---
key2: value2  # With an EOL comment 2
"""
        Test_common_comments.compare_yaml(
            self.delete_from(quiet_logger, src, "key1"),
            cmp
        )

    def test_simple_delete_hkv_1_buffered_comment_eols(self, quiet_logger):
        src = """---
# Unrelated comment buffered by an empty line

# Comment on key1
key1: value1  # With an EOL comment 1
key2: value2  # With an EOL comment 2
"""
        cmp = """---
# Unrelated comment buffered by an empty line

key2: value2  # With an EOL comment 2
"""
        Test_common_comments.compare_yaml(
            self.delete_from(quiet_logger, src, "key1"),
            cmp
        )

    def test_simple_delete_hkv_2_comment_eols(self, quiet_logger):
        src = """---
# Comment on key1
key1: value1  # With an EOL comment 1
key2: value2  # With an EOL comment 2
"""
        cmp = """---
# Comment on key1
key1: value1  # With an EOL comment 1
"""
        Test_common_comments.compare_yaml(
            self.delete_from(quiet_logger, src, "key2"),
            cmp
        )

    def test_simple_delete_hkv_uncommented_spaced(self, quiet_logger):
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

    def test_simple_delete_hkv_1_comment_spaced(self, quiet_logger):
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

    def test_simple_delete_hkv_1_buffered_comment_spaced(self, quiet_logger):
        src = """---
# Unrelated comment buffered by an empty line

# Comment on key1
key1: value1

key2: value2
"""
        cmp = """---
# Unrelated comment buffered by an empty line

key2: value2
"""
        Test_common_comments.compare_yaml(
            self.delete_from(quiet_logger, src, "key1"),
            cmp
        )

    def test_simple_delete_hkv_2_comment_spaced(self, quiet_logger):
        src = """---
# Comment on key1
key1: value1

key2: value2
"""
        cmp = """---
# Comment on key1
key1: value1
"""
        Test_common_comments.compare_yaml(
            self.delete_from(quiet_logger, src, "key2"),
            cmp
        )

    def test_simple_delete_hkv_1_comment_eols_spaced(self, quiet_logger):
        src = """---
# Comment on key1
key1: value1  # With an EOL comment 1

key2: value2  # With an EOL comment 2
"""
        cmp = """---

key2: value2  # With an EOL comment 2
"""
        Test_common_comments.compare_yaml(
            self.delete_from(quiet_logger, src, "key1"),
            cmp
        )

    def test_simple_delete_hkv_1_buffered_comment_eols_spaced(self, quiet_logger):
        src = """---
# Unrelated comment buffered by an empty line

# Comment on key1
key1: value1  # With an EOL comment 1

key2: value2  # With an EOL comment 2
"""
        cmp = """---
# Unrelated comment buffered by an empty line

key2: value2  # With an EOL comment 2
"""
        Test_common_comments.compare_yaml(
            self.delete_from(quiet_logger, src, "key1"),
            cmp
        )

    def test_simple_delete_hkv_2_comment_eols_spaced(self, quiet_logger):
        src = """---
# Comment on key1
key1: value1  # With an EOL comment 1

key2: value2  # With an EOL comment 2
"""
        cmp = """---
# Comment on key1
key1: value1  # With an EOL comment 1
"""
        Test_common_comments.compare_yaml(
            self.delete_from(quiet_logger, src, "key2"),
            cmp
        )

    def test_nested_delete_parent1_uncommented(self, quiet_logger):
        src = """---
parent1:
  p1k1: value1
  p1k2: value2
parent2:
  p2k1: value3
  p2k2: value4
"""
        cmp = """---
parent2:
  p2k1: value3
  p2k2: value4
"""
        Test_common_comments.compare_yaml(
            self.delete_from(quiet_logger, src, "parent1"),
            cmp
        )

    def test_nested_delete_parent2_uncommented(self, quiet_logger):
        src = """---
parent1:
  p1k1: value1
  p1k2: value2
parent2:
  p2k1: value3
  p2k2: value4
"""
        cmp = """---
parent1:
  p1k1: value1
  p1k2: value2
"""
        Test_common_comments.compare_yaml(
            self.delete_from(quiet_logger, src, "parent2"),
            cmp
        )

    def test_nested_delete_parent1_spaced(self, quiet_logger):
        src = """---
parent1:
  p1k1: value1
  p1k2: value2

parent2:
  p2k1: value3
  p2k2: value4
"""
        cmp = """---
parent2:
  p2k1: value3
  p2k2: value4
"""
        Test_common_comments.compare_yaml(
            self.delete_from(quiet_logger, src, "parent1"),
            cmp
        )

    def test_nested_delete_parent2_spaced(self, quiet_logger):
        src = """---
parent1:
  p1k1: value1
  p1k2: value2

parent2:
  p2k1: value3
  p2k2: value4
"""
        cmp = """---

parent2:
  p2k1: value3
  p2k2: value4
"""
        Test_common_comments.compare_yaml(
            self.delete_from(quiet_logger, src, "parent1"),
            cmp
        )
