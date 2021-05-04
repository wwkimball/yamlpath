import pytest

from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import PathSegmentTypes, PathSeperators
from yamlpath import YAMLPath

class Test_YAMLPath():
    """Tests for the Path class."""

    @pytest.mark.parametrize("yamlpath,pathsep,output", [
        (YAMLPath(""), PathSeperators.AUTO, ""),
        (YAMLPath("abc"), PathSeperators.AUTO, "abc"),
        ("abc", PathSeperators.AUTO, "abc"),
        ("/abc", PathSeperators.AUTO, "/abc"),
        ("abc.bcd", PathSeperators.AUTO, "abc.bcd"),
        ("/abc[1]", PathSeperators.AUTO, "/abc[1]"),
        ("&abc", PathSeperators.AUTO, "&abc"),
        ("/abc[&def]", PathSeperators.AUTO, "/abc[&def]"),
        ("abc[!def^ghi]", PathSeperators.AUTO, "abc[def!^ghi]"),
        ("/(abc)[0]", PathSeperators.AUTO, "/(abc)[0]"),
        ("abc[def =~ /ghi/]", PathSeperators.AUTO, "abc[def=~/ghi/]"),
        ("/(abc)+(def)-(ghi)", PathSeperators.AUTO, "/(abc)+(def)-(ghi)"),
        (r"abc.'def.g\"h\"i'", PathSeperators.AUTO, r"abc.def\.g\"h\"i"),
        ("/abc[def>=1]", PathSeperators.AUTO, "/abc[def>=1]"),
        ("abc[def<=10]", PathSeperators.AUTO, "abc[def<=10]"),
        ("/abc[def==1]", PathSeperators.AUTO, "/abc[def=1]"),
        ("abc[def$ghi]", PathSeperators.AUTO, "abc[def$ghi]"),
        ("/abc[def%1]", PathSeperators.AUTO, "/abc[def%1]"),
        ("abc[def%'ghi']", PathSeperators.AUTO, "abc[def%ghi]"),
        ("abc*", PathSeperators.AUTO, "[.^abc]"),
        ("*def", PathSeperators.AUTO, "[.$def]"),
        ("a*f", PathSeperators.AUTO, "[.=~/^a.*f$/]"),
        ("a*f*z", PathSeperators.AUTO, "[.=~/^a.*f.*z$/]"),
        ("a*f*z*", PathSeperators.AUTO, "[.=~/^a.*f.*z.*$/]"),
        ("*", PathSeperators.AUTO, "*"),
        ("*.*", PathSeperators.AUTO, "*.*"),
        ("**", PathSeperators.AUTO, "**"),
        ("/**/def", PathSeperators.AUTO, "/**/def"),
        ("abc.**.def", PathSeperators.AUTO, "abc.**.def"),
    ])
    def test_str(self, yamlpath, pathsep, output):
        # Test twice to include cache hits
        testpath = YAMLPath(yamlpath, pathsep)
        assert output == str(testpath) == str(testpath)

    def test_repr(self):
        assert repr(YAMLPath("abc.123")) == "YAMLPath('abc.123', '.')"

    @pytest.mark.parametrize("yamlpath,length", [
        ("", 0),
        ("/abc", 1),
        ("abc.def", 2),
        ("abc[def%'ghi'].jkl", 3),
    ])
    def test_len(self, yamlpath, length):
        assert len(YAMLPath(yamlpath)) == length

    @pytest.mark.parametrize("lhs,rhs,iseq", [
        (YAMLPath(""), YAMLPath(""), True),
        (YAMLPath(""), "", True),
        ("", YAMLPath(""), True),
        (YAMLPath("/abc"), YAMLPath("/abc"), True),
        (YAMLPath("/abc"), "/abc", True),
        ("/abc", YAMLPath("/abc"), True),
        (YAMLPath("abc.def"), YAMLPath("/abc/def"), True),
        (YAMLPath("abc.def"), "/abc/def", True),
        ("abc.def", YAMLPath("/abc/def"), True),
        (YAMLPath("abc.def"), True, False),
        (YAMLPath("abc.def"), None, False),
        (YAMLPath("abc.def"), 5280, False),
        (YAMLPath("abc.def"), "def.abc", False),
    ])
    def test_eq(self, lhs, rhs, iseq):
        if iseq:
            assert lhs == rhs
        else:
            assert not lhs == rhs

    @pytest.mark.parametrize("lhs,rhs,isne", [
        (YAMLPath(""), YAMLPath(""), False),
        (YAMLPath(""), "", False),
        ("", YAMLPath(""), False),
        (YAMLPath("/abc"), YAMLPath("/abc"), False),
        (YAMLPath("/abc"), "/abc", False),
        ("/abc", YAMLPath("/abc"), False),
        (YAMLPath("abc.def"), YAMLPath("/abc/def"), False),
        (YAMLPath("abc.def"), "/abc/def", False),
        ("abc.def", YAMLPath("/abc/def"), False),
        (YAMLPath("abc.def"), False, True),
        (YAMLPath("abc.def"), None, True),
        (YAMLPath("abc.def"), 5280, True),
        (YAMLPath("abc.def"), "def.abc", True),
    ])
    def test_ne(self, lhs, rhs, isne):
        if isne:
            assert lhs != rhs
        else:
            assert not lhs != rhs

    def test_seperator_change(self):
        dotted = "abc.def"
        slashed = "/abc/def"
        testpath = YAMLPath(dotted)
        testpath.seperator = PathSeperators.FSLASH
        assert slashed == str(testpath) != dotted

    def test_escaped(self):
        testpath = YAMLPath(r"abc.def\.ghi")
        assert list(testpath.escaped) == [
            (PathSegmentTypes.KEY, "abc"),
            (PathSegmentTypes.KEY, "def.ghi"),
        ]

    def test_unescaped(self):
        testpath = YAMLPath(r"abc.def\.ghi")
        assert list(testpath.unescaped) == [
            (PathSegmentTypes.KEY, "abc"),
            (PathSegmentTypes.KEY, r"def\.ghi"),
        ]

    def test_append(self):
        yp = YAMLPath("", PathSeperators.DOT)
        yp.append("abc")
        yp.append("def")
        yp.append("ghi").append("jkl").append("mno")
        assert yp == "abc.def.ghi.jkl.mno"

    @pytest.mark.parametrize("path,prefix,result", [
        ("/abc/def", "/abc", "/def"),
        ("/abc/def", None, "/abc/def"),
        ("/abc/def", "/", "/abc/def"),
        ("/abc/def", "/jkl", "/abc/def"),
    ])
    def test_strip_path_prefix(self, path, prefix, result):
        original = YAMLPath(path)
        remove = YAMLPath(prefix) if prefix is not None else None
        compare = YAMLPath(result)
        stripped = YAMLPath.strip_path_prefix(original, remove)
        assert compare == stripped

    def test_parse_double_inversion_error(self):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath("abc[!def!=ghi]"))
        assert -1 < str(ex.value).find("Double search inversion is meaningless")

    @pytest.mark.parametrize("input", [
        ("abc[=ghi]"),
        ("abc[^ghi]"),
    ])
    def test_parse_missing_operand_errors(self, input):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath(input))
        assert -1 < str(ex.value).find("Missing search operand")

    def test_parse_bad_equality_error(self):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath("abc[def^=ghi]"))
        assert -1 < str(ex.value).find("Unsupported search operator")

    def test_parse_bad_tilde_error(self):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath("abc[def~ghi]"))
        assert -1 < str(ex.value).find("Unexpected use of \"~\" operator")

    def test_parse_bad_int_error(self):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath("abc[4F]"))
        assert -1 < str(ex.value).find("Not an integer index")

    def test_parse_unmatched_collector_error(self):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath("(abc"))
        assert -1 < str(ex.value).find("contains an unmatched () collector")

    def test_parse_unmatched_regex_error(self):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath("abc[def=~/ghi]"))
        assert -1 < str(ex.value).find("contains an unterminated Regular Expression")

    def test_parse_unmatched_demarcation_error(self):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath("abc.'def"))
        assert -1 < str(ex.value).find("contains at least one unmatched demarcation mark")

    def test_parse_meaningless_traversal(self):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath("abc**"))
        assert -1 < str(ex.value).find("The ** traversal operator has no meaning when combined with other characters")

    def test_parse_bad_following_char(self):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath("abc[has_child(def)ghi]"))
        assert -1 < str(ex.value).find("Invalid YAML Path at character index 18, \"g\", which must be \"]\"")

    def test_parse_unknown_search_keyword(self):
        with pytest.raises(YAMLPathException) as ex:
            str(YAMLPath("abc[unknown_keyword()]"))
        assert -1 < str(ex.value).find("Unknown Search Keyword at character index 4, \"unknown_keyword\"")

    @pytest.mark.parametrize("path,pops,results", [
        ("/abc", 1, [(PathSegmentTypes.KEY, "abc")]),
        ("abc", 1, [(PathSegmentTypes.KEY, "abc")]),
        ("/abc/def", 2, [(PathSegmentTypes.KEY, "def"), (PathSegmentTypes.KEY, "abc")]),
        ("abc.def", 2, [(PathSegmentTypes.KEY, "def"), (PathSegmentTypes.KEY, "abc")]),
        ("/abc/def[3]", 3, [(PathSegmentTypes.INDEX, 3), (PathSegmentTypes.KEY, "def"), (PathSegmentTypes.KEY, "abc")]),
        ("abc.def[3]", 3, [(PathSegmentTypes.INDEX, 3), (PathSegmentTypes.KEY, "def"), (PathSegmentTypes.KEY, "abc")]),
        ("/abc/def[3][1]", 4, [(PathSegmentTypes.INDEX, 1), (PathSegmentTypes.INDEX, 3), (PathSegmentTypes.KEY, "def"), (PathSegmentTypes.KEY, "abc")]),
        ("abc.def[3][1]", 4, [(PathSegmentTypes.INDEX, 1), (PathSegmentTypes.INDEX, 3), (PathSegmentTypes.KEY, "def"), (PathSegmentTypes.KEY, "abc")]),
    ])
    def test_pop_segments(self, path, pops, results):
        yp = YAMLPath(path)
        for pop in range(pops):
            assert results[pop] == yp.pop()

    def test_pop_too_many(self):
        yp = YAMLPath("abc.def")
        with pytest.raises(YAMLPathException) as ex:
            for _ in range(5):
                yp.pop()
        assert -1 < str(ex.value).find("Cannot pop when")
