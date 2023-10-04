#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

# (c) 2020 Red Hat, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
"""CLI tool for reporting on incidental test coverage."""
from __future__ import annotations

# noinspection PyCompatibility
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import hashlib

try:
    # noinspection PyPackageRequirements
    import argcomplete
except ImportError:
    argcomplete = None

# Following changes should be made to improve the overall style:
# TODO use new style formatting method.
# TODO type hints.
# TODO pathlib.


def main():
    """Main program body."""
    args = parse_args()

    try:
        incidental_report(args)
    except ApplicationError as ex:
        sys.exit(ex)


def parse_args():
    """Parse and return args."""
    source = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    parser = argparse.ArgumentParser(description='Report on incidental test coverage downloaded from Azure Pipelines.')

    parser.add_argument('result',
                        type=directory,
                        help='path to directory containing test results downloaded from Azure Pipelines')

    parser.add_argument('--output',
                        type=optional_directory,
                        default=os.path.join(source, 'test', 'results', '.tmp', 'incidental'),
                        help='path to directory where reports should be written')

    parser.add_argument('--source',
                        type=optional_directory,
                        default=source,
                        help='path to git repository containing Ansible source')

    parser.add_argument('--skip-checks',
                        action='store_true',
                        help='skip integrity checks, use only for debugging')

    parser.add_argument('--ignore-cache',
                        dest='use_cache',
                        action='store_false',
                        help='ignore cached files')

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='increase verbosity')

    parser.add_argument('--result-sha',
                        default=None,
                        help='Override the result sha')

    targets = parser.add_mutually_exclusive_group()

    targets.add_argument('--targets',
                         type=regex,
                         default='^incidental_',
                         help='regex for targets to analyze, default: %(default)s')

    targets.add_argument('--plugin-path',
                         help='path to plugin to report incidental coverage on')

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    return args


def optional_directory(value):
    if not os.path.exists(value):
        return value

    return directory(value)


def directory(value):
    if not os.path.isdir(value):
        raise argparse.ArgumentTypeError('"%s" is not a directory' % value)

    return value


def regex(value):
    try:
        return re.compile(value)
    except Exception as ex:
        raise argparse.ArgumentTypeError('"%s" is not a valid regex: %s' % (value, ex))


