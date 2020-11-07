import pytest

from types import SimpleNamespace

from ruamel.yaml.comments import CommentedMap, CommentedSeq, TaggedScalar
from ruamel.yaml.scalarstring import PlainScalarString

from yamlpath.wrappers import NodeCoords
from yamlpath.wrappers import ConsolePrinter
from yamlpath import YAMLPath

class Test_wrappers_ConsolePrinter():
    def test_info_noisy(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=False)
        logger = ConsolePrinter(args)
        logger.info("Test")
        console = capsys.readouterr()
        assert console.out == "Test\n"

    def test_info_quiet(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=True, debug=False)
        logger = ConsolePrinter(args)
        logger.info("Test")
        console = capsys.readouterr()
        assert not console.out

    def test_verbose_off(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=False)
        logger = ConsolePrinter(args)
        logger.verbose("Test")
        console = capsys.readouterr()
        assert not console.out

    def test_verbose_noisy(self, capsys):
        args = SimpleNamespace(verbose=True, quiet=False, debug=False)
        logger = ConsolePrinter(args)
        logger.verbose("Test")
        console = capsys.readouterr()
        assert console.out == "Test\n"

    def test_verbose_quiet(self, capsys):
        args = SimpleNamespace(verbose=True, quiet=True, debug=False)
        logger = ConsolePrinter(args)
        logger.verbose("Test")
        console = capsys.readouterr()
        assert not console.out

    def test_debug_off(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=False)
        logger = ConsolePrinter(args)
        logger.debug("Test")
        console = capsys.readouterr()
        assert not console.out

    def test_debug_noisy(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=True)
        logger = ConsolePrinter(args)
        anchoredkey = PlainScalarString("TestKey", anchor="KeyAnchor")
        anchoredval = PlainScalarString("TestVal", anchor="Anchor")

        logger.debug(anchoredval)
        console = capsys.readouterr()
        assert "\n".join([
            "DEBUG:  (&Anchor)TestVal",
        ]) + "\n" == console.out

        logger.debug(["test", anchoredval])
        console = capsys.readouterr()
        assert "\n".join([
            "DEBUG:  [0]test<class 'str'>",
            "DEBUG:  [1](&Anchor)TestVal<class 'ruamel.yaml.scalarstring.PlainScalarString'>",
        ]) + "\n" == console.out

        logger.debug({"ichi": 1, anchoredkey: anchoredval})
        console = capsys.readouterr()
        assert "\n".join([
            "DEBUG:  [ichi]1<class 'int'>",
            "DEBUG:  [TestKey](&KeyAnchor,&Anchor)TestVal<class 'ruamel.yaml.scalarstring.PlainScalarString'>",
        ]) + "\n" == console.out

        logger.debug({"ichi": 1, anchoredkey: "non-anchored value"})
        console = capsys.readouterr()
        assert "\n".join([
            "DEBUG:  [ichi]1<class 'int'>",
            "DEBUG:  [TestKey](&KeyAnchor,_)non-anchored value<class 'str'>",
        ]) + "\n" == console.out

        logger.debug({"ichi": 1, "non-anchored-key": anchoredval})
        console = capsys.readouterr()
        assert "\n".join([
            "DEBUG:  [ichi]1<class 'int'>",
            "DEBUG:  [non-anchored-key](_,&Anchor)TestVal<class 'ruamel.yaml.scalarstring.PlainScalarString'>",
        ]) + "\n" == console.out

        tagged_value = "value"
        tagged_value_node = TaggedScalar(tagged_value, tag="!tag")
        tagged_sequence = CommentedSeq(["a", "b"])
        tagged_sequence.yaml_set_tag("!raz")
        selfref_value = "self_referring"
        selfref_value_node = TaggedScalar(selfref_value, tag="!self_referring")
        logger.debug(
            "test_wrappers_consoleprinter:",
            prefix="test_debug_noisy:  ",
            header="--- HEADER ---",
            footer="=== FOOTER ===",
            data_header="+++ DATA HEADER +++",
            data_footer="::: DATA FOOTER :::",
            data=CommentedMap({
                "key": "value",
                "tagged": tagged_value_node,
                tagged_value_node: "untagged value",
                selfref_value_node: selfref_value_node,
                "array": ["ichi", "ni", "san"],
                "tagged_array": tagged_sequence,
                "aoh": [{"id": 1},{"id": 2},{"id": 3}],
                "aoa": [[True, True], [True, False], [False, True]],
                "dod": {"a": {"b": {"c": "d"}}},
            })
        )
        console = capsys.readouterr()
        assert "\n".join([
            "DEBUG:  test_debug_noisy:  --- HEADER ---",
            "DEBUG:  test_debug_noisy:  test_wrappers_consoleprinter:",
            "DEBUG:  test_debug_noisy:  +++ DATA HEADER +++",
            "DEBUG:  test_debug_noisy:  [key]value<class 'str'>",
            "DEBUG:  test_debug_noisy:  [tagged]<_,!tag>value<class 'ruamel.yaml.comments.TaggedScalar'>(<class 'str'>)",
            "DEBUG:  test_debug_noisy:  [value]<!tag,_>untagged value<class 'str'>",
            "DEBUG:  test_debug_noisy:  [self_referring]<!self_referring,!self_referring>self_referring<class 'ruamel.yaml.comments.TaggedScalar'>(<class 'str'>)",
            "DEBUG:  test_debug_noisy:  [array][0]ichi<class 'str'>",
            "DEBUG:  test_debug_noisy:  [array][1]ni<class 'str'>",
            "DEBUG:  test_debug_noisy:  [array][2]san<class 'str'>",
            "DEBUG:  test_debug_noisy:  [tagged_array]<_,!raz>[0]a<class 'str'>",
            "DEBUG:  test_debug_noisy:  [tagged_array]<_,!raz>[1]b<class 'str'>",
            "DEBUG:  test_debug_noisy:  [aoh][0][id]1<class 'int'>",
            "DEBUG:  test_debug_noisy:  [aoh][1][id]2<class 'int'>",
            "DEBUG:  test_debug_noisy:  [aoh][2][id]3<class 'int'>",
            "DEBUG:  test_debug_noisy:  [aoa][0][0]True<class 'bool'>",
            "DEBUG:  test_debug_noisy:  [aoa][0][1]True<class 'bool'>",
            "DEBUG:  test_debug_noisy:  [aoa][1][0]True<class 'bool'>",
            "DEBUG:  test_debug_noisy:  [aoa][1][1]False<class 'bool'>",
            "DEBUG:  test_debug_noisy:  [aoa][2][0]False<class 'bool'>",
            "DEBUG:  test_debug_noisy:  [aoa][2][1]True<class 'bool'>",
            "DEBUG:  test_debug_noisy:  [dod][a][b][c]d<class 'str'>",
            "DEBUG:  test_debug_noisy:  ::: DATA FOOTER :::",
            "DEBUG:  test_debug_noisy:  === FOOTER ===",
        ]) + "\n" == console.out

        logger.debug(tagged_value_node)
        console = capsys.readouterr()
        assert "\n".join([
            "DEBUG:  <!tag>value<class 'ruamel.yaml.comments.TaggedScalar'>(<class 'str'>)",
        ])

        logger.debug(tagged_sequence)
        console = capsys.readouterr()
        assert "\n".join([
            "DEBUG:  [tagged_array]<!raz>[0]a<class 'str'>",
            "DEBUG:  [tagged_array]<!raz>[1]b<class 'str'>",
        ])

        nc = NodeCoords("value", dict(key="value"), "key", YAMLPath("key"))
        logger.debug(
            "A node coordinate:", prefix="test_debug_noisy:  ", data=nc)
        console = capsys.readouterr()
        assert "\n".join([
            "DEBUG:  test_debug_noisy:  A node coordinate:",
            "DEBUG:  test_debug_noisy:  (path)key",
            "DEBUG:  test_debug_noisy:  (node)value",
            "DEBUG:  test_debug_noisy:  (parent)[key]value<class 'str'>",
            "DEBUG:  test_debug_noisy:  (parentref)key",
        ]) + "\n" == console.out

    def test_debug_quiet(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=True, debug=True)
        logger = ConsolePrinter(args)
        logger.debug("Test")
        console = capsys.readouterr()
        assert not console.out

    def test_warning_noisy(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=False)
        logger = ConsolePrinter(args)
        logger.warning("Test")
        console = capsys.readouterr()
        assert console.out == "WARNING:  Test\n"

    def test_warning_quiet(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=True, debug=False)
        logger = ConsolePrinter(args)
        logger.warning("Test")
        console = capsys.readouterr()
        assert not console.out

    def test_error_noisy_nonexit(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=False)
        logger = ConsolePrinter(args)
        logger.error("Test")
        console = capsys.readouterr()
        assert console.err == "ERROR:  Test\n"

    def test_error_quiet_nonexit(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=True, debug=False)
        logger = ConsolePrinter(args)
        logger.error("Test")
        console = capsys.readouterr()
        assert console.err == "ERROR:  Test\n"

    def test_error_noisy_exit(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=False)
        logger = ConsolePrinter(args)
        with pytest.raises(SystemExit):
            logger.error("Test", 27)
            console = capsys.readouterr()
            assert console.err == "ERROR:  Test\n"

    def test_error_quiet_exit(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=True, debug=False)
        logger = ConsolePrinter(args)
        with pytest.raises(SystemExit):
            logger.error("Test", 27)
            console = capsys.readouterr()
            assert console.err == "ERROR:  Test\n"

    def test_critical_noisy(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=False, debug=False)
        logger = ConsolePrinter(args)
        with pytest.raises(SystemExit):
            logger.critical("Test")
            console = capsys.readouterr()
            assert console.err == "CRITICAL:  Test\n"

    def test_critical_quiet(self, capsys):
        args = SimpleNamespace(verbose=False, quiet=True, debug=False)
        logger = ConsolePrinter(args)
        with pytest.raises(SystemExit):
            logger.critical("Test")
            console = capsys.readouterr()
            assert console.err == "CRITICAL:  Test\n"
