"""YAML Path Collector segment terms.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from yamlpath.enums import CollectorOperators


class CollectorTerms:
    """YAML Path Collector segment terms."""

    def __init__(self, expression: str,
                 operation: CollectorOperators = CollectorOperators.NONE
                ) -> None:
        self.operation = operation
        self.expression = expression

    def __str__(self) -> str:
        from yamlpath import Path
        operator: str = CollectorOperators.to_operator(self.operation)
        return "{}({})".format(operator, Path(self.expression))
