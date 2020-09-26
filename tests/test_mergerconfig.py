import pytest
from types import SimpleNamespace

from yamlpath.enums import AnchorConflictResolutions
from yamlpath import MergerConfig
from tests.conftest import quiet_logger, create_temp_yaml_file

class Test_MergerConfig():
    """Tests for the MergerConfig class."""

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
