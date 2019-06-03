"""Defines a custom type for YAML Path segment attributes."""
from typing import Union

from yamlpath.path import CollectorTerms, SearchTerms


PathAttributes = Union[str, CollectorTerms, SearchTerms]
