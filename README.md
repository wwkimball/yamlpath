# YAML Tools

This is a set of generally-useful [YAML](https://yaml.org/) and
[EYAML](https://github.com/voxpupuli/hiera-eyaml) value editing tools.  Today,
it is based on [ruamel.yaml](https://bitbucket.org/ruamel/yaml/overview) for
[Python](https://www.python.org/) 3.  At the time of this writing, ruamel.yaml
is unstable, presently undergoing a refactoring and feature creation effort.
As it is a moving target, this project is necessarily bound to limited ranges
of compatible versions between it and the ruamel.yaml project.  Futher, this
project comes with fixes to some notable bugs in ruamel.yaml.  As such, you
should note which specific versions of ruamel.yaml which this code is
compatible with.  Failing to do so will probably lead to some incompatbility.

## Compatible ruamel.yaml Versions

This list will not be aggressively updated but rather, from time to time as
in/compatibility reports come in from users of this project.  At present, known
compatible versions include:

YAML Tools Version | ruamel.yaml Min | Max
-------------------|-----------------|---------
1.0.x              | 0.15.92         | 0.15.95

You may find other compatible versions outside these ranges.

## YAML Path

This project presents and utilizes YAML Paths, which are a human-friendly means
of expressing a path through the structure of YAML data to a specific key or a
set of keys matching some search criteria.  For example:

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

Contains these sample YAML Paths:

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

### Some Notable YAML Path Notations

YAML Path understands these forms:

* Anchor lookups in Arrays:  `aliases[&anchor_name]`
* Dot notation for Hash data structure sub-keys:  `hash.child.key`
* Demarcation for dotted Hash keys:  `hash.'dotted.child.key'`
* Escape symbol recognition:  `keys_with_\\slashes`
* Array element selection:  `array[element#]`
* Hash key lookups (which can return zero or more matches):
  * Exact match:  `sensitive::accounts.application.db.users[name=admin].pass`
  * Starts With match:  `sensitive::accounts.application.db.users[name^adm].pass`
  * Ends With match:  `sensitive::accounts.application.db.users[name$min].pass`
  * Contains match:  `sensitive::accounts.application.db.users[name%dmi].pass`
  * Less Than match: `sensitive::accounts.application.db.users[access_level<500].pass`
  * Greater Than match: `sensitive::accounts.application.db.users[access_level>0].pass`
  * Less Than or Equal match: `sensitive::accounts.application.db.users[access_level<=100].pass`
  * Greater Than or Equal match: `sensitive::accounts.application.db.users[access_level>=0].pass`
  * Invert any match with `!`, like: `sensitive::accounts.application.db.users[name!=admin].pass`
  * Demarcate expression values, like: `sensitive::accounts.application.db.users[full_name="Some User\'s Name"].pass`
  * Multi-level matching: `sensitive::accounts.application.db.users[name%admin].pass[encrypted!^ENC\[]`
* Complex combinations: `[2].some::complex.structure[with!=""].any[&valid].[yaml=data]`

## The Files of This Project

This repository contains:

1. Generally-useful Python library files.  These contain the reusable core of
   this project's editing capabilities.
2. Some implementations of those libraries, exhibiting their capabilities and
   simple APIs.
3. Various support, documentation, and build files.

More specifically, the most interesting files include:

* yamlhelpers.py -- A collection of generally-useful YAML methods that enable
  setting and retrieving values via YAML Paths (my own notation for representing
  otherwise complex YAML nodes in human-readable form).
* eyamlhelpers.py -- A collection of generally-useful EYAML methods that
  simplify interacting with the eyaml command to read and write encrypted YAML
  values.

I have used these libraries to write two implementations which I needed for my
own projects and which you may also find use for:

* rotate-eyaml-keys.py -- Rotates the encryption keys used for all EYAML values
  within a set of YAML files, decrypting with old keys and re-encrypting using
  replacement keys.
* yaml-change-value.py -- Changes one or more values in a YAML file at a
  specified YAML Path.  Matched values can be checked before they are replaced
  to mitigate accidental change. When matching singular results, the value can
  be archived to another key before it is replaced.  Further, EYAML can be
  employed to encrypt the new values and/or decrypt old values before checking
  them.

## Basic Usage

The files of this project can be used either as command-line scripts to take
advantage of the existing example implementations or as libraries to supplement
your own implementations.

### Basic Usage:  Command-Line Tools

The command-line implementations (above) are self-documented.  Simply pass
`--help` to them in order to learn their capabilities.  Here are some simple examples.

#### Rotate Your EYAML Keys

If the eyaml command is already on your PATH:

```shell
rotate-eyaml-keys.py \
  --oldprivatekey=~/old-keys/private_key.pkcs7.pem \
  --oldpublickey=~/old-keys/public_key.pkcs7.pem \
  --newprivatekey=~/new-keys/private_key.pkcs7.pem \
  --newpublickey=~/new-keys/public_key.pkcs7.pem \
  my_1st_yaml_file.yaml my_2nd_yaml_file.eyaml ... my_Nth_yaml_file.yaml
```

You could combine this with `find` and `xargs` if your E/YAML file are
dispersed through a directory hierarchy.

#### Change a YAML Value

For a no-frills change to a YAML file with deeply nested Hash structures:

```shell
yaml-change-value.py \
  --key=see.documentation.above.for.many.samples \
  --value="New Value" \
  my_yaml_file.yaml
```

Save a backup copy of the original YAML_FILE (with a .bak file-extension):

```shell
yaml-change-value.py \
  --key=see.documentation.above.for.many.samples \
  --value="New Value" \
  --backup \
  my_yaml_file.yaml
```

To rotate a password, preserving the old password perhaps so your automation can
apply the new password to your application(s):

```shell
yaml-change-value.py \
  --key=the.new.password \
  --saveto=the.old.password \
  --value="New Password" \
  --backup \
  my_yaml_file.yaml
```

To check the old password before rotating it, say to be sure you're changing out the right one:

```shell
yaml-change-value.py \
  --key=the.new.password \
  --saveto=the.old.password \
  --check="Old Password" \
  --value="New Password" \
  --backup \
  my_yaml_file.yaml
```

This tool will create the `--key` within your YAML_FILE if it doesn't already
exist.  This may not always be ideal, perhaps when you need to be absolutely
certain that you're editing the right YAML_FILEs and/or have `--key` set
correctly.  In such cases, you can add `--mustexist` to disallow creating
missing `--key` YAML Paths:

```shell
yaml-change-value.py \
  --key=the.new.password \
  --mustexist \
  --saveto=the.old.password \
  --check="Old Password" \
  --value="New Password" \
  --backup \
  my_yaml_file.yaml
```

You can also add EYAML encryption (assuming the `eyaml` command is on your
PATH).  In this example, I add the optional `--format=folded` for this example
so that the long EYAML value is broken up into a multi-line value rather than
one very long string.  This is the preferred format for EYAML consumers like
Puppet.  Note that `--format` has several other settings and applies only to
new values.

```shell
yaml-change-value.py \
  --key=the.new.password \
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
yaml-change-value.py \
  --key=the.new.password \
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
and editing with ruamel.yaml.  Note that `import ruamelpatches` is entirely
optional; I wrote and use it to block ruamel.yaml's Emitter from injecting
unnecessary newlines into folded values (it improperly converts every single
new-line into two for left-flushed multi-line values, at the time of this
writing).  Since block output EYAML values are left-flushed multi-line folded
strings, this fix is necessary when using EYAML features (at the time of this
writing).

```python
import sys

from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError

import ruamelpatches
from yamlexceptions import YAMLPathException
from consoleprinter import ConsolePrinter
from eyamlhelpers import EYAMLHelpers
from yamlhelpers import YAMLValueFormats

# My examples use ConsolePrinter to handle STDOUT and STDERR messaging.  You
# don't have to but some kind of logger must be passed to my libraries so they
# can write messages _somewhere_.  Your custom message handler or logger must
# provide the same API as ConsolePrinter; review the header documentation in
# consoleprinter.py for details.
args = processcli()
log = ConsolePrinter(args)
validateargs(args, log)
yh = EYAMLHelpers(log)

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
    log.error("YAML parsing error " + str(e.problem_mark).lstrip() + ": " + e.problem)
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
