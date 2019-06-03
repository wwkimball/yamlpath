"""
YAML path Search segment terms.

Copyright 2019 William W. Kimball, Jr. MBA MSIS
"""
from typing import Type

# pylint: disable=locally-disabled,unused-import
from yamlpath.types import PathAttributes
from yamlpath.path import CollectorTerms
from yamlpath.enums import PathSearchMethods


class SearchTerms:
    """YAML path Search segment terms."""

    def __init__(self, inverted: bool, method: PathSearchMethods,
                 attribute: str, term: str) -> None:
        self._inverted: bool = inverted
        self._method: PathSearchMethods = method
        self._attribute: str = attribute
        self._term: str = term

    @classmethod
    def from_path_segment_attrs(
            cls: Type,
            rhs: PathAttributes) -> "SearchTerms":
        """
        Generates a new SearchTerms instance by copying SearchTerms attributes
        from a YAML Path segment's attributes.
        """
        if isinstance(rhs, SearchTerms):
            newinst: SearchTerms = cls(
                rhs.inverted, rhs.method, rhs.attribute, rhs.term
            )
            return newinst
        raise AttributeError

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
            + str(self.method)
            + safe_term
            + "]"
        )

    @property
    def inverted(self) -> bool:
        """
        Accesses the inversion flag for this Search, indicating whether the
        results are to be inverted.
        """
        return self._inverted

    @property
    def method(self) -> PathSearchMethods:
        """
        Accesses the search method, indicating what kind of search is to be
        performed.
        """
        return self._method

    @property
    def attribute(self) -> str:
        """
        Accessor for the attribute being searched.  This is the "haystack" and
        may reference a particular dictionary key, all values of a dictionary,
        or the elements of a list.
        """
        return self._attribute

    @property
    def term(self) -> str:
        """
        Accessor for the search term.  This is the "needle" to search for
        within the attribute ("haystack").
        """
        return self._term
