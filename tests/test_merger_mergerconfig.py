import pytest
from types import SimpleNamespace

from yamlpath.func import get_yaml_editor, get_yaml_data
from yamlpath.merger.enums import (
    AnchorConflictResolutions,
    AoHMergeOpts,
    ArrayMergeOpts,
    HashMergeOpts,
    MultiDocModes,
    OutputDocTypes,
    SetMergeOpts,
)
from yamlpath.wrappers import NodeCoords
from yamlpath.merger import MergerConfig
from yamlpath import YAMLPath
from tests.conftest import (
    info_warn_logger,
    quiet_logger,
    create_temp_yaml_file
)


class Test_merger_MergerConfig():
    """Tests for the MergerConfig class."""

    ###
    # get_insertion_point
    ###
    def test_get_insertion_point_default(self, quiet_logger):
        mc = MergerConfig(quiet_logger, SimpleNamespace())
        assert mc.get_insertion_point() == YAMLPath("/")

    def test_get_insertion_point_cli(self, quiet_logger):
        mc = MergerConfig(quiet_logger, SimpleNamespace(mergeat="la.tee.dah"))
        assert mc.get_insertion_point() == YAMLPath("/la/tee/dah")


    ###
    # get_document_format
    ###
    def test_get_document_format(self, quiet_logger):
        mc = MergerConfig(quiet_logger, SimpleNamespace())
        assert mc.get_document_format() == OutputDocTypes.AUTO


    ###
    # get_multidoc_mode
    ###
    def test_get_multidoc_mode_default(self, quiet_logger):
        mc = MergerConfig(quiet_logger, SimpleNamespace())
        assert mc.get_multidoc_mode() == MultiDocModes.CONDENSE_ALL

    def test_get_multidoc_mode_cli(self, quiet_logger):
        mc = MergerConfig(quiet_logger, SimpleNamespace(multi_doc_mode="matrix_merge"))
        assert mc.get_multidoc_mode() == MultiDocModes.MATRIX_MERGE


    ###
    # anchor_merge_mode
    ###
    def test_anchor_merge_mode_default(self, quiet_logger):
        mc = MergerConfig(quiet_logger, SimpleNamespace(anchors=None))
        assert mc.anchor_merge_mode() == AnchorConflictResolutions.STOP

    @pytest.mark.parametrize("setting, mode", [
        ("left", AnchorConflictResolutions.LEFT),
        ("rename", AnchorConflictResolutions.RENAME),
        ("right", AnchorConflictResolutions.RIGHT),
        ("stop", AnchorConflictResolutions.STOP),
    ])
    def test_anchor_merge_mode_cli(self, quiet_logger, setting, mode):
        mc = MergerConfig(quiet_logger, SimpleNamespace(anchors=setting))
        assert mc.anchor_merge_mode() == mode

    @pytest.mark.parametrize("setting, mode", [
        ("left", AnchorConflictResolutions.LEFT),
        ("rename", AnchorConflictResolutions.RENAME),
        ("right", AnchorConflictResolutions.RIGHT),
        ("stop", AnchorConflictResolutions.STOP),
    ])
    def test_anchor_merge_mode_ini(
        self, quiet_logger, tmp_path_factory, setting, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        anchors = {}
        """.format(setting))
        mc = MergerConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , anchors=None))
        assert mc.anchor_merge_mode() == mode

    @pytest.mark.parametrize("cli, ini, mode", [
        ("left", "stop", AnchorConflictResolutions.LEFT),
        ("rename", "stop", AnchorConflictResolutions.RENAME),
        ("right", "stop", AnchorConflictResolutions.RIGHT),
        ("stop", "rename", AnchorConflictResolutions.STOP),
    ])
    def test_anchor_merge_mode_cli_overrides_ini(
        self, quiet_logger, tmp_path_factory, cli, ini, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        anchors = {}
        """.format(ini))
        mc = MergerConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , anchors=cli))
        assert mc.anchor_merge_mode() == mode

    ###
    # hash_merge_mode
    ###
    def test_hash_merge_mode_default(self, quiet_logger):
        mc = MergerConfig(quiet_logger, SimpleNamespace(hashes=None))
        assert mc.hash_merge_mode(
            NodeCoords(None, None, None)) == HashMergeOpts.DEEP

    @pytest.mark.parametrize("setting, mode", [
        ("deep", HashMergeOpts.DEEP),
        ("left", HashMergeOpts.LEFT),
        ("right", HashMergeOpts.RIGHT),
    ])
    def test_hash_merge_mode_cli(self, quiet_logger, setting, mode):
        mc = MergerConfig(quiet_logger, SimpleNamespace(hashes=setting))
        assert mc.hash_merge_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("setting, mode", [
        ("deep", HashMergeOpts.DEEP),
        ("left", HashMergeOpts.LEFT),
        ("right", HashMergeOpts.RIGHT),
    ])
    def test_hash_merge_mode_ini(
        self, quiet_logger, tmp_path_factory, setting, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        hashes = {}
        """.format(setting))
        mc = MergerConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , hashes=None))
        assert mc.hash_merge_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("cli, ini, mode", [
        ("deep", "left", HashMergeOpts.DEEP),
        ("left", "right", HashMergeOpts.LEFT),
        ("right", "deep", HashMergeOpts.RIGHT),
    ])
    def test_hash_merge_mode_cli_overrides_ini_defaults(
        self, quiet_logger, tmp_path_factory, cli, ini, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        hashes = {}
        """.format(ini))
        mc = MergerConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , hashes=cli))
        assert mc.hash_merge_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("cli, ini_default, ini_rule, mode", [
        ("deep", "left", "right", HashMergeOpts.RIGHT),
        ("left", "right", "deep", HashMergeOpts.DEEP),
        ("right", "deep", "left", HashMergeOpts.LEFT),
    ])
    def test_hash_merge_mode_ini_rule_overrides_cli(
        self, quiet_logger, tmp_path_factory, cli, ini_default, ini_rule, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        hashes = {}
        [rules]
        /hash = {}
        """.format(ini_default, ini_rule))
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
        hash:
          lhs_exclusive: lhs value 1
          merge_targets:
            subkey: lhs value 2
            subarray:
              - one
              - two
        array_of_hashes:
          - name: LHS Record 1
            id: 1
            prop: LHS value AoH 1
          - name: LHS Record 2
            id: 2
            prop: LHS value AoH 2
        """)
        lhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)

        mc = MergerConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , hashes=cli))
        mc.prepare(lhs_data)

        node = lhs_data["hash"]
        parent = lhs_data
        parentref = "hash"

        assert mc.hash_merge_mode(
            NodeCoords(node, parent, parentref)) == mode

    @pytest.mark.parametrize("ini_rule, override_rule, mode", [
        ("left", "right", HashMergeOpts.RIGHT),
        ("right", "deep", HashMergeOpts.DEEP),
        ("deep", "left", HashMergeOpts.LEFT),
    ])
    def test_hash_merge_mode_override_rule_overrides_ini_rule(
        self, quiet_logger, tmp_path_factory, ini_rule, override_rule, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [rules]
        /hash = {}
        """.format(ini_rule))
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
        hash:
          lhs_exclusive: lhs value 1
          merge_targets:
            subkey: lhs value 2
            subarray:
              - one
              - two
        array_of_hashes:
          - name: LHS Record 1
            id: 1
            prop: LHS value AoH 1
          - name: LHS Record 2
            id: 2
            prop: LHS value AoH 2
        """)
        lhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)

        mc = MergerConfig(quiet_logger, SimpleNamespace(config=config_file), rules={"/hash": override_rule})
        mc.prepare(lhs_data)

        node = lhs_data["hash"]
        parent = lhs_data
        parentref = "hash"

        assert mc.hash_merge_mode(
            NodeCoords(node, parent, parentref)) == mode

    ###
    # array_merge_mode
    ###
    def test_array_merge_mode_default(self, quiet_logger):
        mc = MergerConfig(quiet_logger, SimpleNamespace(arrays=None))
        assert mc.array_merge_mode(
            NodeCoords(None, None, None)) == ArrayMergeOpts.ALL

    @pytest.mark.parametrize("setting, mode", [
        ("all", ArrayMergeOpts.ALL),
        ("left", ArrayMergeOpts.LEFT),
        ("right", ArrayMergeOpts.RIGHT),
        ("unique", ArrayMergeOpts.UNIQUE),
    ])
    def test_array_merge_mode_cli(self, quiet_logger, setting, mode):
        mc = MergerConfig(quiet_logger, SimpleNamespace(arrays=setting))
        assert mc.array_merge_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("setting, mode", [
        ("all", ArrayMergeOpts.ALL),
        ("left", ArrayMergeOpts.LEFT),
        ("right", ArrayMergeOpts.RIGHT),
        ("unique", ArrayMergeOpts.UNIQUE),
    ])
    def test_array_merge_mode_ini(
        self, quiet_logger, tmp_path_factory, setting, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        arrays = {}
        """.format(setting))
        mc = MergerConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , arrays=None))
        assert mc.array_merge_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("cli, ini, mode", [
        ("all", "left", ArrayMergeOpts.ALL),
        ("left", "right", ArrayMergeOpts.LEFT),
        ("right", "unique", ArrayMergeOpts.RIGHT),
        ("unique", "all", ArrayMergeOpts.UNIQUE),
    ])
    def test_array_merge_mode_cli_overrides_ini_defaults(
        self, quiet_logger, tmp_path_factory, cli, ini, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        arrays = {}
        """.format(ini))
        mc = MergerConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , arrays=cli))
        assert mc.array_merge_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("cli, ini_default, ini_rule, mode", [
        ("all", "left", "right", ArrayMergeOpts.RIGHT),
        ("left", "right", "unique", ArrayMergeOpts.UNIQUE),
        ("right", "unique", "all", ArrayMergeOpts.ALL),
        ("unique", "all", "left", ArrayMergeOpts.LEFT),
    ])
    def test_array_merge_mode_ini_rule_overrides_cli(
        self, quiet_logger, tmp_path_factory, cli, ini_default, ini_rule, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        arrays = {}
        [rules]
        /hash/merge_targets/subarray = {}
        """.format(ini_default, ini_rule))
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
        hash:
          lhs_exclusive: lhs value 1
          merge_targets:
            subkey: lhs value 2
            subarray:
              - one
              - two
        array_of_hashes:
          - name: LHS Record 1
            id: 1
            prop: LHS value AoH 1
          - name: LHS Record 2
            id: 2
            prop: LHS value AoH 2
        """)
        lhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)

        mc = MergerConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , arrays=cli))
        mc.prepare(lhs_data)

        node = lhs_data["hash"]["merge_targets"]["subarray"]
        parent = lhs_data["hash"]["merge_targets"]
        parentref = "subarray"

        assert mc.array_merge_mode(
            NodeCoords(node, parent, parentref)) == mode

    @pytest.mark.parametrize("ini_rule, override_rule, mode", [
        ("left", "right", ArrayMergeOpts.RIGHT),
        ("right", "unique", ArrayMergeOpts.UNIQUE),
        ("unique", "all", ArrayMergeOpts.ALL),
        ("all", "left", ArrayMergeOpts.LEFT),
    ])
    def test_array_merge_mode_override_rule_overrides_ini_rule(
        self, quiet_logger, tmp_path_factory, ini_rule, override_rule, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [rules]
        /hash/merge_targets/subarray = {}
        """.format(ini_rule))
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
        hash:
          lhs_exclusive: lhs value 1
          merge_targets:
            subkey: lhs value 2
            subarray:
              - one
              - two
        array_of_hashes:
          - name: LHS Record 1
            id: 1
            prop: LHS value AoH 1
          - name: LHS Record 2
            id: 2
            prop: LHS value AoH 2
        """)
        lhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)

        mc = MergerConfig(
            quiet_logger,
            SimpleNamespace(config=config_file),
            rules={"/hash/merge_targets/subarray": override_rule}
        )
        mc.prepare(lhs_data)

        node = lhs_data["hash"]["merge_targets"]["subarray"]
        parent = lhs_data["hash"]["merge_targets"]
        parentref = "subarray"

        assert mc.array_merge_mode(
            NodeCoords(node, parent, parentref)) == mode

    ###
    # aoh_merge_mode
    ###
    def test_aoh_merge_mode_default(self, quiet_logger):
        mc = MergerConfig(quiet_logger, SimpleNamespace(aoh=None))
        assert mc.aoh_merge_mode(
            NodeCoords(None, None, None)) == AoHMergeOpts.ALL

    @pytest.mark.parametrize("setting, mode", [
        ("all", AoHMergeOpts.ALL),
        ("deep", AoHMergeOpts.DEEP),
        ("left", AoHMergeOpts.LEFT),
        ("right", AoHMergeOpts.RIGHT),
        ("unique", AoHMergeOpts.UNIQUE),
    ])
    def test_aoh_merge_mode_cli(self, quiet_logger, setting, mode):
        mc = MergerConfig(quiet_logger, SimpleNamespace(aoh=setting))
        assert mc.aoh_merge_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("setting, mode", [
        ("all", AoHMergeOpts.ALL),
        ("deep", AoHMergeOpts.DEEP),
        ("left", AoHMergeOpts.LEFT),
        ("right", AoHMergeOpts.RIGHT),
        ("unique", AoHMergeOpts.UNIQUE),
    ])
    def test_aoh_merge_mode_ini(
        self, quiet_logger, tmp_path_factory, setting, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        aoh = {}
        """.format(setting))
        mc = MergerConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , aoh=None))
        assert mc.aoh_merge_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("cli, ini, mode", [
        ("all", "deep", AoHMergeOpts.ALL),
        ("deep", "left", AoHMergeOpts.DEEP),
        ("left", "right", AoHMergeOpts.LEFT),
        ("right", "unique", AoHMergeOpts.RIGHT),
        ("unique", "all", AoHMergeOpts.UNIQUE),
    ])
    def test_aoh_merge_mode_cli_overrides_ini_defaults(
        self, quiet_logger, tmp_path_factory, cli, ini, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        aoh = {}
        """.format(ini))
        mc = MergerConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , aoh=cli))
        assert mc.aoh_merge_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("cli, ini_default, ini_rule, mode", [
        ("all", "deep", "left", AoHMergeOpts.LEFT),
        ("deep", "left", "right", AoHMergeOpts.RIGHT),
        ("left", "right", "unique", AoHMergeOpts.UNIQUE),
        ("right", "unique", "all", AoHMergeOpts.ALL),
        ("unique", "all", "deep", AoHMergeOpts.DEEP),
    ])
    def test_aoh_merge_mode_ini_rule_overrides_cli(
        self, quiet_logger, tmp_path_factory, cli, ini_default, ini_rule, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        aoh = {}
        [rules]
        /array_of_hashes = {}
        """.format(ini_default, ini_rule))
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
        hash:
          lhs_exclusive: lhs value 1
          merge_targets:
            subkey: lhs value 2
            subarray:
              - one
              - two
        array_of_hashes:
          - name: LHS Record 1
            id: 1
            prop: LHS value AoH 1
          - name: LHS Record 2
            id: 2
            prop: LHS value AoH 2
        """)
        lhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)

        mc = MergerConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , aoh=cli))
        mc.prepare(lhs_data)

        node = lhs_data["array_of_hashes"]
        parent = lhs_data
        parentref = "array_of_hashes"

        assert mc.aoh_merge_mode(
            NodeCoords(node, parent, parentref)) == mode

    @pytest.mark.parametrize("ini_rule, override_rule, mode", [
        ("deep", "left", AoHMergeOpts.LEFT),
        ("left", "right", AoHMergeOpts.RIGHT),
        ("right", "unique", AoHMergeOpts.UNIQUE),
        ("unique", "all", AoHMergeOpts.ALL),
        ("all", "deep", AoHMergeOpts.DEEP),
    ])
    def test_array_merge_mode_override_rule_overrides_ini_rule(
        self, quiet_logger, tmp_path_factory, ini_rule, override_rule, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [rules]
        /array_of_hashes = {}
        """.format(ini_rule))
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
        hash:
          lhs_exclusive: lhs value 1
          merge_targets:
            subkey: lhs value 2
            subarray:
              - one
              - two
        array_of_hashes:
          - name: LHS Record 1
            id: 1
            prop: LHS value AoH 1
          - name: LHS Record 2
            id: 2
            prop: LHS value AoH 2
        """)
        lhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)

        mc = MergerConfig(
            quiet_logger,
            SimpleNamespace(config=config_file),
            rules={"/array_of_hashes": override_rule}
        )
        mc.prepare(lhs_data)

        node = lhs_data["array_of_hashes"]
        parent = lhs_data
        parentref = "array_of_hashes"

        assert mc.aoh_merge_mode(
            NodeCoords(node, parent, parentref)) == mode

    ###
    # aoh_merge_key
    ###
    def test_aoh_merge_key_default(self, quiet_logger, tmp_path_factory):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
        hash:
          lhs_exclusive: lhs value 1
          merge_targets:
            subkey: lhs value 2
            subarray:
              - one
              - two
        array_of_hashes:
          - name: LHS Record 1
            id: 1
            prop: LHS value AoH 1
          - name: LHS Record 2
            id: 2
            prop: LHS value AoH 2
        """)
        lhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)

        mc = MergerConfig(quiet_logger, SimpleNamespace())
        mc.prepare(lhs_data)

        node = lhs_data["array_of_hashes"]
        parent = lhs_data
        parentref = "array_of_hashes"
        record = node[0]

        assert mc.aoh_merge_key(
            NodeCoords(node, parent, parentref), record) == "name"

    def test_aoh_merge_key_ini(self, quiet_logger, tmp_path_factory):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [keys]
        /array_of_hashes = id
        """)
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
        hash:
          lhs_exclusive: lhs value 1
          merge_targets:
            subkey: lhs value 2
            subarray:
              - one
              - two
        array_of_hashes:
          - name: LHS Record 1
            id: 1
            prop: LHS value AoH 1
          - name: LHS Record 2
            id: 2
            prop: LHS value AoH 2
        """)
        lhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)

        mc = MergerConfig(quiet_logger, SimpleNamespace(config=config_file))
        mc.prepare(lhs_data)

        node = lhs_data["array_of_hashes"]
        parent = lhs_data
        parentref = "array_of_hashes"
        record = node[0]

        assert mc.aoh_merge_key(
            NodeCoords(node, parent, parentref), record) == "id"

    def test_aoh_merge_key_ini_inferred_parent(
        self, quiet_logger, tmp_path_factory
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [keys]
        /array_of_hashes = prop
        """)
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
        hash:
          lhs_exclusive: lhs value 1
          merge_targets:
            subkey: lhs value 2
            subarray:
              - one
              - two
        array_of_hashes:
          - name: LHS Record 1
            id: 1
            prop: LHS value AoH 1
          - name: LHS Record 2
            id: 2
            prop: LHS value AoH 2
        """)
        lhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)

        mc = MergerConfig(quiet_logger, SimpleNamespace(config=config_file))
        mc.prepare(lhs_data)

        node = lhs_data["array_of_hashes"][1]
        parent = lhs_data["array_of_hashes"]
        parentref = 1
        record = node

        assert mc.aoh_merge_key(
            NodeCoords(node, parent, parentref), record) == "prop"

    def test_aoh_merge_key_override_rule_overrides_ini(self, quiet_logger, tmp_path_factory):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [keys]
        /array_of_hashes = name
        """)
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
        hash:
          lhs_exclusive: lhs value 1
          merge_targets:
            subkey: lhs value 2
            subarray:
              - one
              - two
        array_of_hashes:
          - name: LHS Record 1
            id: 1
            prop: LHS value AoH 1
          - name: LHS Record 2
            id: 2
            prop: LHS value AoH 2
        """)
        lhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)

        mc = MergerConfig(quiet_logger, SimpleNamespace(config=config_file), keys={"/array_of_hashes": "id"})
        mc.prepare(lhs_data)

        node = lhs_data["array_of_hashes"]
        parent = lhs_data
        parentref = "array_of_hashes"
        record = node[0]

        assert mc.aoh_merge_key(
            NodeCoords(node, parent, parentref), record) == "id"

    ###
    # set_merge_mode
    ###
    def test_set_merge_mode_default(self, quiet_logger):
        mc = MergerConfig(quiet_logger, SimpleNamespace(sets=None))
        assert mc.set_merge_mode(
            NodeCoords(None, None, None)) == SetMergeOpts.UNIQUE

    @pytest.mark.parametrize("setting, mode", [
        ("left", SetMergeOpts.LEFT),
        ("right", SetMergeOpts.RIGHT),
        ("unique", SetMergeOpts.UNIQUE),
    ])
    def test_set_merge_mode_cli(self, quiet_logger, setting, mode):
        mc = MergerConfig(quiet_logger, SimpleNamespace(sets=setting))
        assert mc.set_merge_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("setting, mode", [
        ("left", SetMergeOpts.LEFT),
        ("right", SetMergeOpts.RIGHT),
        ("unique", SetMergeOpts.UNIQUE),
    ])
    def test_set_merge_mode_ini(
        self, quiet_logger, tmp_path_factory, setting, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        sets = {}
        """.format(setting))
        mc = MergerConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , sets=None))
        assert mc.set_merge_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("cli, ini, mode", [
        ("left", "right", SetMergeOpts.LEFT),
        ("right", "unique", SetMergeOpts.RIGHT),
        ("unique", "all", SetMergeOpts.UNIQUE),
    ])
    def test_set_merge_mode_cli_overrides_ini_defaults(
        self, quiet_logger, tmp_path_factory, cli, ini, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        sets = {}
        """.format(ini))
        mc = MergerConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , sets=cli))
        assert mc.set_merge_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("cli, ini_default, ini_rule, mode", [
        ("left", "right", "unique", SetMergeOpts.UNIQUE),
        ("right", "unique", "left", SetMergeOpts.LEFT),
        ("unique", "left", "right", SetMergeOpts.RIGHT),
    ])
    def test_set_merge_mode_ini_rule_overrides_cli(
        self, quiet_logger, tmp_path_factory, cli, ini_default, ini_rule, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        sets = {}
        [rules]
        /hash/merge_targets/subset = {}
        """.format(ini_default, ini_rule))
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
        hash:
          lhs_exclusive: lhs value 1
          merge_targets:
            subkey: lhs value 2
            subset:
              ? one
              ? two
        """)
        lhs_yaml = get_yaml_editor()
        (lhs_data, lhs_loaded) = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)

        mc = MergerConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , sets=cli))
        mc.prepare(lhs_data)

        node = lhs_data["hash"]["merge_targets"]["subset"]
        parent = lhs_data["hash"]["merge_targets"]
        parentref = "subset"

        assert mc.set_merge_mode(
            NodeCoords(node, parent, parentref)) == mode


    ###
    # Edge Cases
    ###
    def test_warn_when_rules_matches_zero_nodes(
        self, capsys, info_warn_logger, tmp_path_factory
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [rules]
        /does_not_exist = left
        /array_of_hashes[name = "Does Not Compute"] = right
        """)
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
        hash:
          lhs_exclusive: lhs value 1
          merge_targets:
            subkey: lhs value 2
            subarray:
              - one
              - two
        array_of_hashes:
          - name: LHS Record 1
            id: 1
            prop: LHS value AoH 1
          - name: LHS Record 2
            id: 2
            prop: LHS value AoH 2
        """)
        lhs_yaml = get_yaml_editor()
        lhs_data = get_yaml_data(lhs_yaml, info_warn_logger, lhs_yaml_file)

        mc = MergerConfig(info_warn_logger, SimpleNamespace(config=config_file))
        mc.prepare(lhs_data)

        console = capsys.readouterr()
        assert "YAML Path matches no nodes" in console.out
