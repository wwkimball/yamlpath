import os
import pytest
from types import SimpleNamespace

from yamlpath.func import get_yaml_editor, get_yaml_data
from yamlpath.merger.exceptions import MergeException
from yamlpath.merger import MergerConfig, Merger
from tests.conftest import quiet_logger, create_temp_yaml_file


class Test_merger_Merger():
    """Tests for the Merger class."""

    ###
    # merge_with
    ###
    def test_merge_empty_lhs(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
key: value
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
key: value
""")

        output_dir = tmp_path / "test_merge_empty_lhs"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_empty_rhs(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
key: value
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
key: value
""")

        output_dir = tmp_path / "test_merge_empty_rhs"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

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
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_left_simple_hash(
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
  merge_target: LHS original value
""")

        output_dir = tmp_path / "test_merge_left_simple_hash"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(hashes="left")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_right_simple_hash(
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
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
""")

        output_dir = tmp_path / "test_merge_right_simple_hash"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(hashes="right")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_deep_hash(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  merge_target: LHS original value
  deep:
    lhs_key:
      - lhs1
      - lhs2
    common_key:
      - common1
      - common2
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
  deep:
    rhs_key:
      - rhs1
      - rhs2
    common_key:
      - common2
      - common3
  extra: content
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
hash:
  lhs_exclusive: LHS exclusive
  rhs_exclusive: RHS exclusive
  merge_target: RHS override value
  deep:
    lhs_key:
      - lhs1
      - lhs2
    rhs_key:
      - rhs1
      - rhs2
    common_key:
      - common1
      - common2
      - common2
      - common3
  extra: content
""")

        output_dir = tmp_path / "test_merge_deep_hash"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(hashes="deep")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_with_defaults_array_of_floats(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
- 1.1
- 2.2
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
- 2.2
- 3.3
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
  - 1.1
  - 2.2
  - 2.2
  - 3.3
""")

        output_dir = tmp_path / "test_merge_with_defaults_simple_array"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )


    def test_merge_with_defaults_simple_array(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array:
  - one
  - two
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array:
  - two
  - three
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
array:
  - one
  - two
  - two
  - three
""")

        output_dir = tmp_path / "test_merge_with_defaults_simple_array"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_with_defaults_simple_array_no_lhs(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
  - 1
  - 2
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
  - 1
  - 2
""")

        output_dir = tmp_path / "test_merge_with_defaults_simple_array_no_lhs"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_with_defaults_simple_array_empty_rhs(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array: [1, 2]
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array: []
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
array: [1, 2]
""")

        output_dir = tmp_path / "test_merge_with_defaults_simple_array_no_rhs"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_left_simple_array(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array:
  - one
  - two
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array:
  - two
  - three
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
array:
  - one
  - two
""")

        output_dir = tmp_path / "test_merge_left_simple_array"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(arrays="left")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_right_simple_array(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array:
  - one
  - two
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array:
  - two
  - three
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
array:
  - two
  - three
""")

        output_dir = tmp_path / "test_merge_right_simple_array"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(arrays="right")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
            print("Expected:")
            print(merged_fnd.read())
            print("Got:")
            print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_unique_simple_array(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array:
  - one
  - two
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array:
  - two
  - three
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
array:
  - one
  - two
  - three
""")

        output_dir = tmp_path / "test_merge_unique_simple_array"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(arrays="unique")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_with_defaults_simple_aoh(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - identity_key: 1
    name: LHS AoH One
    side: left
    lhs: true
  - identity_key: 2
    name: LHS AoH Two
    side: left
    lhs: true
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - identity_key: 2
    name: RHS AoH One
    side: right
    rhs: true
  - identity_key: 3
    name: RHS AoH Two
    side: right
    rhs: true
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - identity_key: 1
    name: LHS AoH One
    side: left
    lhs: true
  - identity_key: 2
    name: LHS AoH Two
    side: left
    lhs: true
  - identity_key: 2
    name: RHS AoH One
    side: right
    rhs: true
  - identity_key: 3
    name: RHS AoH Two
    side: right
    rhs: true
""")

        output_dir = tmp_path / "test_merge_with_defaults_simple_aoh"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_with_defaults_bare_aoh(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
  - step: 1
    action: LHS blah
  - step: 2
    action: more LHS blah
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
  - step: 2
    action: RHS blah
  - step: 3
    action: more RHS blah
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
  - step: 1
    action: LHS blah
  - step: 2
    action: RHS blah
  - step: 3
    action: more RHS blah
""")

        output_dir = tmp_path / "test_merge_with_defaults_bare_array"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(aoh="deep")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_left_simple_aoh(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - identity_key: 1
    name: LHS AoH One
    side: left
    lhs: true
  - identity_key: 2
    name: LHS AoH Two
    side: left
    lhs: true
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - identity_key: 2
    name: RHS AoH One
    side: right
    rhs: true
  - identity_key: 3
    name: RHS AoH Two
    side: right
    rhs: true
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - identity_key: 1
    name: LHS AoH One
    side: left
    lhs: true
  - identity_key: 2
    name: LHS AoH Two
    side: left
    lhs: true
""")

        output_dir = tmp_path / "test_merge_left_simple_aoh"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(aoh="left")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_right_simple_aoh(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - identity_key: 1
    name: LHS AoH One
    side: left
    lhs: true
  - identity_key: 2
    name: LHS AoH Two
    side: left
    lhs: true
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - identity_key: 2
    name: RHS AoH One
    side: right
    rhs: true
  - identity_key: 3
    name: RHS AoH Two
    side: right
    rhs: true
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - identity_key: 2
    name: RHS AoH One
    side: right
    rhs: true
  - identity_key: 3
    name: RHS AoH Two
    side: right
    rhs: true
""")

        output_dir = tmp_path / "test_merge_right_simple_aoh"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(aoh="right")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_unique_simple_aoh(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - x: 4
    y: 2
  - x: 1
    y: 1
  - x: 0
    y: 0
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - x: 0
    y: 0
  - x: 1
    y: -1
  - x: 4
    y: -2
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - x: 4
    y: 2
  - x: 1
    y: 1
  - x: 0
    y: 0
  - x: 1
    y: -1
  - x: 4
    y: -2
""")

        output_dir = tmp_path / "test_merge_unique_simple_aoh"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(aoh="unique")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_deep_aoh(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - identity_key: 1
    name: LHS AoH One
    side: left
    lhs: true
  - identity_key: 2
    name: LHS AoH Two
    side: left
    lhs: true
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - identity_key: 2
    name: RHS AoH One
    side: right
    rhs: true
  - identity_key: 3
    name: RHS AoH Two
    side: right
    rhs: true
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - identity_key: 1
    name: LHS AoH One
    side: left
    lhs: true
  - identity_key: 2
    name: RHS AoH One
    side: right
    lhs: true
    rhs: true
  - identity_key: 3
    name: RHS AoH Two
    side: right
    rhs: true
""")

        output_dir = tmp_path / "test_merge_deep_aoh"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(aoh="deep")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_deep_aoh_inferred_rhs_key(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - 0
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - identity_key: 2
    name: RHS AoH One
    side: right
    rhs: true
  - identity_key: 3
    name: RHS AoH Two
    side: right
    rhs: true
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - 0
  - identity_key: 2
    name: RHS AoH One
    side: right
    rhs: true
  - identity_key: 3
    name: RHS AoH Two
    side: right
    rhs: true
""")

        output_dir = tmp_path / "test_merge_deep_aoh_inferred_rhs_key"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(aoh="deep")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_missing_aoh_key(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - identity_key: 1
    name: LHS AoH One
    side: left
    lhs: true
  - identity_key: 2
    name: LHS AoH Two
    side: left
    lhs: true
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array_of_hashes:
  - identity_key: 2
    name: RHS AoH One
    side: right
    rhs: true
  - name: RHS AoH Two
    side: right
    rhs: true
""")

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(aoh="deep")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)

        with pytest.raises(MergeException) as ex:
            merger.merge_with(rhs_data)
        assert -1 < str(ex.value).find(
            "Mandatory identity key, identity_key, not present")

    def test_merge_with_defaults_nonconflict_scalar_anchors(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &lhs_exclusive LHS Exclusive Value
  - &shared_anchor Shared Value
lhs_key: *lhs_exclusive
merge_key: *shared_anchor
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &rhs_exclusive RHS Exclusive Value
  - &shared_anchor Shared Value
rhs_key: *rhs_exclusive
merge_key: *shared_anchor
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &lhs_exclusive LHS Exclusive Value
  - &shared_anchor Shared Value
  - &rhs_exclusive RHS Exclusive Value
  - *shared_anchor
lhs_key: *lhs_exclusive
rhs_key: *rhs_exclusive
merge_key: *shared_anchor
""")

        output_dir = tmp_path / "test_merge_with_defaults_nonconflict_scalar_anchors"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_with_defaults_conflict_scalar_anchors(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &shared_anchor Shared Value?
merge_key: *shared_anchor
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &shared_anchor NOT Shared Value!
merge_key: *shared_anchor
""")

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)

        with pytest.raises(MergeException) as ex:
            merger.merge_with(rhs_data)
        assert -1 < str(ex.value).find(
            "Aborting due to anchor conflict")

    def test_merge_with_defaults_nonconflict_hash_anchors(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
hash: &defaults
  name: Default Name
  value: Default Value
records:
  - id: 0
    <<: *defaults
    name: LHS Name
  - id: 1
    <<: *defaults
    value: LSH Value
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
hash: &defaults
  name: Default Name
  value: Default Value
records:
  - id: 1
    <<: *defaults
    name: RHS Name
  - id: 2
    <<: *defaults
    value: RSH Value
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
hash: &defaults
  name: Default Name
  value: Default Value
records:
  - id: 0
    <<: *defaults
    name: LHS Name
  - id: 1
    <<: *defaults
    value: LSH Value
  - id: 1
    <<: *defaults
    name: RHS Name
  - id: 2
    <<: *defaults
    value: RSH Value
""")

        output_dir = tmp_path / "test_merge_with_defaults_nonconflict_hash_anchors"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_anchors_left(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &shared_anchor LHS Value
merge_key: *shared_anchor
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &shared_anchor RHS Value
merge_key: *shared_anchor
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &shared_anchor LHS Value
  - *shared_anchor
merge_key: *shared_anchor
""")

        output_dir = tmp_path / "test_merge_anchors_left"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(anchors="left")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_anchors_right(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &shared_anchor LHS Value
merge_key: *shared_anchor
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &shared_anchor RHS Value
merge_key: *shared_anchor
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &shared_anchor RHS Value
  - *shared_anchor
merge_key: *shared_anchor
""")

        output_dir = tmp_path / "test_merge_anchors_right"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(anchors="right")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_anchors_rename(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &shared_anchor LHS Value
lhs_key: *shared_anchor
merge_key: *shared_anchor
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &shared_anchor RHS Value
rhs_key: *shared_anchor
merge_key: *shared_anchor
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &shared_anchor LHS Value
  - &shared_anchor_1 RHS Value
lhs_key: *shared_anchor
rhs_key: *shared_anchor_1
merge_key: *shared_anchor_1
""")

        output_dir = tmp_path / "test_merge_anchors_rename"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(anchors="rename")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
            print("Expected:")
            print(merged_fnd.read())
            print("Got:")
            print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_with_defaults_hash_appends_to_array(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        """
        While it is impossible to overwrite an Array with a Hash because that
        would be a total loss of data, it is possible to append a Hash to an
        Array (this is different from merging into an Array-of-Hashes, which is
        normal and allowed).  This is admittedly an odd case.  It is very
        likely this is the result of user-error, having provided a silly
        mergeat argument.  But because the result is a complete preservation of
        all data from both the LHS and RHS data sources, it is permitted.

        A deliberately odd mergeat is provided to force this case.
        """
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
merge_into:
  - is
  - an
  - "Array (i.e.:  list)"
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
merge_from:
  is: a
  hash: "i.e.:  map"
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
merge_into:
  - is
  - an
  - "Array (i.e.:  list)"
  - merge_from:
      is: a
      hash: "i.e.:  map"
""")

        output_dir = tmp_path / "test_merge_with_defaults_hash_appends_to_array"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(mergeat="/merge_into")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_with_defaults_hash_cannot_overwrite_nonhash(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
merge:
  - is
  - an
  - Array (i.e.:  list)
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
merge:
  is: a
  hash: "i.e.:  map"
""")

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)

        with pytest.raises(MergeException) as ex:
            merger.merge_with(rhs_data)
        assert -1 < str(ex.value).find(
            "Impossible to add Hash data to non-Hash destination")

    def test_merge_with_defaults_array_to_nonarray(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
merge:
  is: a
  hash: "i.e.:  map"
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
merge:
  - is
  - an
  - Array (i.e.:  list)
""")

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)

        with pytest.raises(MergeException) as ex:
            merger.merge_with(rhs_data)
        assert -1 < str(ex.value).find(
            "Impossible to add Array data to non-Array destination")

    def test_merge_with_defaults_aoh_to_nonarray(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
merge:
  is: a
  hash: "i.e.:  map"
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
merge:
  - identity: key1
    prop: val1
  - identity: key2
    prop: val2
""")

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)

        with pytest.raises(MergeException) as ex:
            merger.merge_with(rhs_data)
        assert -1 < str(ex.value).find(
            "Impossible to add Array-of-Hash data to non-Array destination")

    def test_merge_scalar_to_array(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array:
  - one
  - two
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, "three")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
array:
  - one
  - two
  - three
