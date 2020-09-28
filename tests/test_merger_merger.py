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
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

        assert (
            (os.path.getsize(output_file) == os.path.getsize(merged_yaml))
            and (open(output_file,'r').read() == open(merged_yaml,'r').read())
        )

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
        lhs_data = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        rhs_data = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

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
        #     print("Expected:")
        #     print(merged_fnd.read())
        #     print("Got:")
        #     print(output_fnd.read())

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
        Array.  This is admittedly an odd case.  It is very likely this is the
        result of user-error, having provided a silly mergeat argument.  But
        because the result is a complete preservation of all data from both the
        LHS and RHS data sources, it is permitted.

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

        output_dir = tmp_path / "test_merge_with_defaults_nonconflict_hash_anchors"
        output_dir.mkdir()
        output_file = output_dir / "output.yaml"

        lhs_yaml = get_yaml_editor()
        rhs_yaml = get_yaml_editor()
        lhs_data = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        rhs_data = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

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
        lhs_data = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        rhs_data = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

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
        lhs_data = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        rhs_data = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

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
        lhs_data = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)
        rhs_data = get_yaml_data(rhs_yaml, quiet_logger, rhs_yaml_file)

        args = SimpleNamespace()
        mc = MergerConfig(quiet_logger, args)
        merger = Merger(quiet_logger, lhs_data, mc)

        with pytest.raises(MergeException) as ex:
            merger.merge_with(rhs_data)
        assert -1 < str(ex.value).find(
            "Impossible to add Array-of-Hash data to non-Array destination")
