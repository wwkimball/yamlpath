"""
Implement YAML document Differ.

Copyright 2020 William W. Kimball, Jr. MBA MSIS
"""
from itertools import zip_longest
from typing import Any, Generator, List, Tuple

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
        self._diff_between(YAMLPath(), self._data, document)

    def get_report(self) -> Generator[DiffEntry, None, None]:
        """Get the diff report."""
        for entry in sorted(
            self._diffs, key=lambda e: [int(i) for i in e.index.split('.')]
        ):
            yield entry

    def _purge_document(self, path: YAMLPath, data: Any):
        """Delete every node in the document."""
        if isinstance(data, dict):
            for key, val in data.items():
                next_path = YAMLPath(path).append(key)
                self._diffs.append(
                    DiffEntry(
                        DiffActions.DELETE, next_path, val, None,
                        lhs_parent=data))
        elif isinstance(data, list):
            for idx, ele in enumerate(data):
                next_path = YAMLPath(path).append("[{}]".format(idx))
                self._diffs.append(
                    DiffEntry(
                        DiffActions.DELETE, next_path, ele, None,
                        lhs_parent=data))
        else:
            if data is not None:
                self._diffs.append(
                    DiffEntry(DiffActions.DELETE, path, data, None)
                )

    def _add_everything(self, path: YAMLPath, data: Any) -> None:
        """Add every node in the document."""
        if isinstance(data, dict):
            for key, val in data.items():
                next_path = YAMLPath(path).append(key)
                self._diffs.append(
                    DiffEntry(
                        DiffActions.ADD, next_path, None, val,
                        rhs_parent=data))
        elif isinstance(data, list):
            for idx, ele in enumerate(data):
                next_path = YAMLPath(path).append("[{}]".format(idx))
                self._diffs.append(
                    DiffEntry(
                        DiffActions.ADD, next_path, None, ele,
                        rhs_parent=data))
        else:
            if data is not None:
                self._diffs.append(
                    DiffEntry(DiffActions.ADD, path, None, data)
                )

    def _diff_scalars(
        self, path: YAMLPath, lhs: Any, rhs: Any, **kwargs
    ) -> None:
        """Diff two Scalar values."""
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

    def _diff_dicts(self, path: YAMLPath, lhs: dict, rhs: dict) -> None:
        """Diff two dicts."""
        lhs_keys = set(lhs)
        rhs_keys = set(rhs)

        # Look for deleted keys
        for key in lhs_keys - rhs_keys:
            next_path = YAMLPath(path).append(key)
            self._diffs.append(
                DiffEntry(
                    DiffActions.DELETE, next_path, lhs[key], None,
                    lhs_parent=lhs, rhs_parent=rhs))

        # Look for new keys
        for key in rhs_keys - lhs_keys:
            next_path = YAMLPath(path).append(key)
            self._diffs.append(
                DiffEntry(
                    DiffActions.ADD, next_path, None, rhs[key],
                    lhs_parent=lhs, rhs_parent=rhs))

        # Recurse into the rest
        for key, val in [
            (key, val) for key, val in rhs.items()
            if key in lhs and key in rhs
        ]:
            next_path = YAMLPath(path).append(key)
            self._diff_between(
                next_path, lhs[key], val, lhs_parent=lhs, rhs_parent=rhs,
                parentref=key)

    def _diff_synced_lists(self, path: YAMLPath, lhs: list, rhs: list) -> None:
        """Diff two synchronized lists."""
        # lhs = [1, 2, 2, 3]
        # rhs = [2, 3, 3, 4]
        # syn = [[1, None], [2, 2], [2, None], [3, 3], [None, 3], [None, 4]]
        # lsy = [1,    2, 2,    3, None, None]
        # rsy = [None, 2, None, 3, 3,    4]
        debug_path = path if path else "/"
        self.logger.debug(
            "Synchronizing LHS Array elements at YAML Path, {}:"
            .format(debug_path),
            prefix="Differ::_diff_syncd_lists:  ",
            data=lhs)
        self.logger.debug(
            "Synchronizing RHS Array elements at YAML Path, {}:"
            .format(debug_path),
            prefix="Differ::_diff_syncd_lists:  ",
            data=rhs)

        syn_pairs = Differ.synchronize_lists_by_value(lhs, rhs)
        self.logger.debug(
            "Got synchronized pairs of Array elements at YAML Path, {}:"
            .format(debug_path),
            prefix="Differ::_diff_syncd_lists:  ",
            data=syn_pairs)

        for (lidx, lele, ridx, rele) in syn_pairs:
            if lele is None:
                next_path = YAMLPath(path).append("[{}]".format(ridx))
                self._diffs.append(
                    DiffEntry(
                        DiffActions.ADD, next_path, None, rele,
                        lhs_parent=lhs, rhs_parent=rhs))
            elif rele is None:
                next_path = YAMLPath(path).append("[{}]".format(lidx))
                self._diffs.append(
                    DiffEntry(
                        DiffActions.DELETE, next_path, lele, None,
                        lhs_parent=lhs, rhs_parent=rhs))
            else:
                self._diff_between(
                    next_path, lele, rele, lhs_parent=lhs, rhs_parent=rhs,
                    parentref=ridx)

    def _diff_arrays_of_scalars(
        self, path: YAMLPath, lhs: list, rhs: list, node_coord: NodeCoords
    ) -> None:
        """Diff two lists of scalars."""
        diff_mode = self.config.array_diff_mode(node_coord)
        if diff_mode is ArrayDiffOpts.VALUE:
            self._diff_synced_lists(path, lhs, rhs)
            return

        idx = 0
        for (lele, rele) in zip_longest(lhs, rhs):
            next_path = YAMLPath(path).append("[{}]".format(idx))
            idx += 1
            if lele is None:
                self._diffs.append(
                    DiffEntry(
                        DiffActions.ADD, next_path, None, rele,
                        lhs_parent=lhs, rhs_parent=rhs))
            elif rele is None:
                self._diffs.append(
                    DiffEntry(
                        DiffActions.DELETE, next_path, lele, None,
                        lhs_parent=lhs, rhs_parent=rhs))
            else:
                self._diff_between(
                    next_path, lele, rele, lhs_parent=lhs, rhs_parent=rhs,
                    parentref=idx)

    def _diff_arrays_of_hashes(
        self, path: YAMLPath, lhs: list, rhs: list, node_coord: NodeCoords
    ) -> None:
        """Diff two lists-of-dictionaries."""
        diff_mode = self.config.aoh_diff_mode(node_coord)
        if diff_mode is AoHDiffOpts.POSITION:
            self._diff_arrays_of_scalars(path, lhs, rhs, node_coord)
            return
        if diff_mode is AoHDiffOpts.VALUE:
            self._diff_synced_lists(path, lhs, rhs)
            return

        # Perform either a KEY or DEEP comparison; either way, the elements
        # must first be synchronized based on their identity key values.
        id_key: str = ""
        if len(rhs) > 0 and isinstance(rhs[0], dict):
            id_key = self.config.aoh_merge_key(
                NodeCoords(rhs[0], rhs, 0), rhs[0])
            self.logger.debug(
                "Differ::_diff_arrays_of_hashes:  RHS AoH yielded id_key:"
                "  {}.".format(id_key))

        # TODO:  This...

    def _diff_lists(
        self, path: YAMLPath, lhs: list, rhs: list, **kwargs
    ) -> None:
        """Diff two lists."""
        parent: Any = kwargs.pop("rhs_parent", None)
        parentref: Any = kwargs.pop("parentref", None)
        node_coord = NodeCoords(rhs, parent, parentref)
        if len(rhs) > 0:
            if isinstance(rhs[0], dict):
                # This list is an Array-of-Hashes
                self._diff_arrays_of_hashes(path, lhs, rhs, node_coord)

            # This list is an Array-of-Arrays or a simple list of Scalars
            self._diff_arrays_of_scalars(path, lhs, rhs, node_coord)

    def _diff_between(
        self, path: YAMLPath, lhs: Any, rhs: Any, **kwargs
    ) -> None:
        """Calculate the differences between two document nodes."""
        # If the roots are different, delete all LHS and add all RHS.
        lhs_is_dict = isinstance(lhs, dict)
        lhs_is_list = isinstance(lhs, list)
        lhs_is_scalar = not (lhs_is_dict or lhs_is_list)
        rhs_is_dict = isinstance(rhs, dict)
        rhs_is_list = isinstance(rhs, list)
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
        cls, lhs: list, rhs: list
    ) -> Tuple[int, Any, int, Any]:
        """Synchronize two lists by value."""
        # Build a parallel index array to track the original RHS element
        # indexes of any surviving elements.
        rhs_indexes = []
        for idx in range(len(rhs)):
            rhs_indexes.append(idx)

        rhs_reduced = rhs.copy()
        syn_pairs = []
        for lhs_idx, lhs_ele in enumerate(lhs):
            del_index = -1
            for rhs_idx, rhs_ele in enumerate(rhs_reduced):
                if rhs_ele == lhs_ele:
                    del_index = rhs_idx
                    break
            if del_index > -1:
                rhs_ele = rhs_reduced.pop(del_index)
                rhs_indexes.remove(del_index)
                syn_pairs.append((lhs_idx, lhs_ele, del_index, rhs_ele))
            else:
                syn_pairs.append((lhs_idx, lhs_ele, None, None))
        for (rhs_idx, rhs_ele) in zip(rhs_indexes, rhs_reduced):
            syn_pairs.append((None, None, rhs_idx, rhs_ele))

        return syn_pairs
