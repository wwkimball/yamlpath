import pytest

from types import SimpleNamespace
from collections import deque

from yamlpath.parser import Parser
from yamlpath.exceptions import YAMLPathException
from yamlpath.wrappers import ConsolePrinter

@pytest.fixture
def parser():
    """Returns a Parser with a quiet logger."""
    args = SimpleNamespace(verbose=False, quiet=True, debug=False)
    logger = ConsolePrinter(args)
    return Parser(logger)

def test_empty_str_path(parser):
    assert parser.str_path("") == ""

@pytest.mark.parametrize("yaml_path,stringified", [
    ("aliases[&anchor]", "aliases[&anchor]"),
    ("a l i a s e s [ & a n c h o r ]", "aliases[&anchor]"),
    ("aliases[2]", "aliases[2]"),
    ("namespaced::hash.sub", "namespaced::hash.sub"),
    ("db_creds[2].pass.encrypted", "db_creds[2].pass.encrypted"),
    ("lookup::credentials.backend.database.password.hash", "lookup::credentials.backend.database.password.hash"),
    ("does::not[7].exist[4]", "does::not[7].exist[4]"),
    ("messy.messy.'dotted.sub.key'.child", r"messy.messy.dotted\.sub\.key.child"),
    ('some[search="Name Here"]', r"some[search=Name\ Here]"),
    ('some[search=="Name Here"]', r"some[search=Name\ Here]"),
    ('some[search^"Name "]', r"some[search^Name\ ]"),
    ('some[search$" Here"]', r"some[search$\ Here]"),
    ('some[search%"e H"]', r"some[search%e\ H]"),
    ('some[search>50]', "some[search>50]"),
    ('some[search<42]', "some[search<42]"),
    ('some[search>=5280]', "some[search>=5280]"),
    ('some[search<=14000]', "some[search<=14000]"),
    ('some[search = "Name Here"]', r"some[search=Name\ Here]"),
    ('some[search == "Name Here"]', r"some[search=Name\ Here]"),
    ('some[search ^ "Name "]', r"some[search^Name\ ]"),
    ('some[search $ " Here"]', r"some[search$\ Here]"),
    ('some[search % "e H"]', r"some[search%e\ H]"),
    ('some[search > 50]', "some[search>50]"),
    ('some[search < 42]', "some[search<42]"),
    ('some[search >= 5280]', "some[search>=5280]"),
    ('some[search <= 14000]', "some[search<=14000]"),
    ('some[search != "Name Here"]', r"some[search!=Name\ Here]"),
    ('some[search !== "Name Here"]', r"some[search!=Name\ Here]"),
    ('some[search !^ "Name "]', r"some[search!^Name\ ]"),
    ('some[search !$ " Here"]', r"some[search!$\ Here]"),
    ('some[search !% "e H"]', r"some[search!%e\ H]"),
    ('some[search !> 50]', "some[search!>50]"),
    ('some[search !< 42]', "some[search!<42]"),
    ('some[search !>= 5280]', "some[search!>=5280]"),
    ('some[search !<= 14000]', "some[search!<=14000]"),
    ('some[!search == "Name Here"]', r"some[search!=Name\ Here]"),
    ('some[!search ^ "Name "]', r"some[search!^Name\ ]"),
    ('some[!search $ " Here"]', r"some[search!$\ Here]"),
    ('some[!search % "e H"]', r"some[search!%e\ H]"),
    ('some[!search > 50]', "some[search!>50]"),
    ('some[!search < 42]', "some[search!<42]"),
    ('some[!search >= 5280]', "some[search!>=5280]"),
    ('some[!search <= 14000]', "some[search!<=14000]"),
    (r'some[search =~ /^\d{5}$/]', r'some[search=~/^\d{5}$/]'),
    ('key\\with\\slashes', 'key\\with\\slashes'),
    ('"aliases[&some_name]"', r'aliases\[\&some_name\]'),
    ('&topArrayAnchor[0]', '&topArrayAnchor[0]'),
    ('"&topArrayAnchor[0]"', r'\&topArrayAnchor\[0\]'),
    ('"&subHashAnchor.child1.attr_tst"', r'\&subHashAnchor\.child1\.attr_tst'),
    ("'&topArrayAnchor[!.=~/[Oo]riginal/]'", r"\&topArrayAnchor\[!\.=~/\[Oo\]riginal/\]"),
])
def test_happy_str_path_translations(parser, yaml_path, stringified):
    assert parser.str_path(yaml_path) == stringified

def test_happy_parse_path_list_to_deque(parser):
    assert isinstance(parser.parse_path(["item1", "item2"]), deque)

@pytest.mark.parametrize("yaml_path", [
    ('some[search ^^ "Name "]'),
    ('some[search $$ " Here"]'),
    (r'some[search %% "e H"]'),
    ('some[search >> 50]'),
    ('some[search << 42]'),
    ('some[search >>== 5280]'),
    ('some[search <<== 14000]'),
    ('some[search !!= "Name Here"]'),
    ('some[search !!== "Name Here"]'),
    ('some[search !!^ "Name "]'),
    ('some[search !!$ " Here"]'),
    ('some[search !!% "e H"]'),
    ('some[search !!> 50]'),
    ('some[search !!< 42]'),
    ('some[search !!>= 5280]'),
    ('some[search !!<= 14000]'),
    ('some[!search != "Name Here"]'),
    ('some[!search !== "Name Here"]'),
    ('some[!search !^ "Name "]'),
    ('some[!search !$ " Here"]'),
    ('some[!search !% "e H"]'),
    ('some[!search !> 50]'),
    ('some[!search !< 42]'),
    ('some[!search !>= 5280]'),
    ('some[!search !<= 14000]'),
    ('some[= "missing LHS operand"]'),
    ('some[search ~ "meaningless tilde"]'),
    ('some[search = "unterminated demarcation]'),
    ('some[search =~ /unterminated RegEx]'),
    ('some[search ^= "meaningless operator"]'),
    ('array[4F]'),
    ({}),
])
def test_uphappy_str_path_translations(parser, yaml_path):
    with pytest.raises(YAMLPathException):
        parser.str_path(yaml_path)

@pytest.mark.parametrize("pathsep,yaml_path,stringified", [
    ('.', "some.hash.key", "some.hash.key"),
    ('/', "/some/hash/key", "/some/hash/key"),
    ('.', "/some/hash/key", "some.hash.key"),
    ('/', "some.hash.key", "/some/hash/key"),
])
def test_pathsep(parser, pathsep, yaml_path, stringified):
    assert parser.str_path(yaml_path, pathsep=pathsep) == stringified
