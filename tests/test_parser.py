import pytest

from types import SimpleNamespace

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

# Happy searches
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
    ('some[search !!= "Name Here"]', r"some[search!=Name\ Here]"),
    ('some[search !== "Name Here"]', r"some[search!=Name\ Here]"),
    ('some[search !!== "Name Here"]', r"some[search!=Name\ Here]"),
    ('some[search !^ "Name "]', r"some[search!^Name\ ]"),
    ('some[search !!^ "Name "]', r"some[search!^Name\ ]"),
    ('some[search !$ " Here"]', r"some[search!$\ Here]"),
    ('some[search !!$ " Here"]', r"some[search!$\ Here]"),
    ('some[search !% "e H"]', r"some[search!%e\ H]"),
    ('some[search !!% "e H"]', r"some[search!%e\ H]"),
    ('some[search !> 50]', "some[search!>50]"),
    ('some[search !!> 50]', "some[search!>50]"),
    ('some[search !< 42]', "some[search!<42]"),
    ('some[search !!< 42]', "some[search!<42]"),
    ('some[search !>= 5280]', "some[search!>=5280]"),
    ('some[search !!>= 5280]', "some[search!>=5280]"),
    ('some[search !<= 14000]', "some[search!<=14000]"),
    ('some[search !!<= 14000]', "some[search!<=14000]"),
    ('some[!search == "Name Here"]', r"some[search!=Name\ Here]"),
    ('some[!search ^ "Name "]', r"some[search!^Name\ ]"),
    ('some[!search $ " Here"]', r"some[search!$\ Here]"),
    ('some[!search % "e H"]', r"some[search!%e\ H]"),
    ('some[!search > 50]', "some[search!>50]"),
    ('some[!search < 42]', "some[search!<42]"),
    ('some[!search >= 5280]', "some[search!>=5280]"),
    ('some[!search <= 14000]', "some[search!<=14000]"),
])
def test_happy_str_path_translations(parser, yaml_path, stringified):
    assert parser.str_path(yaml_path) == stringified

# Unhappy searches
@pytest.mark.parametrize("yaml_path,stringified", [
    ('some[search ^^ "Name "]', r"some[search^Name\ ]"),
    ('some[search $$ " Here"]', r"some[search$\ Here]"),
    (r'some[search %% "e H"]', r"some[search%e\ H]"),
    ('some[search >> 50]', "some[search>50]"),
    ('some[search << 42]', "some[search<42]"),
    ('some[search >>== 5280]', "some[search>=5280]"),
    ('some[search <<== 14000]', "some[search<=14000]"),
])
def test_uphappy_str_path_translations(parser, yaml_path, stringified):
    with pytest.raises(YAMLPathException):
        parser.str_path(yaml_path) == stringified
