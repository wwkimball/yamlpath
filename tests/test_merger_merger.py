import os
import pytest
from types import SimpleNamespace

from yamlpath.func import get_yaml_editor, get_yaml_data
from yamlpath.merger import MergerConfig, Merger
from tests.conftest import quiet_logger, create_temp_yaml_file


class Test_merger_Merger():
    """Tests for the Merger class."""

    ###
    # merge_with
    ###
    def test_merge_with_defaults_simple_hash(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
""")

        output_dir = tmp_path / "test_merge_with_defaults_simple_hash"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        lhs_data = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        rhs_data = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print(output_fnd.read())
        #     print(merged_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )
