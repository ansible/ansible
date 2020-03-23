"""Identify aggregated coverage in one file missing from another."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from .... import types as t

from ....encoding import (
    to_bytes,
)

from . import (
    CoverageAnalyzeTargetsConfig,
    get_target_index,
    make_report,
    read_report,
    write_report,
)

if t.TYPE_CHECKING:
    from . import (
        TargetIndexes,
        IndexedPoints,
    )


class CoverageAnalyzeTargetsMissingConfig(CoverageAnalyzeTargetsConfig):
    """Configuration for the `coverage analyze targets missing` command."""
    def __init__(self, args):  # type: (t.Any) -> None
        super(CoverageAnalyzeTargetsMissingConfig, self).__init__(args)

        self.from_file = args.from_file  # type: str
        self.to_file = args.to_file  # type: str
        self.output_file = args.output_file  # type: str

        self.only_gaps = args.only_gaps  # type: bool
        self.only_exists = args.only_exists  # type: bool


def command_coverage_analyze_targets_missing(args):  # type: (CoverageAnalyzeTargetsMissingConfig) -> None
    """Identify aggregated coverage in one file missing from another."""
    from_targets, from_path_arcs, from_path_lines = read_report(args.from_file)
    to_targets, to_path_arcs, to_path_lines = read_report(args.to_file)
    target_indexes = {}

    if args.only_gaps:
        arcs = find_gaps(from_path_arcs, from_targets, to_path_arcs, target_indexes, args.only_exists)
        lines = find_gaps(from_path_lines, from_targets, to_path_lines, target_indexes, args.only_exists)
    else:
        arcs = find_missing(from_path_arcs, from_targets, to_path_arcs, to_targets, target_indexes, args.only_exists)
        lines = find_missing(from_path_lines, from_targets, to_path_lines, to_targets, target_indexes, args.only_exists)

    report = make_report(target_indexes, arcs, lines)
    write_report(args, report, args.output_file)


def find_gaps(
        from_data,  # type: IndexedPoints
        from_index,  # type: t.List[str]
        to_data,  # type: IndexedPoints
        target_indexes,  # type: TargetIndexes
        only_exists,  # type: bool
):  # type: (...) -> IndexedPoints
    """Find gaps in coverage between the from and to data sets."""
    target_data = {}

    for from_path, from_points in from_data.items():
        if only_exists and not os.path.isfile(to_bytes(from_path)):
            continue

        to_points = to_data.get(from_path, {})

        gaps = set(from_points.keys()) - set(to_points.keys())

        if gaps:
            gap_points = dict((key, value) for key, value in from_points.items() if key in gaps)
            target_data[from_path] = dict((gap, set(get_target_index(from_index[i], target_indexes) for i in indexes)) for gap, indexes in gap_points.items())

    return target_data


def find_missing(
        from_data,  # type: IndexedPoints
        from_index,  # type: t.List[str]
        to_data,  # type: IndexedPoints
        to_index,  # type: t.List[str]
        target_indexes,  # type: TargetIndexes
        only_exists,  # type: bool
):  # type: (...) -> IndexedPoints
    """Find coverage in from_data not present in to_data (arcs or lines)."""
    target_data = {}

    for from_path, from_points in from_data.items():
        if only_exists and not os.path.isfile(to_bytes(from_path)):
            continue

        to_points = to_data.get(from_path, {})

        for from_point, from_target_indexes in from_points.items():
            to_target_indexes = to_points.get(from_point, set())

            remaining_targets = set(from_index[i] for i in from_target_indexes) - set(to_index[i] for i in to_target_indexes)

            if remaining_targets:
                target_index = target_data.setdefault(from_path, {}).setdefault(from_point, set())
                target_index.update(get_target_index(name, target_indexes) for name in remaining_targets)

    return target_data