""")

        output_dir = tmp_path / "test_merge_scalar_to_array"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(mergeat="/array")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_scalar_to_leaf_node(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  subkey: original
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, "replacement")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
hash:
  subkey: replacement
""")

        output_dir = tmp_path / "test_merge_scalar_to_leaf_node"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(mergeat="/hash/subkey")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_scalar_to_hash_without_key(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
key: value
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, "replacement")

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)

        with pytest.raises(MergeException) as ex:
            merger.merge_with(rhs_data)
        assert -1 < str(ex.value).find(
            "Impossible to add Scalar value,")

    def test_merge_with_bad_mergeat(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
key: value
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
subkey: another value
""")

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(mergeat="/key[.=nonexistent]")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)

        with pytest.raises(MergeException) as ex:
            merger.merge_with(rhs_data)
        assert -1 < str(ex.value).find(
            "merge was not performed")

    def test_merge_flow_style(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
array: [1, 2]
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, "[{key: val}]")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
array: [1, 2, key: val]
""")

        output_dir = tmp_path / "test_merge_flow_style"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(mergeat="/array")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
            print("Expected:")
            print(merged_fnd.read())
            print("Got:")
            print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_combines_anchored_hashes(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
lhs_hash: &lhs_hash_anchor
  lhs: LHS value
merged_hash:
  <<: *lhs_hash_anchor
  more_lhs: values
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
rhs_hash: &rhs_hash_anchor
  rhs: RHS value
merged_hash:
  <<: *rhs_hash_anchor
  even_more_rhs: values
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
lhs_hash: &lhs_hash_anchor
  lhs: LHS value
rhs_hash: &rhs_hash_anchor
  rhs: RHS value
merged_hash:
  <<: [*lhs_hash_anchor, *rhs_hash_anchor]
  more_lhs: values
  even_more_rhs: values
""")

        output_dir = tmp_path / "test_merge_combines_anchored_hashes"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_rename_anchored_scalar_hash_key(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &key_name LHS Key Name
*key_name :
  subkey: LHS value
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &key_name RHS Key Name
*key_name :
  subkey: RHS value
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &key_name LHS Key Name
  - &key_name_1 RHS Key Name
*key_name :
  subkey: LHS value
*key_name_1 :
  subkey: RHS value
""")

        output_dir = tmp_path / "test_merge_rename_anchored_scalar_hash_key"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(anchors="rename")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_left_anchored_scalar_hash_key(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &key_name LHS Key Name
*key_name :
  subkey: LHS value
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &key_name RHS Key Name
*key_name :
  subkey: RHS value
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
aliases:
  - &key_name LHS Key Name
  - *key_name
*key_name :
  subkey: RHS value
""")

        output_dir = tmp_path / "test_merge_left_anchored_scalar_hash_key"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(anchors="left")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_rename_anchored_complex_hash_key(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
anchorKeys:
  &keyOne lhsAliasOne: 1 1 Alpha 1
  &keyTwo lhsAliasTwo: 2 2 Beta 2
hash:
  *keyOne :
    subval: lhs 1.1
  *keyTwo :
    subval: lhs 2.2
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
anchorKeys:
  &keyOne rhsAliasOne: 1 1 Alpha 1
  &keyTwo rhsAliasTwo: 2 2 Beta 2
hash:
  *keyOne :
    subval: rhs 1.1
  *keyTwo :
    subval: rhs 2.2
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
anchorKeys:
  &keyOne lhsAliasOne: 1 1 Alpha 1
  &keyTwo lhsAliasTwo: 2 2 Beta 2
  &keyOne_1 rhsAliasOne: 1 1 Alpha 1
  &keyTwo_1 rhsAliasTwo: 2 2 Beta 2
hash:
  *keyOne :
    subval: lhs 1.1
  *keyTwo :
    subval: lhs 2.2
  *keyOne_1 :
    subval: rhs 1.1
  *keyTwo_1 :
    subval: rhs 2.2
""")

        output_dir = tmp_path / "test_merge_rename_anchored_complex_hash_key"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(anchors="rename")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_rename_anchored_hash_value(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
lhs_template: &default
  name: LHS
  prop: LHS value
records:
  - <<: *default
    name: LHS Test
  - <<: *default
    prop: LHS Something
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
rhs_template: &default
  name: RHS
  prop: RHS value
records:
  - <<: *default
    name: RHS Test
  - <<: *default
    prop: RHS Something
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
lhs_template: &default
  name: LHS
  prop: LHS value
rhs_template: &default_1
  name: RHS
  prop: RHS value
records:
  - <<: *default
    name: LHS Test
  - <<: *default
    prop: LHS Something
  - <<: *default_1
    name: RHS Test
  - <<: *default_1
    prop: RHS Something
""")

        output_dir = tmp_path / "test_merge_rename_anchored_hash_value"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(anchors="rename")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_hash_with_mergeat_default(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  key: value
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
more_hash:
  key: more value
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
hash:
  key: value
implicit:
  structure:
    to:
      more_hash:
        key: more value
""")

        output_dir = tmp_path / "test_merge_hash_with_mergeat_default"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(mergeat="/implicit/structure/to")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
            print("Expected:")
            print(merged_fnd.read())
            print("Got:")
            print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_hash_with_mergeat_left(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  key: value
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
more_hash:
  key: more value
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
hash:
  key: value
implicit:
  structure:
    to:
      more_hash:
        key: more value
""")

        output_dir = tmp_path / "test_merge_hash_with_mergeat_left"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(hashes="left", mergeat="/implicit/structure/to")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
            print("Expected:")
            print(merged_fnd.read())
            print("Got:")
            print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_hash_with_mergeat_right(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  key: value
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
more_hash:
  key: more value
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
hash:
  key: value
implicit:
  structure:
    to:
      more_hash:
        key: more value
""")

        output_dir = tmp_path / "test_merge_hash_with_mergeat_right"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(hashes="right", mergeat="/implicit/structure/to")
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
            print("Expected:")
            print(merged_fnd.read())
            print("Got:")
            print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

    def test_merge_with_complex_hash_rules(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
[defaults]
hashes = deep

[rules]
/hash/structure/with/several = left
/hash/even = right
/hash/blah = left
/hash/fu = left
/hash/la = right
/hash/ri/fa = left
/force_left = left
/force_right = right
""")
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  structure:
    with:
      several: LHS (several)
      keep: LHS (keep)
    and:
      data: LHS (data)
  even: LHS (even)
  blah:
    tee: LHS (tee)
  fu:
    ru: LHS (ru)
    tu: LHS (tu)
  la:
    ta: LHS (ta)
    da: LHS (da)
  ri:
    me:
      do: LHS (do)
      po: LHS (po)
    fa:
      so: LHS (so)
lhs_exclusive:
  key: LHS (key)
force_left: true
force_right: false
""")
        rhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
