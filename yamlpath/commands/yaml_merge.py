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
  * arrays-of-hashes (requires identifier key; then regular hash options)
  * arrays-of-arrays (regular array options)
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
  merge: deep

Array-of-Arrays:
[[5,6],[1,2],[4,3]]
- - 5
  - 6
- - 1
  - 2
- - 4
  - 3

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
from os import access, R_OK
from os.path import isfile

from yamlpath.enums import AnchorConflictResolutions
from yamlpath.func import get_yaml_data, get_yaml_editor
from yamlpath import Processor

from yamlpath.wrappers import ConsolePrinter

# Implied Constants
MY_VERSION = "0.0.1"

def processcli():
    """Process command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Merges two or more YAML/Compatible files together.",
        epilog="The left-to-right order of yaml_files is significant.  Except\
            when this behavior is deliberately altered by your options, data\
            from files on the right overrides data in files to their left.  \
            For more information about YAML Paths, please visit\
            https://github.com/wwkimball/yamlpath."
    )
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s " + MY_VERSION)

    parser.add_argument("-c", "--config",
                        help="configuration file for YAML Path specified merge\
                              control options")

    parser.add_argument(
        "-a", "--anchors",
        default="stop",
        choices=[l.lower() for l in AnchorConflictResolutions.get_names()],
        type=str.lower,
        help="default means by which Anchor name conflicts are resolved\
              (overridden on a YAML Path basis via --config|-c);\
              default=stop")

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
                        help="one or more YAML files to merge,\
                              order-significant")
    return parser.parse_args()


def validateargs(args, log):
    """Validate command-line arguments."""
    has_errors = False

    # There must be at least two input files
    if len(args.yaml_files) < 2:
        has_errors = True
        log.error("There must be at least two YAML_FILEs.")

    # When set, the configuration file must be a readable file
    if args.config and not (
            isfile(args.config)
            and access(args.config, R_OK)
    ):
        has_errors = True
        log.error(
            "YAML configuration file is not readable:  " + args.config)

    if has_errors:
        sys.exit(1)

def merge_dicts(lhs, rhs, args, config):
    """Merge two dicts."""
    return lhs

def merge_lists(lhs, rhs, args, config):
    """Merge two lists."""
    return lhs

def merge_documents(lhs, rhs, args, config):
    """Merge two YAML documents."""
    # Loop through all elements in RHS
    if isinstance(rhs, dict):
        for key, val in rhs.items():
            if lhs[key]:
                # LHS has the RHS key
                lhs[key] = merge_dicts(lhs[key], rhs[key], args, config)
            else:
                # LHS lacks the RHS key
                lhs[key] = val
    elif isinstance(rhs, list):
        for idx, ele in enumerate(rhs):
            pass

    return lhs

def scan_for_anchors(dom, anchors, log):
    """Scan a document for all anchors contained within."""
    if isinstance(dom, dict):
        for key, val in dom.items():
            if hasattr(key, "anchor") and key.anchor.value is not None:
                # log.debug("scan_for_anchors: Tracking key {} anchor {}"
                #           .format(key, key.anchor.value))
                anchors[key.anchor.value] = key

            if hasattr(val, "anchor") and val.anchor.value is not None:
                # log.debug("scan_for_anchors: Tracking val {} anchor {}"
                #           .format(val, val.anchor.value))
                anchors[val.anchor.value] = val

            # Recurse into complex values
            if isinstance(val, (dict, list)):
                scan_for_anchors(val, anchors, log)

    elif isinstance(dom, list):
        for ele in dom:
            scan_for_anchors(ele, anchors, log)

    elif hasattr(dom, "anchor"):
        # log.debug("scan_for_anchors: Tracking dom {} anchor {}"
        #           .format(dom, dom.anchor.value))
        anchors[dom.anchor.value] = dom

def overwrite_aliased_values(dom, anchor, value, log):
    pass

def calc_unique_anchor(anchor, known_anchors, log):
    """Generate a unique anchor name within a document pair."""
    log.debug("calc_unique_anchor: Preexisting Anchors:")
    log.debug(known_anchors)
    while anchor in known_anchors:
        anchor = "{}_{}".format(anchor, str(hash(anchor)).replace("-", "_"))
        log.debug("calc_unique_anchor: Trying new anchor name, {}."
                  .format(anchor))
    return anchor

def rename_anchor(dom, anchor, new_anchor):
    """Rename every use of an anchor in a document."""
    if isinstance(dom, dict):
        for key, val in dom.items():
            if hasattr(key, "anchor") and key.anchor.value == anchor:
                key.anchor.value = new_anchor
            if hasattr(val, "anchor") and val.anchor.value == anchor:
                val.anchor.value = new_anchor
            rename_anchor(val, anchor, new_anchor)
    elif isinstance(dom, list):
        for ele in dom:
            rename_anchor(ele, anchor, new_anchor)
    elif hasattr(dom, "anchor") and dom.anchor.value == anchor:
        dom.anchor.value = new_anchor

def resolve_anchor_conflicts(lhs, rhs, args, log):
    """Resolve anchor conflicts."""
    lhs_anchors = {}
    scan_for_anchors(lhs, lhs_anchors, log)
    log.debug("LHS Anchors:")
    log.debug(lhs_anchors)

    rhs_anchors = {}
    scan_for_anchors(rhs, rhs_anchors, log)
    log.debug("RHS Anchors:")
    log.debug(rhs_anchors)

    for anchor in rhs_anchors:
        if anchor in lhs_anchors:
            # It is only a conflict if the value differs; however, the
            # value may be a scalar, list, or dict.  Further, lists and
            # dicts may contain other aliased values which must also be
            # checked for equality (or pointing at identical anchors).
            prime_alias = lhs_anchors[anchor]
            reader_alias = rhs_anchors[anchor]
            conflict_mode = AnchorConflictResolutions.from_str(args.anchors)

            if isinstance(prime_alias, dict):
                log.error("Dictionary-based anchor conflict resolution is not"
                          " yet implemented.", 142)
            elif isinstance(prime_alias, list):
                log.error("List-based anchor conflict resolution is not yet"
                          " implemented.", 142)
            else:
                if prime_alias != reader_alias:
                    if conflict_mode is AnchorConflictResolutions.RENAME:
                        log.debug("Anchor {} conflict; will RENAME anchors."
                                  .format(anchor))
                        rename_anchor(rhs, anchor, calc_unique_anchor(anchor,
                                      set(lhs_anchors.keys())
                                      .union(set(rhs_anchors.keys())), log))
                    elif conflict_mode is AnchorConflictResolutions.FIRST:
                        log.debug("Anchor {} conflict; FIRST will override."
                                  .format(anchor))
                        overwrite_aliased_values(rhs, anchor, prime_alias, log)
                    elif conflict_mode is AnchorConflictResolutions.LAST:
                        log.debug("Anchor {} conflict; LAST will override."
                                  .format(anchor))
                        overwrite_aliased_values(lhs, anchor, reader_alias,
                                                 log)
                    else:
                        log.error("Aborting due to anchor conflict, {}"
                                  .format(anchor), 4)

def main():
    """Main code."""
    args = processcli()
    log = ConsolePrinter(args)
    validateargs(args, log)

    # Load the configuration file when one is specified
    processor_config = Processor(log, None)
    if args.config:
        config_yaml = get_yaml_editor()
        config_data = get_yaml_data(config_yaml, log, args.config)
        if config_data:
            processor_config.data = config_data

    # The first input file is the prime
    fileiterator = iter(args.yaml_files)
    yaml_editor = get_yaml_editor()
    prime_file = next(fileiterator)
    yaml_data = get_yaml_data(yaml_editor, log, prime_file)
    processor_prime = Processor(log, yaml_data)

    # Merge additional input files into the prime
    exit_state = 0
    yaml_reader = get_yaml_editor()
    processor_reader = Processor(log, None)
    for yaml_file in fileiterator:
        # Each YAML_FILE must actually be a file; because merge data is
        # expected, this is a fatal failure.
        if not isfile(yaml_file):
            log.error("Not a file:  {}".format(yaml_file))
            exit_state = 2
            break

        log.info("Processing {}...".format(yaml_file))

        # Try to open the file; failures are fatal
        yaml_data = get_yaml_data(yaml_reader, log, yaml_file)
        if yaml_data is None:
            # An error message has already been logged
            exit_state = 3
            break

        processor_reader.data = yaml_data

        resolve_anchor_conflicts(processor_prime.data, processor_reader.data,
                               args, log)
        merge_documents(processor_prime, processor_reader,
                        args, processor_config)

        # Update the prime anchor dict

    sys.exit(exit_state)

if __name__ == "__main__":
    main()  # pragma: no cover
