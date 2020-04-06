"""Analyze integration test target code coverage."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from .... import types as t

from ....io import (
    read_json_file,
    write_json_file,
)

from ....util import (
    ApplicationError,
    display,
)

from .. import (
    CoverageAnalyzeConfig,
)

if t.TYPE_CHECKING:
    TargetKey = t.TypeVar('TargetKey', int, t.Tuple[int, int])
    NamedPoints = t.Dict[str, t.Dict[TargetKey, t.Set[str]]]
    IndexedPoints = t.Dict[str, t.Dict[TargetKey, t.Set[int]]]
    Arcs = t.Dict[str, t.Dict[t.Tuple[int, int], t.Set[int]]]
    Lines = t.Dict[str, t.Dict[int, t.Set[int]]]
    TargetIndexes = t.Dict[str, int]
    TargetSetIndexes = t.Dict[t.FrozenSet[int], int]


class CoverageAnalyzeTargetsConfig(CoverageAnalyzeConfig):
    """Configuration for the `coverage analyze targets` command."""
    def __init__(self, args):  # type: (t.Any) -> None
        super(CoverageAnalyzeTargetsConfig, self).__init__(args)

        self.info_stderr = True


def make_report(target_indexes, arcs, lines):  # type: (TargetIndexes, Arcs, Lines) -> t.Dict[str, t.Any]
    """Condense target indexes, arcs and lines into a compact report."""
    set_indexes = {}
    arc_refs = dict((path, dict((format_arc(arc), get_target_set_index(indexes, set_indexes)) for arc, indexes in data.items())) for path, data in arcs.items())
    line_refs = dict((path, dict((line, get_target_set_index(indexes, set_indexes)) for line, indexes in data.items())) for path, data in lines.items())

    report = dict(
        targets=[name for name, index in sorted(target_indexes.items(), key=lambda kvp: kvp[1])],
        target_sets=[sorted(data) for data, index in sorted(set_indexes.items(), key=lambda kvp: kvp[1])],
        arcs=arc_refs,
        lines=line_refs,
    )

    return report


def load_report(report):  # type: (t.Dict[str, t.Any]) -> t.Tuple[t.List[str], Arcs, Lines]
    """Extract target indexes, arcs and lines from an existing report."""
    try:
        target_indexes = report['targets']  # type: t.List[str]
        target_sets = report['target_sets']  # type: t.List[t.List[int]]
        arc_data = report['arcs']  # type: t.Dict[str, t.Dict[str, int]]
        line_data = report['lines']  # type: t.Dict[str, t.Dict[int, int]]
    except KeyError as ex:
        raise ApplicationError('Document is missing key "%s".' % ex.args)
    except TypeError:
        raise ApplicationError('Document is type "%s" instead of "dict".' % type(report).__name__)

    arcs = dict((path, dict((parse_arc(arc), set(target_sets[index])) for arc, index in data.items())) for path, data in arc_data.items())
    lines = dict((path, dict((int(line), set(target_sets[index])) for line, index in data.items())) for path, data in line_data.items())

    return target_indexes, arcs, lines


def read_report(path):  # type: (str) -> t.Tuple[t.List[str], Arcs, Lines]
    """Read a JSON report from disk."""
    try:
        report = read_json_file(path)
    except Exception as ex:
        raise ApplicationError('File "%s" is not valid JSON: %s' % (path, ex))

    try:
        return load_report(report)
    except ApplicationError as ex:
        raise ApplicationError('File "%s" is not an aggregated coverage data file. %s' % (path, ex))


def write_report(args, report, path):  # type: (CoverageAnalyzeTargetsConfig, t.Dict[str, t.Any], str) -> None
    """Write a JSON report to disk."""
    if args.explain:
        return

    write_json_file(path, report, formatted=False)

    display.info('Generated %d byte report with %d targets covering %d files.' % (
        os.path.getsize(path), len(report['targets']), len(set(report['arcs'].keys()) | set(report['lines'].keys())),
    ), verbosity=1)


def format_arc(value):  # type: (t.Tuple[int, int]) -> str
    """Format an arc tuple as a string."""
    return '%d:%d' % value


def parse_arc(value):  # type: (str) -> t.Tuple[int, int]
    """Parse an arc string into a tuple."""
    first, last = tuple(map(int, value.split(':')))
    return first, last


def get_target_set_index(data, target_set_indexes):  # type: (t.Set[int], TargetSetIndexes) -> int
    """Find or add the target set in the result set and return the target set index."""
    return target_set_indexes.setdefault(frozenset(data), len(target_set_indexes))


def get_target_index(name, target_indexes):  # type: (str, TargetIndexes) -> int
    """Find or add the target in the result set and return the target index."""
    return target_indexes.setdefault(name, len(target_indexes))


def expand_indexes(
        source_data,  # type: IndexedPoints
        source_index,  # type: t.List[str]
        format_func,  # type: t.Callable[t.Tuple[t.Any], str]
):  # type: (...) -> NamedPoints
    """Expand indexes from the source into target names for easier processing of the data (arcs or lines)."""
    combined_data = {}  # type: t.Dict[str, t.Dict[t.Any, t.Set[str]]]

    for covered_path, covered_points in source_data.items():
        combined_points = combined_data.setdefault(covered_path, {})

        for covered_point, covered_target_indexes in covered_points.items():
            combined_point = combined_points.setdefault(format_func(covered_point), set())

            for covered_target_index in covered_target_indexes:
                combined_point.add(source_index[covered_target_index])

    return combined_data


def generate_indexes(target_indexes, data):  # type: (TargetIndexes, NamedPoints) -> IndexedPoints
    """Return an indexed version of the given data (arcs or points)."""
    results = {}  # type: IndexedPoints

    for path, points in data.items():
        result_points = results[path] = {}

        for point, target_names in points.items():
            result_point = result_points[point] = set()

            for target_name in target_names:
                result_point.add(get_target_index(target_name, target_indexes))

    return results
