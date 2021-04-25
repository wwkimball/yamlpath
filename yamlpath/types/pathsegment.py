"""
Defines a custom type for YAML Path segments.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from typing import Tuple

from yamlpath.enums import PathSegmentTypes
from yamlpath.types import PathAttributes

PathSegment = Tuple[PathSegmentTypes, PathAttributes]
