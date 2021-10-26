"""
Defines a custom type for YAML Path segment attributes.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from typing import Union

from yamlpath.path import CollectorTerms
from yamlpath.path import searchterms


PathAttributes = Union[str, int, CollectorTerms, searchterms.SearchTerms, None]
