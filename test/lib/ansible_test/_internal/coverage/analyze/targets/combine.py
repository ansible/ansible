"""Combine integration test target code coverage reports."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from .... import types as t

from . import (
    CoverageAnalyzeTargetsConfig,
    get_target_index,
    make_report,
    read_report,
    write_report,
)

if t.TYPE_CHECKING:
    from . import (
        Arcs,
        IndexedPoints,
        Lines,
        TargetIndexes,
    )


class CoverageAnalyzeTargetsCombineConfig(CoverageAnalyzeTargetsConfig):
    """Configuration for the `coverage analyze targets combine` command."""
    def __init__(self, args):  # type: (t.Any) -> None
        super(CoverageAnalyzeTargetsCombineConfig, self).__init__(args)

        self.input_files = args.input_file  # type: t.List[str]
        self.output_file = args.output_file  # type: str


def command_coverage_analyze_targets_combine(args):  # type: (CoverageAnalyzeTargetsCombineConfig) -> None
    """Combine integration test target code coverage reports."""
    combined_target_indexes = {}  # type: TargetIndexes
    combined_path_arcs = {}  # type: Arcs
    combined_path_lines = {}  # type: Lines

    for report_path in args.input_files:
        covered_targets, covered_path_arcs, covered_path_lines = read_report(report_path)

        merge_indexes(covered_path_arcs, covered_targets, combined_path_arcs, combined_target_indexes)
        merge_indexes(covered_path_lines, covered_targets, combined_path_lines, combined_target_indexes)

    report = make_report(combined_target_indexes, combined_path_arcs, combined_path_lines)

    write_report(args, report, args.output_file)


def merge_indexes(
        source_data,  # type: IndexedPoints
        source_index,  # type: t.List[str]
        combined_data,  # type: IndexedPoints
        combined_index,  # type: TargetIndexes
):  # type: (...) -> None
    """Merge indexes from the source into the combined data set (arcs or lines)."""
    for covered_path, covered_points in source_data.items():
        combined_points = combined_data.setdefault(covered_path, {})

        for covered_point, covered_target_indexes in covered_points.items():
            combined_point = combined_points.setdefault(covered_point, set())

            for covered_target_index in covered_target_indexes:
                combined_point.add(get_target_index(source_index[covered_target_index], combined_index))
