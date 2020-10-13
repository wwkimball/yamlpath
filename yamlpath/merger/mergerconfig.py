"""
Config file processor for the Merger.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
import configparser
from typing import Any, Dict, Union
from argparse import Namespace

from yamlpath.exceptions import YAMLPathException
from yamlpath.merger.enums import (
    AnchorConflictResolutions,
    AoHMergeOpts,
    ArrayMergeOpts,
    HashMergeOpts,
    OutputDocTypes,
)
from yamlpath import Processor, YAMLPath
from yamlpath.wrappers import ConsolePrinter, NodeCoords


class MergerConfig:
    """Config file processor for the Merger."""

    def __init__(self, logger: ConsolePrinter, args: Namespace) -> None:
        """
        Instantiate this class into an object.

        Parameters:
        1. logger (ConsolePrinter) Instance of ConsoleWriter or subclass
        2. args (dict) Default options for merge rules

        Returns:  N/A
        """
        self.log = logger
        self.args = args
        self.config: Union[None, configparser.ConfigParser] = None
        self.rules: Dict[NodeCoords, str] = {}
        self.keys: Dict[NodeCoords, str] = {}

        self._load_config()

    def anchor_merge_mode(self) -> AnchorConflictResolutions:
        """Get Anchor merge mode."""
        # Precedence: CLI > config[defaults] > default
        if hasattr(self.args, "anchors") and self.args.anchors:
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
        if hasattr(self.args, "hashes") and self.args.hashes:
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
        if hasattr(self.args, "arrays") and self.args.arrays:
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
        if hasattr(self.args, "aoh") and self.args.aoh:
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

        # Load new rules and keys
        merge_path = self.get_insertion_point()
        proc = Processor(self.log, data)
        self._prepare_user_rules(proc, merge_path, "rules", self.rules)
        self._prepare_user_rules(proc, merge_path, "keys", self.keys)

    def get_insertion_point(self) -> YAMLPath:
        """Get the YAML Path at which merging shall be performed."""
        if hasattr(self.args, "mergeat"):
            return YAMLPath(self.args.mergeat)
        return YAMLPath("/")

    def get_document_format(self) -> OutputDocTypes:
        """Get the user-desired output format."""
        if hasattr(self.args, "document_format"):
            return OutputDocTypes.from_str(self.args.document_format)
        return OutputDocTypes.AUTO

    def _prepare_user_rules(
        self, proc: Processor, merge_path: YAMLPath, section: str,
        collector: dict
    ) -> None:
        """
        Identify DOM nodes matching user-defined merge rules.

        Parameters:
        1. proc (Processor) Reference to the DOM Processor.
        2. merge_path (YAMLPath) User-specified path within the DOM at which
           merging will take place.
        3. section (str) User-configuration file section defining the merge
           rules to apply.
        4. collector (dict) Storage collector for matching nodes.

        Returns:  N/A
        """
        if self.config is None or not section in self.config:
            self.log.warning(
                "User-specified configuration file has no {} section."
                .format(section))
            return

        for rule_key in self.config[section]:
            rule_value = self.config[section][rule_key]

            if "=" in rule_value:
                # There were at least two = signs on the configuration line
                conf_line = rule_key + "=" + rule_value
                delim_pos = conf_line.rfind("=")
                rule_key = conf_line[0:delim_pos].strip()
                rule_value = conf_line[delim_pos + 1:].strip()
                self.log.debug(
                    "MergerConfig::_prepare_user_rules:  Reconstituted"
                    " configuration line '{}' to extract adjusted key '{}'"
                    " with value '{}'".format(conf_line, rule_key, rule_value))

            rule_path = YAMLPath(rule_key)
            yaml_path = YAMLPath.strip_path_prefix(rule_path, merge_path)
            self.log.debug(
                "MergerConfig::_prepare_user_rules:  Matching '{}' nodes to"
                " YAML Path '{}' from key, {}."
                .format(section, yaml_path, rule_key))
            try:
                for node_coord in proc.get_nodes(yaml_path, mustexist=True):
                    self.log.debug(
                        "Node will have merging rule, {}:"
                        .format(rule_value),
                        prefix="MergerConfig::_prepare_user_rules:  ",
                        data=node_coord.node)
                    collector[node_coord] = rule_value

            except YAMLPathException:
                self.log.warning("{} YAML Path matches no nodes:  {}"
                                .format(section, yaml_path))

        self.log.debug(
            "Matched rules to nodes:",
            prefix="MergerConfig::_prepare_user_rules:  ")
        for node_coord, merge_rule in collector.items():
            self.log.debug(
                "... RULE:  {}".format(merge_rule),
                prefix="MergerConfig::_prepare_user_rules:  ")
            self.log.debug(
                "... NODE:", data=node_coord,
                prefix="MergerConfig::_prepare_user_rules:  ")

    def _load_config(self) -> None:
        """Load the external configuration file."""
        config = configparser.ConfigParser()

        # Load the configuration file when one is specified
        config_file = (
            self.args.config
            if hasattr(self.args, "config")
            else None)

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
            return ""

        for rule_coord, rule_config in section.items():
            if rule_coord.node == node_coord.node \
                    and rule_coord.parent == node_coord.parent \
                    and rule_coord.parentref == node_coord.parentref:
                return str(rule_config)

        return ""

    def _get_rule_for(self, node_coord: NodeCoords) -> str:
        """
        Get a user configured merge rule for a node.

        Parameters:
        1. node_coord (NodeCoords) The node for which to retrieve config.

        Returns: (str) The requested configuration.
        """
        self.log.debug(
            "Seeking rule for node:", prefix="MergerConfig::_get_rule_for:  ",
            header=" ")
        self.log.debug(
            "... NODE:", prefix="MergerConfig::_get_rule_for:  ",
            data=node_coord)
        return self._get_config_for(node_coord, self.rules)

    def _get_key_for(self, node_coord: NodeCoords) -> str:
        """
        Get a user configured merge identity key (field) for a node.

        Parameters:
        1. node_coord (NodeCoords) The node for which to retrieve config.

        Returns: (str) The requested configuration.
        """
        return self._get_config_for(node_coord, self.keys)