hash:
  structure:
    with:
      several: RHS (several)
      having: RHS (having)
      keep: RHS (keep)
  fu:
    do: RHS (do)
    re: RHS (re)
  more: RHS (more)
  even: RHS (even)
  la:
    bi: RHS (bi)
    ti: RHS (ti)
  blah:
    ree: RHS (ree)
  ri:
    fa:
      re: RHS (re)
      be: RHS (be)
rhs_exclusive:
  another_key: RHS (another_key)
force_left: false
force_right: true
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
hash:
  structure:
    with:
      several: LHS (several)
      having: RHS (having)
      keep: RHS (keep)
    and:
      data: LHS (data)
  even: RHS (even)
  more: RHS (more)
  blah:
    tee: LHS (tee)
  fu:
    ru: LHS (ru)
    tu: LHS (tu)
  la:
    bi: RHS (bi)
    ti: RHS (ti)
  ri:
    me:
      do: LHS (do)
      po: LHS (po)
    fa:
      so: LHS (so)
lhs_exclusive:
  key: LHS (key)
rhs_exclusive:
  another_key: RHS (another_key)
force_left: true
force_right: true
""")

        output_dir = tmp_path / "test_merge_with_complex_hash_rules"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs_data, rhs_loaded) = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace(config=config_file)
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )


    def test_merge_with_complex_aoh_rules(
        self, quiet_logger, tmp_path, tmp_path_factory
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
[rules]
baubles = deep
/coordinates = unique

[keys]
/baubles[name = Whatchamacallit] = sku
""")
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
baubles:
  - name: Doohickey
    sku: 0-000-1
    price: 4.75
    weight: 2.7g
  - name: Doodad
    sku: 0-000-2
    price: 10.5
    weight: 5g
  - name: Oddball
    sku: 0-000-3
    price: 25.99
    weight: 25kg
