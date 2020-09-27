import pytest
from types import SimpleNamespace

from yamlpath.func import get_yaml_editor, get_yaml_data
from yamlpath.enums import AnchorConflictResolutions, HashMergeOpts
from yamlpath.wrappers import NodeCoords
from yamlpath import MergerConfig
from tests.conftest import quiet_logger, create_temp_yaml_file

class Test_MergerConfig():
    """Tests for the MergerConfig class."""

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
        lhs_data = get_yaml_data(lhs_yaml, quiet_logger, lhs_yaml_file)

        mc = MergerConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , mergeat="/"
            , hashes=cli))
        mc.prepare(lhs_data)

        node = lhs_data["hash"]
        parent = lhs_data
        parentref = "hash"

        assert mc.hash_merge_mode(
            NodeCoords(node, parent, parentref)) == mode
