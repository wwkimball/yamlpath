"""Implements the PathSegmentTypes enumeration.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from enum import Enum, auto


class PathSegmentTypes(Enum):
    """Supported YAML Path segments"""
    ANCHOR = auto()
    INDEX = auto()
    KEY = auto()
    SEARCH = auto()