coordinates:
  - x: 4
    y: -2
  - x: 1
    y: -1
  - x: 0
    y: 0
lhs_exclusive:
  - step: 1
    action: echo Hello, lefties of the World!
  - step: 2
    action: exit 0
""")
        rhs1_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
baubles:
  - name: Fob
    sku: 0-000-4
    price: 0.99
    weight: 18mg
  - name: Doohickey
    price: 10.5
  - name: Oddball
    sku: 0-000-3
    description: This ball is odd
coordinates:
  - x: 0
    y: 0
  - x: 1
    y: 1
  - x: 4
    y: 2
rhs_exclusive:
  - step: 1
    action: echo Hello, righties of the World!
  - step: 2
    action: exit 0
""")
        rhs2_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
baubles:
  - name: Whatchamacallit
    sku: 0-000-1
""")
        merged_yaml = create_temp_yaml_file(tmp_path_factory, """---
baubles:
  - name: Whatchamacallit
    sku: 0-000-1
    price: 10.5
    weight: 2.7g
  - name: Doodad
    sku: 0-000-2
    price: 10.5
    weight: 5g
  - name: Oddball
    sku: 0-000-3
    price: 25.99
    weight: 25kg
    description: This ball is odd
  - name: Fob
    sku: 0-000-4
    price: 0.99
    weight: 18mg
