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
    expand_indexes,
    format_arc,
    read_report,
)


class CoverageAnalyzeTargetsExpandConfig(CoverageAnalyzeTargetsConfig):
    """Configuration for the `coverage analyze targets expand` command."""
    def __init__(self, args):  # type: (t.Any) -> None
        super(CoverageAnalyzeTargetsExpandConfig, self).__init__(args)

        self.input_file = args.input_file  # type: str
        self.output_file = args.output_file  # type: str


def command_coverage_analyze_targets_expand(args):  # type: (CoverageAnalyzeTargetsExpandConfig) -> None
    """Expand target names in an aggregated coverage file."""
    covered_targets, covered_path_arcs, covered_path_lines = read_report(args.input_file)

    report = dict(
        arcs=expand_indexes(covered_path_arcs, covered_targets, format_arc),
        lines=expand_indexes(covered_path_lines, covered_targets, str),
    )

    if not args.explain:
        write_json_file(args.output_file, report, encoder=SortedSetEncoder)
