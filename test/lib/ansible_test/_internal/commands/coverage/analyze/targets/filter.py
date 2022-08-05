"""Filter an aggregated coverage file, keeping only the specified targets."""
from __future__ import annotations

import collections.abc as c
import re
import typing as t

from .....executor import (
    Delegate,
)

from .....provisioning import (
    prepare_profiles,
)

from . import (
    CoverageAnalyzeTargetsConfig,
    expand_indexes,
    generate_indexes,
    make_report,
    read_report,
    write_report,
)

from . import (
    NamedPoints,
    TargetIndexes,
)


class CoverageAnalyzeTargetsFilterConfig(CoverageAnalyzeTargetsConfig):
    """Configuration for the `coverage analyze targets filter` command."""
    def __init__(self, args: t.Any) -> None:
        super().__init__(args)

        self.input_file: str = args.input_file
        self.output_file: str = args.output_file
        self.include_targets: list[str] = args.include_targets
        self.exclude_targets: list[str] = args.exclude_targets
        self.include_path: t.Optional[str] = args.include_path
        self.exclude_path: t.Optional[str] = args.exclude_path


def command_coverage_analyze_targets_filter(args: CoverageAnalyzeTargetsFilterConfig) -> None:
    """Filter target names in an aggregated coverage file."""
    host_state = prepare_profiles(args)  # coverage analyze targets filter

    if args.delegate:
        raise Delegate(host_state=host_state)

    covered_targets, covered_path_arcs, covered_path_lines = read_report(args.input_file)

    filtered_path_arcs = expand_indexes(covered_path_arcs, covered_targets, lambda v: v)
    filtered_path_lines = expand_indexes(covered_path_lines, covered_targets, lambda v: v)

    include_targets = set(args.include_targets) if args.include_targets else None
    exclude_targets = set(args.exclude_targets) if args.exclude_targets else None

    include_path = re.compile(args.include_path) if args.include_path else None
    exclude_path = re.compile(args.exclude_path) if args.exclude_path else None

    def path_filter_func(path):
        """Return True if the given path should be included, otherwise return False."""
        if include_path and not re.search(include_path, path):
            return False

        if exclude_path and re.search(exclude_path, path):
            return False

        return True

    def target_filter_func(targets):
        """Filter the given targets and return the result based on the defined includes and excludes."""
        if include_targets:
            targets &= include_targets

        if exclude_targets:
            targets -= exclude_targets

        return targets

    filtered_path_arcs = filter_data(filtered_path_arcs, path_filter_func, target_filter_func)
    filtered_path_lines = filter_data(filtered_path_lines, path_filter_func, target_filter_func)

    target_indexes: TargetIndexes = {}
    indexed_path_arcs = generate_indexes(target_indexes, filtered_path_arcs)
    indexed_path_lines = generate_indexes(target_indexes, filtered_path_lines)

    report = make_report(target_indexes, indexed_path_arcs, indexed_path_lines)

    write_report(args, report, args.output_file)


def filter_data(
        data: NamedPoints,
        path_filter_func: c.Callable[[str], bool],
        target_filter_func: c.Callable[[set[str]], set[str]],
) -> NamedPoints:
    """Filter the data set using the specified filter function."""
    result: NamedPoints = {}

    for src_path, src_points in data.items():
        if not path_filter_func(src_path):
            continue

        dst_points = {}

        for src_point, src_targets in src_points.items():
            dst_targets = target_filter_func(src_targets)

            if dst_targets:
                dst_points[src_point] = dst_targets

        if dst_points:
            result[src_path] = dst_points

    return result