coordinates:
  - x: 4
    y: -2
  - x: 1
    y: -1
  - x: 0
    y: 0
  - x: 1
    y: 1
  - x: 4
    y: 2
lhs_exclusive:
  - step: 1
    action: echo Hello, lefties of the World!
  - step: 2
    action: exit 0
rhs_exclusive:
  - step: 1
    action: echo Hello, righties of the World!
  - step: 2
    action: exit 0
""")

        output_dir = tmp_path / "test_merge_with_complex_aoh_rules"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs1_yaml = get_yaml_editor()
        rhs2_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        (rhs1_data, rhs1_loaded) = get_yaml_data(rhs1_yaml, quiet_logger, rhs1_yaml_file)
        (rhs2_data, rhs2_loaded) = get_yaml_data(rhs2_yaml, quiet_logger, rhs2_yaml_file)

        args = SimpleNamespace(config=config_file)
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)
        merger.merge_with(rhs1_data)
        merger.merge_with(rhs2_data)

        with open(output_file, 'w') as yaml_dump:
            lhs_yaml.dump(merger.data, yaml_dump)

        # DEBUG:
        # with open(output_file, 'r') as output_fnd, open(merged_yaml, 'r') as merged_fnd:
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )


    ###
    # set_flow_style
    ###
    def test_deprecated_set_flow_style(self):
        Merger.depwarn_printed = False
        Merger.set_flow_style("", False)


    ###
    # delete_all_comments
    ###
    def test_deprecated_delete_all_comments(self):
        Merger.depwarn_printed = False
        Merger.delete_all_comments(None)

    
    ###
    # combine_merge_anchors
    ###
    def test_deprecated_combine_merge_anchors(self):
        import ruamel.yaml as ry
        lhs = ry.comments.CommentedMap({})
        rhs = ry.comments.CommentedMap({})
        Merger.depwarn_printed = False
        Merger.combine_merge_anchors(lhs, rhs)


    ###
    # rename_anchor
    ###
    def test_deprecated_rename_anchor(self):
        Merger.depwarn_printed = False
        Merger.rename_anchor(None, "", "")


    ###
    # replace_anchor
    ###
    def test_deprecated_replace_anchor(self):
        import ruamel.yaml as ry
        old_node = ry.scalarstring.PlainScalarString("")
        repl_node = ry.scalarstring.PlainScalarString("")
        Merger.depwarn_printed = False
        Merger.replace_anchor(None, old_node, repl_node)


    ###
    # scan_for_anchors
    ###
    def test_deprecated_scan_for_anchors(self):
        Merger.depwarn_printed = False
        Merger.scan_for_anchors(None, {})
