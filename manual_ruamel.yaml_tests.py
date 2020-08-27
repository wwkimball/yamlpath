"""
Something
"""
from sys import maxsize

from ruamel.yaml import YAML
from ruamel.yaml.scalarfloat import ScalarFloat

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.explicit_start = True      # type: ignore
yaml.preserve_quotes = True     # type: ignore
yaml.width = maxsize            # type: ignore

#yaml_data = get_yaml_data(yaml, log, args.yaml_file)
SOURCE_YAML = """---
parameters:
  param1: 0.1
  param2: -0.5280
"""
OUT_FILE = "../bug52-out.yaml"
yaml_data = yaml.load(SOURCE_YAML)

print("Original data:")
print(yaml_data)
print(yaml_data['parameters']['param2'])

print("Change the data:")
yaml_data['parameters']['param2'] = ScalarFloat(
    -123456789.987654321,
    m_sign="-",
    prec=0,
    width=2
)
print(yaml_data)
print(yaml_data['parameters']['param2'])

print("Writing changed data to {}.".format(OUT_FILE))
with open(OUT_FILE, 'w') as yaml_dump:
    yaml.dump(yaml_data, yaml_dump)
