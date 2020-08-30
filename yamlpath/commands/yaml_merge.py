"""
Enable users to merge YAML/Compatible files.

Due to the complexities of merging, users are given deep control over the merge
operation via both default behaviors as well as per YAML Path behaviors.

Copyright 2020 William W. Kimball, Jr. MBA MSIS

=========
DEV NOTES
=========
yaml-merge [OPTIONS] file1 [file... [fileN]]

OPTIONS:
* DEFAULT behaviors when handling:
  * arrays (keep LHS, keep RHS, append uniques, append all [default])
  * hashes (keep LHS, keep RHS, shallow merge, deep merge [default])
  * arrays-of-hashes
  * arrays-of-arrays
* anchor conflict handling (keep LHS, keep RHS, rename per file [aliases in
  same file follow suit], stop merge [default])
* merge-at (a YAML Path which indicates where in the LHS document all RHS
  documents are merged into [default=/])
* output (file)
* Configuration file for per-path options, like:
---
/just/an/array:  first|last|unique|all
/juat/a/hash:  first|last|shallow|deep
some.path.pointing.at.an.array.of.hashes:
  identity: key_with_unique_identifying_values

================================== EXAMPLE ====================================
aliases:
 - &scalar_anchor LHS aliased value
 - &unchanging_anchor Same value everywhere
key: LHS value
hash:
  key1: sub LHS value 1
  key2: sub LHS value 2
  complex:
    subkeyA: *scalar_anchor
array:
  - LHS element 1
  - non-unique element
  - *scalar_anchor
  - *unchanging_anchor

<< (RHS overrides LHS scalars;
    deep Hash merge;
    keep only unique Array elements; and
    rename conflicting anchors)

aliases:
 - &scalar_anchor RHS aliased value
 - &unchanging_anchor Same value everywhere
key: RHS value
hash:
  key1: sub RHS value 1
  key3: sub RHS value 3
  complex:
    subkeyA: *scalar_anchor
    subkeyB:
      - a
      - list
array:
  - RHS element 1
  - non-unique element
  - *scalar_anchor
  - *unchanging_anchor

==

aliases:
 - &scalar_anchor_1 LHS aliased value
 - &scalar_anchor_2 RHS aliased value
 - &unchanging_anchor Same value everywhere
key: RHS value
hash:
  key1: sub RHS value 1
  key2: sub LHS value 2
  key3: sub RHS value 3
  complex:
    subkeyA: *scalar_anchor_2  # Because "RHS overrides LHS scalars"
    subkeyB:
      - a
      - list
array:
  - LHS element 1
  - non-unique element
  - *scalar_anchor_1
  - *unchanging_anchor
  - RHS element 1
  - *scalar_anchor_2
===============================================================================

Processing Requirements:
1. Upon opening a YAML document, immediately scan the entire file for all
   anchor names.  Track those names across all documents as they are opened
   because conflicts must be resolved per user option selection.
"""
import sys
import argparse

from yamlpath.wrappers import ConsolePrinter

# Implied Constants
MY_VERSION = "0.0.1"

def processcli():
    """Process command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Merges two or more YAML/Compatible files together.",
        epilog="For more information about YAML Paths,\
            please visit https://github.com/wwkimball/yamlpath."
    )
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s " + MY_VERSION)

    noise_group = parser.add_mutually_exclusive_group()
    noise_group.add_argument(
        "-d", "--debug", action="store_true",
        help="output debugging details")
    noise_group.add_argument(
        "-v", "--verbose", action="store_true",
        help="increase output verbosity")
    noise_group.add_argument(
        "-q", "--quiet", action="store_true",
        help="suppress all output except errors")

    parser.add_argument("yaml_files", metavar="YAML_FILE", nargs="+",
                        help="one or more YAML files to merge")
    return parser.parse_args()


def validateargs(args, log):
    """Validate command-line arguments."""
    has_errors = False

	# * When set, the configuration file must be a readable file

    if has_errors:
        sys.exit(1)

def main():
    """Main code."""
    args = processcli()
    log = ConsolePrinter(args)
    validateargs(args, log)
