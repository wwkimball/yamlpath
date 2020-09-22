"""
Config file processor for the Merger.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
import configparser
from typing import Any

from yamlpath.enums import (
    AnchorConflictResolutions,
    ArrayMergeOpts,
    HashMergeOpts
)
from yamlpath import Processor
from yamlpath.wrappers import ConsolePrinter, NodeCoords


class MergerConfig:
    """Config file processor for the Merger."""
    def __init__(self, logger: ConsolePrinter, args: dict) -> None:
        self.log = logger
        self.args = args
        self.config = None
        self.rules = {}

        self._load_config()

    def anchor_merge_mode(self) -> AnchorConflictResolutions:
        """Get Anchor merge options."""
        return AnchorConflictResolutions.from_str(self.args.anchors)

    def hash_merge_mode(self, node_coord: NodeCoords) -> HashMergeOpts:
        """Get Hash merge options applicable to the indicated path."""
        merge_rule = self._get_rule_for(node_coord)
        if merge_rule:
            self.log.debug(
                "MergerConfig::hash_merge_mode:  Matched {}"
                .format(merge_rule))
            return HashMergeOpts.from_str(merge_rule)
        self.log.debug("MergerConfig::hash_merge_mode:  NOT Matched")
        return HashMergeOpts.from_str(self.args.hashes)

    def array_merge_mode(self, node_coord: NodeCoords) -> ArrayMergeOpts:
        """Get Array merge options application to the indicated path."""
        merge_rule = self._get_rule_for(node_coord)
        if merge_rule:
            self.log.debug(
                "MergerConfig::array_merge_mode:  Matched {}"
                .format(merge_rule))
            return ArrayMergeOpts.from_str(merge_rule)
        self.log.debug("MergerConfig::array_merge_mode:  NOT Matched")
        return ArrayMergeOpts.from_str(self.args.arrays)

    def prepare(self, data: Any) -> None:
        """Load references to all nodes which match config rules."""
        if self.config is None:
            return

        proc = Processor(self.log, data)
        for yaml_path in self.config['rules']:
            for node_coord in proc.get_nodes(yaml_path):
                self.rules[node_coord] = self.config['rules'][yaml_path]

        self.log.debug("MergerConfig::prepare:  Matched rules to nodes:")
        self.log.debug(self.rules)

    def _load_config(self) -> None:
        """Load the external configuration file."""
        config = configparser.ConfigParser()

        # Load the configuration file when one is specified
        config_file = self.args.config
        if config_file:
            config.read(config_file)
            if config.sections():
                self.config = config

    def _get_rule_for(self, node_coord: NodeCoords) -> str:
        """Get a user configured merge rule for a node."""
        if self.config is None:
            return None

        for rule_coord, merge_rule in self.rules.items():
            if rule_coord.node == node_coord.node \
                    and rule_coord.parent == node_coord.parent \
                    and rule_coord.parentref == node_coord.parentref:
                return merge_rule

        return None
