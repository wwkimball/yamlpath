"""
Config file processor for the Merger.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
import configparser
from typing import Any

from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import (
    AnchorConflictResolutions,
    AoHMergeOpts,
    ArrayMergeOpts,
    HashMergeOpts,
    PathSeperators
)
from yamlpath import Processor, YAMLPath
from yamlpath.wrappers import ConsolePrinter, NodeCoords


class MergerConfig:
    """Config file processor for the Merger."""
    def __init__(self, logger: ConsolePrinter, args: dict) -> None:
        self.log = logger
        self.args = args
        self.config = None
        self.rules = {}
        self.keys = {}

        self._load_config()

    def anchor_merge_mode(self) -> AnchorConflictResolutions:
        """Get Anchor merge mode."""
        # Precedence: CLI > config[defaults] > default
        if self.args.anchors:
            return AnchorConflictResolutions.from_str(self.args.anchors)
        if (self.config is not None
                and "defaults" in self.config
                and "anchors" in self.config["defaults"]):
            return AnchorConflictResolutions.from_str(
                self.config["defaults"]["anchors"])
        return AnchorConflictResolutions.STOP

    def hash_merge_mode(self, node_coord: NodeCoords) -> HashMergeOpts:
        """
        Get Hash merge mode applicable to the indicated path.

        Parameters:
        1. node_coord (NodeCoords) The node for which to query.

        Returns:  (HashMergeOpts) Applicable mode.
        """
        # Precedence: config[rules] > CLI > config[defaults] > default
        merge_rule = self._get_rule_for(node_coord)
        if merge_rule:
            self.log.debug(
                "MergerConfig::hash_merge_mode:  Matched {}"
                .format(merge_rule))
            return HashMergeOpts.from_str(merge_rule)
        self.log.debug("MergerConfig::hash_merge_mode:  NOT Matched")
        if self.args.hashes:
            return HashMergeOpts.from_str(self.args.hashes)
        if (self.config is not None
                and "defaults" in self.config
                and "hashes" in self.config["defaults"]):
            return HashMergeOpts.from_str(self.config["defaults"]["hashes"])
        return HashMergeOpts.DEEP

    def array_merge_mode(self, node_coord: NodeCoords) -> ArrayMergeOpts:
        """
        Get Array merge mode applicable to the indicated path.

        Parameters:
        1. node_coord (NodeCoords) The node for which to query.

        Returns:  (ArrayMergeOpts) Applicable mode.
        """
        # Precedence: config[rules] > CLI > config[defaults] > default
        merge_rule = self._get_rule_for(node_coord)
        if merge_rule:
            self.log.debug(
                "MergerConfig::array_merge_mode:  Matched {}"
                .format(merge_rule))
            return ArrayMergeOpts.from_str(merge_rule)
        self.log.debug("MergerConfig::array_merge_mode:  NOT Matched")
        if self.args.arrays:
            return ArrayMergeOpts.from_str(self.args.arrays)
        if (self.config is not None
                and "defaults" in self.config
                and "arrays" in self.config["defaults"]):
            return ArrayMergeOpts.from_str(self.config["defaults"]["arrays"])
        return ArrayMergeOpts.ALL

    def aoh_merge_mode(self, node_coord: NodeCoords) -> AoHMergeOpts:
        """
        Get Array-of-Hashes merge mode applicable to the indicated path.

        Parameters:
        1. node_coord (NodeCoords) The node for which to query.

        Returns:  (AoHMergeOpts) Applicable mode.
        """
        # Precedence: config[rules] > CLI > config[defaults] > default
        merge_rule = self._get_rule_for(node_coord)
        if merge_rule:
            self.log.debug(
                "MergerConfig::aoh_merge_mode:  Matched {}"
                .format(merge_rule))
            return AoHMergeOpts.from_str(merge_rule)
        self.log.debug("MergerConfig::aoh_merge_mode:  NOT Matched")
        if self.args.aoh:
            return AoHMergeOpts.from_str(self.args.aoh)
        if (self.config is not None
                and "defaults" in self.config
                and "aoh" in self.config["defaults"]):
            return AoHMergeOpts.from_str(self.config["defaults"]["aoh"])
        return AoHMergeOpts.ALL

    def aoh_merge_key(
        self, node_coord: NodeCoords, data: dict
    ) -> str:
        """
        Get the user-defined identity key for Array-of-Hashes merging.

        Parameters:
        1. node_coord (NodeCoords) The node for which to query.
        2. data (dict) The merge source node from which an identity key will
           be inferred if not explicity provided via user configuration.

        Returns: (str) The identity key field name.
        """
        # Check the user config for a specific key; fallback to first key.
        merge_key = self._get_key_for(node_coord)
        if not merge_key:
            # This node may be a child of one of the registered keys.  That
            # registered key's node will match this node's parent.
            for eval_nc, eval_key in self.keys.items():
                if node_coord.parent == eval_nc.node:
                    merge_key = eval_key
                    break
        if not merge_key and len(data.keys()) > 0:
            # Fallback to using the first key of the dict as an identity key
            merge_key = list(data)[0]
        return merge_key

    def prepare(self, data: Any) -> None:
        """
        Load references to all nodes which match config rules.

        Parameters:
        1. data (Any) The DOM for which to load configuration.

        Returns:  N/A
        """
        if self.config is None:
            return

        # Eliminate previous rules and keys to limit scanning to only those
        # nodes which exist within this new document.
        self.rules = {}
        self.keys = {}

        # Adjust data paths for mergeat prefix
        merge_path = None
        if self.args.mergeat:
            merge_path = YAMLPath(self.args.mergeat)
            merge_path.seperator = PathSeperators.FSLASH

        def strip_path_prefix(prefix: YAMLPath, path: str) -> YAMLPath:
            if prefix is None:
                self.log.debug(
                    "MergerConfig::prepare::strip_path_prefix:  No prefix to"
                    " strip.")
                return YAMLPath(path)

            prefix.seperator = PathSeperators.FSLASH
            if str(prefix) == "/":
                self.log.debug(
                    "MergerConfig::prepare::strip_path_prefix:  Ignoring root"
                    " prefix.")
                return YAMLPath(path)

            self.log.debug(
                "MergerConfig::prepare::strip_path_prefix:  Starting with"
                " path={}, prefix={}.".format(path, prefix))
            yaml_path = YAMLPath(path)
            prefix.seperator = PathSeperators.FSLASH
            yaml_path.seperator = PathSeperators.FSLASH
            prefix_str = str(prefix)
            path_str = str(yaml_path)
            if path_str.startswith(prefix_str):
                path_str = path_str[len(prefix_str):]
                self.log.debug(
                    "MergerConfig::prepare::strip_path_prefix:  Reduced path"
                    " to {}.".format(path_str))
                return YAMLPath(path_str)

            self.log.debug(
                "MergerConfig::prepare::strip_path_prefix:  Prefix, {}, NOT"
                " present in path, {}.".format(prefix, yaml_path))
            return yaml_path

        proc = Processor(self.log, data)
        for rule_path in self.config["rules"]:
            yaml_path = strip_path_prefix(merge_path, rule_path)
            self.log.debug(
                "MergerConfig::prepare:  Matching 'rules' nodes to {} from {}."
                .format(yaml_path, rule_path))
            try:
                for node_coord in proc.get_nodes(yaml_path, mustexist=True):
                    self.rules[node_coord] = self.config["rules"][rule_path]
            except YAMLPathException:
                self.log.warning("Rule YAML Path matches no nodes:  {}"
                                 .format(yaml_path))

        self.log.debug("MergerConfig::prepare:  Matched rules to nodes:")
        self.log.debug(self.rules)

        for key_path in self.config["keys"]:
            yaml_path = strip_path_prefix(merge_path, key_path)
            self.log.debug(
                "MergerConfig::prepare:  Matching 'keys' nodes to {} from {}."
                .format(yaml_path, key_path))
            try:
                for node_coord in proc.get_nodes(yaml_path, mustexist=True):
                    self.keys[node_coord] = self.config["keys"][key_path]
            except YAMLPathException:
                self.log.warning("Merge key YAML Path matches no nodes:  {}"
                                 .format(yaml_path))

        self.log.debug("MergerConfig::prepare:  Matched keys to nodes:")
        self.log.debug(self.keys)

    def get_insertion_point(self) -> YAMLPath:
        """Returns the YAML Path at which merging shall be performed."""
        return YAMLPath(self.args.mergeat)

    def _load_config(self) -> None:
        """Load the external configuration file."""
        config = configparser.ConfigParser()

        # Load the configuration file when one is specified
        config_file = self.args.config
        if config_file:
            config.read(config_file)
            if config.sections():
                self.config = config

    def _get_config_for(self, node_coord: NodeCoords, section: dict) -> str:
        """
        Get user configuration applicable to a node.

        Parameters:
        1. node_coord (NodeCoords) The node for which to retrieve config.
        2. section (dict) The configuration section to query.

        Returns: (str) The requested configuration.
        """
        if self.config is None:
            return None

        for rule_coord, rule_config in section.items():
            if rule_coord.node == node_coord.node \
                    and rule_coord.parent == node_coord.parent \
                    and rule_coord.parentref == node_coord.parentref:
                return rule_config

        return None

    def _get_rule_for(self, node_coord: NodeCoords) -> str:
        """
        Get a user configured merge rule for a node.

        Parameters:
        1. node_coord (NodeCoords) The node for which to retrieve config.

        Returns: (str) The requested configuration.
        """
        return self._get_config_for(node_coord, self.rules)

    def _get_key_for(self, node_coord: NodeCoords) -> str:
        """
        Get a user configured merge identity key (field) for a node.

        Parameters:
        1. node_coord (NodeCoords) The node for which to retrieve config.

        Returns: (str) The requested configuration.
        """
        return self._get_config_for(node_coord, self.keys)
