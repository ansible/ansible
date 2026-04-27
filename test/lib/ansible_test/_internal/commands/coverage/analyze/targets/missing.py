"""Identify aggregated coverage in one file missing from another."""

from __future__ import annotations

import os
import typing as t

from .....encoding import (
    to_bytes,
)

from .....executor import (
    Delegate,
)

from .....provisioning import (
    prepare_profiles,
)

from . import (
    CoverageAnalyzeTargetsConfig,
    get_target_index,
    make_report,
    read_report,
    write_report,
)

from . import (
    TargetIndexes,
    IndexedPoints,
)


class CoverageAnalyzeTargetsMissingConfig(CoverageAnalyzeTargetsConfig):
    """Configuration for the `coverage analyze targets missing` command."""

    def __init__(self, args: t.Any) -> None:
        super().__init__(args)

        self.from_file: str = args.from_file
        self.to_file: str = args.to_file
        self.output_file: str = args.output_file

        self.only_gaps: bool = args.only_gaps
        self.only_exists: bool = args.only_exists


def command_coverage_analyze_targets_missing(args: CoverageAnalyzeTargetsMissingConfig) -> None:
    """Identify aggregated coverage in one file missing from another."""
    host_state = prepare_profiles(args)  # coverage analyze targets missing

    if args.delegate:
        raise Delegate(host_state=host_state)

    from_targets, from_path_arcs, from_path_lines = read_report(args.from_file)
    to_targets, to_path_arcs, to_path_lines = read_report(args.to_file)
    target_indexes: TargetIndexes = {}

    if args.only_gaps:
        arcs = find_gaps(from_path_arcs, from_targets, to_path_arcs, target_indexes, args.only_exists)
        lines = find_gaps(from_path_lines, from_targets, to_path_lines, target_indexes, args.only_exists)
    else:
        arcs = find_missing(from_path_arcs, from_targets, to_path_arcs, to_targets, target_indexes, args.only_exists)
        lines = find_missing(from_path_lines, from_targets, to_path_lines, to_targets, target_indexes, args.only_exists)

    report = make_report(target_indexes, arcs, lines)
    write_report(args, report, args.output_file)


def find_gaps(
    from_data: IndexedPoints,
    from_index: list[str],
    to_data: IndexedPoints,
    target_indexes: TargetIndexes,
    only_exists: bool,
) -> IndexedPoints:
    """Find gaps in coverage between the from and to data sets."""
    target_data: IndexedPoints = {}

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
    from_data: IndexedPoints,
    from_index: list[str],
    to_data: IndexedPoints,
    to_index: list[str],
    target_indexes: TargetIndexes,
    only_exists: bool,
) -> IndexedPoints:
    """Find coverage in from_data not present in to_data (arcs or lines)."""
    target_data: IndexedPoints = {}

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
