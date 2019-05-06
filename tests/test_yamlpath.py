import pytest

from types import SimpleNamespace

from ruamel.yaml import YAML

from yamlpath import YAMLPath
from yamlpath.exceptions import YAMLPathException

from yamlpath.wrappers import ConsolePrinter

@pytest.fixture
def yamlpath():
    """Returns a YAMLPath with a quiet logger."""
    args = SimpleNamespace(verbose=False, quiet=True, debug=False)
    logger = ConsolePrinter(args)
    return YAMLPath(logger)

@pytest.fixture
def yamldata():
    yaml = YAML()
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
    - id: 2
      name: ni
    - id: 3
      name: san
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
    return yaml.load(data)

def test_empty_get_nodes(yamlpath, yamldata):
    for node in yamlpath.get_nodes(yamldata, None):
        assert node == None

    for node in yamlpath.get_nodes(yamldata, None, mustexist=True):
        assert node == None

    for node in yamlpath.get_nodes(None, "top_scalar"):
        assert node == None

    for node in yamlpath.get_nodes(None, "top_scalar", mustexist=True):
        assert node == None

@pytest.mark.parametrize("search,compare", [
    ("aliases[&test_scalarstring]", "This is a scalar string."),
    ("aliases[&test_foldedstring]", "This is a folded multi-line string."),
    ("aliases[&test_literalstring]", "This is a\nliteral multi-line\nstring."),
    ("top_scalar", "value"),
    ("top_alias", "This is a scalar string."),
    ("top_array_anchor[0]", "This is a scalar string."),
    ("top_array_anchor[1]", "An original value"),
    ("top_array_anchor[2]", "This is a folded multi-line string."),
    ("top_array_anchor[3]", "Another original value"),
    ("&topArrayAnchor[0]", "This is a scalar string."),
    ("&topArrayAnchor[1]", "An original value"),
    ("&topArrayAnchor[2]", "This is a folded multi-line string."),
    ("&topArrayAnchor[3]", "Another original value"),
    ("sub_hash_anchor.child1.attr_tst", "child 1"),
    ("sub_hash_anchor.child1.attr_val", 100),
    ("sub_hash_anchor.child2.attr_tst", "child 2"),
    ("sub_hash_anchor.child2.attr_val", 200),
    ("sub_hash_anchor.child3.attr_tst", "child 3"),
    ("sub_hash_anchor.child3.attr_val", 300),
    ("sub_hash_anchor.childN.attr_tst", "child N"),
    ("sub_hash_anchor.childN.attr_val", 999),
    ("&subHashAnchor.child1.attr_tst", "child 1"),
    ("&subHashAnchor.child1.attr_val", 100),
    ("&subHashAnchor.child2.attr_tst", "child 2"),
    ("&subHashAnchor.child2.attr_val", 200),
    ("&subHashAnchor.child3.attr_tst", "child 3"),
    ("&subHashAnchor.child3.attr_val", 300),
    ("&subHashAnchor.childN.attr_tst", "child N"),
    ("&subHashAnchor.childN.attr_val", 999),
    ("top_hash_anchor.key1", "value 1"),
    ("top_hash_anchor.key2", "value 2"),
    ("top_hash_anchor.key3", "value 3"),
    ("top_hash_anchor.key_complex.child1.attr_tst", "child 1"),
    ("top_hash_anchor.key_complex.child1.attr_val", 100),
    ("top_hash_anchor.key_complex.child2.attr_tst", "child 2"),
    ("top_hash_anchor.key_complex.child2.attr_val", 200),
    ("top_hash_anchor.key_complex.child3.attr_tst", "child 3"),
    ("top_hash_anchor.key_complex.child3.attr_val", 300),
    ("top_hash_anchor.key_complex.childN.attr_tst", "child N"),
    ("top_hash_anchor.key_complex.childN.attr_val", 999),
    ("&topHashAnchor.key1", "value 1"),
    ("&topHashAnchor.key2", "value 2"),
    ("&topHashAnchor.key3", "value 3"),
    ("&topHashAnchor.key_complex.child1.attr_tst", "child 1"),
    ("&topHashAnchor.key_complex.child1.attr_val", 100),
    ("&topHashAnchor.key_complex.child2.attr_tst", "child 2"),
    ("&topHashAnchor.key_complex.child2.attr_val", 200),
    ("&topHashAnchor.key_complex.child3.attr_tst", "child 3"),
    ("&topHashAnchor.key_complex.child3.attr_val", 300),
    ("&topHashAnchor.key_complex.childN.attr_tst", "child N"),
    ("&topHashAnchor.key_complex.childN.attr_val", 999),
    ("namespaced::hash.with_array[0]", "one"),
    ("namespaced::hash.with_array[1]", "two"),
    ("namespaced::hash.with_array[2]", "three"),
    ("namespaced::hash.with_array_of_hashes[0].id", 1),
    ("namespaced::hash.with_array_of_hashes[0].name", "ichi"),
    ("namespaced::hash.with_array_of_hashes[1].id", 2),
    ("namespaced::hash.with_array_of_hashes[1].name", "ni"),
    ("namespaced::hash.with_array_of_hashes[2].id", 3),
    ("namespaced::hash.with_array_of_hashes[2].name", "san"),
    ("namespaced::hash.with_array_alias[0]", "This is a scalar string."),
    ("namespaced::hash.with_array_alias[1]", "An original value"),
    ("namespaced::hash.with_array_alias[2]", "This is a folded multi-line string."),
    ("namespaced::hash.with_array_alias[3]", "Another original value"),
    ("namespaced::hash.with_hash_alias.key1", "value 1"),
    ("namespaced::hash.with_hash_alias.key2", "value 2"),
    ("namespaced::hash.with_hash_alias.key3", "value 3.2"),
    ("namespaced::hash.with_hash_alias.key4", "value 4.0"),
    ("namespaced::hash.with_hash_alias.key_complex.child1.attr_tst", "child 1"),
    ("namespaced::hash.with_hash_alias.key_complex.child1.attr_val", 100),
    ("namespaced::hash.with_hash_alias.key_complex.child2.attr_tst", "child 2"),
    ("namespaced::hash.with_hash_alias.key_complex.child2.attr_val", 200),
    ("namespaced::hash.with_hash_alias.key_complex.child3.attr_tst", "child 3"),
    ("namespaced::hash.with_hash_alias.key_complex.child3.attr_val", 300),
    ("namespaced::hash.with_hash_alias.key_complex.child4.attr_tst", "child 4"),
    ("namespaced::hash.with_hash_alias.key_complex.child4.attr_val", 400),
    ("namespaced::hash.with_hash_alias.key_complex.child5.attr_tst", "child 5"),
    ("namespaced::hash.with_hash_alias.key_complex.child5.attr_val", 500),
    ("namespaced::hash.with_hash_alias.key_complex.childN.attr_tst", "child N2"),
    ("namespaced::hash.with_hash_alias.key_complex.childN.attr_val", 0),
    (r"namespaced::hash.and\.with\.dotted\.child.that", "has it's own"),
    (r"namespaced::hash.and\.with\.dotted\.child.child", "nodes"),
    ("namespaced::hash.with_array_of_hashes[id=1].name", "ichi"),
    ("namespaced::hash.with_array_of_hashes[name=ichi].id", 1),
    ("namespaced::hash.with_array_of_hashes[name='ichi'].id", 1),
    ("namespaced::hash.with_array_of_hashes[id=2].name", "ni"),
    ("namespaced::hash.with_array_of_hashes[name=ni].id", 2),
    ("namespaced::hash.with_array_of_hashes[name='ni'].id", 2),
    ("namespaced::hash.with_array_of_hashes[id=3].name", "san"),
    ("namespaced::hash.with_array_of_hashes[name=san].id", 3),
    ("namespaced::hash.with_array_of_hashes[name='san'].id", 3),
    ("namespaced::hash.with_array_of_hashes[name^ich].id", 1),
    ("namespaced::hash.with_array_of_hashes[name$n].id", 3),
    (r"namespaced::hash.with_array_of_hashes[name%a].id", 3),
    ("namespaced::hash.with_array_of_hashes[id<2].name", "ichi"),
    ("namespaced::hash.with_array_of_hashes[id>2].name", "san"),
    ("namespaced::hash.with_array_of_hashes[id<=1].name", "ichi"),
    ("namespaced::hash.with_array_of_hashes[id>=3].name", "san"),
    (r"namespaced::hash.with_array_of_hashes[name!%i].id", 3),
])
def test_happy_singular_get_leaf_nodes(yamlpath, yamldata, search, compare):
    for node in yamlpath.get_nodes(yamldata, search):
        assert node == compare

    for node in yamlpath.get_nodes(yamldata, search, mustexist=True):
        assert node == compare

