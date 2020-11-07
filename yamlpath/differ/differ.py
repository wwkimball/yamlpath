"""
Implement YAML document Differ.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from itertools import zip_longest
from typing import Any, Dict, Generator, List, Optional, Tuple

from ruamel.yaml.comments import CommentedMap, CommentedSeq

from yamlpath import YAMLPath
from yamlpath.wrappers import ConsolePrinter, NodeCoords
from yamlpath.eyaml import EYAMLProcessor
from .enums import ArrayDiffOpts, AoHDiffOpts, DiffActions
from .diffentry import DiffEntry
from .differconfig import DifferConfig


class Differ:
    """Calculates the difference between two YAML documents."""

    def __init__(
        self, config: DifferConfig, logger: ConsolePrinter, document: Any,
        **kwargs
    ) -> None:
        """
        Instantiate this class into an object.

        Parameters:
        1. logger (ConsolePrinter) Instance of ConsoleWriter or subclass
        2. document (Any) The basis document

        Returns:  N/A

        Raises:  N/A
        """
        ignore_eyaml = kwargs.pop("ignore_eyaml_values", True)

        self.config: DifferConfig = config
        self.logger: ConsolePrinter = logger
        self._data: Any = document
        self._diffs: List[DiffEntry] = []
        self._ignore_eyaml: bool = ignore_eyaml
        self._eyamlproc = (None
                           if ignore_eyaml
                           else EYAMLProcessor(logger, document, **kwargs))

    def compare_to(self, document: Any) -> None:
        """Perform the diff calculation."""
        self._diffs.clear()
        self.config.prepare(document)
        self._diff_between(YAMLPath(), self._data, document)

    def get_report(self) -> Generator[DiffEntry, None, None]:
        """Get the diff report."""
        for entry in sorted(
            self._diffs, key=lambda e: [int(i) for i in e.index.split('.')]
        ):
            yield entry

    def _purge_document(self, path: YAMLPath, data: Any):
        """Delete every node in the document."""
        if isinstance(data, CommentedMap):
            lhs_iteration = -1
            for key, val in data.items():
                lhs_iteration += 1
                next_path = (path +
                    YAMLPath.escape_path_section(key, path.seperator))
                self._diffs.append(
                    DiffEntry(
                        DiffActions.DELETE, next_path, val, None,
                        lhs_parent=data, lhs_iteration=lhs_iteration))
        elif isinstance(data, CommentedSeq):
            for idx, ele in enumerate(data):
                next_path = path + "[{}]".format(idx)
                self._diffs.append(
                    DiffEntry(
                        DiffActions.DELETE, next_path, ele, None,
                        lhs_parent=data, lhs_iteration=idx))
        else:
            if data is not None:
                self._diffs.append(
                    DiffEntry(DiffActions.DELETE, path, data, None)
                )

    def _add_everything(self, path: YAMLPath, data: Any) -> None:
        """Add every node in the document."""
        if isinstance(data, CommentedMap):
            rhs_iteration = -1
            for key, val in data.items():
                rhs_iteration += 1
                next_path = (path +
                    YAMLPath.escape_path_section(key, path.seperator))
                self._diffs.append(
                    DiffEntry(
                        DiffActions.ADD, next_path, None, val,
                        rhs_parent=data, rhs_iteration=rhs_iteration))
        elif isinstance(data, CommentedSeq):
            for idx, ele in enumerate(data):
                next_path = path + "[{}]".format(idx)
                self._diffs.append(
                    DiffEntry(
                        DiffActions.ADD, next_path, None, ele,
                        rhs_parent=data, rhs_iteration=idx))
        else:
            if data is not None:
                self._diffs.append(
                    DiffEntry(DiffActions.ADD, path, None, data)
                )

    def _diff_scalars(
        self, path: YAMLPath, lhs: Any, rhs: Any, **kwargs
    ) -> None:
        """Diff two Scalar values."""
        self.logger.debug(
            "Comparing LHS:",
            prefix="Differ::_diff_scalars:  ",
            data=lhs)
        self.logger.debug(
            "Against RHS:",
            prefix="Differ::_diff_scalars:  ",
            data=rhs)

        lhs_val = lhs
        rhs_val = rhs
        if (not self._ignore_eyaml
            and isinstance(self._eyamlproc, EYAMLProcessor)
        ):
            if self._eyamlproc.is_eyaml_value(lhs):
                lhs_val = self._eyamlproc.decrypt_eyaml(lhs)
                lhs = lhs.replace("\r", "").replace(" ", "")
            if self._eyamlproc.is_eyaml_value(rhs):
                rhs_val = self._eyamlproc.decrypt_eyaml(rhs)
                rhs = rhs.replace("\r", "").replace(" ", "")

        if lhs_val == rhs_val:
            self._diffs.append(
                DiffEntry(DiffActions.SAME, path, lhs, rhs, **kwargs)
            )
        else:
            self._diffs.append(
                DiffEntry(DiffActions.CHANGE, path, lhs, rhs, **kwargs)
            )

    def _diff_dicts(
        self, path: YAMLPath, lhs: CommentedMap, rhs: CommentedMap
    ) -> None:
        """Diff two dicts."""
        self.logger.debug(
            "Comparing LHS:",
            prefix="Differ::_diff_dicts:  ",
            data=lhs)
        self.logger.debug(
            "Against RHS:",
            prefix="Differ::_diff_dicts:  ",
            data=rhs)

        # Check first for a difference in YAML Tag
        lhs_tag = lhs.tag.value if hasattr(lhs, "tag") else None
        rhs_tag = rhs.tag.value if hasattr(rhs, "tag") else None
        if lhs_tag != rhs_tag:
            self.logger.debug(
                "Dictionaries have different YAML Tags; {} != {}:".format(
                    lhs_tag, rhs_tag),
                prefix="Differ::_diff_dicts:  ")
            self._diffs.append(
                DiffEntry(
                    DiffActions.DELETE, path, lhs, None, key_tag=lhs_tag))
            self._diffs.append(
                DiffEntry(
                    DiffActions.ADD, path, None, rhs, key_tag=rhs_tag))
            return

        lhs_keys = set(lhs)
        rhs_keys = set(rhs)
        lhs_key_indicies = Differ._get_key_indicies(lhs)
        rhs_key_indicies = Differ._get_key_indicies(rhs)

        self.logger.debug(
            "Got LHS key indicies:",
            prefix="Differ::_diff_dicts:  ",
            data=lhs_key_indicies)
        self.logger.debug(
            "Got RHS key indicies:",
            prefix="Differ::_diff_dicts:  ",
            data=rhs_key_indicies)

        # Look for changes
        for key, val in [
            (key, val) for key, val in rhs.items()
            if key in lhs and key in rhs
        ]:
            next_path = (path +
                YAMLPath.escape_path_section(key, path.seperator))
            self._diff_between(
                next_path, lhs[key], val,
                lhs_parent=lhs, lhs_iteration=lhs_key_indicies[key],
                rhs_parent=rhs, rhs_iteration=rhs_key_indicies[key],
                parentref=key)

        # Look for deleted keys
        for key in lhs_keys - rhs_keys:
            next_path = (path +
                YAMLPath.escape_path_section(key, path.seperator))
            self._diffs.append(
                DiffEntry(
                    DiffActions.DELETE, next_path, lhs[key], None,
                    lhs_parent=lhs, lhs_iteration=lhs_key_indicies[key],
                    rhs_parent=rhs,
                    key_tag=key.tag.value if hasattr(key, "tag") else None))

        # Look for new keys
        for key in rhs_keys - lhs_keys:
            next_path = (path +
                YAMLPath.escape_path_section(key, path.seperator))
            self._diffs.append(
                DiffEntry(
                    DiffActions.ADD, next_path, None, rhs[key],
                    lhs_parent=lhs,
                    rhs_parent=rhs, rhs_iteration=rhs_key_indicies[key],
                    key_tag=key.tag.value if hasattr(key, "tag") else None))

    def _diff_synced_lists(
        self, path: YAMLPath, lhs: CommentedSeq, rhs: CommentedSeq
    ) -> None:
        """Diff two synchronized lists."""
        self.logger.debug("Differ::_diff_synced_lists:  Starting...")
        self.logger.debug(
            "Synchronizing LHS Array elements at YAML Path, {}:"
            .format(path if path else "/"),
            prefix="Differ::_diff_syncd_lists:  ",
            data=lhs)
        self.logger.debug(
            "Synchronizing RHS Array elements at YAML Path, {}:"
            .format(path if path else "/"),
            prefix="Differ::_diff_syncd_lists:  ",
            data=rhs)

        syn_pairs = Differ.synchronize_lists_by_value(lhs, rhs)
        self.logger.debug(
            "Got synchronized pairs of Array elements at YAML Path, {}:"
            .format(path if path else "/"),
            prefix="Differ::_diff_syncd_lists:  ",
            data=syn_pairs)

        for (lidx, lele, ridx, rele) in syn_pairs:
            if lele is None:
                next_path = path + "[{}]".format(ridx)
                diff_action = DiffActions.ADD
                opposite_val = None
                pop_index = -1
                for idx, ele in reversed(list(enumerate(self._diffs))):
                    if (ele.action is DiffActions.DELETE
                        and ele.path == next_path
                    ):
                        pop_index = idx
                        break

                # This YAML Path has ALREADY been recorded as a DELETE.  Since
                # a DELETE->ADD action is really just a CHANGE, remove the
                # conflicting entry and convert this pending ADD to a CHANGE.
                if pop_index > -1:
                    opposite_val = self._diffs.pop(pop_index).lhs
                    diff_action = DiffActions.CHANGE

                self._diffs.append(DiffEntry(
                    diff_action, next_path, opposite_val, rele,
                    lhs_parent=lhs, lhs_iteration=lidx,
                    rhs_parent=rhs, rhs_iteration=ridx))
            elif rele is None:
                next_path = path + "[{}]".format(lidx)
                self._diffs.append(
                    DiffEntry(
                        DiffActions.DELETE, next_path, lele, None,
                        lhs_parent=lhs, lhs_iteration=lidx,
                        rhs_parent=rhs, rhs_iteration=ridx))
            else:
                next_path = path + "[{}]".format(lidx)
                self._diff_between(
                    next_path, lele, rele,
                    lhs_parent=lhs, lhs_iteration=lidx,
                    rhs_parent=rhs, rhs_iteration=ridx,
                    parentref=ridx)

    def _diff_arrays_of_scalars(
        self, path: YAMLPath, lhs: CommentedSeq, rhs: CommentedSeq,
        node_coord: NodeCoords, **kwargs
    ) -> None:
        """Diff two lists of scalars."""
        self.logger.debug(
            "Comparing LHS:",
            prefix="Differ::_diff_arrays_of_scalars:  ",
            data=lhs)
        self.logger.debug(
            "Against RHS:",
            prefix="Differ::_diff_arrays_of_scalars:  ",
            data=rhs)

        diff_mode = self.config.array_diff_mode(node_coord)
        if diff_mode is ArrayDiffOpts.VALUE:
            self._diff_synced_lists(path, lhs, rhs)
            return

        idx = 0
        diff_deeply = kwargs.pop("diff_deeply", True)
        for (lele, rele) in zip_longest(lhs, rhs):
            next_path = path + "[{}]".format(idx)
            idx += 1
            if lele is None:
                self._diffs.append(
                    DiffEntry(
                        DiffActions.ADD, next_path, None, rele,
                        lhs_parent=lhs, lhs_iteration=idx,
                        rhs_parent=rhs, rhs_iteration=idx))
            elif rele is None:
                self._diffs.append(
                    DiffEntry(
                        DiffActions.DELETE, next_path, lele, None,
                        lhs_parent=lhs, lhs_iteration=idx,
                        rhs_parent=rhs, rhs_iteration=idx))
            elif diff_deeply:
                self._diff_between(
                    next_path, lele, rele,
                    lhs_parent=lhs, lhs_iteration=idx,
                    rhs_parent=rhs, rhs_iteration=idx,
                    parentref=idx)
            elif lele != rele:
                self._diffs.append(
                    DiffEntry(
                        DiffActions.CHANGE, next_path, lele, rele,
                        lhs_parent=lhs, lhs_iteration=idx,
                        rhs_parent=rhs, rhs_iteration=idx,
                        parentref=idx))

    def _diff_arrays_of_hashes(
        self, path: YAMLPath, lhs: CommentedSeq, rhs: CommentedSeq,
        node_coord: NodeCoords
    ) -> None:
        """Diff two lists-of-dictionaries."""
        self.logger.debug(
            "Comparing LHS:",
            prefix="Differ::_diff_arrays_of_hashes:  ",
            data=lhs)
        self.logger.debug(
            "Against RHS:",
            prefix="Differ::_diff_arrays_of_hashes:  ",
            data=rhs)

        diff_mode = self.config.aoh_diff_mode(node_coord)
        if diff_mode is AoHDiffOpts.POSITION:
            self._diff_arrays_of_scalars(
                path, lhs, rhs, node_coord, diff_deeply=False)
            return
        if diff_mode is AoHDiffOpts.DPOS:
            self._diff_arrays_of_scalars(
                path, lhs, rhs, node_coord, diff_deeply=True)
            return
        if diff_mode is AoHDiffOpts.VALUE:
            self._diff_synced_lists(path, lhs, rhs)
            return
        deep_diff = diff_mode is AoHDiffOpts.DEEP

        self.logger.debug(
            "Synchronizing LHS Array elements at YAML Path, {}:"
            .format(path if path else "/"),
            prefix="Differ::_diff_arrays_of_hashes:  ",
            data=lhs)
        self.logger.debug(
            "Synchronizing RHS Array elements at YAML Path, {}:"
            .format(path if path else "/"),
            prefix="Differ::_diff_arrays_of_hashes:  ",
            data=rhs)

        # Perform either a KEY or DEEP comparison; either way, the elements
        # must first be synchronized based on their identity key values.
        syn_pairs = self.synchronize_lods_by_key(path, lhs, rhs)
        self.logger.debug(
            "Got synchronized pairs of Array elements at YAML Path, {}:"
            .format(path if path else "/"),
            prefix="Differ::_diff_arrays_of_hashes:  ",
            data=syn_pairs)

        for (lidx, lele, ridx, rele) in syn_pairs:
            if lele is None:
                next_path = path + "[{}]".format(ridx)
                self._diffs.append(
                    DiffEntry(
                        DiffActions.ADD, next_path, None, rele,
                        lhs_parent=lhs, lhs_iteration=lidx,
                        rhs_parent=rhs, rhs_iteration=ridx))
            elif rele is None:
                next_path = path + "[{}]".format(lidx)
                self._diffs.append(
                    DiffEntry(
                        DiffActions.DELETE, next_path, lele, None,
                        lhs_parent=lhs, lhs_iteration=lidx,
                        rhs_parent=rhs, rhs_iteration=ridx))
            else:
                if deep_diff:
                    next_path = path + "[{}]".format(ridx)
                    self._diff_between(
                        next_path, lele, rele,
                        lhs_parent=lhs, lhs_iteration=lidx,
                        rhs_parent=rhs, rhs_iteration=ridx,
                        parentref=ridx)
                else:
                    # KEY-based comparisons
                    next_path = path + "[{}]".format(lidx)
                    diff_action = (DiffActions.SAME
                                  if lele == rele
                                  else DiffActions.CHANGE)
                    self._diffs.append(
                        DiffEntry(diff_action, next_path, lele, rele,
                        lhs_parent=lhs, lhs_iteration=lidx,
                        rhs_parent=rhs, rhs_iteration=ridx,
                        parentref=lidx))

    def _diff_lists(
        self, path: YAMLPath, lhs: CommentedSeq, rhs: CommentedSeq, **kwargs
    ) -> None:
        """Diff two lists."""
        self.logger.debug(
            "Comparing LHS:",
            prefix="Differ::_diff_lists:  ",
            data=lhs)
        self.logger.debug(
            "Against RHS:",
            prefix="Differ::_diff_lists:  ",
            data=rhs)

        parent: Any = kwargs.pop("rhs_parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        node_coord = NodeCoords(rhs, parent, parentref)
        if len(rhs) > 0:
            if isinstance(rhs[0], CommentedMap):
                # This list is an Array-of-Hashes
                self._diff_arrays_of_hashes(path, lhs, rhs, node_coord)
            else:
                # This list is an Array-of-Arrays or a simple list of Scalars
                self._diff_arrays_of_scalars(path, lhs, rhs, node_coord)

    def _diff_between(
        self, path: YAMLPath, lhs: Any, rhs: Any, **kwargs
    ) -> None:
        """Calculate the differences between two document nodes."""
        self.logger.debug(
            "Comparing LHS:",
            prefix="Differ::_diff_between:  ",
            data=lhs)
        self.logger.debug(
            "Against RHS:",
            prefix="Differ::_diff_between:  ",
            data=rhs)

        # If the roots are different, delete all LHS and add all RHS.
        lhs_is_dict = isinstance(lhs, CommentedMap)
        lhs_is_list = isinstance(lhs, CommentedSeq)
        lhs_is_scalar = not (lhs_is_dict or lhs_is_list)
        rhs_is_dict = isinstance(rhs, CommentedMap)
        rhs_is_list = isinstance(rhs, CommentedSeq)
        rhs_is_scalar = not (rhs_is_dict or rhs_is_list)
        same_types = (
            (lhs_is_dict and rhs_is_dict)
            or (lhs_is_list and rhs_is_list)
            or (lhs_is_scalar and rhs_is_scalar)
        )
        if same_types:
            if lhs_is_dict:
                self._diff_dicts(path, lhs, rhs)
            elif lhs_is_list:
                self._diff_lists(path, lhs, rhs, **kwargs)
            else:
                self._diff_scalars(path, lhs, rhs, **kwargs)
        else:
            self._purge_document(path, lhs)
            self._add_everything(path, rhs)

    @classmethod
    def synchronize_lists_by_value(
        cls, lhs: CommentedSeq, rhs: CommentedSeq
    ) -> List[Tuple[
        Optional[int], Optional[Any], Optional[int], Optional[Any]
    ]]:
        """Synchronize two lists by value."""
        # Build a parallel index array to track the original RHS element
        # indexes of any surviving elements.
        rhs_reduced = []
        for original_idx, val in enumerate(rhs):
            rhs_reduced.append((original_idx, val))

        syn_pairs: List[Tuple[
            Optional[int], Optional[Any], Optional[int], Optional[Any]
        ]] = []
        for lhs_idx, lhs_ele in enumerate(lhs):
            del_index = -1
            for reduced_idx, rhs_pair in enumerate(rhs_reduced):
                (_, rhs_ele) = rhs_pair
                if rhs_ele == lhs_ele:
                    del_index = reduced_idx
                    break

            if del_index > -1:
                (rhs_original_idx, rhs_ele) = rhs_reduced.pop(del_index)
                syn_pairs.append((lhs_idx, lhs_ele, rhs_original_idx, rhs_ele))
            else:
                syn_pairs.append((lhs_idx, lhs_ele, None, None))

        for rhs_pair in rhs_reduced:
            (rhs_original_idx, rhs_ele) = rhs_pair
            syn_pairs.append((None, None, rhs_original_idx, rhs_ele))

        return syn_pairs

    #pylint: disable=too-many-locals
    def synchronize_lods_by_key(
        self, path: YAMLPath, lhs: CommentedSeq, rhs: CommentedSeq
    ) -> List[Tuple[
        Optional[int], Optional[Any], Optional[int], Optional[Any]
    ]]:
        """Synchronize two lists-of-dictionaries by identity key."""
        # Build a parallel index array to track the original RHS element
        # indexes of any surviving elements.
        key_attr: str = ""
        if len(rhs) > 0 and isinstance(rhs[0], CommentedMap):
            (key_attr, _) = self.config.aoh_diff_key(
                NodeCoords(rhs[0], rhs, 0))
            self.logger.debug(
                "Differ::synchronize_lods_by_key:  RHS AoH yielded key_attr:"
                "  {}.".format(key_attr))

        rhs_reduced = []
        for original_idx, val in enumerate(rhs):
            rhs_reduced.append((original_idx, val))

        syn_pairs: List[Tuple[
            Optional[int], Optional[Any], Optional[int], Optional[Any]
        ]] = []
        for lhs_idx, lhs_ele in enumerate(lhs):
            if not key_attr in lhs_ele:
                # Impossible to match this LHS record to any RHS record
                self.logger.debug(
                    "LHS record has no identity key, {}, for record at {}:"
                    .format(key_attr, path),
                    data=lhs_ele,
                    prefix="Differ::synchronize_lods_by_key:  ")
                syn_pairs.append((lhs_idx, lhs_ele, None, None))
                continue

            del_index = -1
            for reduced_idx, rhs_pair in enumerate(rhs_reduced):
                (rhs_idx, rhs_ele) = rhs_pair

                # Check for a custom identity key assignment for this record
                use_key = key_attr
                (alt_key, is_user_key) = self.config.aoh_diff_key(
                    NodeCoords(rhs_ele, rhs, rhs_idx))

                if is_user_key and alt_key:
                    use_key = alt_key
                    self.logger.debug(
                        "Using alternate key, {}, for record at {}[{}]."
                        .format(use_key, path, rhs_idx),
                        data=rhs_ele,
                        prefix="Differ::synchronize_lods_by_key:  ")
                else:
                    self.logger.debug(
                        "Using inferred key, {}, for record at {}[{}]."
                        .format(use_key, path, rhs_idx),
                        data=rhs_ele,
                        prefix="Differ::synchronize_lods_by_key:  ")

                if not use_key in rhs_ele:
                    # Impossible to match this RHS record to any LHS record
                    continue

                if rhs_ele[use_key] == lhs_ele[use_key]:
                    del_index = reduced_idx
                    break

            if del_index > -1:
                (rhs_original_idx, rhs_ele) = rhs_reduced.pop(del_index)
                syn_pairs.append((lhs_idx, lhs_ele, rhs_original_idx, rhs_ele))
            else:
                syn_pairs.append((lhs_idx, lhs_ele, None, None))

        for rhs_pair in rhs_reduced:
            (rhs_original_idx, rhs_ele) = rhs_pair
            syn_pairs.append((None, None, rhs_original_idx, rhs_ele))

        return syn_pairs

    @classmethod
    def _get_key_indicies(cls, data: CommentedMap) -> Dict[Any, int]:
        """Get a dictionary mapping of keys to relative positions."""
        key_map = {}
        if isinstance(data, CommentedMap):
            for idx, key in enumerate(data.keys()):
                key_map[key] = idx
        return key_map