def incidental_report(args):
    """Generate incidental coverage report."""
    ct = CoverageTool()
    git = Git(os.path.abspath(args.source))
    coverage_data = CoverageData(os.path.abspath(args.result))

    result_sha = args.result_sha or coverage_data.result_sha

    try:
        git.show([result_sha, '--'])
    except subprocess.CalledProcessError:
        raise ApplicationError('%s: commit not found: %s\n'
                               'make sure your source repository is up-to-date' % (git.path, result_sha))

    if coverage_data.result != "succeeded":
        check_failed(args, 'results indicate tests did not pass (result: %s)\n'
                           're-run until passing, then download the latest results and re-run the report using those results' % coverage_data.result)

    if not coverage_data.paths:
        raise ApplicationError('no coverage data found\n'
                               'make sure the downloaded results are from a code coverage run on Azure Pipelines')

    # generate a unique subdirectory in the output directory based on the input files being used
    path_hash = hashlib.sha256(b'\n'.join(p.encode() for p in coverage_data.paths)).hexdigest()
    output_path = os.path.abspath(os.path.join(args.output, path_hash))

    data_path = os.path.join(output_path, 'data')
    reports_path = os.path.join(output_path, 'reports')

    for path in [data_path, reports_path]:
        if not os.path.exists(path):
            os.makedirs(path)

    # combine coverage results into a single file
    combined_path = os.path.join(output_path, 'combined.json')
    cached(combined_path, args.use_cache, args.verbose,
           lambda: ct.combine(coverage_data.paths, combined_path))

    with open(combined_path) as combined_file:
        combined = json.load(combined_file)

    if args.plugin_path:
        # reporting on coverage missing from the test target for the specified plugin
        # the report will be on a single target
        cache_path_format = '%s' + '-for-%s' % os.path.splitext(os.path.basename(args.plugin_path))[0]
        target_pattern = '^%s$' % get_target_name_from_plugin_path(args.plugin_path)
        include_path = args.plugin_path
        missing = True
        target_name = get_target_name_from_plugin_path(args.plugin_path)
    else:
        # reporting on coverage exclusive to the matched targets
        # the report can contain multiple targets
        cache_path_format = '%s'
        target_pattern = args.targets
        include_path = None
        missing = False
        target_name = None

    # identify integration test targets to analyze
    target_names = sorted(combined['targets'])
    incidental_target_names = [target for target in target_names if re.search(target_pattern, target)]

    if not incidental_target_names:
        if target_name:
            # if the plugin has no tests we still want to know what coverage is missing
            incidental_target_names = [target_name]
        else:
            raise ApplicationError('no targets to analyze')

    # exclude test support plugins from analysis
    # also exclude six, which for an unknown reason reports bogus coverage lines (indicating coverage of comments)
    exclude_path = '^(test/support/|lib/ansible/module_utils/six/)'

    # process coverage for each target and then generate a report
    # save sources for generating a summary report at the end
    summary = {}
    report_paths = {}

    for target_name in incidental_target_names:
        cache_name = cache_path_format % target_name

        only_target_path = os.path.join(data_path, 'only-%s.json' % cache_name)
        cached(only_target_path, args.use_cache, args.verbose,
               lambda: ct.filter(combined_path, only_target_path, include_targets=[target_name], include_path=include_path, exclude_path=exclude_path))

        without_target_path = os.path.join(data_path, 'without-%s.json' % cache_name)
        cached(without_target_path, args.use_cache, args.verbose,
               lambda: ct.filter(combined_path, without_target_path, exclude_targets=[target_name], include_path=include_path, exclude_path=exclude_path))

        if missing:
            source_target_path = missing_target_path = os.path.join(data_path, 'missing-%s.json' % cache_name)
            cached(missing_target_path, args.use_cache, args.verbose,
                   lambda: ct.missing(without_target_path, only_target_path, missing_target_path, only_gaps=True))
        else:
            source_target_path = exclusive_target_path = os.path.join(data_path, 'exclusive-%s.json' % cache_name)
            cached(exclusive_target_path, args.use_cache, args.verbose,
                   lambda: ct.missing(only_target_path, without_target_path, exclusive_target_path, only_gaps=True))

        source_expanded_target_path = os.path.join(os.path.dirname(source_target_path), 'expanded-%s' % os.path.basename(source_target_path))
        cached(source_expanded_target_path, args.use_cache, args.verbose,
               lambda: ct.expand(source_target_path, source_expanded_target_path))

        summary[target_name] = sources = collect_sources(source_expanded_target_path, git, coverage_data, result_sha)

        txt_report_path = os.path.join(reports_path, '%s.txt' % cache_name)
        cached(txt_report_path, args.use_cache, args.verbose,
               lambda: generate_report(sources, txt_report_path, coverage_data, target_name, missing=missing))

        report_paths[target_name] = txt_report_path

    # provide a summary report of results
    for target_name in incidental_target_names:
        sources = summary[target_name]
        report_path = os.path.relpath(report_paths[target_name])

        print('%s: %d arcs, %d lines, %d files - %s' % (
            target_name,
            sum(len(s.covered_arcs) for s in sources),
            sum(len(s.covered_lines) for s in sources),
            len(sources),
            report_path,
        ))

    if not missing:
        sys.stderr.write('NOTE: This report shows only coverage exclusive to the reported targets. '
                         'As targets are removed, exclusive coverage on the remaining targets will increase.\n')


def get_target_name_from_plugin_path(path):  # type: (str) -> str
    """Return the integration test target name for the given plugin path."""
    parts = os.path.splitext(path)[0].split(os.path.sep)
    plugin_name = parts[-1]

    if path.startswith('lib/ansible/modules/'):
        plugin_type = None
    elif path.startswith('lib/ansible/plugins/'):
        plugin_type = parts[3]
    elif path.startswith('lib/ansible/module_utils/'):
        plugin_type = parts[2]
    elif path.startswith('plugins/'):
        plugin_type = parts[1]
    else:
        raise ApplicationError('Cannot determine plugin type from plugin path: %s' % path)

    if plugin_type is None:
        target_name = plugin_name
    else:
        target_name = '%s_%s' % (plugin_type, plugin_name)

    return target_name


class CoverageData:
    def __init__(self, result_path):
        with open(os.path.join(result_path, 'run.json')) as run_file:
            run = json.load(run_file)

        self.result_sha = run["resources"]["repositories"]["self"]["version"]
        self.result = run['result']

        self.github_base_url = 'https://github.com/ansible/ansible/blob/%s/' % self.result_sha

        # locate available results
        self.paths = sorted(glob.glob(os.path.join(result_path, '*', 'coverage-analyze-targets.json')))


class Git:
    def __init__(self, path):
        self.git = 'git'
        self.path = path

        try:
            self.show()
        except subprocess.CalledProcessError:
            raise ApplicationError('%s: not a git repository' % path)

    def show(self, args=None):
        return self.run(['show'] + (args or []))

    def run(self, command):
        return subprocess.check_output([self.git] + command, cwd=self.path)


