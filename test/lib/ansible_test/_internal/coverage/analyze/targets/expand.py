"""Expand target names in an aggregated coverage file."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from .... import types as t

from ....io import (
    SortedSetEncoder,
    write_json_file,
)

from . import (
    CoverageAnalyzeTargetsConfig,
    format_arc,
    read_report,
)


def command_coverage_analyze_targets_expand(args):  # type: (CoverageAnalyzeTargetsExpandConfig) -> None
    """Expand target names in an aggregated coverage file."""
    covered_targets, covered_path_arcs, covered_path_lines = read_report(args.input_file)

    report = dict(
        arcs=expand_indexes(covered_path_arcs, covered_targets, format_arc),
        lines=expand_indexes(covered_path_lines, covered_targets, str),
    )

    if not args.explain:
        write_json_file(args.output_file, report, encoder=SortedSetEncoder)


def expand_indexes(
        source_data,  # type: t.Dict[str, t.Dict[t.Any, t.Set[int]]]
        source_index,  # type: t.List[str]
        format_func,  # type: t.Callable[t.Tuple[t.Any], str]
):  # type: (...) -> t.Dict[str, t.Dict[t.Any, t.Set[str]]]
    """Merge indexes from the source into the combined data set (arcs or lines)."""
    combined_data = {}  # type: t.Dict[str, t.Dict[t.Any, t.Set[str]]]

    for covered_path, covered_points in source_data.items():
        combined_points = combined_data.setdefault(covered_path, {})

        for covered_point, covered_target_indexes in covered_points.items():
            combined_point = combined_points.setdefault(format_func(covered_point), set())

            for covered_target_index in covered_target_indexes:
                combined_point.add(source_index[covered_target_index])

    return combined_data


class CoverageAnalyzeTargetsExpandConfig(CoverageAnalyzeTargetsConfig):
    """Configuration for the `coverage analyze targets expand` command."""
    def __init__(self, args):  # type: (t.Any) -> None
        super(CoverageAnalyzeTargetsExpandConfig, self).__init__(args)

        self.input_file = args.input_file  # type: str
        self.output_file = args.output_file  # type: str
