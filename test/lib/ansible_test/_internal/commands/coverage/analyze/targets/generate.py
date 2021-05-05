"""Analyze code coverage data to determine which integration test targets provide coverage for each arc or line."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from .... import types as t

from ....encoding import (
    to_text,
)

from ....data import (
    data_context,
)

from ....util_common import (
    ResultType,
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

if t.TYPE_CHECKING:
    from . import (
        Arcs,
        Lines,
        TargetIndexes,
    )


class CoverageAnalyzeTargetsGenerateConfig(CoverageAnalyzeTargetsConfig):
    """Configuration for the `coverage analyze targets generate` command."""
    def __init__(self, args):  # type: (t.Any) -> None
        super(CoverageAnalyzeTargetsGenerateConfig, self).__init__(args)

        self.input_dir = args.input_dir or ResultType.COVERAGE.path  # type: str
        self.output_file = args.output_file  # type: str


def command_coverage_analyze_targets_generate(args):  # type: (CoverageAnalyzeTargetsGenerateConfig) -> None
    """Analyze code coverage data to determine which integration test targets provide coverage for each arc or line."""
    root = data_context().content.root
    target_indexes = {}
    arcs = dict((os.path.relpath(path, root), data) for path, data in analyze_python_coverage(args, args.input_dir, target_indexes).items())
    lines = dict((os.path.relpath(path, root), data) for path, data in analyze_powershell_coverage(args, args.input_dir, target_indexes).items())
    report = make_report(target_indexes, arcs, lines)
    write_report(args, report, args.output_file)


def analyze_python_coverage(
        args,  # type: CoverageAnalyzeTargetsGenerateConfig
        path,  # type: str
        target_indexes,  # type: TargetIndexes
):  # type: (...) -> Arcs
    """Analyze Python code coverage."""
    results = {}  # type: Arcs
    collection_search_re, collection_sub_re = get_collection_path_regexes()
    modules = get_python_modules()
    python_files = get_python_coverage_files(path)
    coverage = initialize_coverage(args)

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
        args,  # type: CoverageAnalyzeTargetsGenerateConfig
        path,  # type: str
        target_indexes,  # type: TargetIndexes
):  # type: (...) -> Lines
    """Analyze PowerShell code coverage"""
    results = {}  # type: Lines
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
        args,  # type: CoverageAnalyzeTargetsGenerateConfig
        results,  # type: t.Dict[str, t.Any]
        collection_search_re=None,  # type: t.Optional[str]
):  # type: (...) -> None
    """Remove invalid filenames from the given result set."""
    path_checker = PathChecker(args, collection_search_re)

    for path in list(results.keys()):
        if not path_checker.check_path(path):
            del results[path]


def get_target_name(path):  # type: (str) -> str
    """Extract the test target name from the given coverage path."""
    return to_text(os.path.basename(path).split('=')[1])


def is_integration_coverage_file(path):  # type: (str) -> bool
    """Returns True if the coverage file came from integration tests, otherwise False."""
    return os.path.basename(path).split('=')[0] in ('integration', 'windows-integration', 'network-integration')