class CoverageTool:
    def __init__(self):
        self.analyze_cmd = ['ansible-test', 'coverage', 'analyze', 'targets']

    def combine(self, input_paths, output_path):
        subprocess.check_call(self.analyze_cmd + ['combine'] + input_paths + [output_path])

    def filter(self, input_path, output_path, include_targets=None, exclude_targets=None, include_path=None, exclude_path=None):
        args = []

        if include_targets:
            for target in include_targets:
                args.extend(['--include-target', target])

        if exclude_targets:
            for target in exclude_targets:
                args.extend(['--exclude-target', target])

        if include_path:
            args.extend(['--include-path', include_path])

        if exclude_path:
            args.extend(['--exclude-path', exclude_path])

        subprocess.check_call(self.analyze_cmd + ['filter', input_path, output_path] + args)

    def missing(self, from_path, to_path, output_path, only_gaps=False):
        args = []

        if only_gaps:
            args.append('--only-gaps')

        subprocess.check_call(self.analyze_cmd + ['missing', from_path, to_path, output_path] + args)

    def expand(self, input_path, output_path):
        subprocess.check_call(self.analyze_cmd + ['expand', input_path, output_path])


class SourceFile:
    def __init__(self, path, source, coverage_data, coverage_points):
        self.path = path
        self.lines = source.decode().splitlines()
        self.coverage_data = coverage_data
        self.coverage_points = coverage_points
        self.github_url = coverage_data.github_base_url + path

        is_arcs = ':' in dict(coverage_points).popitem()[0]

        if is_arcs:
            parse = parse_arc
        else:
            parse = int

        self.covered_points = set(parse(v) for v in coverage_points)
        self.covered_arcs = self.covered_points if is_arcs else None
        self.covered_lines = set(abs(p[0]) for p in self.covered_points) | set(abs(p[1]) for p in self.covered_points)


def collect_sources(data_path, git, coverage_data, result_sha):
    with open(data_path) as data_file:
        data = json.load(data_file)

    sources = []

    for path_coverage in data.values():
        for path, path_data in path_coverage.items():
            sources.append(SourceFile(path, git.show(['%s:%s' % (result_sha, path)]), coverage_data, path_data))

    return sources


def generate_report(sources, report_path, coverage_data, target_name, missing):
    output = [
        'Target: %s (%s coverage)' % (target_name, 'missing' if missing else 'exclusive'),
        'GitHub: %stest/integration/targets/%s' % (coverage_data.github_base_url, target_name),
    ]

    for source in sources:
        if source.covered_arcs:
            output.extend([
                '',
                'Source: %s (%d arcs, %d/%d lines):' % (source.path, len(source.covered_arcs), len(source.covered_lines), len(source.lines)),
                'GitHub: %s' % source.github_url,
                '',
            ])
        else:
            output.extend([
                '',
                'Source: %s (%d/%d lines):' % (source.path, len(source.covered_lines), len(source.lines)),
                'GitHub: %s' % source.github_url,
                '',
            ])

        last_line_no = 0

        for line_no, line in enumerate(source.lines, start=1):
            if line_no not in source.covered_lines:
                continue

            if last_line_no and last_line_no != line_no - 1:
                output.append('')

            notes = ''

            if source.covered_arcs:
                from_lines = sorted(p[0] for p in source.covered_points if abs(p[1]) == line_no)
                to_lines = sorted(p[1] for p in source.covered_points if abs(p[0]) == line_no)

                if from_lines:
                    notes += '  ### %s -> (here)' % ', '.join(str(from_line) for from_line in from_lines)

                if to_lines:
                    notes += '  ### (here) -> %s' % ', '.join(str(to_line) for to_line in to_lines)

            output.append('%4d  %s%s' % (line_no, line, notes))
            last_line_no = line_no

    with open(report_path, 'w') as report_file:
        report_file.write('\n'.join(output) + '\n')


def parse_arc(value):
    return tuple(int(v) for v in value.split(':'))


def cached(path, use_cache, show_messages, func):
    if os.path.exists(path) and use_cache:
        if show_messages:
            sys.stderr.write('%s: cached\n' % path)
            sys.stderr.flush()
        return

    if show_messages:
        sys.stderr.write('%s: generating ... ' % path)
        sys.stderr.flush()

    func()

    if show_messages:
        sys.stderr.write('done\n')
        sys.stderr.flush()


def check_failed(args, message):
    if args.skip_checks:
        sys.stderr.write('WARNING: %s\n' % message)
        return

    raise ApplicationError(message)


class ApplicationError(Exception):
    pass


if __name__ == '__main__':
    main()
