"""
Config file processor for the Merger.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
import configparser
from typing import Any

from yamlpath.enums import (
    AnchorConflictResolutions,
    AoHMergeOpts,
    ArrayMergeOpts,
    HashMergeOpts
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
        """Get Anchor merge options."""
        # Precedence: CLI > config[defaults] > default
        if self.args.anchors:
            return AnchorConflictResolutions.from_str(self.args.anchors)
        if "defaults" in self.config and "anchors" in self.config["defaults"]:
            return AnchorConflictResolutions.from_str(
                self.config["defaults"]["anchors"])
        return AnchorConflictResolutions.STOP

    def hash_merge_mode(self, node_coord: NodeCoords) -> HashMergeOpts:
        """Get Hash merge options applicable to the indicated path."""
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
        if "defaults" in self.config and "hashes" in self.config["defaults"]:
            return HashMergeOpts.from_str(self.config["defaults"]["hashes"])
        return HashMergeOpts.DEEP

    def array_merge_mode(self, node_coord: NodeCoords) -> ArrayMergeOpts:
        """Get Array merge options applicable to the indicated path."""
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
        if "defaults" in self.config and "arrays" in self.config["defaults"]:
            return ArrayMergeOpts.from_str(self.config["defaults"]["arrays"])
        return ArrayMergeOpts.ALL

    def aoh_merge_mode(self, node_coord: NodeCoords) -> AoHMergeOpts:
        """
        Get Array-of-Hashes merge options applicable to the indicated path.
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
        if "defaults" in self.config and "aoh" in self.config["defaults"]:
            return AoHMergeOpts.from_str(self.config["defaults"]["aoh"])
        return AoHMergeOpts.ALL

    def aoh_merge_key(
        self, node_coord: NodeCoords, data: dict
    ) -> str:
        """Get the identity key of a dict based on user settings."""
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
        """Load references to all nodes which match config rules."""
        if self.config is None:
            return

        # Eliminate previous rules and keys to limit scanning to only those
        # nodes which exist within this new document.
        self.rules = {}
        self.keys = {}

        proc = Processor(self.log, data)
        for yaml_path in self.config["rules"]:
            for node_coord in proc.get_nodes(yaml_path):
                self.rules[node_coord] = self.config["rules"][yaml_path]
        self.log.debug("MergerConfig::prepare:  Matched rules to nodes:")
        self.log.debug(self.rules)

        for yaml_path in self.config["keys"]:
            for node_coord in proc.get_nodes(yaml_path):
                self.keys[node_coord] = self.config["keys"][yaml_path]
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
        """Get user configuration applicable to a node."""
        if self.config is None:
            return None

        for rule_coord, rule_config in section.items():
            if rule_coord.node == node_coord.node \
                    and rule_coord.parent == node_coord.parent \
                    and rule_coord.parentref == node_coord.parentref:
                return rule_config

        return None

    def _get_rule_for(self, node_coord: NodeCoords) -> str:
        """Get a user configured merge rule for a node."""
        return self._get_config_for(node_coord, self.rules)

    def _get_key_for(self, node_coord: NodeCoords) -> str:
        """Get a user configured merge rule for a node."""
        return self._get_config_for(node_coord, self.keys)
