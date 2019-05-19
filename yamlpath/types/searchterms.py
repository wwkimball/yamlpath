"""YAML path Search segment terms.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from yamlpath.enums import PathSearchMethods


class SearchTerms:
    """YAML path Search segment terms."""

    def __init__(self, inverted: bool, method: PathSearchMethods,
                 attribute: str, term: str) -> None:
        self.inverted = inverted
        self.method = method
        self.attribute = attribute
        self.term = term

    def __str__(self) -> str:
        if self.method == PathSearchMethods.REGEX:
            safe_term = "/{}/".format(self.term.replace("/", r"\/"))
        else:
            # Replace unescaped spaces with escaped spaces
            safe_term = r"\ ".join(
                list(map(
                    lambda ele: ele.replace(" ", r"\ ")
                    , self.term.split(r"\ ")
                ))
            )

        return (
            "["
            + str(self.attribute)
            + ("!" if self.inverted else "")
            + PathSearchMethods.to_operator(self.method)
            + safe_term
            + "]"
        )
