import pytest
from datetime import date
from types import SimpleNamespace

from ruamel.yaml import YAML
from ruamel.yaml.comments import TaggedScalar

from yamlpath.func import unwrap_node_coords
from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import (
    PathSeperators,
    PathSegmentTypes,
    PathSearchMethods,
    YAMLValueFormats,
)
from yamlpath.path import SearchTerms
from yamlpath.wrappers import ConsolePrinter
from yamlpath import YAMLPath, Processor
from tests.conftest import quiet_logger


class Test_Processor():
    """Tests for the Processor class."""

    def test_get_none_data_nodes(self, quiet_logger):
        processor = Processor(quiet_logger, None)
        yamlpath = YAMLPath("abc")
        optional_matches = 0
        must_exist_matches = 0
        req_node_matches = 0
        traversal_matches = 0

        for node in processor.get_nodes(yamlpath, mustexist=False):
            optional_matches += 1
        for node in processor.get_nodes(yamlpath, mustexist=True):
            must_exist_matches += 1
        for node in processor._get_required_nodes(None, yamlpath):
            req_node_matches += 1
        for node in processor._get_nodes_by_traversal(None, yamlpath, 0):
            traversal_matches += 1

        assert optional_matches == 0
        assert must_exist_matches == 0
        assert req_node_matches == 0
        assert traversal_matches == 1   # A None node traverses into null

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
        (r"squads[.=~/^\w{6,}$/]", [3.3], True, None),
        ("squads[alpha=1.1]", [1.1], True, None),
        ("(&arrayOfHashes.step)+(/rollback_hashes/on_condition/failure/step)-(disabled_steps)", [[1, 4]], True, None),
        ("(&arrayOfHashes.step)+((/rollback_hashes/on_condition/failure/step)-(disabled_steps))", [[1, 2, 4]], True, None),
        ("(disabled_steps)+(&arrayOfHashes.step)", [[2, 3, 1, 2]], True, None),
        ("(&arrayOfHashes.step)+(disabled_steps)[1]", [2], True, None),
        ("((&arrayOfHashes.step)[1])[0]", [2], True, None),
        ("does.not.previously.exist[7]", ["Huzzah!"], False, "Huzzah!"),
        ("/number_keys/1", ["one"], True, None),
        ("**.[.^Hey]", ["Hey, Number Two!"], True, None),
        ("/**/Hey*", ["Hey, Number Two!"], True, None),
        ("lots_of_names.**.name", ["Name 1-1", "Name 2-1", "Name 3-1", "Name 4-1", "Name 4-2", "Name 4-3", "Name 4-4"], True, None),
        ("/array_of_hashes/**", [1, "one", 2, "two"], True, None),
        ("products_hash.*[dimensions.weight==4].(availability.start.date)+(availability.stop.date)", [[date(2020, 8, 1), date(2020, 9, 25)], [date(2020, 1, 1), date(2020, 1, 1)]], True, None),
        ("products_array[dimensions.weight==4].product", ["doohickey", "widget"], True, None),
        ("(products_hash.*.dimensions.weight)[max()][parent(2)].dimensions.weight", [10], True, None)
    ])
    def test_get_nodes(self, quiet_logger, yamlpath, results, mustexist, default):
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
number_keys:
  1: one
  2: two
  3: three

# For traversal tests:
name: Name 0-0
lots_of_names:
  name: Name 1-1
  tier1:
    name: Name 2-1
    tier2:
      name: Name 3-1
      list_of_named_objects:
        - name: Name 4-1
          tag: Tag 4-1
          other: Other 4-1
          dude: Dude 4-1
        - tag: Tag 4-2
          name: Name 4-2
          dude: Dude 4-2
          other: Other 4-2
        - other: Other 4-3
          dude: Dude 4-3
          tag: Tag 4-3
          name: Name 4-3
        - dude: Dude 4-4
          tag: Tag 4-4
          name: Name 4-4
          other: Other 4-4

###############################################################################
# For descendent searching:
products_hash:
  doodad:
    availability:
      start:
        date: 2020-10-10
        time: 08:00
      stop:
        date: 2020-10-29
        time: 17:00
    dimensions:
      width: 5
      height: 5
      depth: 5
      weight: 10
  doohickey:
    availability:
      start:
        date: 2020-08-01
        time: 10:00
      stop:
        date: 2020-09-25
        time: 10:00
    dimensions:
      width: 1
      height: 2
      depth: 3
      weight: 4
  widget:
    availability:
      start:
        date: 2020-01-01
        time: 12:00
      stop:
        date: 2020-01-01
        time: 16:00
    dimensions:
      width: 9
      height: 10
      depth: 1
      weight: 4
products_array:
  - product: doodad
    availability:
      start:
        date: 2020-10-10
        time: 08:00
      stop:
        date: 2020-10-29
        time: 17:00
    dimensions:
      width: 5
      height: 5
      depth: 5
      weight: 10
  - product: doohickey
    availability:
      start:
        date: 2020-08-01
        time: 10:00
      stop:
        date: 2020-09-25
        time: 10:00
    dimensions:
      width: 1
      height: 2
      depth: 3
      weight: 4
  - product: widget
    availability:
      start:
        date: 2020-01-01
        time: 12:00
      stop:
        date: 2020-01-01
        time: 16:00
    dimensions:
      width: 9
      height: 10
      depth: 1
      weight: 4
###############################################################################
"""
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        matchidx = 0
        for node in processor.get_nodes(
                yamlpath, mustexist=mustexist, default_value=default
        ):
            assert unwrap_node_coords(node) == results[matchidx]
            matchidx += 1
        assert len(results) == matchidx

    @pytest.mark.parametrize("mustexist,yamlpath,results,yp_error", [
        (True, "baseball_legends", [set(['Mark McGwire', 'Sammy Sosa', 'Ty Cobb', 'Ken Griff'])], None),
        (True, "baseball_legends.*bb", ["Ty Cobb"], None),
        (True, "baseball_legends[A:S]", ["Mark McGwire", "Ken Griff"], None),
        (True, "baseball_legends[2]", [], "Array indexing is invalid against unordered set"),
        (True, "baseball_legends[&bl_anchor]", ["Ty Cobb"], None),
        (True, "baseball_legends([A:M])+([T:Z])", [["Ken Griff", "Ty Cobb"]], None),
        (True, "baseball_legends([A:Z])-([S:Z])", [["Mark McGwire", "Ken Griff"]], None),
        (True, "**", ["Ty Cobb", "Mark McGwire", "Sammy Sosa", "Ty Cobb", "Ken Griff"], None),
        (False, "baseball_legends", [set(['Mark McGwire', 'Sammy Sosa', 'Ty Cobb', 'Ken Griff'])], None),
        (False, "baseball_legends.*bb", ["Ty Cobb"], None),
        (False, "baseball_legends[A:S]", ["Mark McGwire", "Ken Griff"], None),
        (False, "baseball_legends[2]", [], "Array indexing is invalid against unordered set"),
        (False, "baseball_legends[&bl_anchor]", ["Ty Cobb"], None),
        (False, "baseball_legends([A:M])+([T:Z])", [["Ken Griff", "Ty Cobb"]], None),
        (False, "baseball_legends([A:Z])-([S:Z])", [["Mark McGwire", "Ken Griff"]], None),
        (False, "**", ["Ty Cobb", "Mark McGwire", "Sammy Sosa", "Ty Cobb", "Ken Griff"], None),
        (False, "baseball_legends(rbi)+(errate)", [], "Cannot add PathSegmentTypes.COLLECTOR subreference to sets"),
        (False, r"baseball_legends.Ted\ Williams", [set(['Mark McGwire', 'Sammy Sosa', 'Ty Cobb', 'Ken Griff', "Ted Williams"])], None),
    ])
    def test_get_from_sets(self, quiet_logger, mustexist, yamlpath, results, yp_error):
        yamldata = """---
