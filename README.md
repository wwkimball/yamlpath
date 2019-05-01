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

## Compatible ruamel.yaml Versions

This list will not be aggressively updated but rather, from time to time as
in/compatibility reports come it from users of this project.  At present, known
compatible versions include:

YAML Tools Version | ruamel.yaml Min | Max
-------------------|-----------------|---------
1.0.x              | 0.15.92         | 0.15.95

You may find other compatible versions outside these ranges.

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
  employed to encrypt the new values and/or decrypt an old value before checking
  them.
