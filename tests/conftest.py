"""Define reusable pytest fixtures."""
import tempfile

import pytest


def create_test_file(tmp_path_factory, content):
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
    return create_test_file(tmp_path_factory, content)

@pytest.fixture(scope="module")
def badsyntax_yaml_file(request, tmp_path_factory):
    """
    Creates a YAML file that causes a ScannerError when read by ruamel.yaml.
    """
    tmp_subdir = getattr(request.module, "tmpdir", "test_files")
    file_name = "badsyntax.test.yaml"
    yaml_file = tmp_path_factory.mktemp(tmp_subdir) / file_name
    file_content = """---
    # This YAML content contains a critical syntax error
    & bad_anchor: is bad
    """
    with open(yaml_file, 'w') as fhnd:
        fhnd.write(file_content)
    return yaml_file

@pytest.fixture(scope="module")
def badcmp_yaml_file(request, tmp_path_factory):
    """
    Creates a YAML file that causes a ComposerError when read by ruamel.yaml.
    """
    tmp_subdir = getattr(request.module, "tmpdir", "test_files")
    file_name = "badcmp.test.yaml"
    yaml_file = tmp_path_factory.mktemp(tmp_subdir) / file_name
    file_content = """---
    # This YAML file is improperly composed
    this is a parsing error: *no such capability
    """
    with open(yaml_file, 'w') as fhnd:
        fhnd.write(file_content)
    return yaml_file
