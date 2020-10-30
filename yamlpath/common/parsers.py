"""
Implement Parsers, a static library of generally-useful code for data parsers.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
import warnings
from sys import maxsize, stdin
from datetime import date
from typing import Any, Generator, Tuple

from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError
from ruamel.yaml.composer import ComposerError, ReusedAnchorWarning
from ruamel.yaml.constructor import ConstructorError, DuplicateKeyError
from ruamel.yaml.scanner import ScannerError

from yamlpath.wrappers import ConsolePrinter


class Parsers:
    """Helper methods for common YAML/JSON/Compatible parser operations."""

    @staticmethod
    def get_yaml_editor(**kwargs: Any) -> Any:
        """
        Build and return a generic YAML editor based on ruamel.yaml.

        Parameters:  N/A

        Keyword Arguments:
        * explicit_start (bool) True = ensure the YAML Start-of-Document marker
          (---<EOL>) is written in the output; False = remove it; default=True
        * explode_aliases (bool) True = convert all aliases (*name) and YAML
          merge operators (<<: *name) to their referenced content, removing the
          aliases and merge operators; False = maintain the references;
          default=False
        * preserve_quotes (bool) True = retain any and all quoting of keys and
          values including whatever demarcation symbol was used (" versus ');
          False = only quote values when necessary, removing unnecessary
          demarcation; default=True

        Returns (Any) The ready-for-use YAML editor.

        Raises:  N/A
        """
        explicit_start = kwargs.pop("explicit_start", True)
        explode_aliases = kwargs.pop("explode_aliases", False)
        preserve_quotes = kwargs.pop("preserve_quotes", True)

        # The ruamel.yaml class appears to be missing some typing data, so
        # these valid assignments cannot be type-checked.
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.explicit_start = explicit_start       # type: ignore
        yaml.preserve_quotes = preserve_quotes     # type: ignore
        yaml.width = maxsize                       # type: ignore

        if explode_aliases:
            yaml.default_flow_style = False

        return yaml

    @staticmethod
    # pylint: disable=too-many-branches,too-many-statements
    def get_yaml_data(
        parser: Any, logger: ConsolePrinter, source: str
    ) -> Tuple[Any, bool]:
        """
        Parse YAML/Compatible data and return the ruamel.yaml object result.

        All known issues are caught and distinctively logged.

        Parameters:
        1. parser (ruamel.yaml.YAML) The YAML data parser
        2. logger (ConsolePrinter) The logging facility
        3. source (str) The source file to load; can be - for reading from
           STDIN

        Returns:  Tuple[Any, bool] A tuple containing the document and its
        success/fail state.  The first field is the parsed document; will be
        None for empty documents and for documents which could not be read.
        The second field will be True when there were no errors during parsing
        and False, otherwise.
        """
        yaml_data = None
        data_available = True

        # This code traps errors and warnings from ruamel.yaml, substituting
        # lengthy stack-dumps with specific, meaningful feedback.  Further,
        # some warnings are treated as errors by ruamel.yaml, so these are also
        # coallesced into cleaner feedback.
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("error")
                if source == "-":
                    yaml_data = parser.load(stdin.read())
                else:
                    with open(source, 'r') as fhnd:
                        yaml_data = parser.load(fhnd)
        except KeyboardInterrupt:
            logger.error("Aborting data load due to keyboard interrupt!")
            data_available = False
        except FileNotFoundError:
            logger.error("File not found:  {}".format(source))
            data_available = False
        except ParserError as ex:
            logger.error("YAML parsing error {}:  {}"
                        .format(str(ex.problem_mark).lstrip(), ex.problem))
            data_available = False
        except ComposerError as ex:
            logger.error("YAML composition error {}:  {}"
                        .format(str(ex.problem_mark).lstrip(), ex.problem))
            data_available = False
        except ConstructorError as ex:
            logger.error("YAML construction error {}:  {}"
                        .format(str(ex.problem_mark).lstrip(), ex.problem))
            data_available = False
        except ScannerError as ex:
            logger.error("YAML syntax error {}:  {}"
                        .format(str(ex.problem_mark).lstrip(), ex.problem))
            data_available = False
        except DuplicateKeyError as dke:
            omits = [
                "while constructing", "To suppress this", "readthedocs",
                "future releases", "the new API",
            ]
            message = str(dke).split("\n")
            newmsg = ""
            for line in message:
                line = line.strip()
                if not line:
                    continue
                write_line = True
                for omit in omits:
                    if omit in line:
                        write_line = False
                        break
                if write_line:
                    newmsg += "\n   " + line
            logger.error("Duplicate Hash key detected:  {}"
                        .format(newmsg))
            data_available = False
        except ReusedAnchorWarning as raw:
            logger.error("Duplicate YAML Anchor detected:  {}"
                        .format(
                            str(raw)
                            .replace("occurrence   ", "occurrence ")
                            .replace("\n", "\n   ")))
            data_available = False

        return (yaml_data, data_available)

    @staticmethod
    # pylint: disable=too-many-branches,too-many-statements,too-many-locals
    def get_yaml_multidoc_data(
        parser: Any, logger: ConsolePrinter, source: str
    ) -> Generator[Tuple[Any, bool], None, None]:
        """
        Parse YAML/Compatible multi-docs and yield each ruamel.yaml object.

        All known issues are caught and distinctively logged.

        Parameters:
        1. parser (ruamel.yaml.YAML) The YAML data parser
        2. logger (ConsolePrinter) The logging facility
        3. source (str) The source file to load; can be - for reading from
           STDIN

        Returns:  Generator[Tuple[Any, bool], None, None] A tuple for each
        document as it is parsed.  The first field is the parsed document; will
        be None for empty documents and for documents which could not be read.
        The second field will be True when there were no errors during parsing
        and False, otherwise.
        """
        # This code traps errors and warnings from ruamel.yaml, substituting
        # lengthy stack-dumps with specific, meaningful feedback.  Further,
        # some warnings are treated as errors by ruamel.yaml, so these are also
        # coallesced into cleaner feedback.
        has_error = False
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("error")
                if source == "-":
                    doc_yielded = False
                    for document in parser.load_all(stdin.read()):
                        doc_yielded = True
                        logger.debug(
                            "Yielding document from {}:".format(source),
                            prefix="get_yaml_multidoc_data: ", data=document)
                        yield (document, True)

                    # The user sent a deliberately empty document via STDIN
                    if not doc_yielded:
                        yield ("", True)
                else:
                    with open(source, 'r') as fhnd:
                        for document in parser.load_all(fhnd):
                            logger.debug(
                                "Yielding document from {}:".format(source),
                                prefix="get_yaml_multidoc_data: ",
                                data=document)
                            yield (document, True)
        except KeyboardInterrupt:
            has_error = True
            logger.error("Aborting data load due to keyboard interrupt!")
        except FileNotFoundError:
            has_error = True
            logger.error("File not found:  {}".format(source))
        except ParserError as ex:
            has_error = True
            logger.error("YAML parsing error {}:  {}"
                        .format(str(ex.problem_mark).lstrip(), ex.problem))
        except ComposerError as ex:
            has_error = True
            logger.error("YAML composition error {}:  {}"
                        .format(str(ex.problem_mark).lstrip(), ex.problem))
        except ConstructorError as ex:
            has_error = True
            logger.error("YAML construction error {}:  {}"
                        .format(str(ex.problem_mark).lstrip(), ex.problem))
        except ScannerError as ex:
            has_error = True
            logger.error("YAML syntax error {}:  {}"
                        .format(str(ex.problem_mark).lstrip(), ex.problem))
        except DuplicateKeyError as dke:
            has_error = True
            omits = [
                "while constructing", "To suppress this", "readthedocs",
                "future releases", "the new API",
            ]
            message = str(dke).split("\n")
            newmsg = ""
            for line in message:
                line = line.strip()
                if not line:
                    continue
                write_line = True
                for omit in omits:
                    if omit in line:
                        write_line = False
                        break
                if write_line:
                    newmsg += "\n   " + line
            logger.error("Duplicate Hash key detected:  {}"
                        .format(newmsg))
        except ReusedAnchorWarning as raw:
            has_error = True
            logger.error("Duplicate YAML Anchor detected:  {}"
                        .format(
                            str(raw)
                            .replace("occurrence   ", "occurrence ")
                            .replace("\n", "\n   ")))

        if has_error:
            yield (None, False)

    @staticmethod
    def stringify_dates(data: Any) -> Any:
        """
        Recurse through a data structure, converting all dates to strings.

        This is required for JSON output, which has no serialization support
        for native date objects.
        """
        if isinstance(data, dict):
            for key, val in data.items():
                data[key] = Parsers.stringify_dates(val)
        elif isinstance(data, list):
            for idx, ele in enumerate(data):
                data[idx] = Parsers.stringify_dates(ele)
        elif isinstance(data, date):
            return str(data)
        return data
