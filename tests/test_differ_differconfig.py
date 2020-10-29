import pytest
from types import SimpleNamespace

from yamlpath.func import get_yaml_editor, get_yaml_data
from yamlpath.differ.enums import (
    AoHDiffOpts,
    ArrayDiffOpts,
)
from yamlpath.wrappers import NodeCoords
from yamlpath.differ import DifferConfig
from yamlpath import YAMLPath
from tests.conftest import (
    info_warn_logger,
    quiet_logger,
    create_temp_yaml_file
)

class Test_differ_DifferConfig():
    """Tests for the DifferConfig class."""

    ###
    # array_diff_mode
    ###
    def test_array_diff_mode_default(self, quiet_logger):
        mc = DifferConfig(quiet_logger, SimpleNamespace(arrays=None))
        assert mc.array_diff_mode(
            NodeCoords(None, None, None)) == ArrayDiffOpts.POSITION

    @pytest.mark.parametrize("setting, mode", [
        ("position", ArrayDiffOpts.POSITION),
        ("value", ArrayDiffOpts.VALUE),
    ])
    def test_array_diff_mode_cli(self, quiet_logger, setting, mode):
        mc = DifferConfig(quiet_logger, SimpleNamespace(arrays=setting))
        assert mc.array_diff_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("setting, mode", [
        ("position", ArrayDiffOpts.POSITION),
        ("value", ArrayDiffOpts.VALUE),
    ])
    def test_array_diff_mode_ini(
        self, quiet_logger, tmp_path_factory, setting, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        arrays = {}
        """.format(setting))
        mc = DifferConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , arrays=None))
        assert mc.array_diff_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("cli, ini, mode", [
        ("position", "value", ArrayDiffOpts.POSITION),
        ("value", "position", ArrayDiffOpts.VALUE),
    ])
    def test_array_diff_mode_cli_overrides_ini_defaults(
        self, quiet_logger, tmp_path_factory, cli, ini, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        arrays = {}
        """.format(ini))
        mc = DifferConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , arrays=cli))
        assert mc.array_diff_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("cli, ini_default, ini_rule, mode", [
        ("value", "value", "position", ArrayDiffOpts.POSITION),
        ("position", "position", "value", ArrayDiffOpts.VALUE),
    ])
    def test_array_diff_mode_ini_rule_overrides_cli(
        self, quiet_logger, tmp_path_factory, cli, ini_default, ini_rule, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        arrays = {}
        [rules]
        /hash/diff_targets/subarray = {}
        """.format(ini_default, ini_rule))
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
        hash:
          lhs_exclusive: lhs value 1
          diff_targets:
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

        mc = DifferConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , arrays=cli))
        mc.prepare(lhs_data)

        node = lhs_data["hash"]["diff_targets"]["subarray"]
        parent = lhs_data["hash"]["diff_targets"]
        parentref = "subarray"

        assert mc.array_diff_mode(
            NodeCoords(node, parent, parentref)) == mode


    ###
    # aoh_diff_mode
    ###
    def test_aoh_diff_mode_default(self, quiet_logger):
        mc = DifferConfig(quiet_logger, SimpleNamespace(aoh=None))
        assert mc.aoh_diff_mode(
            NodeCoords(None, None, None)) == AoHDiffOpts.POSITION

    @pytest.mark.parametrize("setting, mode", [
        ("deep", AoHDiffOpts.DEEP),
        ("dpos", AoHDiffOpts.DPOS),
        ("key", AoHDiffOpts.KEY),
        ("position", AoHDiffOpts.POSITION),
        ("value", AoHDiffOpts.VALUE),
    ])
    def test_aoh_diff_mode_cli(self, quiet_logger, setting, mode):
        mc = DifferConfig(quiet_logger, SimpleNamespace(aoh=setting))
        assert mc.aoh_diff_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("setting, mode", [
        ("deep", AoHDiffOpts.DEEP),
        ("dpos", AoHDiffOpts.DPOS),
        ("key", AoHDiffOpts.KEY),
        ("position", AoHDiffOpts.POSITION),
        ("value", AoHDiffOpts.VALUE),
    ])
    def test_aoh_diff_mode_ini(
        self, quiet_logger, tmp_path_factory, setting, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        aoh = {}
        """.format(setting))
        mc = DifferConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , aoh=None))
        assert mc.aoh_diff_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("cli, ini, mode", [
        ("deep", "dpos", AoHDiffOpts.DEEP),
        ("dpos", "key", AoHDiffOpts.DPOS),
        ("key", "position", AoHDiffOpts.KEY),
        ("position", "value", AoHDiffOpts.POSITION),
        ("value", "deep", AoHDiffOpts.VALUE),
    ])
    def test_aoh_diff_mode_cli_overrides_ini_defaults(
        self, quiet_logger, tmp_path_factory, cli, ini, mode
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [defaults]
        aoh = {}
        """.format(ini))
        mc = DifferConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , aoh=cli))
        assert mc.aoh_diff_mode(
            NodeCoords(None, None, None)) == mode

    @pytest.mark.parametrize("cli, ini_default, ini_rule, mode", [
        ("deep", "dpos", "key", AoHDiffOpts.KEY),
        ("dpos", "key", "position", AoHDiffOpts.POSITION),
        ("key", "position", "value", AoHDiffOpts.VALUE),
        ("position", "value", "deep", AoHDiffOpts.DEEP),
        ("value", "deep", "dpos", AoHDiffOpts.DPOS),
    ])
    def test_aoh_diff_mode_ini_rule_overrides_cli(
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
          diff_targets:
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

        mc = DifferConfig(quiet_logger, SimpleNamespace(
            config=config_file
            , aoh=cli))
        mc.prepare(lhs_data)

        node = lhs_data["array_of_hashes"]
        parent = lhs_data
        parentref = "array_of_hashes"

        assert mc.aoh_diff_mode(
            NodeCoords(node, parent, parentref)) == mode


    ###
    # aoh_diff_key
    ###
    def test_aoh_diff_key_default(self, quiet_logger, tmp_path_factory):
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
        hash:
          lhs_exclusive: lhs value 1
          diff_targets:
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

        mc = DifferConfig(quiet_logger, SimpleNamespace())
        mc.prepare(lhs_data)

        parent = lhs_data["array_of_hashes"]
        parentref = 0
        node = parent[parentref]
        nc = NodeCoords(node, parent, parentref)
        (key_attr, is_user_defined) = mc.aoh_diff_key(nc)

        assert key_attr == "name" and is_user_defined == False

    def test_aoh_diff_key_ini(self, quiet_logger, tmp_path_factory):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [keys]
        /array_of_hashes = id
        """)
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
        hash:
          lhs_exclusive: lhs value 1
          diff_targets:
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

        mc = DifferConfig(quiet_logger, SimpleNamespace(config=config_file))
        mc.prepare(lhs_data)

        parent = lhs_data["array_of_hashes"]
        parentref = 0
        node = parent[parentref]
        nc = NodeCoords(node, parent, parentref)
        (key_attr, is_user_defined) = mc.aoh_diff_key(nc)

        assert key_attr == "id" and is_user_defined == True

    def test_aoh_diff_key_ini_inferred_parent(
        self, quiet_logger, tmp_path_factory
    ):
        config_file = create_temp_yaml_file(tmp_path_factory, """
        [keys]
        /array_of_hashes = prop
        """)
        lhs_yaml_file = create_temp_yaml_file(tmp_path_factory, """---
        hash:
          lhs_exclusive: lhs value 1
          diff_targets:
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

        mc = DifferConfig(quiet_logger, SimpleNamespace(config=config_file))
        mc.prepare(lhs_data)

        parent = lhs_data["array_of_hashes"]
        parentref = 1
        node = parent[parentref]
        nc = NodeCoords(node, parent, parentref)
        (key_attr, is_user_defined) = mc.aoh_diff_key(nc)

        assert key_attr == "prop" and is_user_defined == True


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
          diff_targets:
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

        mc = DifferConfig(info_warn_logger, SimpleNamespace(config=config_file))
        mc.prepare(lhs_data)

        console = capsys.readouterr()
        assert "YAML Path matches no nodes" in console.out