@pytest.mark.parametrize("search,compare", [
    ("namespaced::hash.with_array_of_hashes[id<3].name", ["ichi", "ni"]),
    ("namespaced::hash.with_array_of_hashes[id<3].id", [1, 2]),
    ("namespaced::hash.with_array_of_hashes[id>=2].id", [2, 3]),
    ("namespaced::hash.with_array_of_hashes[id>=2].name", ["ni", "san"]),
    ("namespaced::hash.with_array_of_hashes[!id>=2].name", ["ichi"]),
    ("namespaced::hash.with_array_of_hashes[!id>=2].id", [1]),
    ("complex.hash_of_hashes[.^child].children.first", ["ichi", "shi", "shichi", "ju"]),
    (r"complex.hash_of_hashes[.^child].children[first%ichi]", ["ichi", "shichi"]),
])
def test_happy_multiple_get_nodes(yamlpath, yamldata, search, compare):
    matches = []
    for node in yamlpath.get_nodes(yamldata, search):
        matches.append(node)
    assert matches == compare

    matches = []
    for node in yamlpath.get_nodes(yamldata, search, mustexist=True):
        matches.append(node)
    assert matches == compare

@pytest.mark.parametrize("search,compare", [
    ("aliases[&doesNotExist]", "This Anchor does not exist!"),
    ("top_fake_scalar", "No such value."),
    ("top_array_anchor[4]", "No such index."),
])
def test_unhappy_singular_get_leaf_nodes(yamlpath, yamldata, search, compare):
    with pytest.raises(YAMLPathException):
        for node in yamlpath.get_nodes(yamldata, search, mustexist=True):
            node == compare
