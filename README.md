# YAML Path and Command-Line Tools

[![Build Status](https://travis-ci.org/wwkimball/yamlpath.svg?branch=master)](https://travis-ci.org/wwkimball/yamlpath)
[![Python versions](https://img.shields.io/pypi/pyversions/yamlpath.svg)](https://pypi.org/project/yamlpath/)
[![PyPI version](https://badge.fury.io/py/yamlpath.svg)](https://pypi.org/project/yamlpath/)
[![Coverage Status](https://coveralls.io/repos/github/wwkimball/yamlpath/badge.svg?branch=master)](https://coveralls.io/github/wwkimball/yamlpath?branch=master)

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
of identifying one or more nodes within a [YAML](https://yaml.org/),
[EYAML](https://github.com/voxpupuli/hiera-eyaml), or compatible data structure.
The libraries (modules) and several [command-line tool
implementations](#command-line-tools) are provided.

This implementation of YAML Path is a query langauge in addition to a node
descriptor.  With it, you can select a single precise node or search for any
number of nodes which match criteria that can be expressed in several ways.
Keys, values, and elements can all be searched at any number of levels within
the data structure using the same query.

Other versions of "yaml-path" exist but they fill different needs.  This
implementation was created specifically to enable selecting and editing YAML --
and compatible -- data of any complexity via an intuitive, expressive syntax.
Starting with the ubiquitous -- albeit limited -- dot-notation for accessing
Hash members, this YAML Path solution grew to include new syntax for:

* Array elements
* Anchors by name
* Search expressions for single or multiple matches
* Forward-slash notation

To illustrate some of these concepts, consider this sample YAML data:

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

Dot Notation                                                         | Forward-Slash Notation
---------------------------------------------------------------------|------------------------------------------------------------------
`aliases[&commonUsername]`                                           | `/aliases[&commonUsername]`
`aliases[&commonPassword]`                                           | `/aliases[&commonPassword]`
`configuration::application.'general.settings'.slash\\key`           | `/configuration::application/general.settings/slash\\key`
`configuration::application.'general.settings'.'a.dotted.subkey'[0]` | `/configuration::application/general.settings/a.dotted.subkey[0]`
`configuration::application.'general.settings'.'a.dotted.subkey'[1]` | `/configuration::application/general.settings/a.dotted.subkey[1]`
`configuration::application.'general.settings'.'a.dotted.subkey'[2]` | `/configuration::application/general.settings/a.dotted.subkey[2]`
`sensitive::accounts.database.app_user`                              | `/sensitive::accounts/database/app_user`
`sensitive::accounts.database.app_pass`                              | `/sensitive::accounts/database/app_pass`
`sensitive::accounts.application.db.users[0].name`                   | `/sensitive::accounts/application/db/users[0]/name`
`sensitive::accounts.application.db.users[0].pass`                   | `/sensitive::accounts/application/db/users[0]/pass`
`sensitive::accounts.application.db.users[0].access_level`           | `/sensitive::accounts/application/db/users[0]/access_level`
`sensitive::accounts.application.db.users[1].name`                   | `/sensitive::accounts/application/db/users[1]/name`
`sensitive::accounts.application.db.users[1].pass`                   | `/sensitive::accounts/application/db/users[1]/pass`
`sensitive::accounts.application.db.users[1].access_level`           | `/sensitive::accounts/application/db/users[1]/access_level`

You could also access some of these sample nodes using search expressions, like:

Dot Notation                                                                          | Forward-Slash Notation
--------------------------------------------------------------------------------------|------------------------------------------------------------------
`configuration::application.general\.settings.'a.dotted.subkey'[.=~/^element[1-2]$/]` | `/configuration::application/general.settings/a.dotted.subkey[.=~/^element[1-2]$/]`
`configuration::application.general\.settings.'a.dotted.subkey'[1:2]`                 | `/configuration::application/general.settings/a.dotted.subkey[0:-2]`
`sensitive::accounts.application.db.users[name=admin].access_level`                   | `/sensitive::accounts/application/db/users[name=admin]/access_level`
`sensitive::accounts.application.db.users[access_level<500].name`                     | `/sensitive::accounts/application/db/users[access_level<500]/name`

## Supported YAML Path Forms

YAML Path understands these forms:

* Top-level Array element selection: `[#]` where `#` is the 0-based element number (`#` can also be negative, causing the element to be selected from the end of the Array)
* Top-level Hash key selection: `key`
* Dot notation for Hash sub-keys:  `hash.child.key`
* Demarcation for dotted Hash keys:  `hash.'dotted.child.key'` or `hash."dotted.child.key"`
* Array element selection:  `array[#]` where `array` is omitted for top-level Arrays or is the name of the Hash key containing Array data and `#` is the 0-based element number (`#` can also be negative, causing the element to be selected from the end of the Array)
* Array slicing: `array[start#:stop#]` where `start#` is the first, zero-based element and `stop#` is the last element to select (either or both can be negative, causing the elements to be selected from the end of the Array)
* Hash slicing: `hash[min:max]` where `min` and `max` are alphanumeric terms between which the Hash's keys are compared
* Escape symbol recognition:  `hash.dotted\.child\.key` or `keys_with_\\slashes`
* Top-level (Hash) Anchor lookups: `&anchor_name`
* Anchor lookups in Arrays:  `array[&anchor_name]`
* Hash attribute searches (which can return zero or more matches):
  * Exact match:  `sensitive::accounts.application.db.users[name=admin].pass`
  * Starts With match:  `sensitive::accounts.application.db.users[name^adm].pass`
  * Ends With match:  `sensitive::accounts.application.db.users[name$min].pass`
  * Contains match:  `sensitive::accounts.application.db.users[name%dmi].pass`
  * Less Than match: `sensitive::accounts.application.db.users[access_level<500].pass`
  * Greater Than match: `sensitive::accounts.application.db.users[access_level>0].pass`
  * Less Than or Equal match: `sensitive::accounts.application.db.users[access_level<=100].pass`
  * Greater Than or Equal match: `sensitive::accounts.application.db.users[access_level>=0].pass`
  * Regular Expression matches using any delimiter you choose (other than `/`, if you need something else): `sensitive::accounts.application.db.users[access_level=~/^\D+$/].pass` or `some::hash[containing=~"/path/values"]`
  * Invert any match with `!`, like: `sensitive::accounts.application.db.users[name!=admin].pass`
  * Demarcate and/or escape expression values, like: `sensitive::accounts.application.db.users[full\ name="Some User\'s Name"].pass`
  * Multi-level matching: `sensitive::accounts.application.db.users[name%admin].pass[encrypted!^ENC\[]`
* Array element and Hash key-name searches with all of the search methods above via `.` (yields their values, not the keys themselves): `sensitive::accounts.database[.^app_]`
* Complex combinations: `some::deep.hierarchy[with!=""].'any.valid'[.$yaml][data%structure].or[!complexity=~/^.{4}$/][2]`
* Forward-slash rather than dot notation:  `/key` up to `/some::deep/hierarchy[with!=""]/any.valid[.$yaml][data%structure]/or[!complexity=~/^.{4}$/][2]`

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
that this code is compatible with.  Failing to do so will probably lead to some
incompatbility.

This list will not be aggressively updated but rather, from time to time as
in/compatibility reports come in from users of this project.  At present, known
and tested compatible versions include:

YAML Path Version | ruamel.yaml Min | Max
------------------|-----------------|---------
1.0.x             | 0.15.92         | 0.15.94
1.1.x             | 0.15.92         | 0.15.94

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

```text
usage: eyaml-rotate-keys [-h] [-V] [-d | -v | -q] [-b] [-x EYAML]
                         -i OLDPRIVATEKEY -c OLDPUBLICKEY
                         -r NEWPRIVATEKEY -u NEWPUBLICKEY
                         YAML_FILE [YAML_FILE ...]

Rotates the encryption keys used for all EYAML values within a set of YAML
files, decrypting with old keys and re-encrypting using replacement keys.

positional arguments:
  YAML_FILE             one or more YAML files containing EYAML values

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -d, --debug           output debugging details
  -v, --verbose         increase output verbosity
  -q, --quiet           suppress all output except errors
  -b, --backup          save a backup of each modified YAML_FILE with an extra
                        .bak file-extension
  -x EYAML, --eyaml EYAML
                        the eyaml binary to use when it isn't on the PATH

EYAML_KEYS:
  All key arguments are required

  -r NEWPRIVATEKEY, --newprivatekey NEWPRIVATEKEY
                        the new EYAML private key
  -u NEWPUBLICKEY, --newpublickey NEWPUBLICKEY
                        the new EYAML public key
  -i OLDPRIVATEKEY, --oldprivatekey OLDPRIVATEKEY
                        the old EYAML private key
  -c OLDPUBLICKEY, --oldpublickey OLDPUBLICKEY
                        the old EYAML public key

Any YAML_FILEs lacking EYAML values will not be modified (or backed up, even
when -b/--backup is specified).
```

* [yaml-get](bin/yaml-get) -- Retrieves one or more values from a YAML file at a
  specified YAML Path.  Output is printed to STDOUT, one line per match.  When
  a result is a complex data-type (Array or Hash), a Python-compatible dump is
  produced to represent the entire complex result.  EYAML can be employed to
  decrypt the values.

```text
usage: yaml-get [-h] [-V] -p YAML_PATH [-x EYAML] [-r PRIVATEKEY]
                [-u PUBLICKEY] [-d | -v | -q]
                YAML_FILE

Gets one or more values from a YAML file at a specified YAML Path. Can employ
EYAML to decrypt values.

positional arguments:
  YAML_FILE             the YAML file to query

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -d, --debug           output debugging details
  -v, --verbose         increase output verbosity
  -q, --quiet           suppress all output except errors

required settings:
  -p YAML_PATH, --query YAML_PATH
                        YAML Path to query

EYAML options:
  Left unset, the EYAML keys will default to your system or user defaults.
  Both keys must be set either here or in your system or user EYAML
  configuration file when using EYAML.

  -x EYAML, --eyaml EYAML
                        the eyaml binary to use when it isn't on the PATH
  -r PRIVATEKEY, --privatekey PRIVATEKEY
                        EYAML private key
  -u PUBLICKEY, --publickey PUBLICKEY
                        EYAML public key

For more information about YAML Paths, please visit
https://github.com/wwkimball/yamlpath.
```

* [yaml-set](bin/yaml-set) -- Changes one or more values in a YAML file at a
  specified YAML Path.  Matched values can be checked before they are replaced
  to mitigate accidental change. When matching singular results, the value can
  be archived to another key before it is replaced.  Further, EYAML can be
  employed to encrypt the new values and/or decrypt old values before checking
  them.

```text
usage: yaml-set [-h] [-V] -g YAML_PATH [-a VALUE | -f FILE | -i | -R LENGTH]
                [-F {bare,boolean,default,dquote,float,folded,int,literal,squote}]
                [-c CHECK] [-s YAML_PATH] [-m] [-b] [-e] [-x EYAML]
                [-r PRIVATEKEY] [-u PUBLICKEY] [-d | -v | -q]
                YAML_FILE

Changes one or more values in a YAML file at a specified YAML Path. Matched
values can be checked before they are replaced to mitigate accidental change.
When matching singular results, the value can be archived to another key
before it is replaced. Further, EYAML can be employed to encrypt the new
values and/or decrypt an old value before checking them.

positional arguments:
  YAML_FILE             the YAML file to update

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show program's version number and exit
  -F {bare,boolean,default,dquote,float,folded,int,literal,squote}, --format {bare,boolean,default,dquote,float,folded,int,literal,squote}
                        override automatic formatting of the new value
  -c CHECK, --check CHECK
                        check the value before replacing it
  -s YAML_PATH, --saveto YAML_PATH
                        save the old value to YAML_PATH before replacing it
  -m, --mustexist       require that the --change YAML_PATH already exist in
                        YAML_FILE
  -b, --backup          save a backup YAML_FILE with an extra .bak file-
                        extension
  -d, --debug           output debugging details
  -v, --verbose         increase output verbosity
  -q, --quiet           suppress all output except errors

required settings:
  -g YAML_PATH, --change YAML_PATH
                        YAML Path where the target value is found

input options:
  -a VALUE, --value VALUE
                        set the new value from the command-line instead of
                        STDIN
  -f FILE, --file FILE  read the new value from file (discarding any trailing
                        new-lines)
  -i, --stdin           accept the new value from STDIN (best for sensitive
                        data)
  -R LENGTH, --random LENGTH
                        randomly generate a replacement value of a set length

EYAML options:
  Left unset, the EYAML keys will default to your system or user defaults.
  Both keys must be set either here or in your system or user EYAML
  configuration file when using EYAML.

  -e, --eyamlcrypt      encrypt the new value using EYAML
  -x EYAML, --eyaml EYAML
                        the eyaml binary to use when it isn't on the PATH
  -r PRIVATEKEY, --privatekey PRIVATEKEY
                        EYAML private key
  -u PUBLICKEY, --publickey PUBLICKEY
                        EYAML public key

When no changes are made, no backup is created, even when -b/--backup is
specified. For more information about YAML Paths, please visit
https://github.com/wwkimball/yamlpath.
```

### Libraries

While there are several supporting library files like enumerations and
exceptions, the most interesting library files include:

* [parser.py](yamlpath/parser.py) -- The core YAML Path parser logic.
* [yamlpath.py](yamlpath/yamlpath.py) -- A collection of generally-useful YAML
  methods that enable easily setting and retrieving values via YAML Paths.
* [eyamlpath.py](yamlpath/eyaml/eyamlpath.py) -- Extends the YAMLPath class to
  support EYAML data encryption and decryption.

## Basic Usage

The files of this project can be used either as command-line tools -- to take
advantage of the existing example implementations -- or as libraries to
supplement your own implementations.

### Basic Usage:  Command-Line Tools

The command-line tools are self-documented and [their documentation is captured
above](#command-line-tools) for easy reference.  Simply pass `--help` to them in
order to obtain the same detailed documentation.  Here are some simple examples
of their typical use-cases.

#### Rotate Your EYAML Keys

If the eyaml command is already on your PATH (if not, be sure to also supply
the optional `--eyaml` or `-x` argument):

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
yaml-get \
  --query=see.documentation.above.for.many.samples \
  my_yaml_file.yaml
```

#### Change a YAML Value

For a no-frills change to a YAML file with deeply nested Hash structures:

```shell
yaml-set \
  --change=see.documentation.above.for.many.samples \
  --value="New Value" \
  my_yaml_file.yaml
```

To rotate a password, preserving the old password perhaps so your automation can
apply the new password to your application(s):

```shell
yaml-set \
  --change=the.new.password \
  --saveto=the.old.password \
  --value="New Password" \
  my_yaml_file.yaml
```

For the extremely cautious, you could check the old password before rotating
it, save a backup of the original file, and mandate that the password path
already exist within the data before replacing it:

```shell
yaml-set \
  --mustexist \
  --change=the.new.password \
  --saveto=the.old.password \
  --check="Old Password" \
  --value="New Password" \
  --backup \
  my_yaml_file.yaml
```

You can also add EYAML encryption (assuming the `eyaml` command is on your
PATH; if not, you can pass `--eyaml` to specify its location).  In this example,
I add the optional `--format=folded` so that the long EYAML value is broken up
into a multi-line value rather than one very long string.  This is the preferred
format for EYAML consumers like Puppet.  Note that `--format` has several other
settings and applies only to new values.

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

You can even tell EYAML which keys to use, if not your default system or user
keys:

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
wrapper for Python's standard logging facilities if you require targets other
than STDOUT and STDERR.

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
unless you prefer Python's native stack traces.  When using EYAML, you should
also catch `EYAMLCommandException`s for the same reason.  Whether you are
working with a single result or many, you must consume the Generator output with
a pattern similar to:

```python
yaml_path = "see.documentation.above.for.many.samples"
try:
    for node in yh.get_eyaml_values(yaml_data, yaml_path):
        log.debug("Got {} from {}.".format(node, yaml_path))

        # Do something with each node...
except YAMLPathException as ex:
    # If merely retrieving data, this exception may be deemed non-critical
    # unless your later code absolutely depends upon a result.
    log.error(ex)
except EYAMLCommandException as ex:
    log.critical(ex, 120)
```

#### Changing Values

At its simplest, you only need to supply the pre-parsed YAML data, the YAML
Path to one or more nodes to update, and the value to apply to them.  Catching
`YAMLPathException` is optional but usually preferred over allowing Python to
dump the call stack in front of your users.  When using EYAML, the same applies
to `EYAMLCommandException`.

```python
try:
    yh.set_value(yaml_data, yaml_path, new_value)
except YAMLPathException as ex:
    log.critical(ex, 119)
except EYAMLCommandException as ex:
    log.critical(ex, 120)
```
