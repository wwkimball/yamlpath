import pytest
import sys
from types import SimpleNamespace

from ruamel.yaml import YAML

import yamlpath.patches
from yamlpath import Processor
from yamlpath.wrappers import ConsolePrinter

@pytest.fixture
def yamlpath_fixture():
        """Returns a YAMLPath with a quiet logger."""
        args = SimpleNamespace(verbose=False, quiet=True, debug=False)
        logger = ConsolePrinter(args)
        return Processor(logger)

def test_yaml_dump(yamlpath_fixture):
        data = """---
aliases:
  - &test_scalarstring This is a scalar string.
  - &test_foldedstring >-
    This is a
    folded multi-line
    string.
  - &test_literalstring |-
    This is a
    literal multi-line
    string.

top_scalar:  value
top_alias: *test_scalarstring
top_array_anchor: &topArrayAnchor
  - *test_scalarstring
  - An original value
  - *test_foldedstring
  - Another original value

sub_hash_anchor: &subHashAnchor
  child1:
    attr_tst: child 1
    attr_val: 100
  child2:
    attr_tst: child 2
    attr_val: 200
  child3:
    attr_tst: child 3
    attr_val: 300
  childN:
    attr_tst: child N
    attr_val: 999
top_hash_anchor: &topHashAnchor
  key1: value 1
  key2: value 2
  key3: value 3
  key_complex:
    <<: *subHashAnchor

namespaced::hash:
  with_array:
    - one
    - two
    - three
  with_array_of_hashes:
    - id: 1
      name: ichi
      ref: 1.4142135623
    - id: 2
      name: ni
      ref: 2.7182818284
    - id: 3
      name: san
      ref: 3.1415926535
  with_array_alias: *topArrayAnchor
  with_hash_alias:
    <<: *topHashAnchor
    key3: value 3.2
    key4: value 4.0
    key_complex:
      <<: *subHashAnchor
      child4:
        attr_tst: child 4
        attr_val: 400
      child5:
        attr_tst: child 5
        attr_val: 500
      childN:
        attr_tst: child N2
        attr_val: 0
  'and.with.dotted.child':
    that: has it's own
    child: nodes

complex:
  array_of_hashes:
    - id: 1
      key: child1
      name: one
      children:
        first: ichi
        second: ni
        third: san
    - id: 2
      key: child2
      name: two
      children:
        first: shi
        second: go
        third: roku
    - id: 3
      key: child3
      name: three
      children:
        first: shichi
        second: hachi
        third: ku
    - id: 4
      key: child4
      name: four
      children:
        first: ju
        second: ju ichi
        third: ji ni
  hash_of_hashes:
    child1:
      id: 1
      name: one
      children:
        first: ichi
        second: ni
        third: san
    child2:
      id: 2
      name: two
      children:
        first: shi
        second: go
        third: roku
    child3:
      id: 3
      name: three
      children:
        first: shichi
        second: hachi
        third: ku
    child4:
      id: 4
      name: four
      children:
        first: ju
        second: ju ichi
        third: ji ni
"""
        yaml = YAML()
        yaml_data = yaml.load(data)
        yaml.dump(yaml_data, sys.stdout)

def test_newlines_before_anchored_list_comments(capsys):
    yamldoc = """---
aliases:
  # First-element comment
  - &firstEntry First entry
  # Second-element comment
  - &secondEntry Second entry

  # Third-element comment is
  # a multi-line value
  - &thirdEntry Third entry
"""

    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.explicit_start = True
    yaml.preserve_quotes = True
    yaml.width = sys.maxsize
    yamldata = yaml.load(yamldoc)
    yaml.dump(yamldata, sys.stdout)

    console = capsys.readouterr()
    assert yamldoc == console.out

def test_newlines_between_anchored_multiline_list_elements(capsys):
    yamldoc = """---
aliases:
  # Folded-element comment
  # for a multi-line value
  - &FoldedEntry >
    THIS IS A
    FOLDED, MULTI-LINE
    VALUE

  # Literal-element comment
  # for a multi-line value
  - &literalEntry |
    THIS IS A
    LITERAL, MULTI-LINE
    VALUE

  # Plain-element comment
  - &plainEntry Plain entry
"""

    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.explicit_start = True
    yaml.preserve_quotes = True
    yaml.width = sys.maxsize
    yamldata = yaml.load(yamldoc)
    yaml.dump(yamldata, sys.stdout)

    console = capsys.readouterr()
    assert yamldoc == console.out
