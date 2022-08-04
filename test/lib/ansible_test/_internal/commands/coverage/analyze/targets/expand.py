"""Expand target names in an aggregated coverage file."""
from __future__ import annotations
import typing as t

from .....io import (
    SortedSetEncoder,
    write_json_file,
)

from .....executor import (
    Delegate,
)

from .....provisioning import (
    prepare_profiles,
)

from . import (
    CoverageAnalyzeTargetsConfig,
    expand_indexes,
    format_arc,
    format_line,
    read_report,
)


class CoverageAnalyzeTargetsExpandConfig(CoverageAnalyzeTargetsConfig):
    """Configuration for the `coverage analyze targets expand` command."""
    def __init__(self, args: t.Any) -> None:
        super().__init__(args)

        self.input_file: str = args.input_file
        self.output_file: str = args.output_file


def command_coverage_analyze_targets_expand(args: CoverageAnalyzeTargetsExpandConfig) -> None:
    """Expand target names in an aggregated coverage file."""
    host_state = prepare_profiles(args)  # coverage analyze targets expand

    if args.delegate:
        raise Delegate(host_state=host_state)

    covered_targets, covered_path_arcs, covered_path_lines = read_report(args.input_file)

    report = dict(
        arcs=expand_indexes(covered_path_arcs, covered_targets, format_arc),
        lines=expand_indexes(covered_path_lines, covered_targets, format_line),
    )

    if not args.explain:
        write_json_file(args.output_file, report, encoder=SortedSetEncoder)
