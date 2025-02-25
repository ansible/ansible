"""Analyze code coverage data to determine which integration test targets provide coverage for each arc or line."""

from __future__ import annotations

import os
import typing as t

from .....encoding import (
    to_text,
)

from .....data import (
    data_context,
)

from .....util_common import (
    ResultType,
)

from .....executor import (
    Delegate,
)

from .....provisioning import (
    prepare_profiles,
    HostState,
)

from ... import (
    enumerate_powershell_lines,
    enumerate_python_arcs,
    get_collection_path_regexes,
    get_powershell_coverage_files,
    get_python_coverage_files,
    get_python_modules,
    initialize_coverage,
    PathChecker,
)

from . import (
    CoverageAnalyzeTargetsConfig,
    get_target_index,
    make_report,
    write_report,
)

from . import (
    Arcs,
    Lines,
    TargetIndexes,
)


class CoverageAnalyzeTargetsGenerateConfig(CoverageAnalyzeTargetsConfig):
    """Configuration for the `coverage analyze targets generate` command."""

    def __init__(self, args: t.Any) -> None:
        super().__init__(args)

        self.input_dir: str = args.input_dir or ResultType.COVERAGE.path
        self.output_file: str = args.output_file


def command_coverage_analyze_targets_generate(args: CoverageAnalyzeTargetsGenerateConfig) -> None:
    """Analyze code coverage data to determine which integration test targets provide coverage for each arc or line."""
    host_state = prepare_profiles(args)  # coverage analyze targets generate

    if args.delegate:
        raise Delegate(host_state)

    root = data_context().content.root
    target_indexes: TargetIndexes = {}
    arcs = dict((os.path.relpath(path, root), data) for path, data in analyze_python_coverage(args, host_state, args.input_dir, target_indexes).items())
    lines = dict((os.path.relpath(path, root), data) for path, data in analyze_powershell_coverage(args, args.input_dir, target_indexes).items())
    report = make_report(target_indexes, arcs, lines)
    write_report(args, report, args.output_file)


def analyze_python_coverage(
    args: CoverageAnalyzeTargetsGenerateConfig,
    host_state: HostState,
    path: str,
    target_indexes: TargetIndexes,
) -> Arcs:
    """Analyze Python code coverage."""
    results: Arcs = {}
    collection_search_re, collection_sub_re = get_collection_path_regexes()
    modules = get_python_modules()
    python_files = get_python_coverage_files(path)
    coverage = initialize_coverage(args, host_state)

    for python_file in python_files:
        if not is_integration_coverage_file(python_file):
            continue

        target_name = get_target_name(python_file)
        target_index = get_target_index(target_name, target_indexes)

        for filename, covered_arcs in enumerate_python_arcs(python_file, coverage, modules, collection_search_re, collection_sub_re):
            arcs = results.setdefault(filename, {})

            for covered_arc in covered_arcs:
                arc = arcs.setdefault(covered_arc, set())
                arc.add(target_index)

    prune_invalid_filenames(args, results, collection_search_re=collection_search_re)

    return results


def analyze_powershell_coverage(
    args: CoverageAnalyzeTargetsGenerateConfig,
    path: str,
    target_indexes: TargetIndexes,
) -> Lines:
    """Analyze PowerShell code coverage"""
    results: Lines = {}
    collection_search_re, collection_sub_re = get_collection_path_regexes()
    powershell_files = get_powershell_coverage_files(path)

    for powershell_file in powershell_files:
        if not is_integration_coverage_file(powershell_file):
            continue

        target_name = get_target_name(powershell_file)
        target_index = get_target_index(target_name, target_indexes)

        for filename, hits in enumerate_powershell_lines(powershell_file, collection_search_re, collection_sub_re):
            lines = results.setdefault(filename, {})

            for covered_line in hits:
                line = lines.setdefault(covered_line, set())
                line.add(target_index)

    prune_invalid_filenames(args, results)

    return results


def prune_invalid_filenames(
    args: CoverageAnalyzeTargetsGenerateConfig,
    results: dict[str, t.Any],
    collection_search_re: t.Optional[t.Pattern] = None,
) -> None:
    """Remove invalid filenames from the given result set."""
    path_checker = PathChecker(args, collection_search_re)

    for path in list(results.keys()):
        if not path_checker.check_path(path):
            del results[path]


def get_target_name(path: str) -> str:
    """Extract the test target name from the given coverage path."""
    return to_text(os.path.basename(path).split('=')[1])


def is_integration_coverage_file(path: str) -> bool:
    """Returns True if the coverage file came from integration tests, otherwise False."""
    return os.path.basename(path).split('=')[0] in ('integration', 'windows-integration', 'network-integration')