aliases:
  - &bl_anchor Ty Cobb

baseball_legends: !!set
  ? Mark McGwire
  ? Sammy Sosa
  ? *bl_anchor
  ? Ken Griff
"""
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        matchidx = 0

        try:
            for node in processor.get_nodes(yamlpath, mustexist=mustexist):
                assert unwrap_node_coords(node) == results[matchidx]
                matchidx += 1
        except YAMLPathException as ex:
            if yp_error is not None:
                assert yp_error in str(ex)
            else:
                # Unexpected error
                assert False

        assert len(results) == matchidx

    @pytest.mark.parametrize("setpath,value,verifypath,tally", [
        ("aliases[&bl_anchor]", "REPLACEMENT", "**.&bl_anchor", 2),
        (r"baseball_legends.Sammy\ Sosa", "REPLACEMENT", "baseball_legends.REPLACEMENT", 1),
    ])
    def test_change_values_in_sets(self, quiet_logger, setpath, value, verifypath, tally):
        yamldata = """---
aliases:
  - &bl_anchor Ty Cobb

baseball_legends: !!set
  ? Mark McGwire
  ? Sammy Sosa
  ? *bl_anchor
  ? Ken Griff
"""
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)
        processor.set_value(setpath, value)
        matchtally = 0
        for node in processor.get_nodes(verifypath):
            changed_value = unwrap_node_coords(node)
            if isinstance(changed_value, list):
                for result in changed_value:
                    assert result == value
                    matchtally += 1
                continue
            assert changed_value == value
            matchtally += 1
        assert matchtally == tally

    @pytest.mark.parametrize("delete_yamlpath,old_deleted_nodes,new_flat_data", [
        ("**[&bl_anchor]", ["Ty Cobb", "Ty Cobb"], ["Mark McGwire", "Sammy Sosa", "Ken Griff"]),
        (r"/baseball_legends/Ken\ Griff", ["Ken Griff"], ["Ty Cobb", "Mark McGwire", "Sammy Sosa", "Ty Cobb"]),
    ])
    def test_delete_from_sets(self, quiet_logger, delete_yamlpath, old_deleted_nodes, new_flat_data):
        yamldata = """---
aliases:
  - &bl_anchor Ty Cobb

baseball_legends: !!set
  ? Mark McGwire
  ? Sammy Sosa
  ? *bl_anchor
  ? Ken Griff
"""
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)

        # The return set must be received lest no nodes will be deleted
        deleted_nodes = []
        for nc in processor.delete_nodes(delete_yamlpath):
            deleted_nodes.append(nc)

        for (test_value, verify_node_coord) in zip(old_deleted_nodes, deleted_nodes):
            assert test_value, unwrap_node_coords(verify_node_coord)

        for (test_value, verify_node_coord) in zip(new_flat_data, processor.get_nodes("**")):
            assert test_value, unwrap_node_coords(verify_node_coord)

    def test_enforce_pathsep(self, quiet_logger):
        yamldata = """---
        aliases:
          - &aliasAnchorOne Anchored Scalar Value
        """
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        yamlpath = YAMLPath("aliases[&aliasAnchorOne]")
        for node in processor.get_nodes(yamlpath, pathsep=PathSeperators.FSLASH):
            assert unwrap_node_coords(node) == "Anchored Scalar Value"

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
        ("abc.**", True),
    ])
    def test_get_impossible_nodes_error(self, quiet_logger, yamlpath, mustexist):
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
        processor = Processor(quiet_logger, yaml.load(yamldata))
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(processor.get_nodes(yamlpath, mustexist=mustexist))
        assert -1 < str(ex.value).find("does not match any nodes")

    def test_illegal_traversal_recursion(self, quiet_logger):
        yamldata = """---
        any: data
        """
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(processor.get_nodes("**.**"))
        assert -1 < str(ex.value).find("Repeating traversals are not allowed")

    def test_set_value_in_empty_data(self, capsys, quiet_logger):
        import sys
        yamldata = ""
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)
        processor.set_value("abc", "void")
        yaml.dump(data, sys.stdout)
        assert -1 == capsys.readouterr().out.find("abc")

    def test_set_value_in_none_data(self, capsys, quiet_logger):
        import sys
        yaml = YAML()
        data = None
        processor = Processor(quiet_logger, data)
        processor._update_node(None, None, None, YAMLValueFormats.DEFAULT)
        yaml.dump(data, sys.stdout)
        assert -1 == capsys.readouterr().out.find("abc")

    @pytest.mark.parametrize("yamlpath,value,tally,mustexist,vformat,pathsep", [
        ("aliases[&testAnchor]", "Updated Value", 1, True, YAMLValueFormats.DEFAULT, PathSeperators.AUTO),
        (YAMLPath("top_scalar"), "New top-level value", 1, False, YAMLValueFormats.DEFAULT, PathSeperators.DOT),
        ("/top_array/2", 42, 1, False, YAMLValueFormats.INT, PathSeperators.FSLASH),
        ("/top_hash/positive_float", 0.009, 1, True, YAMLValueFormats.FLOAT, PathSeperators.FSLASH),
        ("/top_hash/negative_float", -0.009, 1, True, YAMLValueFormats.FLOAT, PathSeperators.FSLASH),
        ("/top_hash/positive_float", -2.71828, 1, True, YAMLValueFormats.FLOAT, PathSeperators.FSLASH),
        ("/top_hash/negative_float", 5283.4, 1, True, YAMLValueFormats.FLOAT, PathSeperators.FSLASH),
        ("/null_value", "No longer null", 1, True, YAMLValueFormats.DEFAULT, PathSeperators.FSLASH),
        ("(top_array[0])+(top_hash.negative_float)+(/null_value)", "REPLACEMENT", 3, True, YAMLValueFormats.DEFAULT, PathSeperators.FSLASH),
        ("(((top_array[0])+(top_hash.negative_float))+(/null_value))", "REPLACEMENT", 3, False, YAMLValueFormats.DEFAULT, PathSeperators.FSLASH),
    ])
    def test_set_value(self, quiet_logger, yamlpath, value, tally, mustexist, vformat, pathsep):
        yamldata = """---
aliases:
  - &testAnchor Initial Value
top_array:
  # Comment 1
  - 1
  # Comment 2
  - 2
