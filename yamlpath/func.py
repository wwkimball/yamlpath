"""
Collection of general helper functions.

Copyright 2018, 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
import sys

from yamlpath.common import Anchors, Nodes, Parsers, Searches
from yamlpath.wrappers import NodeCoords
from yamlpath import YAMLPath


DEPRECATION_WARNING = ("WARNING:  Deprecated functions will be removed in the"
                       " next major release of yamlpath.  Please refer to the"
                       " CHANGES file for more information (and how to get rid"
                       " of this message).")
print(DEPRECATION_WARNING, file=sys.stderr)

def get_yaml_editor(*args, **kwargs):
    """Relay function call to static method."""
    return Parsers.get_yaml_editor(*args, **kwargs)

def get_yaml_data(*args, **kwargs):
    """Relay function call to static method."""
    return Parsers.get_yaml_data(*args, **kwargs)

def get_yaml_multidoc_data(*args, **kwargs):
    """Relay function call to static method."""
    for (data, loaded) in Parsers.get_yaml_multidoc_data(*args, **kwargs):
        yield (data, loaded)

def build_next_node(*args):
    """Relay function call to static method."""
    return Nodes.build_next_node(*args)

def append_list_element(*args):
    """Relay function call to static method."""
    return Nodes.append_list_element(*args)

def wrap_type(*args):
    """Relay function call to static method."""
    return Nodes.wrap_type(*args)

def clone_node(*args):
    """Relay function call to static method."""
    return Nodes.clone_node(*args)

def make_float_node(*args):
    """Relay function call to static method."""
    return Nodes.make_float_node(*args)

def make_new_node(*args):
    """Relay function call to static method."""
    return Nodes.make_new_node(*args)

def get_node_anchor(*args):
    """Relay function call to static method."""
    return Anchors.get_node_anchor(*args)

def search_matches(*args):
    """Relay function call to static method."""
    return Searches.search_matches(*args)

def search_anchor(*args, **kwargs):
    """Relay function call to static method."""
    return Searches.search_anchor(*args, **kwargs)

def ensure_escaped(*args):
    """Relay function call to static method."""
    return YAMLPath.ensure_escaped(*args)

def escape_path_section(*args):
    """Relay function call to static method."""
    return YAMLPath.escape_path_section(*args)

def create_searchterms_from_pathattributes(*args):
    """Relay function call to static method."""
    return Searches.create_searchterms_from_pathattributes(*args)

def unwrap_node_coords(*args):
    """Relay function call to static method."""
    return NodeCoords.unwrap_node_coords(*args)

def stringify_dates(*args):
    """Relay function call to static method."""
    return Parsers.stringify_dates(*args)
