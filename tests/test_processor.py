import pytest
from datetime import date

from ruamel.yaml import YAML

from yamlpath.func import unwrap_node_coords
from yamlpath.exceptions import YAMLPathException
from yamlpath.enums import (
    PathSeperators,
    PathSegmentTypes,
    PathSearchMethods,
    YAMLValueFormats,
)
from yamlpath.path import SearchTerms
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

    def test_enforce_pathsep(self, quiet_logger):
        yamldata = """---
        aliases:
          - &aliasAnchorOne Anchored Scalar Value
        """
        yaml = YAML()
        processor = Processor(quiet_logger, yaml.load(yamldata))
        yamlpath = YAMLPath("aliases[&firstAlias]")
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
        """
        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)
        processor.set_value(yamlpath, value, mustexist=mustexist, value_format=vformat, pathsep=pathsep)
        matchtally = 0
        for node in processor.get_nodes(yamlpath, mustexist=mustexist):
            assert unwrap_node_coords(node) == value
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

        # Note that Python/pytest is translating nothingthing into a string, "null".
        # This is NOT yamlpath doing this.  In fact, the yaml-get command-line tool
        # actually translates true nulls into "\x00" (hexadecimal NULL control-characters).
        results = [6, 6.8, "yes", "no", True, False, "", "null", "", "null"]

        yaml = YAML()
        data = yaml.load(yamldata)
        processor = Processor(quiet_logger, data)
        yamlpath = YAMLPath("*")

        match_index = 0
        for node in processor.get_nodes(yamlpath):
            assert unwrap_node_coords(node) == results[match_index]
            match_index += 1
