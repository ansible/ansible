"""Filter an aggregated coverage file, keeping only the specified targets."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re

from .... import types as t

from . import (
    CoverageAnalyzeTargetsConfig,
    expand_indexes,
    generate_indexes,
    make_report,
    read_report,
    write_report,
)

if t.TYPE_CHECKING:
    from . import (
        NamedPoints,
        TargetIndexes,
    )


class CoverageAnalyzeTargetsFilterConfig(CoverageAnalyzeTargetsConfig):
    """Configuration for the `coverage analyze targets filter` command."""
    def __init__(self, args):  # type: (t.Any) -> None
        super(CoverageAnalyzeTargetsFilterConfig, self).__init__(args)

        self.input_file = args.input_file  # type: str
        self.output_file = args.output_file  # type: str
        self.include_targets = args.include_targets  # type: t.List[str]
        self.exclude_targets = args.exclude_targets  # type: t.List[str]
        self.include_path = args.include_path  # type: t.Optional[str]
        self.exclude_path = args.exclude_path  # type: t.Optional[str]


def command_coverage_analyze_targets_filter(args):  # type: (CoverageAnalyzeTargetsFilterConfig) -> None
    """Filter target names in an aggregated coverage file."""
    covered_targets, covered_path_arcs, covered_path_lines = read_report(args.input_file)

    filtered_path_arcs = expand_indexes(covered_path_arcs, covered_targets, lambda v: v)
    filtered_path_lines = expand_indexes(covered_path_lines, covered_targets, lambda v: v)

    include_targets = set(args.include_targets) if args.include_targets else None
    exclude_targets = set(args.exclude_targets) if args.exclude_targets else None

    include_path = re.compile(args.include_path) if args.include_path else None
    exclude_path = re.compile(args.exclude_path) if args.exclude_path else None

    def path_filter_func(path):
        if include_path and not re.search(include_path, path):
            return False

        if exclude_path and re.search(exclude_path, path):
            return False

        return True

    def target_filter_func(targets):
        if include_targets:
            targets &= include_targets

        if exclude_targets:
            targets -= exclude_targets

        return targets

    filtered_path_arcs = filter_data(filtered_path_arcs, path_filter_func, target_filter_func)
    filtered_path_lines = filter_data(filtered_path_lines, path_filter_func, target_filter_func)

    target_indexes = {}  # type: TargetIndexes
    indexed_path_arcs = generate_indexes(target_indexes, filtered_path_arcs)
    indexed_path_lines = generate_indexes(target_indexes, filtered_path_lines)

    report = make_report(target_indexes, indexed_path_arcs, indexed_path_lines)

    write_report(args, report, args.output_file)


def filter_data(
        data,  # type: NamedPoints
        path_filter_func,  # type: t.Callable[[str], bool]
        target_filter_func,  # type: t.Callable[[t.Set[str]], t.Set[str]]
):  # type: (...) -> NamedPoints
    """Filter the data set using the specified filter function."""
    result = {}  # type: NamedPoints

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
