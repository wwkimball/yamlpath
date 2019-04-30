# YAML Tools

This is a set of generally-useful YAML and EYAML value editing tools.  Today, it
is based on [ruamel.yaml](https://bitbucket.org/ruamel/yaml/overview) for Python
3.  At the time of this writing, ruamel.yaml is unstable, presently undergoing a
refactoring and feature creation effort.  As it is a moving target, this project
is necessarily bound to limited ranges of compatible versions between it and the
ruamel.yaml project.  Futher, this project comes with fixes to some notable bugs
in ruamel.yaml.  As such, you should note which specific versions of ruamel.yaml
which this code is compatible with.  Failing to do so will probably lead to some
incompatbility.

## YAML Path

This project presents and utilizes YAML Paths, which are a human-friendly means
of expressing a path through the structure of YAML data to a specific key.  For
example:

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
        - name: *commonUsername
          pass: *commonPassword
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
11. `sensitive::accounts.application.db.users[1].name`
12. `sensitive::accounts.application.db.users[2].pass`

### Some Notable Notations

These examples illustrate some YAML Path representations of:

* Anchor lookups in Arrays:  `aliases[&anchor_name]`
* Dot notation for Hash data structure sub-keys:  `hash.child.key`
* Demarcation for dotted Hash keys:  `hash.'dotted.child.key'`
* Escape symbol recognition:  `keys_with_\\slashes`
* Array element selection:  `array[element#]`
* Array-of-Hashes unique key lookups:  `sensitive::accounts.application.db.users[name=admin].pass`

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
* yaml-change-value.py -- Changes a value in a YAML file at a specified YAML
  Path.  The value can be checked before it is replaced to mitigate accidental
  changes.  The value can also be archived to another key before it is replaced.
  EYAML can also be employed to encrypt the new value and/or decrypt the old
  value before checking it.
