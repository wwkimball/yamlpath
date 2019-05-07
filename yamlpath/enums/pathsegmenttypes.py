"""Implements the PathSegmentTypes enumeration."""
from enum import Enum, auto


class PathSegmentTypes(Enum):
    """Supported YAML Path segments"""
    ANCHOR = auto()
    INDEX = auto()
    KEY = auto()
    SEARCH = auto()
