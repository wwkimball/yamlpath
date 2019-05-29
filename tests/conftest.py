"""Define reusable pytest fixtures."""
import tempfile

import pytest


def create_temp_yaml_file(tmp_path_factory, content):
    """Creates a test YAML input file."""
    fhnd = tempfile.NamedTemporaryFile(mode='w',
                                       dir=tmp_path_factory.getbasetemp(),
                                       suffix='.yaml',
                                       delete=False)
    fhnd.write(content)
    return fhnd.name

@pytest.fixture(scope="session")
def imparsible_yaml_file(tmp_path_factory):
    """
    Creates a YAML file that causes a ParserError when read by ruamel.yaml.
    """
    content = '''{"json": "is YAML", "but_bad_json": "isn't anything!"'''
    return create_temp_yaml_file(tmp_path_factory, content)

@pytest.fixture(scope="session")
def badsyntax_yaml_file(tmp_path_factory):
    """
    Creates a YAML file that causes a ScannerError when read by ruamel.yaml.
    """
    content = """---
    # This YAML content contains a critical syntax error
    & bad_anchor: is bad
    """
    return create_temp_yaml_file(tmp_path_factory, content)

@pytest.fixture(scope="session")
def badcmp_yaml_file(tmp_path_factory):
    """
    Creates a YAML file that causes a ComposerError when read by ruamel.yaml.
    """
    content = """---
    # This YAML file is improperly composed
    this is a parsing error: *no such capability
    """
    return create_temp_yaml_file(tmp_path_factory, content)
