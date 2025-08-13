"""Combine integration test target code coverage reports."""

from __future__ import annotations
import typing as t

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
    Arcs,
    IndexedPoints,
    Lines,
    TargetIndexes,
)


class CoverageAnalyzeTargetsCombineConfig(CoverageAnalyzeTargetsConfig):
    """Configuration for the `coverage analyze targets combine` command."""

    def __init__(self, args: t.Any) -> None:
        super().__init__(args)

        self.input_files: list[str] = args.input_file
        self.output_file: str = args.output_file


def command_coverage_analyze_targets_combine(args: CoverageAnalyzeTargetsCombineConfig) -> None:
    """Combine integration test target code coverage reports."""
    host_state = prepare_profiles(args)  # coverage analyze targets combine

    if args.delegate:
        raise Delegate(host_state=host_state)

    combined_target_indexes: TargetIndexes = {}
    combined_path_arcs: Arcs = {}
    combined_path_lines: Lines = {}

    for report_path in args.input_files:
        covered_targets, covered_path_arcs, covered_path_lines = read_report(report_path)

        merge_indexes(covered_path_arcs, covered_targets, combined_path_arcs, combined_target_indexes)
        merge_indexes(covered_path_lines, covered_targets, combined_path_lines, combined_target_indexes)

    report = make_report(combined_target_indexes, combined_path_arcs, combined_path_lines)

    write_report(args, report, args.output_file)


def merge_indexes(
    source_data: IndexedPoints,
    source_index: list[str],
    combined_data: IndexedPoints,
    combined_index: TargetIndexes,
) -> None:
    """Merge indexes from the source into the combined data set (arcs or lines)."""
    for covered_path, covered_points in source_data.items():
        combined_points = combined_data.setdefault(covered_path, {})

        for covered_point, covered_target_indexes in covered_points.items():
            combined_point = combined_points.setdefault(covered_point, set())

            for covered_target_index in covered_target_indexes:
                combined_point.add(get_target_index(source_index[covered_target_index], combined_index))
