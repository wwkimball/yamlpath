import pytest

from types import SimpleNamespace

from yamlpath.wrappers import ConsolePrinter

def test_info_noisy(capsys):
    args = SimpleNamespace(verbose=False, quiet=False, debug=False)
    logger = ConsolePrinter(args)
    logger.info("Test")
    console = capsys.readouterr()
    assert console.out == "Test\n"

def test_info_quiet(capsys):
    args = SimpleNamespace(verbose=False, quiet=True, debug=False)
    logger = ConsolePrinter(args)
    logger.info("Test")
    console = capsys.readouterr()
    assert not console.out

def test_verbose_off(capsys):
    args = SimpleNamespace(verbose=False, quiet=False, debug=False)
    logger = ConsolePrinter(args)
    logger.verbose("Test")
    console = capsys.readouterr()
    assert not console.out

def test_verbose_noisy(capsys):
    args = SimpleNamespace(verbose=True, quiet=False, debug=False)
    logger = ConsolePrinter(args)
    logger.verbose("Test")
    console = capsys.readouterr()
    assert console.out == "Test\n"

def test_verbose_quiet(capsys):
    args = SimpleNamespace(verbose=True, quiet=True, debug=False)
    logger = ConsolePrinter(args)
    logger.verbose("Test")
    console = capsys.readouterr()
    assert not console.out

def test_debug_off(capsys):
    args = SimpleNamespace(verbose=False, quiet=False, debug=False)
    logger = ConsolePrinter(args)
    logger.debug("Test")
    console = capsys.readouterr()
    assert not console.out

def test_debug_noisy(capsys):
    args = SimpleNamespace(verbose=False, quiet=False, debug=True)
    logger = ConsolePrinter(args)
    logger.debug("Test")
    console = capsys.readouterr()
    assert console.out == "DEBUG:  Test\n"

    logger.debug(["ichi", "ni", "san"])
    console = capsys.readouterr()
    assert console.out == "DEBUG:  [0]=ichi\nDEBUG:  [1]=ni\nDEBUG:  [2]=san\n"

    logger.debug({"ichi": 1, "ni": 2, "san": 3})
    console = capsys.readouterr()
    assert console.out == "DEBUG:  [ichi]=>1\nDEBUG:  [ni]=>2\nDEBUG:  [san]=>3\n"

def test_debug_quiet(capsys):
    args = SimpleNamespace(verbose=False, quiet=True, debug=True)
    logger = ConsolePrinter(args)
    logger.debug("Test")
    console = capsys.readouterr()
    assert not console.out

def test_warning_noisy(capsys):
    args = SimpleNamespace(verbose=False, quiet=False, debug=False)
    logger = ConsolePrinter(args)
    logger.warning("Test")
    console = capsys.readouterr()
    assert console.out == "WARNING:  Test\n"

def test_warning_quiet(capsys):
    args = SimpleNamespace(verbose=False, quiet=True, debug=False)
    logger = ConsolePrinter(args)
    logger.warning("Test")
    console = capsys.readouterr()
    assert not console.out

def test_error_noisy_nonexit(capsys):
    args = SimpleNamespace(verbose=False, quiet=False, debug=False)
    logger = ConsolePrinter(args)
    logger.error("Test")
    console = capsys.readouterr()
    assert console.err == "ERROR:  Test\n"

def test_error_quiet_nonexit(capsys):
    args = SimpleNamespace(verbose=False, quiet=True, debug=False)
    logger = ConsolePrinter(args)
    logger.error("Test")
    console = capsys.readouterr()
    assert console.err == "ERROR:  Test\n"

def test_error_noisy_exit(capsys):
    args = SimpleNamespace(verbose=False, quiet=False, debug=False)
    logger = ConsolePrinter(args)
    with pytest.raises(SystemExit):
        logger.error("Test", 27)
        console = capsys.readouterr()
        assert console.err == "ERROR:  Test\n"

def test_error_quiet_exit(capsys):
    args = SimpleNamespace(verbose=False, quiet=True, debug=False)
    logger = ConsolePrinter(args)
    with pytest.raises(SystemExit):
        logger.error("Test", 27)
        console = capsys.readouterr()
        assert console.err == "ERROR:  Test\n"

def test_critical_noisy(capsys):
    args = SimpleNamespace(verbose=False, quiet=False, debug=False)
    logger = ConsolePrinter(args)
    with pytest.raises(SystemExit):
        logger.critical("Test")
        console = capsys.readouterr()
        assert console.err == "CRITICAL:  Test\n"

def test_critical_quiet(capsys):
    args = SimpleNamespace(verbose=False, quiet=True, debug=False)
    logger = ConsolePrinter(args)
    with pytest.raises(SystemExit):
        logger.critical("Test")
        console = capsys.readouterr()
        assert console.err == "CRITICAL:  Test\n"
