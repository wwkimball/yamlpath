# YAML Path and Command-Line Tools

[![Build Status](https://travis-ci.org/wwkimball/yamlpath.svg?branch=master)](https://travis-ci.org/wwkimball/yamlpath)

Contents:

1. [Introduction](#introduction)
2. [Installing](#installing)
3. [Supported YAML Path Forms](#supported-yaml-path-forms)
4. [Based on ruamel.yaml and Python 3](#based-on-ruamelyaml-and-python-3)
   1. [Compatible ruamel.yaml Versions](#compatible-ruamelyaml-versions)
5. [The Files of This Project](#the-files-of-this-project)
   1. [Command-Line Tools](#command-line-tools)
   2. [Libraries](#libraries)
6. [Basic Usage](#basic-usage)
   1. [Basic Usage:  Command-Line Tools](#basic-usage--command-line-tools)
      1. [Rotate Your EYAML Keys](#rotate-your-eyaml-keys)
      2. [Get a YAML Value](#get-a-yaml-value)
      3. [Change a YAML Value](#change-a-yaml-value)
   2. [Basic Usage:  Libraries](#basic-usage--libraries)
      1. [Initialize ruamel.yaml and These Helpers](#initialize-ruamelyaml-and-these-helpers)
      2. [Searching for YAML Nodes](#searching-for-yaml-nodes)
      3. [Changing Values](#changing-values)

## Introduction

This project presents and utilizes YAML Paths, which are a human-friendly means
of identifying one or more nodes within a [YAML](https://yaml.org/) or
[EYAML](https://github.com/voxpupuli/hiera-eyaml) data structure.  The libraries
(modules) and several sample command-line tool implementations are provided
(discussed later).

To illustrate some YAML Path capabilities, review this sample YAML data:

```yaml
---
# Sample YAML data
aliases:
  - &commonUsername username
  - &commonPassword 5uP3r 53kr17 P@55\/\/0rD

configuration::application:
  'general.settings':
    slash\key: ENC[some-lengthy-EYAML-value]
    'a.dotted.subkey':
      - element1
      - element2
      - element3

sensitive::accounts:
  database:
    app_user: *commonUsername
    app_pass: *commonPassword
  application:
    db:
      users:
        - name: admin
          pass: 1s0L@73d @cC0u|\|7
          access_level: 0
        - name: *commonUsername
          pass: *commonPassword
          access_level: 500
```

This YAML data sample contains these single-result YAML Paths:

1. `aliases[&commonUsername]`
2. `aliases[&commonPassword]`
3. `configuration::application.'general.settings'.slash\\key`
4. `configuration::application.'general.settings'.'a.dotted.subkey'[0]`
5. `configuration::application.'general.settings'.'a.dotted.subkey'[1]`
6. `configuration::application.'general.settings'.'a.dotted.subkey'[2]`
7. `sensitive::accounts.database.app_user`
8. `sensitive::accounts.database.app_pass`
9. `sensitive::accounts.application.db.users[0].name`
10. `sensitive::accounts.application.db.users[0].pass`
11. `sensitive::accounts.application.db.users[0].access_level`
12. `sensitive::accounts.application.db.users[1].name`
13. `sensitive::accounts.application.db.users[1].pass`
14. `sensitive::accounts.application.db.users[1].access_level`

You could also access some of these sample nodes using search expressions, like:

1. `sensitive::accounts.application.db.users[name=admin].access_level`
2. `sensitive::accounts.application.db.users[access_level<500].name`

## Supported YAML Path Forms

YAML Path understands these forms:

* Array element selection:  `array[#]` (where `#` is the 0-based element number)
* Dot notation for Hash data structure sub-keys:  `hash.child.key`
* Demarcation for dotted Hash keys:  `hash.'dotted.child.key'` or `hash."dotted.child.key"`
* Escape symbol recognition:  `hash.dotted\.child\.key` or `keys_with_\\slashes`
* Top-level (Hash) Anchor lookups: `&anchor_name`
* Anchor lookups in Arrays:  `aliases[&anchor_name]`
* Hash attribute searches (which can return zero or more matches):
  * Exact match:  `sensitive::accounts.application.db.users[name=admin].pass`
  * Starts With match:  `sensitive::accounts.application.db.users[name^adm].pass`
  * Ends With match:  `sensitive::accounts.application.db.users[name$min].pass`
  * Contains match:  `sensitive::accounts.application.db.users[name%dmi].pass`
  * Less Than match: `sensitive::accounts.application.db.users[access_level<500].pass`
  * Greater Than match: `sensitive::accounts.application.db.users[access_level>0].pass`
  * Less Than or Equal match: `sensitive::accounts.application.db.users[access_level<=100].pass`
  * Greater Than or Equal match: `sensitive::accounts.application.db.users[access_level>=0].pass`
  * Invert any match with `!`, like: `sensitive::accounts.application.db.users[name!=admin].pass`
  * Demarcate and/or escape expression values, like: `sensitive::accounts.application.db.users[full\ name="Some User\'s Name"].pass`
  * Multi-level matching: `sensitive::accounts.application.db.users[name%admin].pass[encrypted!^ENC\[]`
* Hash key-name searches using `.`, yielding their values, not the keys themselves:  `sensitive::accounts.database[.^app_]`
* Complex combinations: `[2].some::deep.hierarchy[with!=""].'any.valid'[.$yaml][data%structure].complexity`

## Installing

This project requires [Python](https://www.python.org/) 3.6.  Most operating
systems and distributions have access to Python 3 even if only Python 2 came
pre-installed.  It is generally safe to have more than one version of Python on
your system at the same time.  Each version of Python uses a unique binary name
as well as different library and working directories, like `python2.7` versus
`python3.6`.  Further, each often provides symlinks like `python` (usually for
Python 2) and `python3`, respectively.

This project runs on all operating systems and distributions where Python 3.6
and project dependencies are able to run.  While the documentation examples here
are presented in Linux/OSX shell form, the same commands can be used on Windows
with minor adjustment.  Cygwin users are also able to enjoy this project.

Each published version of this project can be installed from
[PyPI](https://pypi.org/) using `pip`.  Note that on systems with more than one
version of Python, you will probably need to use `pip3`, or equivalent (e.g.:
Cygwin users may need to use `pip3.6`).

```shell
pip3 install yamlpath
```

## Based on ruamel.yaml and Python 3

In order to support the best available YAML editing capability (so called,
round-trip editing with support for comment preservation), this project is based
on [ruamel.yaml](https://bitbucket.org/ruamel/yaml/overview) for
Python 3.6.  While ruamel.yaml is based on PyYAML --
Python's "standard" YAML library -- ruamel.yaml is [objectively better than
PyYAML](https://yaml.readthedocs.io/en/latest/pyyaml.html).

Should PyYAML ever merge with -- or at least, catch up with -- ruamel.yaml, this
project can be (lightly) adapted to depend on it, instead:

* [Is this time to pass the baton?](https://github.com/yaml/pyyaml/issues/31)
* [Rebase off ruamel? - many new valuable features](https://github.com/yaml/pyyaml/issues/46)

### Compatible ruamel.yaml Versions

At the time of this writing, ruamel.yaml is unstable, presently undergoing a
refactoring and feature creation effort.  As it is a moving target, this project
is necessarily bound to limited ranges of compatible versions between it and the
ruamel.yaml project.  Futher, this project comes with fixes to some notable bugs
in ruamel.yaml.  As such, you should note which specific versions of ruamel.yaml
which this code is compatible with.  Failing to do so will probably lead to some
incompatbility.

This list will not be aggressively updated but rather, from time to time as
in/compatibility reports come in from users of this project.  At present, known
and tested compatible versions include:

YAML Path Version | ruamel.yaml Min | Max
------------------|-----------------|---------
1.0.x             | 0.15.92         | 0.15.94

You may find other compatible versions outside these ranges.  If you do, please
drop a note so this table can be updated!

## The Files of This Project

This repository contains:

1. Generally-useful Python library files.  These contain the reusable core of
   this project's YAML Path capabilities.
2. Some implementations of those libraries, exhibiting their capabilities and
   simple-to-use APIs.
3. Various support, documentation, and build files.

### Command-Line Tools

This project provides some command-line tool implementations which utilize
these YAML Path libraries:

* [eyaml-rotate-keys](bin/eyaml-rotate-keys) -- Rotates the encryption keys used
  for all EYAML values within a set of YAML files, decrypting with old keys and
  re-encrypting using replacement keys.
* [yaml-get](bin/yaml-get) -- Retrieves one or more values from a YAML file at a
  specified YAML Path.  Output is printed to STDOUT, one line per match.  When
  a result is a complex data-type (Array or Hash), a Python-compatible dump is
  produced to represent the entire complex result.  EYAML can be employed to
  decrypt the values.
* [yaml-set](bin/yaml-set) -- Changes one or more values in a YAML file at a
  specified YAML Path.  Matched values can be checked before they are replaced
  to mitigate accidental change. When matching singular results, the value can
  be archived to another key before it is replaced.  Further, EYAML can be
  employed to encrypt the new values and/or decrypt old values before checking
  them.

### Libraries

While there are several supporting library files like enumerations and
exceptions, the most interesting library files include:

* [parser.py](yamlpath/parser.py) The core YAML Path parser logic.
* [yamlpath.py](yamlpath/yamlpath.py) -- A collection of generally-useful YAML
  methods that enable easily setting and retrieving values via YAML Paths.
* [eyamlpath.py](yamlpath/eyaml/eyamlpath.py) -- Extends the YAMLPath class to
  support EYAML data encryption and decryption.

## Basic Usage

The files of this project can be used either as command-line tools -- to take
advantage of the existing example implementations -- or as libraries to
supplement your own implementations.

### Basic Usage:  Command-Line Tools

The command-line tools are self-documented.  Simply pass `--help` to them in
order to obtain detailed documentation.  Here are some simple examples of their
typical use-cases.

#### Rotate Your EYAML Keys

If the eyaml command is already on your PATH:

```shell
eyaml-rotate-keys \
  --oldprivatekey=~/old-keys/private_key.pkcs7.pem \
  --oldpublickey=~/old-keys/public_key.pkcs7.pem \
  --newprivatekey=~/new-keys/private_key.pkcs7.pem \
  --newpublickey=~/new-keys/public_key.pkcs7.pem \
  my_1st_yaml_file.yaml my_2nd_yaml_file.eyaml ... my_Nth_yaml_file.yaml
```

You could combine this with `find` and `xargs` if your E/YAML file are
dispersed through a directory hierarchy.

#### Get a YAML Value

At its simplest:

```shell
yaml-get --query=see.documentation.above.for.many.samples my_yaml_file.yaml
```

#### Change a YAML Value

For a no-frills change to a YAML file with deeply nested Hash structures:

```shell
yaml-set \
  --change=see.documentation.above.for.many.samples \
  --value="New Value" \
  my_yaml_file.yaml
```

Save a backup copy of the original YAML_FILE (with a .bak file-extension):

```shell
yaml-set \
  --change=see.documentation.above.for.many.samples \
  --value="New Value" \
  --backup \
  my_yaml_file.yaml
```

To rotate a password, preserving the old password perhaps so your automation can
apply the new password to your application(s):

```shell
yaml-set \
  --change=the.new.password \
  --saveto=the.old.password \
  --value="New Password" \
  --backup \
  my_yaml_file.yaml
```

To check the old password before rotating it, say to be sure you're changing out
the right one:

```shell
yaml-set \
  --change=the.new.password \
  --saveto=the.old.password \
  --check="Old Password" \
  --value="New Password" \
  --backup \
  my_yaml_file.yaml
```

This tool will create the `--change` within your YAML_FILE if it doesn't already
exist.  This may not always be ideal, perhaps when you need to be absolutely
certain that you're editing the right YAML_FILEs and/or have `--change` set
correctly.  In such cases, you can add `--mustexist` to disallow creating any
missing `--change` YAML Paths:

```shell
yaml-set \
  --change=the.new.password \
  --mustexist \
  --saveto=the.old.password \
  --check="Old Password" \
  --value="New Password" \
  --backup \
  my_yaml_file.yaml
```

You can also add EYAML encryption (assuming the `eyaml` command is on your
PATH; if not, you can pass `--eyaml` to specify its location).  In this example,
I add the optional `--format=folded` for this example so that the long EYAML
value is broken up into a multi-line value rather than one very long string.
This is the preferred format for EYAML consumers like Puppet.  Note that
`--format` has several other settings and applies only to new values.

```shell
yaml-set \
  --change=the.new.password \
  --mustexist \
  --saveto=the.old.password \
  --check="Old Password" \
  --value="New Password" \
  --eyamlcrypt \
  --format=folded \
  --backup \
  my_yaml_file.yaml
```

You can even tell EYAML which keys to use:

```shell
yaml-set \
  --change=the.new.password \
  --mustexist \
  --saveto=the.old.password \
  --check="Old Password" \
  --value="New Password" \
  --eyamlcrypt \
  --format=folded \
  --privatekey=/secret/keys/private_key.pkcs7.pem \
  --publickey=/secret/keys/public_key.pkcs7.pem \
  --backup \
  my_yaml_file.yaml
```

Note that for even greater security scenarios, you can keep the new value off of
your command-line, process list, and command history by swapping out `--value`
for one of `--stdin`, `--file`, or even `--random LENGTH` (use Python's
strongest random value generator if you don't need to specify the replacement
value in advance).

### Basic Usage:  Libraries

As for the libraries, they are also heavily documented and the example
implementations may perhaps serve as good copy-paste fodder (provided you give
credit to the source).  That said, here's a general flow/synopsis.

#### Initialize ruamel.yaml and These Helpers

Your preferences may differ, but I use this setup for round-trip YAML parsing
and editing with ruamel.yaml.  I also use `EYAMLPath` in virtually all cases
rather than `YAMLPath`, but you can do the opposite if you are absolutely
certain that your data will never be EYAML encrypted.

Note that `import yamlpath.patches` is entirely optional; I wrote and use it to
block ruamel.yaml's Emitter from injecting unnecessary newlines into folded
values (it improperly converts every single new-line into two for left-flushed
multi-line values, at the time of this writing).  Since block output EYAML
values are left-flushed multi-line folded strings, this fix is necessary when
using EYAML features.

Note also that these examples use `ConsolePrinter` to handle STDOUT and STDERR
messaging.  You don't have to.  However, some kind of logger must be passed to
these libraries so they can write messages _somewhere_.  Your custom message
handler or logger must provide the same API as ConsolePrinter; review the header
documentation in [consoleprinter.py](yamlpath/wrappers/consoleprinter.py) for
details.  Generally speaking, it would be trivial to write your own custom
wrapper for Python's standard logger facility for your own implementations which
may need to write to your operating system's central logging facility or even to
log files.

```python
import sys

from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError

from yamlpath.exceptions import YAMLPathException
from yamlpath.eyaml import EYAMLPath
from yamlpath.enums import YAMLValueFormats

import yamlpath.patches
from yamlpath.wrappers import ConsolePrinter

# Process command-line arguments, initialize the output writer and the YAMLPath
# processor.
args = processcli()
log = ConsolePrinter(args)
processor = EYAMLPath(log)

# Prep the YAML parser
yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.explicit_start = True
yaml.preserve_quotes = True
yaml.width = sys.maxsize

# At this point, you'd load or parse your YAML file, stream, or string.  When
# loading from file, I typically follow this pattern:
try:
    with open(args.yaml_file, 'r') as f:
        yaml_data = yaml.load(f)
except ParserError as e:
    log.error("YAML parsing error {}:  {}".format(str(e.problem_mark).lstrip(), e.problem))
```

#### Searching for YAML Nodes

These libraries use [Generators](https://wiki.python.org/moin/Generators) to get
nodes from parsed YAML data.  Identify which node(s) to get via
[YAML Path](#yaml-path) strings.  You should also catch `YAMLPathException`s
unless you prefer Python's native stack traces.  Whether you are working with a
single result or many, you must consume the Generator output with a pattern
similar to:

```python
yaml_path = "see.documentation.above.for.many.samples"
try:
    for node in yh.get_eyaml_values(yaml_data, yaml_path):
        # These Generators can return None, which means a node wasn't found but
        # because searches are recursive and can be multi-tier, the non-matching
        # leaf nodes can be encountered anywhere during the search, not only at
        # the very end.
        if node is None:
            continue

        log.debug("Got {} from {}.".format(node, yaml_path))

        # Do something with each node...
except YAMLPathException as ex:
    log.error(ex, 1)
```

#### Changing Values

At its simplest, you simply need to supply the pre-parsed YAML data, the YAML
Path to one or more nodes to update, and the value to apply to them.  Catching
`YAMLPathException` is optional but usually preferred over allowing Python to
dump the call stack in front of your users.

```python
try:
    yh.set_value(yaml_data, yaml_path, new_value)
except YAMLPathException as ex:
    log.error(ex, 1)
```
