"""
Config file processor for the Differ.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
import configparser
from typing import Any, Dict, Tuple, Union
from argparse import Namespace

from yamlpath.exceptions import YAMLPathException
from yamlpath.differ.enums import AoHDiffOpts, ArrayDiffOpts
from yamlpath import Processor, YAMLPath
from yamlpath.wrappers import ConsolePrinter, NodeCoords


class DifferConfig:
    """Config file processor for the Differ."""

    def __init__(self, logger: ConsolePrinter, args: Namespace) -> None:
        """
        Instantiate this class into an object.

        Parameters:
        1. logger (ConsolePrinter) Instance of ConsoleWriter or subclass
        2. args (dict) Default options for diff rules

        Returns:  N/A
        """
        self.log = logger
        self.args = args
        self.config: Union[None, configparser.ConfigParser] = None
        self.rules: Dict[NodeCoords, str] = {}
        self.keys: Dict[NodeCoords, str] = {}

        self._load_config()

    def array_diff_mode(self, node_coord: NodeCoords) -> ArrayDiffOpts:
        """
        Get Array diff mode applicable to the indicated path.

        Parameters:
        1. node_coord (NodeCoords) The node for which to query.

        Returns:  (ArrayDiffOpts) Applicable mode.
        """
        # Precedence: config[rules] > CLI > config[defaults] > default
        diff_rule = self._get_rule_for(node_coord)
        if diff_rule:
            self.log.debug(
                "DifferConfig::array_diff_mode:  Matched {}"
                .format(diff_rule))
            return ArrayDiffOpts.from_str(diff_rule)
        self.log.debug("DifferConfig::array_diff_mode:  NOT Matched")
        if hasattr(self.args, "arrays") and self.args.arrays:
            return ArrayDiffOpts.from_str(self.args.arrays)
        if (self.config is not None
                and "defaults" in self.config
                and "arrays" in self.config["defaults"]):
            return ArrayDiffOpts.from_str(self.config["defaults"]["arrays"])
        return ArrayDiffOpts.POSITION

    def aoh_diff_mode(self, node_coord: NodeCoords) -> AoHDiffOpts:
        """
        Get Array-of-Hashes diff mode applicable to the indicated path.

        Parameters:
        1. node_coord (NodeCoords) The node for which to query.

        Returns:  (AoHDiffOpts) Applicable mode.
        """
        # Precedence: config[rules] > CLI > config[defaults] > default
        diff_rule = self._get_rule_for(node_coord)
        if diff_rule:
            self.log.debug(
                "DifferConfig::aoh_diff_mode:  Matched {}"
                .format(diff_rule))
            return AoHDiffOpts.from_str(diff_rule)
        self.log.debug("DifferConfig::aoh_diff_mode:  NOT Matched")
        if hasattr(self.args, "aoh") and self.args.aoh:
            return AoHDiffOpts.from_str(self.args.aoh)
        if (self.config is not None
                and "defaults" in self.config
                and "aoh" in self.config["defaults"]):
            return AoHDiffOpts.from_str(self.config["defaults"]["aoh"])
        return AoHDiffOpts.POSITION

    def aoh_diff_key(self, node_coord: NodeCoords) -> Tuple[str, bool]:
        """
        Get the user-defined identity key for Array-of-Hashes comparisons.

        Parameters:
        1. node_coord (NodeCoords) The node for which to query.

        Returns: (str, bool) The identity key field name and whether the key
          is specifically user-defined or inferred from the data.
        """
        # Check the user config for a specific key; fallback to first key.
        is_user_key = True
        diff_key = self._get_key_for(node_coord)
        if not diff_key:
            # This node may be a child of one of the registered keys.  That
            # registered key's node will match this node's parent.
            for eval_nc, eval_key in self.keys.items():
                if node_coord.parent == eval_nc.node:
                    diff_key = eval_key
                    break

        node = node_coord.node
        if not diff_key and isinstance(node, dict) and len(node.keys()) > 0:
            # Fallback to using the first key of the dict as an identity key
            is_user_key = False
            diff_key = list(node)[0]

        return (diff_key, is_user_key)

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
        proc = Processor(self.log, data)
        self._prepare_user_rules(proc, "rules", self.rules)
        self._prepare_user_rules(proc, "keys", self.keys)

    def _prepare_user_rules(
        self, proc: Processor, section: str, collector: dict
    ) -> None:
        """
        Identify DOM nodes matching user-defined diff rules.

        Parameters:
        1. proc (Processor) Reference to the DOM Processor.
        2. section (str) User-configuration file section defining the diff
           rules to apply.
        3. collector (dict) Storage collector for matching nodes.

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
                    "DifferConfig::_prepare_user_rules:  Reconstituted"
                    " configuration line '{}' to extract adjusted key '{}'"
                    " with value '{}'".format(conf_line, rule_key, rule_value))

            rule_path = YAMLPath(rule_key)
            yaml_path = YAMLPath(rule_path)
            self.log.debug(
                "DifferConfig::_prepare_user_rules:  Matching '{}' nodes to"
                " YAML Path '{}' from key, {}."
                .format(section, yaml_path, rule_key))
            try:
                for node_coord in proc.get_nodes(yaml_path, mustexist=True):
                    self.log.debug(
                        "Node will have comparisons rule, {}:"
                        .format(rule_value),
                        prefix="DifferConfig::_prepare_user_rules:  ",
                        data=node_coord.node)
                    collector[node_coord] = rule_value

            except YAMLPathException:
                self.log.warning("{} YAML Path matches no nodes:  {}"
                                .format(section, yaml_path))

        self.log.debug(
            "Matched rules to nodes:",
            prefix="DifferConfig::_prepare_user_rules:  ")
        for node_coord, diff_rule in collector.items():
            self.log.debug(
                "... RULE:  {}".format(diff_rule),
                prefix="DifferConfig::_prepare_user_rules:  ")
            self.log.debug(
                "... NODE:", data=node_coord,
                prefix="DifferConfig::_prepare_user_rules:  ")

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
        Get a user configured diff rule for a node.

        Parameters:
        1. node_coord (NodeCoords) The node for which to retrieve config.

        Returns: (str) The requested configuration.
        """
        self.log.debug(
            "Seeking rule for node:", prefix="DifferConfig::_get_rule_for:  ",
            header=" ")
        self.log.debug(
            "... NODE:", prefix="DifferConfig::_get_rule_for:  ",
            data=node_coord)
        return self._get_config_for(node_coord, self.rules)

    def _get_key_for(self, node_coord: NodeCoords) -> str:
        """
        Get a user configured diff identity key (field) for a node.

        Parameters:
        1. node_coord (NodeCoords) The node for which to retrieve config.

        Returns: (str) The requested configuration.
        """
        return self._get_config_for(node_coord, self.keys)
