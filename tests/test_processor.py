import pytest

from types import SimpleNamespace

from ruamel.yaml import YAML

from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import (
    PathSeperators,
    PathSegmentTypes,
    PathSearchMethods,
    YAMLValueFormats,
)
from yamlpath.wrappers import ConsolePrinter
from yamlpath.path import Path, SearchTerms
from yamlpath import Processor

@pytest.fixture
def logger_f():
    """Returns a quiet ConsolePrinter."""
    args = SimpleNamespace(verbose=False, quiet=True, debug=False)
    return ConsolePrinter(args)

class Test_Processor():
    """Tests for the Processor class."""

    def test_get_none_data_nodes(self, logger_f):
        processor = Processor(logger_f, None)
        matches = 0
        for node in processor.get_nodes("abc"):
            matches += 1
        assert matches == 0

    @pytest.mark.parametrize("yamlpath,results,mustexist,default", [
        ("aliases[&aliasAnchorOne]", ["Anchored Scalar Value"], True, None),
        ("aliases[&newAlias]", ["Not in the original data"], False, "Not in the original data"),
        ("aliases[0]", ["Anchored Scalar Value"], True, None),
        ("aliases.0", ["Anchored Scalar Value"], True, None),
        ("(array_of_hashes.name)+(rollback_hashes.on_condition.failure.name)", [["one", "two", "three", "four"]], True, None),
        ("/array_of_hashes/name", ["one", "two"], True, None),
        ("aliases[1:2]", [["Hey, Number Two!"]], True, None),
        ("aliases[1:1]", [["Hey, Number Two!"]], True, None),
        ("squads[bravo:charlie]", [2.2, 3.3], True, None),
        ("/&arrayOfHashes/1/step", [2], True, None),
        ("&arrayOfHashes[step=1].name", ["one"], True, None),
        ("squads[.!=""][.=1.1]", [1.1], True, None),
        ("squads[.!=""][.>1.1][.<3.3]", [2.2], True, None),
        ("aliases[.^Hey]", ["Hey, Number Two!"], True, None),
        ("aliases[.$Value]", ["Anchored Scalar Value"], True, None),
        ("aliases[.%Value]", ["Anchored Scalar Value"], True, None),
        ("&arrayOfHashes[step>1].name", ["two"], True, None),
        ("&arrayOfHashes[step<2].name", ["one"], True, None),
        ("squads[.>charlie]", [4.4], True, None),
        ("squads[.>=charlie]", [3.3, 4.4], True, None),
        ("squads[.<bravo]", [1.1], True, None),
        ("squads[.<=bravo]", [1.1, 2.2], True, None),
        ("squads[.=~/^\w{6,}$/]", [3.3], True, None),
        ("squads[alpha=1.1]", [1.1], True, None),
        ("(&arrayOfHashes.step)+(/rollback_hashes/on_condition/failure/step)-(disabled_steps)", [[1, 4]], True, None),
        ("(&arrayOfHashes.step)+((/rollback_hashes/on_condition/failure/step)-(disabled_steps))", [[1, 2, 4]], True, None),
        ("(disabled_steps)+(&arrayOfHashes.step)", [[2, 3, 1, 2]], True, None),
        ("(&arrayOfHashes.step)+(disabled_steps)[1]", [2], True, None),
    ])
    def test_get_nodes(self, logger_f, yamlpath, results, mustexist, default):
        yamldata = """---
        aliases:
          - &aliasAnchorOne Anchored Scalar Value
          - &aliasAnchorTwo Hey, Number Two!
        array_of_hashes: &arrayOfHashes
          - step: 1
            name: one
          - step: 2
            name: two
        rollback_hashes:
          on_condition:
            failure:
              - step: 3
                name: three
              - step: 4
                name: four
        disabled_steps:
          - 2
          - 3
        squads:
          alpha: 1.1
          bravo: 2.2
          charlie: 3.3
          delta: 4.4
        """
        yaml = YAML()
        processor = Processor(logger_f, yaml.load(yamldata))
        matchidx = 0
        for node in processor.get_nodes(
                yamlpath, mustexist=mustexist, default_value=default
        ):
            assert node == results[matchidx]
            matchidx += 1
        assert len(results) == matchidx

    def test_enforce_pathsep(self, logger_f):
        yamldata = """---
        aliases:
          - &aliasAnchorOne Anchored Scalar Value
        """
        yaml = YAML()
        processor = Processor(logger_f, yaml.load(yamldata))
        yamlpath = Path("aliases[&firstAlias]")
        for node in processor.get_nodes(yamlpath, pathsep=PathSeperators.FSLASH):
            assert node == "Anchored Scalar Value"

    @pytest.mark.parametrize("yamlpath,mustexist", [
        ("abc", True),
        ("/ints/[.=4F]", True),
        ("/ints/[.>4F]", True),
        ("/ints/[.<4F]", True),
        ("/ints/[.>=4F]", True),
        ("/ints/[.<=4F]", True),
        ("/floats/[.=4.F]", True),
        ("/floats/[.>4.F]", True),
        ("/floats/[.<4.F]", True),
        ("/floats/[.>=4.F]", True),
        ("/floats/[.<=4.F]", True),
    ])
    def test_get_impossible_nodes(self, logger_f, yamlpath, mustexist):
        yamldata = """---
        ints:
          - 1
          - 2
          - 3
          - 4
          - 5
        floats:
          - 1.1
          - 2.2
          - 3.3
        """
        yaml = YAML()
        processor = Processor(logger_f, yaml.load(yamldata))
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(processor.get_nodes(yamlpath, mustexist=mustexist))
        assert -1 < str(ex.value).find("does not match any nodes")

    def test_set_value_in_none_data(self, capsys, logger_f):
        import sys
        yamldata = ""
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(logger_f, data)
        processor.set_value("abc", "void")
        yaml.dump(data, sys.stdout)
        assert -1 == capsys.readouterr().out.find("abc")

    @pytest.mark.parametrize("yamlpath,value,tally,mustexist,vformat,pathsep", [
        ("aliases[&testAnchor]", "Updated Value", 1, True, YAMLValueFormats.DEFAULT, PathSeperators.AUTO),
        (Path("top_scalar"), "New top-level value", 1, False, YAMLValueFormats.DEFAULT, PathSeperators.DOT),
    ])
    def test_set_value(self, logger_f, yamlpath, value, tally, mustexist, vformat, pathsep):
        yamldata = """---
        aliases:
          - &testAnchor Initial Value
        top_scalar: Top-level plain scalar string
        """
        yaml = YAML()
        processor = Processor(logger_f, yaml.load(yamldata))
        processor.set_value(yamlpath, value, mustexist=mustexist, value_format=vformat, pathsep=pathsep)
        matchtally = 0
        for node in processor.get_nodes(yamlpath, mustexist=mustexist):
            assert node == value
            matchtally += 1
        assert matchtally == tally

    def test_cannot_set_nonexistent_required_node(self, logger_f):
        yamldata = """---
        key: value
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(logger_f, data)

        with pytest.raises(YAMLPathException) as ex:
            processor.set_value("abc", "void", mustexist=True)
        assert -1 < str(ex.value).find("No nodes matched")

    def test_none_data_to_get_nodes_by_path_segment(self, capsys, logger_f):
        import sys
        yamldata = ""
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(logger_f, data)
        nodes = list(processor._get_nodes_by_path_segment(data, Path("abc"), 0))
        yaml.dump(data, sys.stdout)
        assert -1 == capsys.readouterr().out.find("abc")

    def test_bad_segment_index_for_get_nodes_by_path_segment(self, capsys, logger_f):
        import sys
        yamldata = """---
        key: value
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(logger_f, data)
        nodes = list(processor._get_nodes_by_path_segment(data, Path("abc"), 10))
        yaml.dump(data, sys.stdout)
        assert -1 == capsys.readouterr().out.find("abc")

    def test_get_nodes_by_unknown_path_segment(self, logger_f):
        from collections import deque
        from enum import Enum
        from yamlpath.enums import PathSegmentTypes
        names = [m.name for m in PathSegmentTypes] + ['DNF']
        PathSegmentTypes = Enum('PathSegmentTypes', names)

        yamldata = """---
        key: value
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(logger_f, data)
        path = Path("abc")
        stringified = str(path)     # Force Path to parse
        path._escaped = deque([
            (PathSegmentTypes.DNF, "abc"),
        ])

        with pytest.raises(NotImplementedError):
            nodes = list(processor._get_nodes_by_path_segment(data, path, 0))

    def test_non_int_slice(self, logger_f):
        yamldata = """---
        - step: 1
        - step: 2
        - step: 3
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(logger_f, data)

        with pytest.raises(YAMLPathException) as ex:
            processor.set_value("[1:4F]", "")
        assert -1 < str(ex.value).find("is not an integer array slice")

    def test_non_int_array_index(self, logger_f):
        from collections import deque
        yamldata = """---
        - 1
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        path = Path("[0]")
        processor = Processor(logger_f, data)
        strp = str(path)

        path._escaped = deque([
            (PathSegmentTypes.INDEX, "0F"),
        ])
        path._unescaped = deque([
            (PathSegmentTypes.INDEX, "0F"),
        ])

        with pytest.raises(YAMLPathException) as ex:
            nodes = list(processor._get_nodes_by_index(data, path, 0))
        assert -1 < str(ex.value).find("is not an integer array index")

    def test_nonexistant_path_search_method(self, logger_f):
        from enum import Enum
        from yamlpath.enums import PathSearchMethods
        names = [m.name for m in PathSearchMethods] + ['DNF']
        PathSearchMethods = Enum('PathSearchMethods', names)

        yamldata = """---
        top_scalar: value
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(logger_f, data)

        with pytest.raises(NotImplementedError):
            nodes = list(processor._get_nodes_by_search(
                data,
                SearchTerms(True, PathSearchMethods.DNF, ".", "top_scalar")
            ))

    def test_adjoined_collectors_error(self, logger_f):
        yamldata = """---
        key: value
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(logger_f, data)

        with pytest.raises(YAMLPathException) as ex:
            nodes = list(processor.get_nodes("(&arrayOfHashes.step)(disabled_steps)"))
        assert -1 < str(ex.value).find("has no meaning")