# Comment N
top_scalar: Top-level plain scalar string
top_hash:
  positive_float: 3.14159265358
  negative_float: -11.034
null_value:
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)
        processor.set_value(yamlpath, value, mustexist=mustexist, value_format=vformat, pathsep=pathsep)
        matchtally = 0
        for node in processor.get_nodes(yamlpath, mustexist=mustexist):
            changed_value = unwrap_node_coords(node)
            if isinstance(changed_value, list):
                for result in changed_value:
                    assert result == value
                    matchtally += 1
                continue
            assert changed_value == value
            matchtally += 1
        assert matchtally == tally

    def test_cannot_set_nonexistent_required_node_error(self, quiet_logger):
        yamldata = """---
        key: value
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)

        with pytest.raises(YAMLPathException) as ex:
            processor.set_value("abc", "void", mustexist=True)
        assert -1 < str(ex.value).find("No nodes matched")

    def test_none_data_to_get_nodes_by_path_segment(self, capsys, quiet_logger):
        import sys
        yamldata = ""
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)
        nodes = list(processor._get_nodes_by_path_segment(data, YAMLPath("abc"), 0))
        yaml.dump(data, sys.stdout)
        assert -1 == capsys.readouterr().out.find("abc")

    def test_bad_segment_index_for_get_nodes_by_path_segment(self, capsys, quiet_logger):
        import sys
        yamldata = """---
        key: value
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)
        nodes = list(processor._get_nodes_by_path_segment(data, YAMLPath("abc"), 10))
        yaml.dump(data, sys.stdout)
        assert -1 == capsys.readouterr().out.find("abc")

    def test_get_nodes_by_unknown_path_segment_error(self, quiet_logger):
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
        processor = Processor(quiet_logger, data)
        path = YAMLPath("abc")
        stringified = str(path)     # Force Path to parse
        path._escaped = deque([
            (PathSegmentTypes.DNF, "abc"),
        ])

        with pytest.raises(NotImplementedError):
            nodes = list(processor._get_nodes_by_path_segment(data, path, 0))

    def test_non_int_slice_error(self, quiet_logger):
        yamldata = """---
        - step: 1
        - step: 2
        - step: 3
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)

        with pytest.raises(YAMLPathException) as ex:
            processor.set_value("[1:4F]", "")
        assert -1 < str(ex.value).find("is not an integer array slice")

    def test_non_int_array_index_error(self, quiet_logger):
        from collections import deque
        yamldata = """---
        - 1
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        path = YAMLPath("[0]")
        processor = Processor(quiet_logger, data)
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

    def test_nonexistant_path_search_method_error(self, quiet_logger):
        from enum import Enum
        from yamlpath.enums import PathSearchMethods
        names = [m.name for m in PathSearchMethods] + ['DNF']
        PathSearchMethods = Enum('PathSearchMethods', names)

        yamldata = """---
        top_scalar: value
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)

        with pytest.raises(NotImplementedError):
            nodes = list(processor._get_nodes_by_search(
                data,
                SearchTerms(True, PathSearchMethods.DNF, ".", "top_scalar")
            ))

    def test_adjoined_collectors_error(self, quiet_logger):
        yamldata = """---
        key: value
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)

        with pytest.raises(YAMLPathException) as ex:
            nodes = list(processor.get_nodes("(&arrayOfHashes.step)(disabled_steps)"))
        assert -1 < str(ex.value).find("has no meaning")

    def test_no_attrs_to_arrays_error(self, quiet_logger):
        yamldata = """---
        array:
          - one
          - two
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)

        with pytest.raises(YAMLPathException) as ex:
            nodes = list(processor.get_nodes("array.attr"))
        assert -1 < str(ex.value).find("Cannot add")

    def test_no_index_to_hashes_error(self, quiet_logger):
        # Using [#] syntax is a disambiguated INDEX ELEMENT NUMBER.  In
        # DICTIONARY context, this would create an ambiguous request to access
        # either the #th value or a value whose key is the literal #.  As such,
        # an error is deliberately generated when [#] syntax is used against
        # dictionaries.  When you actually want a DICTIONARY KEY that happens
        # to be an integer, omit the square braces, [].
        yamldata = """---
        hash:
          key: value
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)

        with pytest.raises(YAMLPathException) as ex:
            nodes = list(processor.get_nodes("hash[6]"))
        assert -1 < str(ex.value).find("Cannot add")

    def test_get_nodes_array_impossible_type_error(self, quiet_logger):
        yamldata = """---
        array:
          - 1
          - 2
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)

        with pytest.raises(YAMLPathException) as ex:
            nodes = list(processor.get_nodes(r"/array/(.=~/^.{3,4}$/)", default_value="New value"))
        assert -1 < str(ex.value).find("Cannot add")

    def test_no_attrs_to_scalars_errors(self, quiet_logger):
        yamldata = """---
        scalar: value
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)

        with pytest.raises(YAMLPathException) as ex:
            nodes = list(processor.get_nodes("scalar[6]"))
        assert -1 < str(ex.value).find("Cannot add")

        with pytest.raises(YAMLPathException) as ex:
            nodes = list(processor.get_nodes("scalar.key"))
        assert -1 < str(ex.value).find("Cannot add")

    @pytest.mark.parametrize("yamlpath,value,tally,mustexist,vformat,pathsep", [
        ("/anchorKeys[&keyOne]", "Set self-destruct", 1, True, YAMLValueFormats.DEFAULT, PathSeperators.AUTO),
        ("/hash[&keyTwo]", "Confirm", 1, True, YAMLValueFormats.DEFAULT, PathSeperators.AUTO),
        ("/anchorKeys[&recursiveAnchorKey]", "Recurse more", 1, True, YAMLValueFormats.DEFAULT, PathSeperators.AUTO),
        ("/hash[&recursiveAnchorKey]", "Recurse even more", 1, True, YAMLValueFormats.DEFAULT, PathSeperators.AUTO),
    ])
    def test_key_anchor_changes(self, quiet_logger, yamlpath, value, tally, mustexist, vformat, pathsep):
        yamldata = """---
        anchorKeys:
          &keyOne aliasOne: 11A1
          &keyTwo aliasTwo: 22B2
          &recursiveAnchorKey subjectKey: *recursiveAnchorKey

        hash:
          *keyOne :
            subval: 1.1
          *keyTwo :
            subval: 2.2
          *recursiveAnchorKey :
            subval: 3.3
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)

        yamlpath = YAMLPath(yamlpath)
        processor.set_value(yamlpath, value, mustexist=mustexist, value_format=vformat, pathsep=pathsep)
        matchtally = 0
        for node in processor.get_nodes(yamlpath):
            assert unwrap_node_coords(node) == value
            matchtally += 1
        assert matchtally == tally

    def test_key_anchor_children(self, quiet_logger):
        yamldata = """---
        anchorKeys:
          &keyOne aliasOne: 1 1 Alpha 1
          &keyTwo aliasTwo: 2 2 Beta 2

        hash:
          *keyOne :
            subval: 1.1
          *keyTwo :
            subval: 2.2
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)

        yamlpath = YAMLPath("hash[&keyTwo].subval")
        newvalue = "Mute audibles"
        processor.set_value(yamlpath, newvalue, mustexist=True)
        matchtally = 0
        for node in processor.get_nodes(yamlpath):
            assert unwrap_node_coords(node) == newvalue
            matchtally += 1
        assert matchtally == 1

    def test_cannot_add_novel_alias_keys(self, quiet_logger):
        yamldata = """---
        anchorKeys:
          &keyOne aliasOne: 1 1 Alpha 1
          &keyTwo aliasTwo: 2 2 Beta 2

        hash:
          *keyOne :
            subval: 1.1
          *keyTwo :
            subval: 2.2
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)

        yamlpath = YAMLPath("hash[&keyThree].subval")
        newvalue = "Abort"
        with pytest.raises(YAMLPathException) as ex:
            nodes = list(processor.get_nodes(yamlpath))
        assert -1 < str(ex.value).find("Cannot add")

    @pytest.mark.parametrize("yamlpath,value,verifications", [
        ("number", 5280, [
            ("aliases[&alias_number]", 1),
            ("number", 5280),
            ("alias_number", 1),
            ("hash.number", 1),
            ("hash.alias_number", 1),
            ("complex.hash.number", 1),
            ("complex.hash.alias_number", 1),
        ]),
        ("aliases[&alias_number]", 5280, [
            ("aliases[&alias_number]", 5280),
            ("number", 1),
            ("alias_number", 5280),
            ("hash.number", 1),
            ("hash.alias_number", 5280),
            ("complex.hash.number", 1),
            ("complex.hash.alias_number", 5280),
        ]),
        ("bool", False, [
            ("aliases[&alias_bool]", True),
            ("bool", False),
            ("alias_bool", True),
            ("hash.bool", True),
            ("hash.alias_bool", True),
            ("complex.hash.bool", True),
            ("complex.hash.alias_bool", True),
        ]),
        ("aliases[&alias_bool]", False, [
            ("aliases[&alias_bool]", False),
            ("bool", True),
            ("alias_bool", False),
            ("hash.bool", True),
            ("hash.alias_bool", False),
            ("complex.hash.bool", True),
            ("complex.hash.alias_bool", False),
        ]),
    ])
    def test_set_nonunique_values(self, quiet_logger, yamlpath, value, verifications):
        yamldata = """---
        aliases:
          - &alias_number 1
          - &alias_bool true
        number: 1
        bool: true
        alias_number: *alias_number
        alias_bool: *alias_bool
        hash:
          number: 1
          bool: true
          alias_number: *alias_number
          alias_bool: *alias_bool
        complex:
          hash:
            number: 1
            bool: true
            alias_number: *alias_number
            alias_bool: *alias_bool
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)
        processor.set_value(yamlpath, value)
        for verification in verifications:
            for verify_node_coord in processor.get_nodes(verification[0]):
                assert unwrap_node_coords(verify_node_coord) == verification[1]

    @pytest.mark.parametrize("yamlpath,results", [
        ("(temps[. >= 100]) - (temps[. > 110])", [[110, 100]]),
        ("(temps[. < 32]) - (temps[. >= 114])", [[0]]),
        ("(temps[. < 32]) + (temps[. > 110])", [[0, 114]]),
        ("(temps[. <= 32]) + (temps[. > 110])", [[32, 0, 114]]),
        ("(temps[. < 32]) + (temps[. >= 110])", [[0, 110, 114]]),
        ("(temps[. <= 32]) + (temps[. >= 110])", [[32, 0, 110, 114]]),
        ("(temps[. < 0]) + (temps[. >= 114])", [[114]]),
    ])
    def test_get_singular_collectors(self, quiet_logger, yamlpath, results):
        yamldata = """---
        temps:
          - 32
          - 0
          - 110
          - 100
          - 72
          - 68
          - 114
          - 34
          - 36
        """
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        matchidx = 0
        # Note that Collectors deal with virtual DOMs, so mustexist must always
        # be set True.  Otherwise, ephemeral virtual nodes would be created and
        # discarded.  Is this desirable?  Maybe, but not today.  For now, using
        # Collectors without setting mustexist=True will be undefined behavior.
        for node in processor.get_nodes(yamlpath, mustexist=True):
            assert unwrap_node_coords(node) == results[matchidx]
            matchidx += 1
        assert len(results) == matchidx

    @pytest.mark.parametrize("yamlpath,results", [
        ("(/list1) + (/list2)", [[1, 2, 3, 4, 5, 6]]),
        ("(/list1) - (/exclude)", [[1, 2]]),
        ("(/list2) - (/exclude)", [[5, 6]]),
        ("(/list1) + (/list2) - (/exclude)", [[1, 2, 5, 6]]),
        ("((/list1) + (/list2)) - (/exclude)", [[1, 2, 5, 6]]),
        ("(/list1) + ((/list2) - (/exclude))", [[1, 2, 3, 5, 6]]),
        ("((/list1) - (/exclude)) + ((/list2) - (/exclude))", [[1, 2, 5, 6]]),
        ("((/list1) - (/exclude)) + ((/list2) - (/exclude))*", [1, 2, 5, 6]),
        ("(((/list1) - (/exclude)) + ((/list2) - (/exclude)))[2]", [5]),
    ])
    def test_scalar_collectors(self, quiet_logger, yamlpath, results):
        yamldata = """---
list1:
  - 1
  - 2
  - 3
list2:
  - 4
  - 5
  - 6
exclude:
  - 3
  - 4
"""
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        matchidx = 0
        # Note that Collectors deal with virtual DOMs, so mustexist must always
        # be set True.  Otherwise, ephemeral virtual nodes would be created and
        # discarded.  Is this desirable?  Maybe, but not today.  For now, using
        # Collectors without setting mustexist=True will be undefined behavior.
        for node in processor.get_nodes(yamlpath, mustexist=True):
            assert unwrap_node_coords(node) == results[matchidx]
            matchidx += 1
        assert len(results) == matchidx

    @pytest.mark.parametrize("yamlpath,results", [
        ("(hash.*)-(array[1])", [["value1", "value3"]]),
        ("(hash)-(hoh.two.*)", [[{"key1": "value1"}]]),
        ("(aoa)-(hoa.two)", [[["value1", "value2", "value3"], ["value3"]]]),
        ("(aoh)-(aoh[max(key1)])", [[{"key2": "value2", "key3": "value3"}, {"key3": "value3"}]]),
    ])
    def test_collector_math(self, quiet_logger, yamlpath, results):
        yamldata = """---
hash:
  key1: value1
  key2: value2
  key3: value3

array:
  - value1
  - value2
  - vlaue3

hoh:
  one:
    key1: value1
    key2: value2
    key3: value3
  two:
    key2: value2
    key3: value3
  three:
    key3: value3

aoh:
  - key1: value1
    key2: value2
    key3: value3
  - key2: value2
    key3: value3
  - key3: value3

aoa:
  - - value1
    - value2
    - value3
  - - value2
    - value3
  - - value3

hoa:
  one:
    - value1
    - value2
    - value3
  two:
    - value2
    - value3
  three:
    - value3
"""
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        matchidx = 0
        for node in processor.get_nodes(yamlpath, mustexist=True):
            assert unwrap_node_coords(node) == results[matchidx]
            matchidx += 1
        assert len(results) == matchidx

    def test_get_every_data_type(self, quiet_logger):
        # Contributed by https://github.com/AndydeCleyre
        yamldata = """---
intthing: 6
floatthing: 6.8
yesthing: yes
nothing: no
truething: true
falsething: false
nullthing: null
nothingthing:
emptystring: ""
nullstring: "null"
        """

        results = [6, 6.8, "yes", "no", True, False, None, None, "", "null"]

        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)
        yamlpath = YAMLPath("*")

        match_index = 0
        for node in processor.get_nodes(yamlpath):
            assert unwrap_node_coords(node) == results[match_index]
            match_index += 1

    @pytest.mark.parametrize("delete_yamlpath,pathseperator,old_deleted_nodes,new_flat_data", [
        (YAMLPath("/**[&alias_number]"), PathSeperators.FSLASH, [1, 1, 1], [1,1,True,1,1,True,1,1,True,1,"ABC",123,"BCD",987,"CDE","8B8"]),
        ("records[1]", PathSeperators.AUTO, ["ABC",123,"BCD",987], [1,1,1,True,1,1,1,True,1,1,1,True,1,1,"CDE","8B8"]),
    ])
    def test_delete_nodes(self, quiet_logger, delete_yamlpath, pathseperator, old_deleted_nodes, new_flat_data):
        yamldata = """---
aliases:
  - &alias_number 1
  - &alias_bool true
number: 1
bool: true
alias_number: *alias_number
alias_bool: *alias_bool
hash:
  number: 1
  bool: true
  alias_number: *alias_number
  alias_bool: *alias_bool
complex:
  hash:
    number: 1
    bool: true
    alias_number: *alias_number
    alias_bool: *alias_bool
records:
  - id: ABC
    data: 123
  - id: BCD
    data: 987
  - id: CDE
    data: 8B8
"""
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)

        # The return set must be received lest no nodes will be deleted
        deleted_nodes = []
        for nc in processor.delete_nodes(delete_yamlpath, pathsep=pathseperator):
            deleted_nodes.append(nc)

        for (test_value, verify_node_coord) in zip(old_deleted_nodes, deleted_nodes):
            assert test_value, unwrap_node_coords(verify_node_coord)

        for (test_value, verify_node_coord) in zip(new_flat_data, processor.get_nodes("**")):
            assert test_value, unwrap_node_coords(verify_node_coord)

    def test_null_docs_have_nothing_to_delete(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=True)
        logger = ConsolePrinter(args)
        processor = Processor(logger, None)

        deleted_nodes = []
        for nc in processor.delete_nodes("**"):
            deleted_nodes.append(nc)

        console = capsys.readouterr()
        assert "Refusing to delete nodes from a null document" in console.out

    def test_null_docs_have_nothing_to_gather_and_alias(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=True)
        logger = ConsolePrinter(args)
        processor = Processor(logger, None)

        processor.alias_nodes("/alias*", "/anchor")

        console = capsys.readouterr()
        assert "Refusing to alias nodes in a null document" in console.out

    def test_null_docs_have_nothing_to_alias(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=True)
        logger = ConsolePrinter(args)
        processor = Processor(logger, None)

        processor.alias_gathered_nodes([], "/anchor")

        console = capsys.readouterr()
        assert "Refusing to alias nodes in a null document" in console.out

    def test_null_docs_have_nothing_to_gather_and_ymk(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=True)
        logger = ConsolePrinter(args)
        processor = Processor(logger, None)

        processor.ymk_nodes("/alias*", "/anchor")

        console = capsys.readouterr()
        assert "Refusing to set a YAML Merge Key to nodes in a null document" in console.out

    def test_null_docs_have_nothing_to_ymk(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=True)
        logger = ConsolePrinter(args)
        processor = Processor(logger, None)

        processor.ymk_gathered_nodes([], "/alias*", "/anchor")

        console = capsys.readouterr()
        assert "Refusing to set a YAML Merge Key to nodes in a null document" in console.out

    def test_null_docs_have_nothing_to_tag(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=True)
        logger = ConsolePrinter(args)
        processor = Processor(logger, None)

        processor.tag_nodes("/tag_nothing", "tag_this")

        console = capsys.readouterr()
        assert "Refusing to tag nodes from a null document" in console.out

    @pytest.mark.parametrize("alias_path,anchor_path,anchor_name,pathseperator", [
        (YAMLPath("/a_hash/a_key"), YAMLPath("/some_key"), "", PathSeperators.FSLASH),
        ("a_hash.a_key", "some_key", "", PathSeperators.AUTO),
    ])
    def test_anchor_nodes(self, quiet_logger, alias_path, anchor_path, anchor_name, pathseperator):
        anchor_value = "This is the Anchored value!"
        yamlin = """---
some_key: {}
a_hash:
  a_key: A value
""".format(anchor_value)

        yaml = YAML()
        data = yaml.load(yamlin)
        processor = Processor(quiet_logger, data)

        processor.alias_nodes(
            alias_path, anchor_path,
            pathsep=pathseperator, anchor_name=anchor_name)

        match_count = 0
        for node in processor.get_nodes(
            alias_path, mustexist=True
        ):
            match_count += 1
            assert unwrap_node_coords(node) == anchor_value
        assert match_count == 1

    @pytest.mark.parametrize("change_path,ymk_path,anchor_name,pathseperator,validations", [
        ("target", "source", "", PathSeperators.AUTO, [
            ("target.target_key", ["other"]),
            ("target.source_key", ["value"]),
            ("target[&source].source_key", ["value"]),
            ("target.override_this", ["overridden"]),
            ("target[&source].override_this", ["original"]),
        ]),
        (YAMLPath("target"), YAMLPath("source"), "", PathSeperators.DOT, [
            ("target.target_key", ["other"]),
            ("target.source_key", ["value"]),
            ("target[&source].source_key", ["value"]),
            ("target.override_this", ["overridden"]),
            ("target[&source].override_this", ["original"]),
        ]),
        ("/target", "/source", "", PathSeperators.FSLASH, [
            ("/target/target_key", ["other"]),
            ("/target/source_key", ["value"]),
            ("/target/&source/source_key", ["value"]),
            ("/target/override_this", ["overridden"]),
            ("/target/&source/override_this", ["original"]),
        ]),
        ("target", "source", "custom_name", PathSeperators.DOT, [
            ("target.target_key", ["other"]),
            ("target.source_key", ["value"]),
            ("target[&custom_name].source_key", ["value"]),
            ("target.override_this", ["overridden"]),
            ("target[&custom_name].override_this", ["original"]),
        ]),
    ])
    def test_ymk_nodes(self, quiet_logger, change_path, ymk_path, anchor_name, pathseperator, validations):
        yamlin = """---
source:
  source_key: value
  override_this: original

target:
  target_key: other
  override_this: overridden
"""

        yaml = YAML()
        data = yaml.load(yamlin)
        processor = Processor(quiet_logger, data)

        processor.ymk_nodes(
            change_path, ymk_path,
            pathsep=pathseperator, anchor_name=anchor_name)

        for (valid_path, valid_values) in validations:
            match_count = 0
            for check_node in processor.get_nodes(valid_path, mustexist=True):
                assert unwrap_node_coords(check_node) == valid_values[match_count]
                match_count += 1
            assert len(valid_values) == match_count

    @pytest.mark.parametrize("yaml_path,tag,pathseperator", [
        (YAMLPath("/key"), "!taggidy", PathSeperators.FSLASH),
        ("key", "taggidy", PathSeperators.AUTO),
    ])
    def test_tag_nodes(self, quiet_logger, yaml_path, tag, pathseperator):
        yamlin = """---
key: value
"""

        yaml = YAML()
        data = yaml.load(yamlin)
        processor = Processor(quiet_logger, data)

        processor.tag_nodes(yaml_path, tag, pathsep=pathseperator)

        if tag and not tag[0] == "!":
            tag = "!{}".format(tag)

        assert isinstance(data['key'], TaggedScalar)
        assert data['key'].tag.value == tag

    @pytest.mark.parametrize("yaml_path,value,old_data,new_data", [
        (YAMLPath("/key[name()]"), "renamed_key", {'key': 'value'}, {'renamed_key': 'value'}),
    ])
    def test_rename_dict_key(self, quiet_logger, yaml_path, value, old_data, new_data):
        processor = Processor(quiet_logger, old_data)
        processor.set_value(yaml_path, value)
        assert new_data == old_data

    @pytest.mark.parametrize("yaml_path,value,old_data", [
        (YAMLPath("/key[name()]"), "renamed_key", {'key': 'value', 'renamed_key': 'value'}),
    ])
    def test_rename_dict_key_cannot_overwrite(self, quiet_logger, yaml_path, value, old_data):
        processor = Processor(quiet_logger, old_data)
        with pytest.raises(YAMLPathException) as ex:
            processor.set_value(yaml_path, value)
        assert -1 < str(ex.value).find("already exists at the same document level")

    def test_traverse_with_null(self, quiet_logger):
        # Contributed by https://github.com/rbordelo
        yamldata = """---
Things:
  - name: first thing
    rank: 42
  - name: second thing
    rank: 5
  - name: third thing
    rank: null
  - name: fourth thing
    rank: 1
"""

        results = ["first thing", "second thing", "third thing", "fourth thing"]

        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)
        yamlpath = YAMLPath("/**/name")

        match_index = 0
        for node in processor.get_nodes(yamlpath):
            assert unwrap_node_coords(node) == results[match_index]
            match_index += 1

    @pytest.mark.parametrize("yamlpath,results", [
        ("reuse1.key12", ["overridden value in reuse1 for definition1"]),
        ("reuse1.&alias_name1.key12", ["value12"]),
        ("reuse1[&alias_name1].key12", ["value12"]),
    ])
    def test_yaml_merge_keys_access(self, quiet_logger, yamlpath, results):
        yamldata = """---
definition1: &alias_name1
  key11: value11
  key12: value12

definition2: &alias_name2
  key21: value21
  key22: value22

compound_definition: &alias_name3
  <<: [ *alias_name1, *alias_name2 ]
  key31: value31
  key32: value32

reuse1: &alias_name4
  <<: *alias_name1
  key1: new key in reuse1
  key12: overridden value in reuse1 for definition1

reuse2: &alias_name5
  <<: [*alias_name1, *alias_name2 ]
  key2: new key in reuse2

reuse3: &alias_name6
  <<: *alias_name3
  key3: new key3 in reuse3
  key4: new key4 in reuse3

re_reuse1:
  <<: *alias_name4
  re_key1: new key in re_reuse1
  key1: override key from reuse1
  key12: override overridden key from reuse1

re_reuse2:
  <<: *alias_name6
  re_key2: new key in re_reuse2
  key3: override key from reuse3
  key31: override key from compound_definition
  key12: override key from definition1
"""
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        matchidx = 0
        for node in processor.get_nodes(yamlpath, mustexist=True):
            assert unwrap_node_coords(node) == results[matchidx]
            matchidx += 1
        assert len(results) == matchidx

    @pytest.mark.parametrize("yamlpath,results", [
        ("/list*[has_child(&anchored_value)][name()]", ["list_matches"]),
        ("/list*[!has_child(&anchored_value)][name()]", ["list_no_match"]),
        ("/hash*[has_child(&anchored_hash)][name()]", ["hash_ymk_matches"]),
        ("/hash*[!has_child(&anchored_hash)][name()]", ["hash_key_matches", "hash_val_matches", "hash_no_match"]),
        ("/hash*[has_child(&anchored_key)][name()]", ["hash_key_matches"]),
        ("/hash*[!has_child(&anchored_key)][name()]", ["hash_ymk_matches", "hash_val_matches", "hash_no_match"]),
        ("/hash*[has_child(&anchored_value)][name()]", ["hash_val_matches"]),
        ("/hash*[!has_child(&anchored_value)][name()]", ["hash_key_matches", "hash_ymk_matches", "hash_no_match"]),
        ("/aoh[has_child(&anchored_hash)]/intent", ["hash_match"]),
        ("/aoh[!has_child(&anchored_hash)]/intent", ["no_match"]),
        ("/aoa/*[has_child(&anchored_value)][name()]", [0]),
        ("/aoa/*[!has_child(&anchored_value)][name()]", [1]),
    ])
    def test_yaml_merge_key_queries(self, quiet_logger, yamlpath, results):
        yamldata = """---
aliases:
  - &anchored_key anchored_key
  - &anchored_value This value is Anchored

anchored_hash: &anchored_hash
  default_key_1: Some default value
  default_key_2: Another default value

list_matches:
  - l1e1
  - *anchored_value

list_no_match:
  - l2e1
  - l2e2

hash_key_matches:
  *anchored_key : A dynamic key-name for a static value
  static_key: A static key-name with a static value

hash_ymk_matches:
  <<: *anchored_hash
  h1k1: An implementation value

hash_val_matches:
  k2k1: *anchored_value
  k2k2: static value

hash_no_match:
  h2k1: A value
  h2k2: Another value

aoh:
  - intent: hash_match
    <<: *anchored_hash
  - intent: no_match
    aohk1: non-matching value
  - null

aoa:
  - - 0.0
    - *anchored_value
  - - 1.0
    - 1.1
"""
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        matchidx = 0
        for node in processor.get_nodes(yamlpath, mustexist=True):
            assert unwrap_node_coords(node) == results[matchidx]
            matchidx += 1
        assert len(results) == matchidx

    @pytest.mark.parametrize("yamlpath,results", [
        (r"temperature[. =~ /\d{3}/]", [110, 100, 114]),
    ])
    def test_wiki_array_element_searches(self, quiet_logger, yamlpath, results):
        yamldata = """---
temperature:
  - 32
  - 0
  - 110
  - 100
  - 72
  - 68
  - 114
  - 34
  - 36
"""
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        matchidx = 0
        for node in processor.get_nodes(yamlpath, mustexist=True):
            assert unwrap_node_coords(node) == results[matchidx]
            matchidx += 1
        assert len(results) == matchidx

    @pytest.mark.parametrize("yamlpath,results", [
        ("consoles[. % SEGA]", ["SEGA Master System", "SEGA Genesis", "SEGA CD", "SEGA 32X", "SEGA Saturn", "SEGA DreamCast"]),
    ])
    def test_wiki_collectors(self, quiet_logger, yamlpath, results):
        yamldata = """---
consoles:
  - ColecoVision
  - Atari 2600
  - Atari 4800
  - Nintendo Entertainment System
  - SEGA Master System
  - SEGA Genesis
  - Nintendo SNES
  - SEGA CD
  - TurboGrafx 16
  - SEGA 32X
  - NeoGeo
  - SEGA Saturn
  - Sony PlayStation
  - Nintendo 64
  - SEGA DreamCast
  - Sony PlayStation 2
  - Microsoft Xbox
  - Sony PlayStation 3
  - Nintendo Wii
  - Microsoft Xbox 360
  - Sony PlayStation 4
  - Nintendo Wii-U
  - Microsoft Xbox One
  - Microsoft Xbox One S
  - Sony PlayStation 4 Pro
  - Microsoft Xbox One X
  - Nintendo Switch
"""
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        matchidx = 0
        for node in processor.get_nodes(yamlpath, mustexist=True):
            assert unwrap_node_coords(node) == results[matchidx]
            matchidx += 1
        assert len(results) == matchidx

    @pytest.mark.parametrize("yamlpath,results", [
        ("(/standard/setup/action) + (/standard/teardown/action) + (/change/action)", [["Initialize", "Provision", "Deprovision", "Terminate", "Do something", "Do something else"]]),
        ("(/standard[.!='']/action) + (/change/action)", [["Initialize", "Provision", "Deprovision", "Terminate", "Do something", "Do something else"]]),
        ("(/standard[.!='']/id) + (/change/id) - (/disabled_ids)", [[0, 1, 2, 4]]),
    ])
    def test_wiki_collector_math(self, quiet_logger, yamlpath, results):
        yamldata = """---
standard:
  setup:
    - id: 0
      step: 1
      action: Initialize
    - id: 1
      step: 2
      action: Provision
  teardown:
    - id: 2
      step: 1
      action: Deprovision
    - id: 3
      step: 2
      action: Terminate

change:
  - id: 4
    step: 1
    action: Do something
  - id: 5
    step: 2
    action: Do something else

rollback:
  data_error:
    - id: 6
      step: 1
      action: Flush
  app_error:
    - id: 7
      step: 1
      action: Abend
    - id: 8
      step: 2
      action: Shutdown

disabled_ids:
  - 3
  - 5
  - 8
"""
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        matchidx = 0
        for node in processor.get_nodes(yamlpath, mustexist=True):
            assert unwrap_node_coords(node) == results[matchidx]
            matchidx += 1
        assert len(results) == matchidx

    @pytest.mark.parametrize("yamlpath,results", [
        ("(/list1) + (/list2)", [[1, 2, 3, 4, 5, 6]]),
        ("(/list1) - (/exclude)", [[1, 2]]),
        ("(/list2) - (/exclude)", [[5, 6]]),
        ("(/list1) + (/list2) - (/exclude)", [[1, 2, 5, 6]]),
        ("((/list1) - (/exclude)) + (/list2)", [[1, 2, 4, 5, 6]]),
        ("(/list1) + ((/list2) - (/exclude))", [[1, 2, 3, 5, 6]]),
    ])
    def test_wiki_collector_order_of_ops(self, quiet_logger, yamlpath, results):
        yamldata = """---
list1:
  - 1
  - 2
  - 3
list2:
  - 4
  - 5
  - 6
exclude:
  - 3
  - 4
"""
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        matchidx = 0
        for node in processor.get_nodes(yamlpath, mustexist=True):
            assert unwrap_node_coords(node) == results[matchidx]
            matchidx += 1
        assert len(results) == matchidx

    @pytest.mark.parametrize("yamlpath,results", [
        ("warriors[power_level > 9000]", [{"name": "Goku Higashi", "power_level": 9001, "style": "Z fight"}]),
        ("warriors[power_level = 5280]", [
            {"name": "Chi-chi Shiranui", "power_level": 5280, "style": "Dragon fury"},
            {"name": "Krillin Bogard", "power_level": 5280, "style": "Fatal ball"}
        ]),
    ])
    def test_wiki_search_array_of_hashes(self, quiet_logger, yamlpath, results):
        yamldata = """---
warriors:
  - name: Chi-chi Shiranui
    power_level: 5280
    style: Dragon fury
  - name: Goku Higashi
    power_level: 9001
    style: Z fight
  - name: Krillin Bogard
    power_level: 5280
    style: Fatal ball
  - name: Bulma Sakazaki
    power_level: 1024
    style: Super final
"""
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        matchidx = 0
        for node in processor.get_nodes(yamlpath, mustexist=True):
            assert unwrap_node_coords(node) == results[matchidx]
            matchidx += 1
        assert len(results) == matchidx

    @pytest.mark.parametrize("yamlpath,results", [
        ("contrast_ct[. % bowel]", [0.095, 0.355]),
    ])
    def test_wiki_search_key_names(self, quiet_logger, yamlpath, results):
        yamldata = """---
contrast_ct:
  appendicitis: .009
  colitis: .002
  diverticulitis: .015
  gastroenteritis: .007
  ileus: .227
  large_bowel_obstruction: .095
  peptic_ulcer_disease: .007
  small_bowel_obstruction: .355
  ulcerative_colitis: .010
"""
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        matchidx = 0
        for node in processor.get_nodes(yamlpath, mustexist=True):
            assert unwrap_node_coords(node) == results[matchidx]
            matchidx += 1
        assert len(results) == matchidx

    @pytest.mark.parametrize("yamlpath,results", [
        ("hash_of_hashes.*[!has_child(child_two)]", [{"child_one": "value2.1", "child_three": "value2.3"}]),
        ("/array_of_hashes/*[!has_child(child_two)]", [{"id": "two", "child_one": "value2.1", "child_three": "value2.3"}]),
        ("/hash_of_hashes/*[!has_child(child_two)][name()]", ["two"]),
        ("array_of_hashes.*[!has_child(child_two)].id", ["two"]),
        ("/array_of_arrays/*[!has_child(value2.1)]", [["value1.1", "value1.2"], ["value3.1", "value3.2"]]),
        ("array_of_arrays[*!=value2.1]", [["value1.1", "value1.2"], ["value3.1", "value3.2"]]),
        ("array_of_arrays.*[!has_child(value2.1)][name()]", [0, 2]),
        ("/array_of_arrays[*!=value2.1][name()]", [0, 2]),
        ("(/array_of_arrays/*[!has_child(value2.1)][name()])[0]", [0]),
        ("(array_of_arrays[*!=value2.1][name()])[0]", [0]),
        ("(array_of_arrays.*[!has_child(value2.1)][name()])[-1]", [2]),
        ("(/array_of_arrays[*!=value2.1][name()])[-1]", [2]),
        ("/simple_array[has_child(value1.1)]", [["value1.1", "value1.2", "value2.1", "value2.3", "value3.1", "value3.2"]]),
        ("/simple_array[!has_child(value1.3)]", [["value1.1", "value1.2", "value2.1", "value2.3", "value3.1", "value3.2"]]),
    ])
    def test_wiki_has_child(self, quiet_logger, yamlpath, results):
        yamldata = """---
hash_of_hashes:
  one:
    child_one: value1.1
    child_two: value1.2
  two:
    child_one: value2.1
    child_three: value2.3
  three:
    child_one: value3.1
    child_two: value3.2

array_of_hashes:
  - id: one
    child_one: value1.1
    child_two: value1.2
  - id: two
    child_one: value2.1
    child_three: value2.3
  - id: three
    child_one: value3.1
    child_two: value3.2

simple_array:
  - value1.1
  - value1.2
  - value2.1
  - value2.3
  - value3.1
  - value3.2

array_of_arrays:
  - - value1.1
    - value1.2
  - - value2.1
    - value2.3
  - - value3.1
    - value3.2
"""
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        matchidx = 0
        for node in processor.get_nodes(yamlpath, mustexist=True):
            assert unwrap_node_coords(node) == results[matchidx]
            matchidx += 1
        assert len(results) == matchidx

    @pytest.mark.parametrize("yamlpath,results", [
        ("/prices_aoh[max(price)]", [{"product": "whatchamacallit", "price": 9.95}]),
        ("/prices_hash[max(price)]", [{"price": 9.95}]),
        ("/prices_aoh[max(price)]/price", [9.95]),
        ("/prices_hash[max(price)]/price", [9.95]),
        ("/prices_aoh[max(price)]/product", ["whatchamacallit"]),
        ("/prices_hash[max(price)][name()]", ["whatchamacallit"]),
        ("prices_array[max()]", [9.95]),
        ("bad_prices_aoh[max(price)]", [{"product": "fob", "price": "not set"}]),
        ("bad_prices_hash[max(price)]", [{"price": "not set"}]),
        ("bad_prices_array[max()]", ["not set"]),
        ("bare[max()]", ["value"]),
        ("(prices_aoh[!max(price)])[max(price)]", [{"product": "doohickey", "price": 4.99}, {"product": "fob", "price": 4.99}]),
        ("(prices_hash[!max(price)])[max(price)]", [{"price": 4.99}, {"price": 4.99}]),
        ("(prices_aoh)-(prices_aoh[max(price)])[max(price)]", [{"product": "doohickey", "price": 4.99}, {"product": "fob", "price": 4.99}]),
        ("(prices_hash)-(prices_hash[max(price)]).*[max(price)]", [{"price": 4.99}, {"price": 4.99}]),
        ("((prices_aoh[!max(price)])[max(price)])[0]", [{"product": "doohickey", "price": 4.99}]),
        ("((prices_hash[!max(price)])[max(price)])[0]", [{"price": 4.99}]),
        ("((prices_aoh[!max(price)])[max(price)])[0].price", [4.99]),
        ("((prices_hash[!max(price)])[max(price)])[0].price", [4.99]),
        ("/prices_aoh[min(price)]", [{"product": "widget", "price": 0.98}]),
        ("/prices_hash[min(price)]", [{"price": 0.98}]),
        ("/prices_aoh[min(price)]/price", [0.98]),
        ("/prices_hash[min(price)]/price", [0.98]),
        ("/prices_aoh[min(price)]/product", ["widget"]),
        ("/prices_hash[min(price)][name()]", ["widget"]),
        ("prices_array[min()]", [0.98]),
        ("bad_prices_aoh[min(price)]", [{"product": "widget", "price": True}]),
        ("bad_prices_hash[min(price)]", [{"price": True}]),
        ("bad_prices_array[min()]", [0.98]),
        ("bare[min()]", ["value"]),
    ])
    def test_wiki_min_max(self, quiet_logger, yamlpath, results):
        yamldata = """---
# Consistent Data Types
prices_aoh:
  - product: doohickey
    price: 4.99
  - product: fob
    price: 4.99
  - product: whatchamacallit
    price: 9.95
  - product: widget
    price: 0.98
  - product: unknown

prices_hash:
  doohickey:
    price: 4.99
  fob:
    price: 4.99
  whatchamacallit:
    price: 9.95
  widget:
    price: 0.98
  unknown:

prices_array:
  - 4.99
  - 4.99
  - 9.95
  - 0.98
  - null

# TODO: Inconsistent Data Types
bare: value

bad_prices_aoh:
  - product: doohickey
    price: 4.99
  - product: fob
    price: not set
  - product: whatchamacallit
    price: 9.95
  - product: widget
    price: true
  - product: unknown

bad_prices_hash:
  doohickey:
    price: 4.99
  fob:
    price: not set
  whatchamacallit:
    price: 9.95
  widget:
    price: true
  unknown:

bad_prices_array:
  - 4.99
  - not set
  - 9.95
  - 0.98
  - null
"""
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        matchidx = 0
        for node in processor.get_nodes(yamlpath, mustexist=True):
            assert unwrap_node_coords(node) == results[matchidx]
            matchidx += 1
        assert len(results) == matchidx

    @pytest.mark.parametrize("yamlpath,results", [
        ("**.Opal[parent()][name()]", ["silicates"]),
        ("minerals.*.*.mohs_hardness[.>7][parent(2)][name()]", ["Tourmaline", "Uvarovite"]),
        ("minerals.*.*.[mohs_hardness[1]>7][name()]", ["Tourmaline", "Uvarovite"]),
        ("minerals.*.*(([mohs_hardness[0]>=4])-([mohs_hardness[1]>5]))[name()]", ["Flourite"]),
    ])
    def test_wiki_parent(self, quiet_logger, yamlpath, results):
        yamldata = """---
minerals:
  silicates:
    Opal:
      mohs_hardness: [5.5,6]
      specific_gravity: [2.06,2.23]
    Tourmaline:
      mohs_hardness: [7,7.5]
      specific_gravity: [3,3.26]
  non-silicates:
    Azurite:
      mohs_hardness: [3.5,4]
      specific_gravity: [3.773,3.78]
    Bismuth:
      mohs_hardness: [2.25,2.25]
      specific_gravity: [9.87]
    Crocoite:
      mohs_hardness: [2.5,3]
      specific_gravity: [6,6]
    Flourite:
      mohs_hardness: [4,4]
      specific_gravity: [3.175,3.184]
    Rhodochrosite:
      mohs_hardness: [3.5,4]
      specific_gravity: [3.5,3.7]
    "Rose Quartz":
      mohs_hardness: [7,7]
      specific_gravity: [2.6,2.7]
    Uvarovite:
      mohs_hardness: [6.5,7.5]
      specific_gravity: [3.77,3.81]
"""
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        matchidx = 0
        for node in processor.get_nodes(yamlpath, mustexist=True):
            assert unwrap_node_coords(node) == results[matchidx]
            matchidx += 1
        assert len(results) == matchidx

