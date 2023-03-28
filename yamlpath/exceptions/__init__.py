"""Make all of the custom YAML Path exceptions available."""
from yamlpath.exceptions.yamlpathexception import YAMLPathException
from yamlpath.exceptions.badaliasyamlpathexception import (
    BadAliasYAMLPathException)
from yamlpath.exceptions.duplicatekeyyamlpathexception import (
    DuplicateKeyYAMLPathException)
from yamlpath.exceptions.nodocumentyamlpathexception import (
    NoDocumentYAMLPathException)
from yamlpath.exceptions.recursionyamlpathexception import (
    RecursionYAMLPathException)
from yamlpath.exceptions.typemismatchyamlpathexception import (
    TypeMismatchYAMLPathException)
from yamlpath.exceptions.unmatchedyamlpathexception import (
    UnmatchedYAMLPathException)
