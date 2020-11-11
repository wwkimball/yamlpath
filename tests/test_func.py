import pytest

from types import SimpleNamespace

from ruamel.yaml.comments import CommentedSeq, CommentedMap
from ruamel.yaml.scalarstring import PlainScalarString
from ruamel.yaml.scalarbool import ScalarBoolean
from ruamel.yaml.scalarfloat import ScalarFloat
from ruamel.yaml.scalarint import ScalarInt

from yamlpath.enums import AnchorMatches, PathSearchMethods, YAMLValueFormats
from yamlpath.types import PathAttributes
from yamlpath.path import SearchTerms
from yamlpath import YAMLPath
from yamlpath.func import (
    append_list_element,
    build_next_node,
    clone_node,
    create_searchterms_from_pathattributes,
    ensure_escaped,
    escape_path_section,
    get_node_anchor,
    get_yaml_data,
    get_yaml_editor,
    get_yaml_multidoc_data,
    make_float_node,
    make_new_node,
    search_anchor,
    search_matches,
    stringify_dates,
    wrap_type,
)

from tests.conftest import create_temp_yaml_file, quiet_logger


@pytest.fixture
def force_ruamel_load_keyboardinterrupt(monkeypatch):
    from ruamel.yaml import YAML as break_class

    def fake_load(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(break_class, "load", fake_load)
    monkeypatch.setattr(break_class, "load_all", fake_load)

class Test_func():
    ###
    # build_next_node
    ###
    def test_build_next_node(self):
        yaml_path = YAMLPath("/test/path")
        next_node = build_next_node(yaml_path, 0)
        assert isinstance(next_node, dict)

    ###
    # get_yaml_editor
    ###
    def test_get_yaml_editor(self):
        assert get_yaml_editor()

    def test_get_json_editor(self):
        assert get_yaml_editor(explode_aliases=True)


    ###
    # get_yaml_data
    ###
    def test_get_yaml_data_keyboardinterrupt_error(
        self, capsys, quiet_logger, tmp_path_factory,
        force_ruamel_load_keyboardinterrupt
    ):
        yp = get_yaml_editor()
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        (yaml_data, doc_loaded) = get_yaml_data(yp, quiet_logger, yaml_file)
        assert doc_loaded == False
        captured = capsys.readouterr()
        assert -1 < captured.err.find("keyboard interrupt")

    def test_get_yaml_data_filenotfound_error(
        self, capsys, quiet_logger,
        force_ruamel_load_keyboardinterrupt
    ):
        yp = get_yaml_editor()
        (yaml_data, doc_loaded) = get_yaml_data(yp, quiet_logger, "no-such.file")
        assert doc_loaded == False
        captured = capsys.readouterr()
        assert -1 < captured.err.find("File not found")

    def test_get_yaml_data_parser_error(
        self, capsys, quiet_logger,
        imparsible_yaml_file
    ):
        yp = get_yaml_editor()
        (yaml_data, doc_loaded) = get_yaml_data(yp, quiet_logger, imparsible_yaml_file)
        assert doc_loaded == False
        captured = capsys.readouterr()
        assert -1 < captured.err.find("YAML parsing error")

    def test_get_yaml_data_composition_error(
        self, capsys, quiet_logger,
        badcmp_yaml_file
    ):
        yp = get_yaml_editor()
        (yaml_data, doc_loaded) = get_yaml_data(yp, quiet_logger, badcmp_yaml_file)
        assert doc_loaded == False
        captured = capsys.readouterr()
        assert -1 < captured.err.find("YAML composition error")

    def test_get_yaml_data_construction_error(
        self, capsys, quiet_logger, tmp_path_factory
    ):
        yp = get_yaml_editor()
        content = """---
        missing:
          <<:
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        (yaml_data, doc_loaded) = get_yaml_data(yp, quiet_logger, yaml_file)
        assert doc_loaded == False
        captured = capsys.readouterr()
        assert -1 < captured.err.find("YAML construction error")

    def test_get_yaml_data_syntax_error(
        self, capsys, quiet_logger, tmp_path_factory, badsyntax_yaml_file
    ):
        yp = get_yaml_editor()
        (yaml_data, doc_loaded) = get_yaml_data(yp, quiet_logger, badsyntax_yaml_file)
        assert doc_loaded == False
        captured = capsys.readouterr()
        assert -1 < captured.err.find("YAML syntax error")

    def test_get_yaml_data_duplicatekey_error(
        self, capsys, quiet_logger, tmp_path_factory
    ):
        yp = get_yaml_editor()
        content = """---
        key: value1
        key: value2
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        (yaml_data, doc_loaded) = get_yaml_data(yp, quiet_logger, yaml_file)
        assert doc_loaded == False
        captured = capsys.readouterr()
        assert -1 < captured.err.find("Duplicate Hash key detected")

    def test_get_yaml_data_duplicateanchor_error(
        self, capsys, quiet_logger, tmp_path_factory
    ):
        yp = get_yaml_editor()
        content = """---
        aliases:
          - &anchor value1
          - &anchor value2
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        (yaml_data, doc_loaded) = get_yaml_data(yp, quiet_logger, yaml_file)
        assert doc_loaded == False
        captured = capsys.readouterr()
        assert -1 < captured.err.find("Duplicate YAML Anchor detected")


    ###
    # get_yaml_multidoc_data
    ###
    def test_get_yaml_multidoc_data_keyboardinterrupt_error(
        self, capsys, quiet_logger, tmp_path_factory,
        force_ruamel_load_keyboardinterrupt
    ):
        yp = get_yaml_editor()
        content = """---
        no: ''
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        docs_yielded = 0
        for doc in get_yaml_multidoc_data(yp, quiet_logger, yaml_file):
            if not doc and not isinstance(doc, bool):
                docs_yielded += 1
        assert docs_yielded == 0
        captured = capsys.readouterr()
        assert -1 < captured.err.find("keyboard interrupt")

    def test_get_yaml_multidoc_data_filenotfound_error(
        self, capsys, quiet_logger,
        force_ruamel_load_keyboardinterrupt
    ):
        yp = get_yaml_editor()
        docs_yielded = 0
        for doc in get_yaml_multidoc_data(yp, quiet_logger, "no-such.file"):
            if not doc and not isinstance(doc, bool):
                docs_yielded += 1
        assert docs_yielded == 0
        captured = capsys.readouterr()
        assert -1 < captured.err.find("File not found")

    def test_get_yaml_multidoc_data_parser_error(
        self, capsys, quiet_logger,
        imparsible_yaml_file
    ):
        yp = get_yaml_editor()
        docs_yielded = 0
        for doc in get_yaml_multidoc_data(yp, quiet_logger, imparsible_yaml_file):
            if not doc and not isinstance(doc, bool):
                docs_yielded += 1
        assert docs_yielded == 0
        captured = capsys.readouterr()
        assert -1 < captured.err.find("YAML parsing error")

    def test_get_yaml_multidoc_data_composition_error(
        self, capsys, quiet_logger,
        badcmp_yaml_file
    ):
        yp = get_yaml_editor()
        docs_yielded = 0
        for doc in get_yaml_multidoc_data(yp, quiet_logger, badcmp_yaml_file):
            if not doc and not isinstance(doc, bool):
                docs_yielded += 1
        assert docs_yielded == 0
        captured = capsys.readouterr()
        assert -1 < captured.err.find("YAML composition error")

    def test_get_yaml_multidoc_data_construction_error(
        self, capsys, quiet_logger, tmp_path_factory
    ):
        yp = get_yaml_editor()
        content = """---
        missing:
          <<:
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        docs_yielded = 0
        for doc in get_yaml_multidoc_data(yp, quiet_logger, yaml_file):
            if not doc and not isinstance(doc, bool):
                docs_yielded += 1
        assert docs_yielded == 0
        captured = capsys.readouterr()
        assert -1 < captured.err.find("YAML construction error")

    def test_get_yaml_multidoc_data_syntax_error(
        self, capsys, quiet_logger, tmp_path_factory, badsyntax_yaml_file
    ):
        yp = get_yaml_editor()
        docs_yielded = 0
        for doc in get_yaml_multidoc_data(yp, quiet_logger, badsyntax_yaml_file):
            if not doc and not isinstance(doc, bool):
                docs_yielded += 1
        assert docs_yielded == 0
        captured = capsys.readouterr()
        assert -1 < captured.err.find("YAML syntax error")

    def test_get_yaml_multidoc_data_duplicatekey_error(
        self, capsys, quiet_logger, tmp_path_factory
    ):
        yp = get_yaml_editor()
        content = """---
        key: value1
        key: value2
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        docs_yielded = 0
        for doc in get_yaml_multidoc_data(yp, quiet_logger, yaml_file):
            if not doc and not isinstance(doc, bool):
                docs_yielded += 1
        assert docs_yielded == 0
        captured = capsys.readouterr()
        assert -1 < captured.err.find("Duplicate Hash key detected")

    def test_get_yaml_multidoc_data_duplicateanchor_error(
        self, capsys, quiet_logger, tmp_path_factory
    ):
        yp = get_yaml_editor()
        content = """---
        aliases:
          - &anchor value1
          - &anchor value2
        """
        yaml_file = create_temp_yaml_file(tmp_path_factory, content)
        docs_yielded = 0
        for doc in get_yaml_multidoc_data(yp, quiet_logger, yaml_file):
            if not doc and not isinstance(doc, bool):
                docs_yielded += 1
        assert docs_yielded == 0
        captured = capsys.readouterr()
        assert -1 < captured.err.find("Duplicate YAML Anchor detected")


    ###
    # append_list_element
    ###
    def test_anchorless_list_element_error(self):
        with pytest.raises(ValueError) as ex:
            append_list_element({}, YAMLPath("foo"), "bar")
        assert -1 < str(ex.value).find("Impossible to add an Anchor")


    ###
    # wrap_type
    ###
    @pytest.mark.parametrize("value,checktype", [
        ([], CommentedSeq),
        ({}, CommentedMap),
        ("", PlainScalarString),
        (1, ScalarInt),
        (1.1, ScalarFloat),
        (True, ScalarBoolean),
        (SimpleNamespace(), SimpleNamespace),
    ])
    def test_wrap_type(self, value, checktype):
        assert isinstance(wrap_type(value), checktype)


    ###
    # clone_node
    ###
    def test_clone_node(self):
        test_val = "test"
        assert test_val == clone_node(test_val)

        anchor_val = PlainScalarString(test_val, anchor="anchor")
        assert anchor_val == clone_node(anchor_val)


    ###
    # make_new_node
    ###
    @pytest.mark.parametrize("source,value,check,vformat", [
        ("", " ", " ", YAMLValueFormats.BARE),
        ("", '" "', '" "', YAMLValueFormats.DQUOTE),
        ("", "' '", "' '", YAMLValueFormats.SQUOTE),
        ("", " ", " ", YAMLValueFormats.FOLDED),
        ("", " ", " ", YAMLValueFormats.LITERAL),
        (True, False, False, YAMLValueFormats.BOOLEAN),
        (True, "no", False, YAMLValueFormats.BOOLEAN),
        (1.1, 1.2, 1.2, YAMLValueFormats.FLOAT),
        (ScalarFloat(1.1, anchor="test"), 1.2, 1.2, YAMLValueFormats.FLOAT),
        (1, 2, 2, YAMLValueFormats.INT),
    ])
    def test_make_new_node(self, source, value, check, vformat):
        assert check == make_new_node(source, value, vformat)

    @pytest.mark.parametrize("source,value,vformat,etype,estr", [
        ("", " ", "DNF", NameError, "Unknown YAML Value Format"),
        (1.1, "4F", YAMLValueFormats.FLOAT, ValueError, "cannot be cast to a floating-point number"),
        (1, "4F", YAMLValueFormats.INT, ValueError, "cannot be cast to an integer number"),
    ])
    def test_make_new_node_errors(self, source, value, vformat, etype, estr):
        with pytest.raises(etype) as ex:
            value == make_new_node(source, value, vformat)
        assert -1 < str(ex.value).find(estr)


    ###
    # ensure_escaped
    ###
    def test_ensure_escaped(self):
        assert r"\(\)" == ensure_escaped("()", "(", ")")


    ###
    # escape_path_section
    ###
    def test_escape_path_section(self):
        from yamlpath.enums.pathseperators import PathSeperators
        assert r"a\\b\.c\(\)\[\]\^\$\%\ \'\"" == escape_path_section("a\\b.c()[]^$% '\"", PathSeperators.DOT)


    ###
    # create_searchterms_from_pathattributes
    ###
    def test_create_searchterms_from_pathattributes(self):
        st = SearchTerms(False, PathSearchMethods.EQUALS, ".", "key")
        assert str(st) == str(create_searchterms_from_pathattributes(st))

        with pytest.raises(AttributeError):
            _ = create_searchterms_from_pathattributes("nothing-to-see-here")


    ###
    # search_anchor
    ###
    def test_search_anchor(self):
        anchor_value = "anchor_name"
        node = PlainScalarString("anchored value", anchor=anchor_value)
        terms = SearchTerms(False, PathSearchMethods.CONTAINS, ".", "name")
        seen_anchors = []
        search_anchors = True
        include_aliases = True
        assert search_anchor(node, terms, seen_anchors, search_anchors=search_anchors, include_aliases=include_aliases) == AnchorMatches.MATCH


    ###
    # search_matches
    ###
    def test_search_matches(self):
        method = PathSearchMethods.CONTAINS
        needle = "a"
        haystack = "parents"
        assert search_matches(method, needle, haystack) == True


    ###
    # stringify_dates
    ###
    def test_stringify_dates(self):
        from datetime import date
        yaml_safe_data = CommentedMap({ "string": "Value", "number": 1, "date": date(2020, 10, 19) })
        json_safe_data = { "string": "Value", "number": 1, "date": "2020-10-19" }
        assert stringify_dates(yaml_safe_data) == json_safe_data


    ###
    # make_float_node
    ###
    def test_make_float(self):
        assert isinstance(make_float_node(3.14159265385), ScalarFloat)


    ###
    # get_node_anchor
    ###
    def test_get_node_anchor(self):
        anchor_value = "anchored"
        node = PlainScalarString("value")
        node.yaml_set_anchor(anchor_value)
        assert get_node_anchor(node) == anchor_value
