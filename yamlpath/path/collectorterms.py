"""
YAML Path Collector segment terms.

Copyright 2019, 2020 William W. Kimball, Jr. MBA MSIS
"""
from yamlpath.enums import CollectorOperators


class CollectorTerms:
    """YAML Path Collector segment terms."""

    def __init__(self, expression: str,
                 operation: CollectorOperators = CollectorOperators.NONE
                ) -> None:
        """
        Instantiate a Collector Term.

        Parameters:
        1. expression (str) The YAML Path being collected
        2. operation (CollectorOperators) The operation for this Collector,
           relative to its subsequent peer Collector
        """
        self._expression: str = expression
        self._operation: CollectorOperators = operation

    def __str__(self) -> str:
        """Get the String rendition of this Collector Term."""
        operator: str = str(self.operation)
        return "{}({})".format(operator, self.expression)

    @property
    def operation(self) -> CollectorOperators:
        """
        Get the operation for this Collector.

        This indicates whether its results are independent, added to the prior
        Collector, or removed from the prior Collector.
        """
        return self._operation

    @property
    def expression(self) -> str:
        """Get the Collector expression, which is a stringified YAML Path."""
        return self._expression
